"""Historical Data Ingestion for PowerFlex BD v3.

Provides legitimate Bangladesh electricity data ingestion from
verified sources. Each source must be independently verified
before being marked as ACTIVE.

NEVER fabricate historical data.
NEVER invent data that doesn't exist.
"""

import csv
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("powerflex.historical_data")

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# =========================================================
# BANGLADESH TIMEZONE
# =========================================================

BST = timezone(timedelta(hours=6))


# =========================================================
# HISTORICAL DATA MODELS
# =========================================================

@dataclass
class HistoricalDemandRecord:
    """Normalized historical demand record."""
    timestamp_utc: datetime
    timestamp_local: datetime
    demand_mw: float
    supply_mw: Optional[float] = None
    load_shedding_mw: Optional[float] = None
    deficit_mw: Optional[float] = None
    source_id: str = "unknown"
    quality_flag: str = "GOOD"
    is_interpolated: bool = False
    is_estimated: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp_utc": self.timestamp_utc.isoformat(),
            "timestamp_local": self.timestamp_local.isoformat(),
            "demand_mw": self.demand_mw,
            "supply_mw": self.supply_mw,
            "load_shedding_mw": self.load_shedding_mw,
            "deficit_mw": self.deficit_mw,
            "source_id": self.source_id,
            "quality_flag": self.quality_flag,
            "is_interpolated": self.is_interpolated,
            "is_estimated": self.is_estimated,
        }


@dataclass
class HistoricalSupplyRecord:
    """Normalized historical supply record."""
    timestamp_utc: datetime
    timestamp_local: datetime
    supply_mw: float
    gas_mw: Optional[float] = None
    coal_mw: Optional[float] = None
    oil_mw: Optional[float] = None
    hydro_mw: Optional[float] = None
    solar_mw: Optional[float] = None
    wind_mw: Optional[float] = None
    import_mw: Optional[float] = None
    other_mw: Optional[float] = None
    source_id: str = "unknown"
    quality_flag: str = "GOOD"
    is_estimated: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp_utc": self.timestamp_utc.isoformat(),
            "timestamp_local": self.timestamp_local.isoformat(),
            "supply_mw": self.supply_mw,
            "gas_mw": self.gas_mw,
            "coal_mw": self.coal_mw,
            "oil_mw": self.oil_mw,
            "hydro_mw": self.hydro_mw,
            "solar_mw": self.solar_mw,
            "wind_mw": self.wind_mw,
            "import_mw": self.import_mw,
            "other_mw": self.other_mw,
            "source_id": self.source_id,
            "quality_flag": self.quality_flag,
            "is_estimated": self.is_estimated,
        }


# =========================================================
# DATA QUALITY VALIDATION
# =========================================================

