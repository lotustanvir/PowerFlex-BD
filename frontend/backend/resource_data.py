from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from backend.services.grid_service import get_grid_live
from backend.services.solar_service import get_solar_live
from backend.services.wind_service import get_wind_live


# =========================================================
# POWERFLEX BD - UNIFIED RESOURCE DATA SERVICE
# =========================================================
#
# Normalizes all 9 Bangladesh electricity resources
# into a single structure.
#
# Resources:
#   1. Solar      - PGCB + Solar AI
#   2. Wind       - PGCB + Wind AI
#   3. Hydro      - PGCB generation breakdown
#   4. Biomass    - No current operational plants
#   5. Waste      - Under construction
#   6. Gas        - PGCB generation breakdown
#   7. Liquid Fuel - PGCB generation breakdown
#   8. Coal       - PGCB generation breakdown
#   9. Nuclear    - Rooppur under commissioning
#
# IMPORTANT:
#   - Never fabricate current MW values
#   - Every value includes source + classification
#   - Reuses existing PGCB adapter (no duplicate requests)
#   - Solar/Wind AI preserved from existing modules
# =========================================================


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/api/resources",
    tags=["Unified Resources"],
)


# =========================================================
# HELPERS
# =========================================================

def safe_float(value: Any, default=None):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


# =========================================================
# REFERENCE DATA (International Sources)
# =========================================================
#
# Installed capacity from international authoritative
# sources. Used ONLY when no Bangladesh current data
# exists. Clearly marked as INTERNATIONAL_REFERENCE.
# =========================================================

REFERENCE_DATA = {
    "biomass": {
        "installed_capacity_mw": 0.0,
        "source": "BPDB / SREDA / US Trade.gov",
        "source_type": "INTERNATIONAL_REFERENCE",
        "url": "https://ndre.sreda.gov.bd",
        "note": (
            "No utility-scale grid-connected biomass "
            "power plant is operational in Bangladesh. "
            "Only off-grid micro-projects exist "
            "(~400 kWp total)."
        ),
    },
    "waste": {
        "installed_capacity_mw": 42.5,
        "source": "AIIB / NDB / CMEC",
        "source_type": "INTERNATIONAL_REFERENCE",
        "url": "https://www.aiib.org",
        "note": (
            "North Dhaka WtE Plant at Amin Bazar "
            "under construction by CMEC. "
            "Capacity: 42.5 MW gross. "
            "Expected COD: July 2026 (construction "
            "started 2024). Not yet operational."
        ),
    },
    "nuclear": {
        "installed_capacity_mw": 2400.0,
        "source": "World Nuclear Association / Rosatom",
        "source_type": "INTERNATIONAL_REFERENCE",
        "url": "https://www.world-nuclear.org",
        "note": (
            "Rooppur Nuclear Power Plant (RNPP). "
            "2 x VVER-1200, 2,400 MW gross. "
            "Unit 1 fuel loading began Apr 2026. "
            "First grid connection expected mid-2026. "
            "Unit 1 full COD: Dec 2026. "
            "Unit 2 full COD: Dec 2027. "
            "Not yet generating to grid."
        ),
    },
}


# =========================================================
# BUILD RESOURCE STRUCTURE
# =========================================================

def build_resource(
    name: str,
    generation_mw=None,
    available_mw=None,
    installed_capacity_mw=None,
    timestamp=None,
    source="",
    source_type="",
    url="",
    data_classification="",
    resource_status="",
    is_bangladesh_data=True,
    is_current=False,
    note="",
) -> Dict[str, Any]:

    return {
        "resource": name,
        "generation_mw": generation_mw,
        "available_mw": available_mw,
        "installed_capacity_mw": installed_capacity_mw,
        "timestamp": timestamp,
        "source_metadata": {
            "source": source,
            "source_type": source_type,
            "url": url,
            "timestamp": timestamp,
            "data_classification": data_classification,
        },
        "resource_status": resource_status,
        "is_bangladesh_data": is_bangladesh_data,
        "is_current": is_current,
        "note": note,
    }


# =========================================================
# FETCH ALL RESOURCES
# =========================================================

