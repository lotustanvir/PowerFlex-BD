import csv
import io
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

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

    try:
        session = get_session()
        try:
            existing = (
                session.query(DemandHistory)
                .filter(
                    DemandHistory.pgcb_timestamp
                    == pgcb_timestamp,
                    DemandHistory.demand_mw
                    == round(demand_mw, 1),
                    DemandHistory.supply_mw
                    == round(supply_mw, 1),
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


# =========================================================
# API: GET /api/demand/history
# =========================================================

@router.get("/history")
def get_demand_history():

    records = read_history()
    count = len(records)

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
        "message": (
            f"{count} official PGCB observations "
            f"recorded."
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
