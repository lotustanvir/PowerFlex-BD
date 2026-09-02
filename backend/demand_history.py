import csv
import io
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from database.connection import get_session
from database.models import DemandHistory

logger = logging.getLogger("powerflex.demand_history")


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/api/demand",
    tags=["Demand History"],
)


# =========================================================
# PROJECT ROOT (for CSV backup reference only)
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HISTORY_FILE = PROJECT_ROOT / "data" / "pgcb_demand_history.csv"


# =========================================================
# DUPLICATE CHECK (PostgreSQL)
# =========================================================

def is_duplicate(
    pgcb_timestamp: str,
    demand_mw: float,
    supply_mw: float,
) -> bool:
    """Check if this observation is a rapid-polling duplicate.

    Matches on demand_mw + supply_mw within a 30-minute window
    rather than pgcb_timestamp, because PGCB returns sub-second
    timestamp variations on each poll that prevent exact timestamp
    matching.
    """
    try:
        session = get_session()
        try:
            # Look back 30 minutes from now for matching values
            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(minutes=30)

            existing = (
                session.query(DemandHistory)
                .filter(
                    DemandHistory.demand_mw
                    == round(demand_mw, 1),
                    DemandHistory.supply_mw
                    == round(supply_mw, 1),
                    DemandHistory.timestamp >= cutoff,
                )
                .first()
            )
            return existing is not None
        finally:
            session.close()

    except Exception as e:
        logger.warning(
            "Duplicate check failed (DB unavailable): %s", e
        )
        return False


# =========================================================
# APPEND RECORD (PostgreSQL)
# =========================================================

def log_pgcb_observation(
    pgcb_timestamp: str,
    demand_mw: float,
    supply_mw: float,
    load_shedding_mw: float,
    deficit_mw: float,
    source: str = "PGCB_ERP",
) -> bool:

    if demand_mw is None or supply_mw is None:
        return False

    if is_duplicate(
        pgcb_timestamp, demand_mw, supply_mw
    ):
        return False

    try:
        session = get_session()
        try:
            observation = DemandHistory(
                timestamp=datetime.now(timezone.utc),
                pgcb_timestamp=pgcb_timestamp,
                demand_mw=round(demand_mw, 1),
                supply_mw=round(supply_mw, 1),
                load_shedding_mw=(
                    round(load_shedding_mw, 1)
                    if load_shedding_mw
                    else 0.0
                ),
                deficit_mw=round(deficit_mw, 1),
                source=source,
                data_classification="OFFICIAL_PGCB",
            )
            session.add(observation)
            session.commit()
            logger.info(
                "PGCB observation recorded: %s",
                pgcb_timestamp,
            )
            return True

        except Exception as e:
            session.rollback()
            logger.error(
                "Failed to record PGCB observation: %s", e
            )
            return False

        finally:
            session.close()

    except Exception as e:
        logger.error(
            "Database unavailable for PGCB observation: %s", e
        )
        return False


# =========================================================
# READ HISTORY (PostgreSQL)
# =========================================================

def read_history() -> list:

    try:
        session = get_session()
        try:
            records = (
                session.query(DemandHistory)
                .order_by(DemandHistory.timestamp.asc())
                .all()
            )

            return [
                {
                    "timestamp": (
                        r.timestamp.isoformat()
                        if r.timestamp else None
                    ),
                    "pgcb_timestamp": (
                        r.pgcb_timestamp.isoformat()
                        if r.pgcb_timestamp else None
                    ),
                    "demand_mw": (
                        float(r.demand_mw)
                        if r.demand_mw else None
                    ),
                    "supply_mw": (
                        float(r.supply_mw)
                        if r.supply_mw else None
                    ),
                    "load_shedding_mw": (
                        float(r.load_shedding_mw)
                        if r.load_shedding_mw else None
                    ),
                    "deficit_mw": (
                        float(r.deficit_mw)
                        if r.deficit_mw else None
                    ),
                    "source": r.source,
                    "data_classification": (
                        r.data_classification
                    ),
                }
                for r in records
            ]

        finally:
            session.close()

    except Exception as e:
        logger.warning(
            "Failed to read history from DB: %s", e
        )
        return []


# =========================================================
# COUNT RECORDS (PostgreSQL)
# =========================================================

