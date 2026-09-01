import csv
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse


# =========================================================
# POWERFLEX BD - DEMAND HISTORY LOGGER
# =========================================================
#
# Records official PGCB demand observations to CSV.
# Used for future model retraining.
#
# data_classification = "OFFICIAL_PGCB"
# Never records fabricated values.
# =========================================================


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/api/demand",
    tags=["Demand History"],
)


# =========================================================
# PROJECT ROOT
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# =========================================================
# CSV PATH
# =========================================================

DATA_DIR = PROJECT_ROOT / "data"
HISTORY_FILE = DATA_DIR / "pgcb_demand_history.csv"

CSV_HEADERS = [
    "timestamp",
    "pgcb_timestamp",
    "demand_mw",
    "supply_mw",
    "load_shedding_mw",
    "deficit_mw",
    "source",
    "data_classification",
]


# =========================================================
# ENSURE CSV EXISTS
# =========================================================

def ensure_csv():
    DATA_DIR.mkdir(exist_ok=True)

    if not HISTORY_FILE.exists():

        with open(
            HISTORY_FILE,
            "w",
            newline="",
            encoding="utf-8",
        ) as f:

            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)


# =========================================================
# DUPLICATE CHECK
# =========================================================

def is_duplicate(
    pgcb_timestamp: str,
    demand_mw: float,
    supply_mw: float,
) -> bool:

    if not HISTORY_FILE.exists():
        return False

    try:

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8",
        ) as f:

            reader = csv.DictReader(f)

            for row in reader:

                if (
                    row.get("pgcb_timestamp")
                    == pgcb_timestamp
                    and row.get("demand_mw")
                    == str(demand_mw)
                    and row.get("supply_mw")
                    == str(supply_mw)
                ):

                    return True

        return False

    except Exception:
        return False


# =========================================================
# APPEND RECORD
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

    ensure_csv()

    now = datetime.now(timezone.utc).isoformat()

    try:

        with open(
            HISTORY_FILE,
            "a",
            newline="",
            encoding="utf-8",
        ) as f:

            writer = csv.writer(f)

            writer.writerow([
                now,
                pgcb_timestamp,
                round(demand_mw, 1),
                round(supply_mw, 1),
                round(
                    load_shedding_mw, 1
                ) if load_shedding_mw else 0.0,
                round(deficit_mw, 1),
                source,
                "OFFICIAL_PGCB",
            ])

        return True

    except Exception:
        return False


# =========================================================
# READ HISTORY
# =========================================================

def read_history() -> list:

    if not HISTORY_FILE.exists():
        return []

    try:

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8",
        ) as f:

            reader = csv.DictReader(f)
            return list(reader)

    except Exception:
        return []


# =========================================================
# COUNT RECORDS
# =========================================================

def count_records() -> int:

    if not HISTORY_FILE.exists():
        return 0

    try:

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8",
        ) as f:

            reader = csv.DictReader(f)
            return sum(1 for _ in reader)

    except Exception:
        return 0


# =========================================================
# API: GET /api/demand/history
# =========================================================

@router.get("/history")
def get_demand_history():
    """
    Return metadata about the PGCB demand history dataset.
    """

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
        "file_path": str(HISTORY_FILE),
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
    """
    Download the PGCB demand history CSV file.
    """

    if not HISTORY_FILE.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "No demand history file found. "
                "Data will be collected when PGCB "
                "grid data is fetched."
            ),
        )

    return FileResponse(
        path=str(HISTORY_FILE),
        filename="pgcb_demand_history.csv",
        media_type="text/csv",
    )
