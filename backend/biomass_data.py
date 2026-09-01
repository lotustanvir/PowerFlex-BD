from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from backend.biomass_sources import (
    SOURCES,
    BANGLADESH_DIVISIONS,
    DIVISION_TO_ZONE,
)
from backend.biomass_fetcher import (
    fetch_all_biomass_data,
)
from backend.biomass_calculator import (
    calculate_all_divisions,
    calculate_division_biomass,
)


# =========================================================
# POWERFLEX BD - BIOMASS DATA API
# =========================================================
#
# FastAPI endpoints for Bangladesh biomass
# energy potential data.
# =========================================================


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/api/resources/biomass",
    tags=["Biomass Data"],
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
# API: GET /api/resources/biomass/live
# =========================================================

@router.get("/live")
def biomass_live():
    """
    Return biomass data with clear classification.
    NOT live data — calculated from official datasets.
    Uses fallback data by default for fast response.
    """

    cached = get_cached("live")

    if cached is not None:
        return cached

    try:

        result = calculate_all_divisions(
            use_fallback=True
        )

        response = {
            "project": "PowerFlex BD",
            "resource": "Biomass",
            "data_classification":
                "CALCULATED_FROM_OFFICIAL_DATA",
            "resource_status": "CALCULATED_POTENTIAL",
            "is_live": False,
            "explanation": (
                "This is calculated biomass energy "
                "potential based on official crop "
                "production and livestock data. "
                "It is NOT real-time generation data."
            ),
            "retrieved_at": result[
                "data_sources"
            ]["retrieved_at"],
            "sources": [
                SOURCES["faostat_crop"],
                SOURCES["dls_livestock"],
                SOURCES["sreda_biomass"],
                SOURCES["das_hoque_2014"],
                SOURCES["kamruzzaman_2024"],
            ],
            "national_summary": result["national"],
            "divisions": [],
        }

        for div_name, div_data in result[
            "divisions"
        ].items():

            zone = DIVISION_TO_ZONE.get(
                div_name, div_name
            )

            response["divisions"].append({
                "division": div_name,
                "powerflex_zone": zone,
                "crop_residue_tonnes_year":
                    div_data[
                        "crop_residue_tonnes_year"
                    ],
                "animal_manure_tonnes_year":
                    div_data[
                        "animal_manure_tonnes_year"
                    ],
                "organic_waste_tonnes_year":
                    div_data[
                        "organic_waste_tonnes_year"
                    ],
                "biogas_m3_year":
                    div_data["biogas_m3_year"],
                "electricity_potential_mwh_year":
                    div_data[
                        "electricity_potential_mwh_year"
                    ],
                "average_potential_mw":
                    div_data[
                        "average_potential_mw"
                    ],
                "dispatchable_mw":
                    div_data["dispatchable_mw"],
            })

        set_cached("live", response)

        return response

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Biomass calculation failed: {error}"
            ),
        )


# =========================================================
# API: GET /api/resources/biomass/divisions
# =========================================================

@router.get("/divisions")
def biomass_divisions():
    """
    Return division-wise biomass breakdown
    with detailed crop and livestock data.
    """

    cached = get_cached("divisions")

    if cached is not None:
        return cached

    try:

        result = calculate_all_divisions()

        response = {
            "project": "PowerFlex BD",
            "resource": "Biomass",
            "data_classification":
                "CALCULATED_FROM_OFFICIAL_DATA",
            "retrieved_at": result[
                "data_sources"
            ]["retrieved_at"],
            "crop_source": result[
                "data_sources"
            ]["crop_data"],
            "livestock_source": result[
                "data_sources"
            ]["livestock_data"],
            "divisions": result["divisions"],
        }

        set_cached("divisions", response)

        return response

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Biomass calculation failed: {error}"
            ),
        )


# =========================================================
# API: GET /api/resources/biomass/potential
# =========================================================

@router.get("/potential")
def biomass_potential():
    """
    Return aggregated biomass potential summary.
    """

    cached = get_cached("potential")

    if cached is not None:
        return cached

    try:

        result = calculate_all_divisions(
            use_fallback=True
        )

        divisions = result["divisions"]

        total_crop = sum(
            d["crop_residue_tonnes_year"]
            for d in divisions.values()
        )

        total_manure = sum(
            d["animal_manure_tonnes_year"]
            for d in divisions.values()
        )

        total_waste = sum(
            d["organic_waste_tonnes_year"]
            for d in divisions.values()
        )

        total_biogas = sum(
            d["biogas_m3_year"]
            for d in divisions.values()
        )

        total_mwh = sum(
            d["electricity_potential_mwh_year"]
            for d in divisions.values()
        )

        total_dispatchable = sum(
            d["dispatchable_mw"]
            for d in divisions.values()
        )

        response = {
            "project": "PowerFlex BD",
            "resource": "Biomass",
            "data_classification":
                "CALCULATED_FROM_OFFICIAL_DATA",
            "retrieved_at": result[
                "data_sources"
            ]["retrieved_at"],
            "national_potential": {
                "crop_residue_tonnes_year": round(
                    total_crop, 1
                ),
                "animal_manure_tonnes_year": round(
                    total_manure, 1
                ),
                "organic_waste_tonnes_year": round(
                    total_waste, 1
                ),
                "biogas_m3_year": round(
                    total_biogas, 1
                ),
                "electricity_potential_mwh_year":
                    round(total_mwh, 1),
                "average_potential_mw": round(
                    total_mwh / 8760, 2
                ),
                "total_dispatchable_mw": round(
                    total_dispatchable, 2
                ),
            },
            "division_breakdown": {
                div: {
                    "electricity_mwh": d[
                        "electricity_potential_mwh_year"
                    ],
                    "dispatchable_mw": d[
                        "dispatchable_mw"
                    ],
                }
                for div, d in divisions.items()
            },
        }

        set_cached("potential", response)

        return response

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Biomass calculation failed: {error}"
            ),
        )


# =========================================================
# API: GET /api/resources/biomass/sources
# =========================================================

@router.get("/sources")
def biomass_sources():
    """
    Return all data sources and metadata
    used in biomass calculations.
    """

    return {
        "project": "PowerFlex BD",
        "resource": "Biomass",
        "sources": SOURCES,
        "conversion_factors": {
            "residue_ratios": {
                k: v["ratio"]
                for k, v in
                __import__(
                    "backend.biomass_sources",
                    fromlist=[
                        "CROP_RESIDUE_RATIOS"
                    ],
                ).CROP_RESIDUE_RATIOS.items()
            },
            "energy_content_mj_kg": (
                __import__(
                    "backend.biomass_sources",
                    fromlist=[
                        "ENERGY_CONTENT_MJ_KG"
                    ],
                ).ENERGY_CONTENT_MJ_KG
            ),
            "biomass_efficiency": 0.25,
            "biogas_efficiency": 0.30,
            "wte_efficiency": 0.20,
            "manure_recoverable": 0.60,
            "biogas_yield_m3_per_kg": 0.04,
            "methane_fraction": 0.60,
        },
        "methodology": {
            "crop_residue": (
                "national_production × division_share "
                "× residue_ratio × recoverable_fraction "
                "× LHV × electricity_efficiency"
            ),
            "animal_manure": (
                "population × manure_per_animal "
                "× recoverable_fraction × biogas_yield "
                "× methane_energy × CHP_efficiency"
            ),
            "organic_waste": (
                "population × waste_per_capita "
                "× organic_fraction × recoverable "
                "× WtE_efficiency"
            ),
        },
    }