def fetch_all_resources(
    prefetched_grid_data=None,
    prefetched_solar_data=None,
    prefetched_wind_data=None,
) -> Dict[str, Any]:

    now = datetime.now(timezone.utc).isoformat()

    grid_data = (
        prefetched_grid_data
        if prefetched_grid_data is not None
        else get_grid_live()
    )

    solar_raw = (
        prefetched_solar_data
        if prefetched_solar_data is not None
        else get_solar_live()
    )
    solar_data = solar_raw if solar_raw and solar_raw.get("status") != "ERROR" else None

    wind_raw = (
        prefetched_wind_data
        if prefetched_wind_data is not None
        else get_wind_live()
    )
    wind_data = wind_raw if wind_raw and wind_raw.get("status") != "ERROR" else None

    resources = {}

    # -------------------------------------------------
    # 1. SOLAR
    # -------------------------------------------------

    solar_gen = None
    solar_timestamp = now
    solar_source = "PGCB + Solar AI"
    solar_classification = "OFFICIAL_PGCB"

    if grid_data and grid_data.get("live"):
        snap = grid_data.get("data", {})
        gen_bd = snap.get("generation_breakdown", {})
        solar_gen = safe_float(gen_bd.get("solar_mw"))
        solar_timestamp = snap.get("timestamp", now)

    solar_best_zone = None
    solar_best_energy = None
    if solar_data:
        bz = solar_data.get("best_forecast_zone", {})
        solar_best_zone = bz.get("zone")
        solar_best_energy = bz.get(
            "expected_energy_mwh_per_1mw_24h"
        )

    resources["solar"] = build_resource(
        name="Solar",
        generation_mw=solar_gen,
        available_mw=solar_gen,
        installed_capacity_mw=757.0,
        timestamp=solar_timestamp,
        source=solar_source,
        source_type="OFFICIAL_BANGLADESH",
        url="https://erp.powergrid.gov.bd/w/generations/view_generations",
        data_classification=solar_classification,
        resource_status="LIVE",
        is_bangladesh_data=True,
        is_current=True,
        note=(
            "Current generation from PGCB ERP. "
            "Zone forecasts from PowerFlex Solar AI."
        ),
    )

    resources["solar"]["solar_ai"] = {
        "best_zone": solar_best_zone,
        "expected_energy_mwh_per_1mw_24h":
            solar_best_energy,
        "source": "Open-Meteo + PowerFlex Solar AI",
        "data_classification": "LIVE",
    }

    # -------------------------------------------------
    # 2. WIND
    # -------------------------------------------------

    wind_gen = None
    wind_timestamp = now
    wind_source = "PGCB + Wind AI"
    wind_classification = "OFFICIAL_PGCB"

    if grid_data and grid_data.get("live"):
        snap = grid_data.get("data", {})
        gen_bd = snap.get("generation_breakdown", {})
        wind_gen = safe_float(gen_bd.get("wind_mw"))
        wind_timestamp = snap.get("timestamp", now)

    wind_best_zone = None
    wind_best_energy = None
    if wind_data:
        bz = wind_data.get("best_forecast_zone", {})
        wind_best_zone = bz.get("zone")
        wind_best_energy = bz.get(
            "expected_energy_mwh_per_1mw_24h"
        )

    resources["wind"] = build_resource(
        name="Wind",
        generation_mw=wind_gen,
        available_mw=wind_gen,
        installed_capacity_mw=62.0,
        timestamp=wind_timestamp,
        source=wind_source,
        source_type="OFFICIAL_BANGLADESH",
        url="https://erp.powergrid.gov.bd/w/generations/view_generations",
        data_classification=wind_classification,
        resource_status="LIVE",
        is_bangladesh_data=True,
        is_current=True,
        note=(
            "Current generation from PGCB ERP. "
            "Zone forecasts from PowerFlex Wind AI."
        ),
    )

    resources["wind"]["wind_ai"] = {
        "best_zone": wind_best_zone,
        "expected_energy_mwh_per_1mw_24h":
            wind_best_energy,
        "source": "Open-Meteo + PowerFlex Wind AI",
        "data_classification": "LIVE",
    }

    # -------------------------------------------------
    # 3. HYDRO
    # -------------------------------------------------

    hydro_gen = None
    hydro_timestamp = now

    if grid_data and grid_data.get("live"):
        snap = grid_data.get("data", {})
        gen_bd = snap.get("generation_breakdown", {})
        hydro_gen = safe_float(gen_bd.get("hydro_mw"))
        hydro_timestamp = snap.get("timestamp", now)

    resources["hydro"] = build_resource(
        name="Hydro",
        generation_mw=hydro_gen,
        available_mw=hydro_gen,
        installed_capacity_mw=230.0,
        timestamp=hydro_timestamp,
        source="PGCB ERP Generation Breakdown",
        source_type="OFFICIAL_BANGLADESH",
        url="https://erp.powergrid.gov.bd/w/generations/view_generations",
        data_classification="OFFICIAL_PGCB",
        resource_status="LIVE",
        is_bangladesh_data=True,
        is_current=True,
        note=(
            "Kaptai Dam (Karnafuli) - only hydro "
            "plant in Bangladesh. 230 MW installed. "
            "Current generation from PGCB ERP."
        ),
    )

    # -------------------------------------------------
    # 4. BIOMASS
    # -------------------------------------------------

    ref = REFERENCE_DATA["biomass"]

    resources["biomass"] = build_resource(
        name="Biomass",
        generation_mw=None,
        available_mw=None,
        installed_capacity_mw=ref["installed_capacity_mw"],
        timestamp=now,
        source=ref["source"],
        source_type=ref["source_type"],
        url=ref["url"],
        data_classification="DATA_UNAVAILABLE",
        resource_status="NO_CURRENT_PUBLIC_DATA",
        is_bangladesh_data=True,
        is_current=False,
        note=ref["note"],
    )

    # -------------------------------------------------
    # 5. WASTE-TO-ENERGY
    # -------------------------------------------------

    ref = REFERENCE_DATA["waste"]

    resources["waste"] = build_resource(
        name="Waste-to-Energy",
        generation_mw=None,
        available_mw=None,
        installed_capacity_mw=ref["installed_capacity_mw"],
        timestamp=now,
        source=ref["source"],
        source_type=ref["source_type"],
        url=ref["url"],
        data_classification="DATA_UNAVAILABLE",
        resource_status="UNDER_CONSTRUCTION",
        is_bangladesh_data=True,
        is_current=False,
        note=ref["note"],
    )

    # -------------------------------------------------
    # 6. GAS
    # -------------------------------------------------

    gas_gen = None
    gas_timestamp = now

    if grid_data and grid_data.get("live"):
        snap = grid_data.get("data", {})
        gen_bd = snap.get("generation_breakdown", {})
        gas_gen = safe_float(gen_bd.get("gas_mw"))
        gas_timestamp = snap.get("timestamp", now)

    resources["gas"] = build_resource(
        name="Gas",
        generation_mw=gas_gen,
        available_mw=gas_gen,
        installed_capacity_mw=12194.0,
        timestamp=gas_timestamp,
        source="PGCB ERP Generation Breakdown",
        source_type="OFFICIAL_BANGLADESH",
        url="https://erp.powergrid.gov.bd/w/generations/view_generations",
        data_classification="OFFICIAL_PGCB",
        resource_status="LIVE",
        is_bangladesh_data=True,
        is_current=True,
        note=(
            "Current generation from PGCB ERP. "
            "Installed ~12,194 MW (BPDB Jul 2026). "
            "Gas shortages limit actual output."
        ),
    )

    # -------------------------------------------------
    # 7. LIQUID FUEL
    # -------------------------------------------------

    lfg_gen = None
    lfg_timestamp = now

    if grid_data and grid_data.get("live"):
        snap = grid_data.get("data", {})
        gen_bd = snap.get("generation_breakdown", {})
        lfg_gen = safe_float(
            gen_bd.get("liquid_fuel_mw")
        )
        lfg_timestamp = snap.get("timestamp", now)

    resources["liquid_fuel"] = build_resource(
        name="Liquid Fuel",
        generation_mw=lfg_gen,
        available_mw=lfg_gen,
        installed_capacity_mw=5634.0,
        timestamp=lfg_timestamp,
        source="PGCB ERP Generation Breakdown",
        source_type="OFFICIAL_BANGLADESH",
        url="https://erp.powergrid.gov.bd/w/generations/view_generations",
        data_classification="OFFICIAL_PGCB",
        resource_status="LIVE",
        is_bangladesh_data=True,
        is_current=True,
        note=(
            "Current generation from PGCB ERP. "
            "Furnace oil + diesel plants. "
            "Mostly peak-hour operation."
        ),
    )

    # -------------------------------------------------
    # 8. COAL
    # -------------------------------------------------

    coal_gen = None
    coal_timestamp = now

    if grid_data and grid_data.get("live"):
        snap = grid_data.get("data", {})
        gen_bd = snap.get("generation_breakdown", {})
        coal_gen = safe_float(gen_bd.get("coal_mw"))
        coal_timestamp = snap.get("timestamp", now)

    resources["coal"] = build_resource(
        name="Coal",
        generation_mw=coal_gen,
        available_mw=coal_gen,
        installed_capacity_mw=7629.0,
        timestamp=coal_timestamp,
        source="PGCB ERP Generation Breakdown",
        source_type="OFFICIAL_BANGLADESH",
        url="https://erp.powergrid.gov.bd/w/generations/view_generations",
        data_classification="OFFICIAL_PGCB",
        resource_status="LIVE",
        is_bangladesh_data=True,
        is_current=True,
        note=(
            "Current generation from PGCB ERP. "
            "Includes domestic plants + Adani Godda "
            "import. Total ~7,629 MW installed."
        ),
    )

    # -------------------------------------------------
    # 9. NUCLEAR
    # -------------------------------------------------

    ref = REFERENCE_DATA["nuclear"]

    resources["nuclear"] = build_resource(
        name="Nuclear",
        generation_mw=None,
        available_mw=None,
        installed_capacity_mw=ref["installed_capacity_mw"],
        timestamp=now,
        source=ref["source"],
        source_type=ref["source_type"],
        url=ref["url"],
        data_classification="DATA_UNAVAILABLE",
        resource_status="UNDER_COMMISSIONING",
        is_bangladesh_data=True,
        is_current=False,
        note=ref["note"],
    )

    return resources


