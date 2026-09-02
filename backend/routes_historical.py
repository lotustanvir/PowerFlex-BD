"""Historical Data API Routes for PowerFlex BD v3.

Provides endpoints for querying validated historical demand/supply data,
assessing data freshness, and managing data quality.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

from backend.historical_data import (
    HistoricalDemandRecord,
    HistoricalDataValidator,
    load_pgcb_demand_history,
    assess_data_freshness,
    BST,
)

logger = logging.getLogger("powerflex.routes.historical")
router = APIRouter(prefix="/api/v3/historical", tags=["v3-historical"])


# =========================================================
# In-memory historical data store
# =========================================================

_historical_demand: list[HistoricalDemandRecord] = []


def _ensure_loaded() -> None:
    """Load historical data on first access."""
    global _historical_demand
    if not _historical_demand:
        _historical_demand = load_pgcb_demand_history()
        if _historical_demand:
            logger.info("Loaded %d historical demand records", len(_historical_demand))


# =========================================================
# GET /api/v3/historical/demand
# =========================================================

@router.get("/demand")
def get_historical_demand(
    hours: int = Query(168, ge=1, le=8760, description="Number of hours of history"),
    quality: Optional[str] = Query(None, description="Filter by quality flag"),
) -> Dict[str, Any]:
    """Return validated historical demand data with quality assessment.

    All records use Bangladesh Standard Time (UTC+06:00).
    """
    _ensure_loaded()

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=hours)

    records = [r for r in _historical_demand if r.timestamp_utc >= cutoff]

    if quality:
        records = [r for r in records if r.quality_flag == quality.upper()]

    records.sort(key=lambda r: r.timestamp_utc)

    validation_issues = []
    for r in records:
        issues = HistoricalDataValidator.validate_demand(r)
        if issues:
            validation_issues.append({
                "timestamp": r.timestamp_utc.isoformat(),
                "issues": issues,
            })

    freshness = assess_data_freshness(_historical_demand)

    return {
        "timestamp": now.isoformat(),
        "count": len(records),
        "records": [r.to_dict() for r in records[:200]],
        "data_freshness": freshness,
        "validation_issues": validation_issues[:50],
        "data_classification": "MEASURED",
        "data_license": "POWER_FLEX_INTERNAL",
        "bst_timezone": "Asia/Dhaka (UTC+06:00)",
    }


# =========================================================
# GET /api/v3/historical/freshness
# =========================================================

@router.get("/freshness")
def get_data_freshness() -> Dict[str, Any]:
    """Assess the freshness of all loaded historical data."""
    _ensure_loaded()
    return assess_data_freshness(_historical_demand)


# =========================================================
# GET /api/v3/historical/validate
# =========================================================

@router.get("/validate")
def validate_historical_data() -> Dict[str, Any]:
    """Run full validation suite on all loaded historical data."""
    _ensure_loaded()

    all_issues = []
    for r in _historical_demand:
        issues = HistoricalDataValidator.validate_demand(r)
        if issues:
            all_issues.append({
                "timestamp": r.timestamp_utc.isoformat(),
                "issues": issues,
            })

    duplicates = HistoricalDataValidator.detect_duplicates(_historical_demand)
    gaps = HistoricalDataValidator.detect_gaps(_historical_demand)

    quality_summary = {}
    for r in _historical_demand:
        quality_summary[r.quality_flag] = quality_summary.get(r.quality_flag, 0) + 1

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_records": len(_historical_demand),
        "validation_issues_count": len(all_issues),
        "validation_issues_sample": all_issues[:50],
        "duplicate_count": len(duplicates),
        "gaps_count": len(gaps),
        "gaps_sample": gaps[:20],
        "quality_summary": quality_summary,
        "data_classification": "MEASURED",
    }


# =========================================================
# GET /api/v3/historical/summary
# =========================================================

@router.get("/summary")
def get_historical_summary() -> Dict[str, Any]:
    """Statistical summary of historical demand data."""
    _ensure_loaded()

    if not _historical_demand:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "NO_DATA",
            "message": "No historical data loaded",
        }

    demands = [r.demand_mw for r in _historical_demand]
    timestamps = [r.timestamp_utc for r in _historical_demand]

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "record_count": len(demands),
        "date_range": {
            "start": min(timestamps).isoformat(),
            "end": max(timestamps).isoformat(),
        },
        "demand_stats": {
            "min_mw": round(min(demands), 1),
            "max_mw": round(max(demands), 1),
            "mean_mw": round(sum(demands) / len(demands), 1),
        },
        "data_classification": "MEASURED",
        "bst_timezone": "Asia/Dhaka (UTC+06:00)",
    }
