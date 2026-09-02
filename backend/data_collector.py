"""Scheduled Data Collection Service for PowerFlex BD.

Provides background data collection from PGCB and other sources.
Implements proper deduplication, retry logic, and health tracking.

Key principle: NEVER fabricate data. Only collect what is actually available.
"""

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from threading import Thread, Lock, Event

logger = logging.getLogger("powerflex.data_collector")


# =========================================================
# DATA COLLECTION CONFIGURATION
# =========================================================

# PGCB updates roughly every 15-60 minutes
# Polling every 10 minutes is reasonable to catch updates
DEFAULT_POLL_INTERVAL_SECONDS = 600  # 10 minutes

# Minimum interval between requests to same source (rate limiting)
MIN_REQUEST_INTERVAL_SECONDS = 60  # 1 minute minimum

# Maximum consecutive failures before backing off
MAX_CONSECUTIVE_FAILURES = 5

# Backoff multiplier after consecutive failures
BACKOFF_MULTIPLIER = 2.0

# Maximum backoff interval (1 hour)
MAX_BACKOFF_SECONDS = 3600


# =========================================================
# DATA COLLECTION STATUS
# =========================================================

@dataclass
class SourceStatus:
    """Status of a data collection source."""
    source_name: str
    status: str = "UNKNOWN"  # LIVE, STALE, ERROR, NOT_CONFIGURED
    last_successful_fetch: Optional[str] = None
    last_attempt: Optional[str] = None
    records_collected: int = 0
    consecutive_failures: int = 0
    total_failures: int = 0
    total_successes: int = 0
    latest_observation: Optional[str] = None
    error_message: Optional[str] = None
    next_fetch_after: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_name": self.source_name,
            "status": self.status,
            "last_successful_fetch": self.last_successful_fetch,
            "last_attempt": self.last_attempt,
            "records_collected": self.records_collected,
            "consecutive_failures": self.consecutive_failures,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "latest_observation": self.latest_observation,
            "error_message": self.error_message,
            "next_fetch_after": self.next_fetch_after,
        }


# =========================================================
# DEDUPLICATION LOGIC
# =========================================================