# =========================================================
# API: GET /api/resources/live
# =========================================================

@router.get("/live")
def get_all_resources():
    """
    Return all 9 Bangladesh electricity resources
    with current generation, source, and classification.
    """

    resources = fetch_all_resources()

    pgcb_available = sum(
        1 for r in resources.values()
        if r.get("source_metadata", {}).get(
            "data_classification"
        ) == "OFFICIAL_PGCB"
        and r.get("generation_mw") is not None
    )

    response = {
        "project": "PowerFlex BD",
        "module": "Unified Resource Data",
        "resource_count": len(resources),
        "pgcb_resources_available": pgcb_available,
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "data_classification_summary": {
            "OFFICIAL_PGCB": pgcb_available,
            "LIVE": sum(
                1 for r in resources.values()
                if r.get("source_metadata", {}).get(
                    "data_classification"
                ) == "LIVE"
            ),
            "DATA_UNAVAILABLE": sum(
                1 for r in resources.values()
                if r.get("data_classification") == "DATA_UNAVAILABLE"
                or r.get("resource_status")
                in ("DATA_UNAVAILABLE",
                    "NO_CURRENT_PUBLIC_DATA",
                    "UNDER_CONSTRUCTION",
                    "UNDER_COMMISSIONING")
            ),
        },
        "resources": resources,
    }
    return response


# =========================================================
# API: GET /api/resources/{resource}
# =========================================================

@router.get("/{resource_name}")
def get_resource(resource_name: str):
    """
    Return a single resource by name.

    Valid names:
      solar, wind, hydro, biomass, waste,
      gas, liquid_fuel, coal, nuclear
    """

    valid_names = [
        "solar", "wind", "hydro", "biomass",
        "waste", "gas", "liquid_fuel", "coal",
        "nuclear",
    ]

    name_lower = resource_name.lower().strip()

    if name_lower not in valid_names:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Resource '{resource_name}' not found. "
                f"Valid: {', '.join(valid_names)}"
            ),
        )

    resources = fetch_all_resources()

    resource = resources.get(name_lower)

    if resource is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Resource '{resource_name}' "
                f"data unavailable."
            ),
        )

    return {
        "project": "PowerFlex BD",
        "module": "Unified Resource Data",
        "resource": resource,
    }