def count_records() -> int:
    """Count ALL rows in demand_history (including duplicates).

    Use count_unique_observations() for forecast gate decisions.
    """
    try:
        session = get_session()
        try:
            return session.query(DemandHistory).count()
        finally:
            session.close()

    except Exception as e:
        logger.warning(
            "Failed to count records from DB: %s", e
        )
        return 0


def count_unique_observations() -> int:
    """Count independent grid observations using state-change detection.

    Walks all records chronologically. Consecutive records with
    identical (demand_mw, supply_mw) values represent the same
    underlying PGCB grid state observed via rapid polling — they
    collapse into one independent observation. A state change
    (different values)标志着 a new independent observation.

    PGCB timestamp semantics:
      - For hourly historical rows: pgcb_timestamp is the grid
        observation time (clean hourly marks like 10:00:00).
      - For rapid-polling live rows: pgcb_timestamp is the page
        fetch time (sub-second like 21:11:23.551687), NOT the
        grid measurement time. Multiple fetches within minutes
        show the same grid state with varying page timestamps.
    """
    try:
        session = get_session()
        try:
            records = (
                session.query(DemandHistory)
                .order_by(DemandHistory.timestamp.asc())
                .all()
            )

            if not records:
                return 0

            independent = 1  # First record is always independent
            for i in range(1, len(records)):
                prev = records[i - 1]
                curr = records[i]
                same_demand = (
                    round(float(prev.demand_mw), 1)
                    == round(float(curr.demand_mw), 1)
                )
                same_supply = (
                    round(float(prev.supply_mw), 1)
                    == round(float(curr.supply_mw), 1)
                )
                if not (same_demand and same_supply):
                    independent += 1

            return independent
        finally:
            session.close()

    except Exception as e:
        logger.warning(
            "Failed to count unique observations from DB: %s", e
        )
        return 0


def get_demand_history_quality() -> Dict[str, Any]:
    """Single source of truth for demand history data quality.

    Uses state-change detection to count independent observations.
    Consecutive records with identical (demand_mw, supply_mw) are
    rapid-polling duplicates of the same PGCB grid state and count
    as one observation.

    Returns:
      - raw_records: total rows in database
      - independent_observations: state-change count (used by forecast gate)
      - duplicates: raw_records - independent_observations
      - duplicate_rate: duplicates / raw_records
      - time_coverage_hours: span from earliest to latest record
      - largest_gap_minutes: largest time gap between consecutive records
      - avg_interval_minutes: average interval between consecutive records
      - hourly_aligned_count: records at minute=0, second=0 (clean hourly marks)
    """
    try:
        session = get_session()
        try:
            records = (
                session.query(DemandHistory)
                .order_by(DemandHistory.timestamp.asc())
                .all()
            )

            if not records:
                return {
                    "raw_records": 0,
                    "independent_observations": 0,
                    "duplicates": 0,
                    "duplicate_rate": 0.0,
                    "time_coverage_hours": 0.0,
                    "largest_gap_minutes": 0.0,
                    "avg_interval_minutes": 0.0,
                    "hourly_aligned_count": 0,
                }

            raw_count = len(records)

            # State-change detection: walk chronologically
            independent = 1
            for i in range(1, len(records)):
                prev = records[i - 1]
                curr = records[i]
                same_demand = (
                    round(float(prev.demand_mw), 1)
                    == round(float(curr.demand_mw), 1)
                )
                same_supply = (
                    round(float(prev.supply_mw), 1)
                    == round(float(curr.supply_mw), 1)
                )
                if not (same_demand and same_supply):
                    independent += 1

            # Time coverage
            timestamps = [
                r.timestamp for r in records
                if r.timestamp is not None
            ]
            time_coverage_hours = 0.0
            largest_gap_minutes = 0.0
            avg_interval_minutes = 0.0

            if len(timestamps) >= 2:
                span = timestamps[-1] - timestamps[0]
                time_coverage_hours = (
                    span.total_seconds() / 3600
                )

                intervals = []
                for i in range(1, len(timestamps)):
                    delta = (
                        timestamps[i] - timestamps[i - 1]
                    )
                    interval_min = delta.total_seconds() / 60
                    intervals.append(interval_min)

                if intervals:
                    largest_gap_minutes = max(intervals)
                    avg_interval_minutes = (
                        sum(intervals) / len(intervals)
                    )

            # Hourly aligned count (minute=0, second=0)
            hourly_aligned = sum(
                1 for r in records
                if r.timestamp is not None
                and r.timestamp.minute == 0
                and r.timestamp.second == 0
            )

            return {
                "raw_records": raw_count,
                "independent_observations": independent,
                "duplicates": raw_count - independent,
                "duplicate_rate": round(
                    (raw_count - independent) / raw_count, 3
                ) if raw_count > 0 else 0.0,
                "time_coverage_hours": round(
                    time_coverage_hours, 2
                ),
                "largest_gap_minutes": round(
                    largest_gap_minutes, 1
                ),
                "avg_interval_minutes": round(
                    avg_interval_minutes, 1
                ),
                "hourly_aligned_count": hourly_aligned,
            }

        finally:
            session.close()

    except Exception as e:
        logger.warning(
            "Failed to assess demand history quality: %s", e
        )
        return {
            "raw_records": 0,
            "independent_observations": 0,
            "duplicates": 0,
            "duplicate_rate": 0.0,
            "time_coverage_hours": 0.0,
            "largest_gap_minutes": 0.0,
            "avg_interval_minutes": 0.0,
            "hourly_aligned_count": 0,
        }