class HistoricalDataValidator:
    """Validates historical data records for quality issues."""

    BANGLADESH_DEMAND_MIN_MW = 3000
    BANGLADESH_DEMAND_MAX_MW = 20000
    BANGLADESH_SUPPLY_MIN_MW = 3000
    BANGLADESH_SUPPLY_MAX_MW = 25000

    @classmethod
    def validate_demand(cls, record: HistoricalDemandRecord) -> List[str]:
        """Validate a demand record. Returns list of issues."""
        issues = []

        if record.demand_mw < 0:
            issues.append("NEGATIVE_DEMAND")

        if record.demand_mw < cls.BANGLADESH_DEMAND_MIN_MW:
            issues.append("BELOW_MIN_DEMAND")

        if record.demand_mw > cls.BANGLADESH_DEMAND_MAX_MW:
            issues.append("ABOVE_MAX_DEMAND")

        if record.load_shedding_mw is not None and record.load_shedding_mw < 0:
            issues.append("NEGATIVE_LOAD_SHEDDING")

        if record.supply_mw is not None and record.supply_mw < 0:
            issues.append("NEGATIVE_SUPPLY")

        if record.timestamp_utc.tzinfo is None:
            issues.append("NAIVE_UTC_TIMESTAMP")

        if record.timestamp_local.hour < 0 or record.timestamp_local.hour > 23:
            issues.append("INVALID_LOCAL_HOUR")

        return issues

    @classmethod
    def validate_supply(cls, record: HistoricalSupplyRecord) -> List[str]:
        """Validate a supply record. Returns list of issues."""
        issues = []

        if record.supply_mw < 0:
            issues.append("NEGATIVE_SUPPLY")

        if record.supply_mw < cls.BANGLADESH_SUPPLY_MIN_MW:
            issues.append("BELOW_MIN_SUPPLY")

        if record.supply_mw > cls.BANGLADESH_SUPPLY_MAX_MW:
            issues.append("ABOVE_MAX_SUPPLY")

        if record.timestamp_utc.tzinfo is None:
            issues.append("NAIVE_UTC_TIMESTAMP")

        return issues

    @classmethod
    def detect_duplicates(
        cls, records: List[HistoricalDemandRecord]
    ) -> List[int]:
        """Detect duplicate timestamps in demand records."""
        seen = set()
        duplicates = []
        for i, r in enumerate(records):
            key = r.timestamp_utc.isoformat()
            if key in seen:
                duplicates.append(i)
            seen.add(key)
        return duplicates

    @classmethod
    def detect_gaps(
        cls,
        records: List[HistoricalDemandRecord],
        expected_interval_minutes: int = 60,
    ) -> List[Dict[str, Any]]:
        """Detect missing timestamps in a time series."""
        if len(records) < 2:
            return []

        sorted_records = sorted(records, key=lambda r: r.timestamp_utc)
        gaps = []

        for i in range(1, len(sorted_records)):
            diff = sorted_records[i].timestamp_utc - sorted_records[i - 1].timestamp_utc
            diff_minutes = diff.total_seconds() / 60
            if diff_minutes > expected_interval_minutes * 1.5:
                gaps.append({
                    "after": sorted_records[i - 1].timestamp_utc.isoformat(),
                    "before": sorted_records[i].timestamp_utc.isoformat(),
                    "gap_minutes": diff_minutes,
                })

        return gaps

    @classmethod
    def interpolate_missing(
        cls,
        records: List[HistoricalDemandRecord],
        target_interval_minutes: int = 60,
    ) -> List[HistoricalDemandRecord]:
        """Linearly interpolate missing timestamps.
        
        Marks interpolated records with is_interpolated=True.
        """
        if len(records) < 2:
            return records

        sorted_records = sorted(records, key=lambda r: r.timestamp_utc)
        result = [sorted_records[0]]

        for i in range(1, len(sorted_records)):
            diff = sorted_records[i].timestamp_utc - sorted_records[i - 1].timestamp_utc
            diff_minutes = diff.total_seconds() / 60

            if diff_minutes > target_interval_minutes * 1.5:
                num_missing = int(diff_minutes / target_interval_minutes) - 1
                if num_missing > 0 and num_missing <= 24:
                    for j in range(1, num_missing + 1):
                        fraction = j / (num_missing + 1)
                        interp_ts = sorted_records[i - 1].timestamp_utc + timedelta(
                            minutes=target_interval_minutes * j
                        )
                        interp_local = interp_ts.astimezone(BST)
                        interp_demand = (
                            sorted_records[i - 1].demand_mw +
                            fraction * (sorted_records[i].demand_mw - sorted_records[i - 1].demand_mw)
                        )
                        result.append(HistoricalDemandRecord(
                            timestamp_utc=interp_ts,
                            timestamp_local=interp_local,
                            demand_mw=round(interp_demand, 2),
                            source_id=sorted_records[i].source_id,
                            quality_flag="INTERPOLATED",
                            is_interpolated=True,
                        ))

            result.append(sorted_records[i])

        return result


# =========================================================
# CSV HISTORICAL DATA LOADER
# =========================================================