class DeduplicationTracker:
    """Track recent observations to prevent duplicates.
    
    Uses demand+supply value matching within a time window
    to catch rapid polling of the same PGCB data.
    """
    
    def __init__(self, window_minutes: int = 30):
        self.window_minutes = window_minutes
        self._recent: List[Dict[str, Any]] = []
        self._lock = Lock()
    
    def is_duplicate(
        self,
        pgcb_timestamp: str,
        demand_mw: float,
        supply_mw: float,
    ) -> bool:
        """Check if this observation is a duplicate.
        
        A record is considered duplicate if:
        1. Same demand_mw AND supply_mw (within rounding)
        2. Within the time window of an existing record
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(minutes=self.window_minutes)
            
            # Clean old entries
            self._recent = [
                r for r in self._recent
                if datetime.fromisoformat(r["timestamp"]) > cutoff
            ]
            
            # Check for duplicates
            for record in self._recent:
                if (abs(record["demand_mw"] - demand_mw) < 0.1 and
                    abs(record["supply_mw"] - supply_mw) < 0.1):
                    logger.debug(
                        "Duplicate detected: demand=%.1f, supply=%.1f",
                        demand_mw, supply_mw,
                    )
                    return True
            
            # Record this observation
            self._recent.append({
                "timestamp": now.isoformat(),
                "pgcb_timestamp": pgcb_timestamp,
                "demand_mw": demand_mw,
                "supply_mw": supply_mw,
            })
            
            return False
    
    def clear(self):
        """Clear the deduplication tracker."""
        with self._lock:
            self._recent.clear()


# =========================================================
# DATA COLLECTION SERVICE
# =========================================================

class DataCollectionService:
    """Background data collection service for PGCB and other sources."""
    
    def __init__(
        self,
        poll_interval_seconds: int = DEFAULT_POLL_INTERVAL_SECONDS,
    ):
        self.poll_interval = poll_interval_seconds
        self._running = Event()
        self._thread: Optional[Thread] = None
        self._lock = Lock()
        
        # Source statuses
        self.sources: Dict[str, SourceStatus] = {
            "PGCB_DEMAND_SUPPLY": SourceStatus("PGCB_DEMAND_SUPPLY"),
            "PGCB_GENERATION": SourceStatus("PGCB_GENERATION"),
        }
        
        # Deduplication
        self._dedup = DeduplicationTracker(window_minutes=30)
        
        # Collection statistics
        self._started_at: Optional[datetime] = None
        self._collection_count: int = 0
    
    def start(self):
        """Start the background collection service."""
        if self._thread and self._thread.is_alive():
            logger.warning("Data collection service already running")
            return
        
        self._running.set()
        self._started_at = datetime.now(timezone.utc)
        self._thread = Thread(
            target=self._collection_loop,
            daemon=True,
            name="data-collector",
        )
        self._thread.start()
        logger.info(
            "Data collection service started (interval=%ds)",
            self.poll_interval,
        )
    
    def stop(self):
        """Stop the background collection service."""
        self._running.clear()
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("Data collection service stopped")
    
    def _collection_loop(self):
        """Main collection loop with exponential backoff."""
        consecutive_failures = 0

        while self._running.is_set():
            try:
                self._collect_once()
                consecutive_failures = 0
            except Exception as e:
                logger.error("Collection cycle failed: %s", e, exc_info=True)
                consecutive_failures += 1

            # Calculate sleep interval with backoff
            sleep_seconds = self.poll_interval
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                backoff = min(
                    self.poll_interval * (
                        BACKOFF_MULTIPLIER ** (
                            consecutive_failures - MAX_CONSECUTIVE_FAILURES + 1
                        )
                    ),
                    MAX_BACKOFF_SECONDS,
                )
                sleep_seconds = int(backoff)
                logger.warning(
                    "Backing off after %d consecutive failures: "
                    "sleeping for %ds",
                    consecutive_failures, sleep_seconds,
                )

            # Wait for next cycle or stop signal
            self._running.wait(timeout=sleep_seconds)
    
    def _collect_once(self):
        """Perform one collection cycle.
        
        Returns a structured result for each source collected.
        """
        logger.debug("Starting collection cycle")
        results = {}
        
        # Collect from PGCB demand/supply
        results["demand_supply"] = self._collect_pgcb_demand_supply()
        
        # Collect from PGCB generation
        results["generation"] = self._collect_pgcb_generation()
        
        self._collection_count += 1
        logger.debug("Collection cycle %d complete", self._collection_count)
        return results
    
    def _validate_grid_data(
        self,
        demand_mw: float,
        supply_mw: float,
        load_shedding_mw: float,
    ) -> list:
        """Validate grid data for physical plausibility.
        
        Returns list of validation issues (empty = valid).
        Does NOT reject data — only flags issues.
        """
        issues = []
        
        if demand_mw < 0:
            issues.append("NEGATIVE_DEMAND")
        if supply_mw < 0:
            issues.append("NEGATIVE_SUPPLY")
        if load_shedding_mw < 0:
            issues.append("NEGATIVE_LOAD_SHEDDING")
        
        # Physical plausibility: Bangladesh demand range
        if demand_mw > 0 and demand_mw < 3000:
            issues.append("BELOW_PLAUSIBLE_DEMAND")
        if demand_mw > 25000:
            issues.append("ABOVE_PLAUSIBLE_DEMAND")
        
        # Logical consistency: demand should be roughly supply + load_shedding
        if demand_mw > 0 and supply_mw > 0:
            expected_gap = demand_mw - supply_mw
            actual_gap = load_shedding_mw
            if abs(expected_gap - actual_gap) > demand_mw * 0.3:
                issues.append("DEMAND_SUPPLY_MISMATCH")
        
        return issues

    def _collect_pgcb_demand_supply(self):
        """Collect demand/supply data from PGCB.
        
        Returns structured collection result.
        """
        source = self.sources["PGCB_DEMAND_SUPPLY"]
        source.last_attempt = datetime.now(timezone.utc).isoformat()
        
        try:
            from backend.grid import fetch_pgcb_demand_supply
            
            result = fetch_pgcb_demand_supply()
            
            if not result.get("connected"):
                source.consecutive_failures += 1
                source.total_failures += 1
                source.status = "ERROR"
                source.error_message = result.get("message", "Connection failed")
                logger.warning(
                    "PGCB demand/supply fetch failed: %s",
                    source.error_message,
                )
                return {
                    "success": False,
                    "collected": False,
                    "reason": "PGCB_UNAVAILABLE",
                    "detail": source.error_message,
                }
            
            data = result.get("data", {})
            if not data:
                source.consecutive_failures += 1
                source.total_failures += 1
                source.status = "ERROR"
                source.error_message = "No data in response"
                return {
                    "success": False,
                    "collected": False,
                    "reason": "NO_DATA",
                }
            
            # Extract values
            demand_mw = data.get("current_demand_mw")
            supply_mw = data.get("current_supply_mw")
            pgcb_timestamp = data.get("timestamp")
            
            if demand_mw is None or supply_mw is None:
                source.consecutive_failures += 1
                source.total_failures += 1
                source.status = "ERROR"
                source.error_message = "Missing demand or supply values"
                return {
                    "success": False,
                    "collected": False,
                    "reason": "MISSING_VALUES",
                }
            
            # Validate data
            load_shedding_mw = data.get("load_shedding_mw", 0) or 0
            validation_issues = self._validate_grid_data(
                demand_mw, supply_mw, load_shedding_mw,
            )
            
            # Check for duplicates
            if self._dedup.is_duplicate(pgcb_timestamp, demand_mw, supply_mw):
                logger.debug("Skipping duplicate observation")
                source.total_successes += 1
                return {
                    "success": True,
                    "collected": False,
                    "duplicate": True,
                    "reason": "DUPLICATE",
                }
            
            # Store the observation
            store_result = self._store_observation(
                pgcb_timestamp=pgcb_timestamp,
                demand_mw=demand_mw,
                supply_mw=supply_mw,
                load_shedding_mw=load_shedding_mw,
                deficit_mw=data.get("deficit_mw", 0) or 0,
            )
            
            if store_result:
                source.consecutive_failures = 0
                source.total_successes += 1
                source.records_collected += 1
                source.status = "LIVE"
                source.last_successful_fetch = datetime.now(timezone.utc).isoformat()
                source.latest_observation = pgcb_timestamp
                source.error_message = None
                logger.info(
                    "PGCB observation collected: demand=%.1f MW, supply=%.1f MW",
                    demand_mw, supply_mw,
                )
                return {
                    "success": True,
                    "collected": True,
                    "duplicate": False,
                    "timestamp": pgcb_timestamp,
                    "demand_mw": demand_mw,
                    "supply_mw": supply_mw,
                    "validation_issues": validation_issues,
                    "quality_status": "VALID" if not validation_issues else "WARNING",
                }
            else:
                source.consecutive_failures += 1
                source.total_failures += 1
                source.status = "ERROR"
                source.error_message = "Failed to store observation"
                return {
                    "success": False,
                    "collected": False,
                    "reason": "DATABASE_ERROR",
                }
                
        except Exception as e:
            source.consecutive_failures += 1
            source.total_failures += 1
            source.status = "ERROR"
            source.error_message = str(e)
            logger.error("PGCB collection error: %s", e, exc_info=True)
            return {
                "success": False,
                "collected": False,
                "reason": "EXCEPTION",
                "detail": str(e),
            }
    
    def _collect_pgcb_generation(self):
        """Collect generation data from PGCB and store to GridSnapshot.
        
        Returns structured collection result.
        """
        source = self.sources["PGCB_GENERATION"]
        source.last_attempt = datetime.now(timezone.utc).isoformat()
        
        try:
            from backend.grid import fetch_pgcb_generation
            
            result = fetch_pgcb_generation()
            
            if not result.get("connected"):
                source.consecutive_failures += 1
                source.total_failures += 1
                source.status = "ERROR"
                source.error_message = result.get("message", "Connection failed")
                return {
                    "success": False,
                    "collected": False,
                    "reason": "PGCB_UNAVAILABLE",
                    "detail": source.error_message,
                }
            
            data = result.get("data", {})
            if not data:
                source.consecutive_failures += 1
                source.total_failures += 1
                source.status = "ERROR"
                source.error_message = "No data in response"
                return {
                    "success": False,
                    "collected": False,
                    "reason": "NO_DATA",
                }
            
            # Store generation snapshot
            store_result = self._store_generation_snapshot(data)
            
            source.consecutive_failures = 0
            source.total_successes += 1
            source.status = "LIVE"
            source.last_successful_fetch = datetime.now(timezone.utc).isoformat()
            
            return {
                "success": True,
                "collected": store_result,
                "timestamp": data.get("timestamp"),
            }
                
        except Exception as e:
            source.consecutive_failures += 1
            source.total_failures += 1
            source.status = "ERROR"
            source.error_message = str(e)
            logger.error("PGCB generation collection error: %s", e, exc_info=True)
            return {
                "success": False,
                "collected": False,
                "reason": "EXCEPTION",
                "detail": str(e),
            }
    
    def _store_generation_snapshot(self, gen_data: dict) -> bool:
        """Store generation breakdown to GridSnapshot."""
        try:
            from database.connection import get_session
            from database.models import GridSnapshot
            from backend.grid import log_grid_snapshot
            
            timestamp = gen_data.get("timestamp", "")
            breakdown = gen_data.get("generation_breakdown", {})
            imports = gen_data.get("imports", {})
            
            # Use log_grid_snapshot which handles dedup by timestamp
            return log_grid_snapshot(
                timestamp=timestamp,
                demand_mw=None,  # Not available from generation endpoint
                supply_mw=None,
                gas_mw=breakdown.get("gas_mw"),
                liquid_fuel_mw=breakdown.get("liquid_fuel_mw"),
                coal_mw=breakdown.get("coal_mw"),
                hydro_mw=breakdown.get("hydro_mw"),
                solar_mw=breakdown.get("solar_mw"),
                wind_mw=breakdown.get("wind_mw"),
                hvdc_mw=imports.get("india_bheramara_hvdc_mw"),
                import_mw=imports.get("total_imports_mw"),
            )
            
        except Exception as e:
            logger.error("Failed to store generation snapshot: %s", e)
            return False
    
    def _store_observation(
        self,
        pgcb_timestamp: str,
        demand_mw: float,
        supply_mw: float,
        load_shedding_mw: float,
        deficit_mw: float,
    ) -> bool:
        """Store an observation in the database."""
        try:
            from backend.demand_history import log_pgcb_observation
            
            return log_pgcb_observation(
                pgcb_timestamp=pgcb_timestamp,
                demand_mw=demand_mw,
                supply_mw=supply_mw,
                load_shedding_mw=load_shedding_mw,
                deficit_mw=deficit_mw,
                source="PGCB_ERP",
            )
            
        except Exception as e:
            logger.error("Failed to store observation: %s", e)
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the data collection service."""
        return {
            "running": self._running.is_set(),
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "poll_interval_seconds": self.poll_interval,
            "collection_count": self._collection_count,
            "sources": {
                name: status.to_dict()
                for name, status in self.sources.items()
            },
            "dedup_tracker_size": len(self._dedup._recent),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    def trigger_collection(self) -> Dict[str, Any]:
        """Manually trigger a collection cycle.
        
        Returns structured results for each source.
        """
        logger.info("Manual collection triggered")
        results = self._collect_once()
        status = self.get_status()
        status["collection_results"] = results
        return status


# =========================================================
# SINGLETON INSTANCE
# =========================================================

_collector_instance: Optional[DataCollectionService] = None
_collector_lock = Lock()


def get_data_collector() -> DataCollectionService:
    """Get or create the singleton data collection service."""
    global _collector_instance
    with _collector_lock:
        if _collector_instance is None:
            poll_interval = int(
                os.getenv("PGCB_POLL_INTERVAL_SECONDS", str(DEFAULT_POLL_INTERVAL_SECONDS))
            )
            _collector_instance = DataCollectionService(
                poll_interval_seconds=poll_interval,
            )
        return _collector_instance


def start_data_collection():
    """Start the background data collection service."""
    collector = get_data_collector()
    collector.start()
    return collector.get_status()


def stop_data_collection():
    """Stop the background data collection service."""
    collector = get_data_collector()
    collector.stop()
    return collector.get_status()


def get_collection_status() -> Dict[str, Any]:
    """Get the current data collection status with quality metrics."""
    collector = get_data_collector()
    status = collector.get_status()
    try:
        from backend.demand_history import get_demand_history_quality
        status["demand_history_quality"] = get_demand_history_quality()
    except Exception:
        status["demand_history_quality"] = {
            "raw_records": 0,
            "independent_observations": 0,
            "duplicates": 0,
            "duplicate_rate": 0.0,
        }
    return status


def trigger_collection() -> Dict[str, Any]:
    """Manually trigger a data collection cycle."""
    collector = get_data_collector()
    return collector.trigger_collection()