# =========================================================
# API: GET /api/demand/history
# =========================================================

@router.get("/history")
def get_demand_history():

    records = read_history()
    count = len(records)
    quality = get_demand_history_quality()

    latest = None
    earliest = None
    latest_demand = None
    latest_supply = None
    latest_load_shed = None

    if count > 0:

        earliest = records[0]
        latest = records[-1]

        try:
            latest_demand = float(
                latest.get("demand_mw", 0)
            )
            latest_supply = float(
                latest.get("supply_mw", 0)
            )
            latest_load_shed = float(
                latest.get("load_shedding_mw", 0)
            )
        except (TypeError, ValueError):
            pass

    return {
        "project": "PowerFlex BD",
        "module": "Demand History",
        "record_count": count,
        "independent_observations": quality["independent_observations"],
        "duplicates": quality["duplicates"],
        "duplicate_rate": quality["duplicate_rate"],
        "storage": "postgresql",
        "latest_record": {
            "timestamp": latest.get("timestamp")
            if latest else None,
            "pgcb_timestamp": latest.get(
                "pgcb_timestamp"
            ) if latest else None,
            "demand_mw": latest_demand,
            "supply_mw": latest_supply,
            "load_shedding_mw": latest_load_shed,
        } if latest else None,
        "earliest_record": {
            "timestamp": earliest.get("timestamp")
            if earliest else None,
            "pgcb_timestamp": earliest.get(
                "pgcb_timestamp"
            ) if earliest else None,
        } if earliest else None,
        "latest_demand_mw": latest_demand,
        "latest_supply_mw": latest_supply,
        "latest_load_shedding_mw": latest_load_shed,
        "data_source": "PGCB_ERP",
        "data_classification": "OFFICIAL_PGCB",
        "quality": {
            "time_coverage_hours": quality["time_coverage_hours"],
            "largest_gap_minutes": quality["largest_gap_minutes"],
            "avg_interval_minutes": quality["avg_interval_minutes"],
            "hourly_aligned_count": quality["hourly_aligned_count"],
        },
        "message": (
            f"{quality['independent_observations']} independent observations "
            f"from {count} raw records "
            f"({quality['duplicates']} rapid-polling duplicates collapsed)."
        ),
    }


# =========================================================
# API: GET /api/demand/history/export
# =========================================================

@router.get("/history/export")
def export_demand_history():

    records = read_history()

    if not records:

        raise HTTPException(
            status_code=404,
            detail=(
                "No demand history data found. "
                "Data will be collected when PGCB "
                "grid data is fetched."
            ),
        )

    output = io.StringIO()
    fieldnames = [
        "timestamp",
        "pgcb_timestamp",
        "demand_mw",
        "supply_mw",
        "load_shedding_mw",
        "deficit_mw",
        "source",
        "data_classification",
    ]

    writer = csv.DictWriter(
        output, fieldnames=fieldnames
    )
    writer.writeheader()

    for record in records:
        writer.writerow({
            k: record.get(k, "") for k in fieldnames
        })

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                "attachment; "
                "filename=pgcb_demand_history.csv"
            ),
        },
    )
