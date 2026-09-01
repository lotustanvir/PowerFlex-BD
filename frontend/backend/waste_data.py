from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from backend.waste_sources import (
    SOURCES,
    WTE_PROJECTS,
    CITY_WASTE_GENERATION,
)
from backend.waste_fetcher import (
    fetch_all_waste_data,
)
from backend.waste_calculator import (
    calculate_project_capacity,
    calculate_all_cities,
    calculate_city_waste_potential,
    map_waste_to_zones,
)


# =========================================================
# POWERFLEX BD - WASTE DATA API
# =========================================================
#
# FastAPI endpoints for Bangladesh Waste-to-Energy
# data and calculated potential.
# =========================================================


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/api/resources/waste",
    tags=["Waste-to-Energy Data"],
)


# =========================================================
# CACHE
# =========================================================

_cache: Dict[str, Any] = {}

_cache_expiry = 3600


def get_cached(key: str):
    import time

    entry = _cache.get(key)

    if entry is None:
        return None

    ts, data = entry

    if time.time() - ts > _cache_expiry:
        return None

    return data


def set_cached(key: str, data: Any):
    import time
    _cache[key] = (time.time(), data)


# =========================================================
# API: GET /api/resources/waste/live
# =========================================================

@router.get("/live")
def waste_live():
    """
    Return waste-to-energy data with clear classification.
    NOT live generation data — documented projects
    + calculated potential.
    """

    cached = get_cached("live")

    if cached is not None:
        return cached

    try:

        projects = calculate_project_capacity()
        cities = calculate_all_cities()
        zones = map_waste_to_zones(
            cities["cities"]
        )

        response = {
            "project": "PowerFlex BD",
            "resource": "Waste-to-Energy",
            "data_classification":
                "OFFICIAL_PROJECT_DATA",
            "resource_status":
                "CALCULATED_POTENTIAL",
            "is_live": False,
            "explanation": (
                "This is calculated waste-to-energy "
                "potential based on documented projects "
                "and city waste generation data. "
                "It is NOT real-time generation data. "
                "Bangladesh has ZERO operational WtE "
                "plants as of August 2026."
            ),
            "national_summary": {
                "total_operational_mw": projects[
                    "total_operational_mw"
                ],
                "total_planned_mw": projects[
                    "total_planned_mw"
                ],
                "calculated_potential_mw":
                    cities["national"][
                        "total_average_mw"
                    ],
                "calculated_dispatchable_mw":
                    cities["national"][
                        "total_dispatchable_mw"
                    ],
                "total_daily_waste_tonnes":
                    cities["national"][
                        "total_daily_waste_tonnes"
                    ],
            },
            "projects": projects["projects"],
            "city_potentials": cities["cities"],
            "zone_allocation": zones,
        }

        set_cached("live", response)

        return response

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Waste data calculation failed: "
                f"{error}"
            ),
        )


# =========================================================
# API: GET /api/resources/waste/projects
# =========================================================

@router.get("/projects")
def waste_projects():
    """
    Return documented WtE projects in Bangladesh.
    """

    cached = get_cached("projects")

    if cached is not None:
        return cached

    try:

        projects = calculate_project_capacity()

        response = {
            "project": "PowerFlex BD",
            "resource": "Waste-to-Energy",
            "data_classification":
                "OFFICIAL_PROJECT_DATA",
            "total_operational_mw": projects[
                "total_operational_mw"
            ],
            "total_planned_mw": projects[
                "total_planned_mw"
            ],
            "projects": projects["projects"],
            "note": (
                "Bangladesh has ZERO operational WtE "
                "plants. All projects are under "
                "construction or planned."
            ),
        }

        set_cached("projects", response)

        return response

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Project data failed: {error}"
            ),
        )


# =========================================================
# API: GET /api/resources/waste/potential
# =========================================================

@router.get("/potential")
def waste_potential():
    """
    Return calculated waste-to-electricity potential
    for all cities.
    """

    cached = get_cached("potential")

    if cached is not None:
        return cached

    try:

        cities = calculate_all_cities()

        response = {
            "project": "PowerFlex BD",
            "resource": "Waste-to-Energy",
            "data_classification":
                "CALCULATED_FROM_OFFICIAL_DATA",
            "national_potential": cities["national"],
            "city_breakdown": cities["cities"],
            "conversion_factors":
                cities["conversion_factors"],
        }

        set_cached("potential", response)

        return response

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Waste potential failed: {error}"
            ),
        )


# =========================================================
# API: GET /api/resources/waste/sources
# =========================================================

@router.get("/sources")
def waste_sources():
    """
    Return all data sources and metadata
    used in waste-to-energy calculations.
    """

    return {
        "project": "PowerFlex BD",
        "resource": "Waste-to-Energy",
        "sources": SOURCES,
        "conversion_factors": {
            "lhv_mj_kg": 7.0,
            "recovery_fraction": 0.50,
            "incineration_efficiency_pct": 0.22,
            "biogas_efficiency_pct": 0.28,
            "kwh_per_mj": round(
                1.0 / 3.6, 4
            ),
        },
        "methodology": {
            "calculated_potential": (
                "daily_waste_tonnes "
                "× recovery_fraction "
                "× LHV "
                "× efficiency "
                "× kwh_per_mj "
                "= MWh/day "
                "= MW average"
            ),
            "dispatchable": (
                "average_mw × 0.80 "
                "(availability factor)"
            ),
        },
        "key_findings": [
            (
                "Bangladesh has ZERO operational "
                "WtE plants as of August 2026"
            ),
            (
                "Aminbazar (42.5 MW) under "
                "construction, COD August 2028"
            ),
            (
                "Matuail (9.1 MW) announced, "
                "no construction started"
            ),
            (
                "Dhaka generates 6,500 tonnes "
                "waste/day — largest potential"
            ),
        ],
    }