class CSVHistoricalDataLoader:
    """Load historical data from CSV files."""

    @staticmethod
    def load_demand_csv(
        filepath: str,
        source_id: str = "csv_import",
        demand_column: str = "demand_mw",
        timestamp_column: str = "timestamp",
    ) -> List[HistoricalDemandRecord]:
        """Load demand data from a CSV file.
        
        Expected format:
        - timestamp column in ISO format or common datetime format
        - demand_mw column with numeric values
        """
        records = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        ts_str = row[timestamp_column]
                        demand = float(row[demand_column])

                        # Parse timestamp
                        if "T" in ts_str:
                            ts_utc = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        else:
                            ts_utc = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                            ts_utc = ts_utc.replace(tzinfo=timezone.utc)

                        ts_local = ts_utc.astimezone(BST)

                        records.append(HistoricalDemandRecord(
                            timestamp_utc=ts_utc,
                            timestamp_local=ts_local,
                            demand_mw=demand,
                            source_id=source_id,
                            quality_flag="IMPORTED",
                        ))
                    except (ValueError, KeyError) as e:
                        logger.warning("Skipping row: %s", e)
                        continue

            logger.info("Loaded %d demand records from %s", len(records), filepath)
        except Exception as e:
            logger.error("Failed to load demand CSV %s: %s", filepath, e)

        return records

    @staticmethod
    def load_supply_csv(
        filepath: str,
        source_id: str = "csv_import",
    ) -> List[HistoricalSupplyRecord]:
        """Load supply data from a CSV file."""
        records = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        ts_str = row.get("timestamp", "")
                        supply = float(row.get("supply_mw", 0))

                        if "T" in ts_str:
                            ts_utc = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        else:
                            ts_utc = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                            ts_utc = ts_utc.replace(tzinfo=timezone.utc)

                        ts_local = ts_utc.astimezone(BST)

                        records.append(HistoricalSupplyRecord(
                            timestamp_utc=ts_utc,
                            timestamp_local=ts_local,
                            supply_mw=supply,
                            gas_mw=float(row.get("gas_mw", 0) or 0),
                            coal_mw=float(row.get("coal_mw", 0) or 0),
                            oil_mw=float(row.get("oil_mw", 0) or 0),
                            hydro_mw=float(row.get("hydro_mw", 0) or 0),
                            solar_mw=float(row.get("solar_mw", 0) or 0),
                            wind_mw=float(row.get("wind_mw", 0) or 0),
                            import_mw=float(row.get("import_mw", 0) or 0),
                            source_id=source_id,
                            quality_flag="IMPORTED",
                        ))
                    except (ValueError, KeyError) as e:
                        logger.warning("Skipping row: %s", e)
                        continue

            logger.info("Loaded %d supply records from %s", len(records), filepath)
        except Exception as e:
            logger.error("Failed to load supply CSV %s: %s", filepath, e)

        return records


# =========================================================
# PGCB DEMAND HISTORY LOADER
# =========================================================

def load_pgcb_demand_history() -> List[HistoricalDemandRecord]:
    """Load existing PGCB demand history from data/pgcb_demand_history.csv."""
    csv_path = PROJECT_ROOT / "data" / "pgcb_demand_history.csv"
    if not csv_path.exists():
        logger.warning("PGCB demand history not found: %s", csv_path)
        return []

    return CSVHistoricalDataLoader.load_demand_csv(
        str(csv_path),
        source_id="pgcb_erp",
        demand_column="demand_mw",
        timestamp_column="timestamp",
    )


# =========================================================
# DATA FRESHNESS CHECK
# =========================================================

def assess_data_freshness(
    records: List[HistoricalDemandRecord],
    max_age_hours: float = 24.0,
) -> Dict[str, Any]:
    """Assess the freshness of historical data."""
    if not records:
        return {
            "status": "EMPTY",
            "record_count": 0,
            "latest_timestamp": None,
            "age_hours": None,
            "freshness": "UNAVAILABLE",
        }

    latest = max(records, key=lambda r: r.timestamp_utc)
    now = datetime.now(timezone.utc)
    age = now - latest.timestamp_utc
    age_hours = age.total_seconds() / 3600

    if age_hours < 2:
        freshness = "FRESH"
    elif age_hours < 6:
        freshness = "RECENT"
    elif age_hours < max_age_hours:
        freshness = "STALE"
    else:
        freshness = "OLD"

    return {
        "status": "OK",
        "record_count": len(records),
        "latest_timestamp": latest.timestamp_utc.isoformat(),
        "age_hours": round(age_hours, 1),
        "freshness": freshness,
        "quality_summary": _summarize_quality(records),
    }


def _summarize_quality(records: List[HistoricalDemandRecord]) -> Dict[str, int]:
    """Summarize quality flags in records."""
    quality_counts: Dict[str, int] = {}
    for r in records:
        quality_counts[r.quality_flag] = quality_counts.get(r.quality_flag, 0) + 1
    return quality_counts
