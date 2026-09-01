from datetime import datetime, timezone
from typing import Any, Dict, Optional

from backend.waste_sources import (
    WTE_PROJECTS,
    CITY_WASTE_GENERATION,
    WASTE_CONVERSION,
    SOURCES,
)


# =========================================================
# POWERFLEX BD - WASTE DATA FETCHER
# =========================================================
#
# Returns documented WtE project data and
# calculated waste generation potential.
#
# Unlike biomass, there are no external APIs to call.
# All data is from published project documents.
# =========================================================


# =========================================================
# CACHE
# =========================================================

_cache: Dict[str, Any] = {}


def get_cached(key: str) -> Optional[Dict]:
    import time

    entry = _cache.get(key)

    if entry is None:
        return None

    ts, data = entry

    if time.time() - ts > 3600:
        return None

    return data


def set_cached(key: str, data: Any):
    import time
    _cache[key] = (time.time(), data)


# =========================================================
# FETCH PROJECT DATA
# =========================================================

def fetch_wte_projects() -> list:
    """
    Return documented WtE projects.
    No API calls needed - data is from project documents.
    """

    cached = get_cached("projects")

    if cached is not None:
        return cached

    projects = WTE_PROJECTS.copy()

    set_cached("projects", projects)

    return projects


# =========================================================
# FETCH WASTE GENERATION DATA
# =========================================================

def fetch_waste_generation() -> Dict[str, Any]:
    """
    Return waste generation data for all cities.
    """

    cached = get_cached("waste_gen")

    if cached is not None:
        return cached

    set_cached("waste_gen", CITY_WASTE_GENERATION)

    return CITY_WASTE_GENERATION


# =========================================================
# FETCH CONVERSION FACTORS
# =========================================================

def fetch_conversion_factors() -> Dict[str, Any]:
    """
    Return waste-to-electricity conversion factors.
    """

    return WASTE_CONVERSION


# =========================================================
# FETCH ALL WASTE DATA
# =========================================================

def fetch_all_waste_data() -> Dict[str, Any]:
    """
    Return all waste-related data.
    """

    projects = fetch_wte_projects()
    waste_gen = fetch_waste_generation()
    conversion = fetch_conversion_factors()

    return {
        "projects": projects,
        "waste_generation": waste_gen,
        "conversion_factors": conversion,
        "sources": SOURCES,
        "retrieved_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }
