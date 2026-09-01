from fastapi import APIRouter, HTTPException
import logging

from backend.services.grid_service import get_grid_live
from backend.services.solar_service import get_solar_live
from backend.services.wind_service import get_wind_live

logger = logging.getLogger("powerflex.loadshield")

from backend.optimizer import (
    optimize,
    BATTERY_POWER_MW,
    BATTERY_SOC_PERCENT,
    FLEXIBLE_DEMAND_MW,
)
from backend.demand_forecast import (
    train_demand_model,
    forecast_24h_demand,
    fetch_current_pgcb_demand,
)
from backend.resource_data import fetch_all_resources
from backend.biomass_calculator import calculate_all_divisions
from backend.waste_calculator import (
    calculate_all_cities,
    map_waste_to_zones,
)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/api/loadshield",
    tags=["LoadShield"],
)


# =========================================================
# HELPERS
# =========================================================

def safe_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


# =========================================================
# RISK
# =========================================================

def calculate_risk(
    gap_mw,
    demand_mw,
):

    if demand_mw is None or demand_mw <= 0:
        return "UNKNOWN"

    if gap_mw <= 0:
        return "LOW"

    gap_percent = (
        gap_mw / demand_mw
    ) * 100

    if gap_percent <= 5:
        return "MODERATE"

    if gap_percent <= 15:
        return "HIGH"

    return "CRITICAL"


def _build_resource_analysis(
    resource_data,
    solar_data,
    wind_data,
    biomass_divisions,
    waste_zones,
):
    """Build the resource_analysis dict for loadshield responses."""

    return {
        "solar": {
            "current_generation_mw":
                resource_data.get("solar", {})
                .get("generation_mw"),
            "best_zone": solar_data.get(
                "best_forecast_zone"
            ),
            "best_opportunity": solar_data.get(
                "best_opportunity"
            ),
            "data_source": "PGCB + Solar AI",
            "data_classification":
                "OFFICIAL_PGCB",
            "is_bangladesh_data": True,
            "is_current": True,
            "usable_for_dispatch": True,
        },
        "wind": {
            "current_generation_mw":
                resource_data.get("wind", {})
                .get("generation_mw"),
            "best_zone": wind_data.get(
                "best_forecast_zone"
            ),
            "best_opportunity": wind_data.get(
                "best_opportunity"
            ),
            "data_source": "PGCB + Wind AI",
            "data_classification":
                "OFFICIAL_PGCB",
            "is_bangladesh_data": True,
            "is_current": True,
            "usable_for_dispatch": True,
        },
        "hydro": {
            "current_generation_mw":
                resource_data.get("hydro", {})
                .get("generation_mw"),
            "installed_capacity_mw": 230.0,
            "data_source": "PGCB ERP",
            "data_classification":
                "OFFICIAL_PGCB",
            "is_bangladesh_data": True,
            "is_current": True,
            "usable_for_dispatch": False,
            "note": (
                "System-wide generation only. "
                "Zone-level dispatch not available."
            ),
        },
        "gas": {
            "current_generation_mw":
                resource_data.get("gas", {})
                .get("generation_mw"),
            "installed_capacity_mw": 12194.0,
            "data_source": "PGCB ERP",
            "data_classification":
                "OFFICIAL_PGCB",
            "is_bangladesh_data": True,
            "is_current": True,
            "usable_for_dispatch": False,
            "note": (
                "System-wide generation only. "
                "Zone-level dispatch not available."
            ),
        },
        "liquid_fuel": {
            "current_generation_mw":
                resource_data.get(
                    "liquid_fuel", {}
                ).get("generation_mw"),
            "installed_capacity_mw": 5634.0,
            "data_source": "PGCB ERP",
            "data_classification":
                "OFFICIAL_PGCB",
            "is_bangladesh_data": True,
            "is_current": True,
            "usable_for_dispatch": False,
            "note": (
                "System-wide generation only. "
                "Zone-level dispatch not available."
            ),
        },
        "coal": {
            "current_generation_mw":
                resource_data.get("coal", {})
                .get("generation_mw"),
            "installed_capacity_mw": 7629.0,
            "data_source": "PGCB ERP",
            "data_classification":
                "OFFICIAL_PGCB",
            "is_bangladesh_data": True,
            "is_current": True,
            "usable_for_dispatch": False,
            "note": (
                "System-wide generation only. "
                "Zone-level dispatch not available."
            ),
        },
        "biomass": {
            "current_generation_mw": None,
            "available_mw":
                sum(
                    safe_float(d.get(
                        "dispatchable_mw"
                    )) or 0.0
                    for d in
                    (biomass_divisions or {}).values()
                )
                if biomass_divisions
                else None,
            "average_potential_mw":
                sum(
                    safe_float(d.get(
                        "average_potential_mw"
                    )) or 0.0
                    for d in
                    (biomass_divisions or {}).values()
                )
                if biomass_divisions
                else None,
            "data_source":
                "FAOSTAT / DLS / BBS / SREDA",
            "data_classification":
                "CALCULATED_FROM_OFFICIAL_DATA",
            "resource_status":
                "CALCULATED_POTENTIAL",
            "is_bangladesh_data": True,
            "is_current": False,
            "usable_for_dispatch": True,
            "note": (
                "Calculated from national crop "
                "and livestock data. Not real-time."
            ),
        },
        "waste_to_energy": {
            "current_generation_mw": None,
            "available_mw":
                sum(
                    safe_float(d.get(
                        "dispatchable_mw"
                    )) or 0.0
                    for d in
                    (waste_zones or {}).values()
                )
                if waste_zones
                else None,
            "average_potential_mw":
                sum(
                    safe_float(d.get(
                        "available_mw"
                    )) or 0.0
                    for d in
                    (waste_zones or {}).values()
                )
                if waste_zones
                else None,
            "data_source":
                "DNCC / DSCC / AIIB / NDB",
            "data_classification":
                "CALCULATED_FROM_OFFICIAL_DATA",
            "resource_status":
                "CALCULATED_POTENTIAL",
            "is_bangladesh_data": True,
            "is_current": False,
            "usable_for_dispatch": True,
            "note": (
                "Calculated from city waste "
                "generation data. No operational "
                "WtE plants in Bangladesh yet."
            ),
        },
        "nuclear": {
            "current_generation_mw": None,
            "available_mw": None,
            "installed_capacity_mw": 2400.0,
            "data_source":
                "World Nuclear Association",
            "data_classification":
                "DATA_UNAVAILABLE",
            "resource_status":
                "UNDER_COMMISSIONING",
            "is_bangladesh_data": True,
            "is_current": False,
            "usable_for_dispatch": False,
        },
        "battery": {
            "status": "PROTOTYPE",
            "power_capacity_mw":
                BATTERY_POWER_MW,
            "soc_percent": BATTERY_SOC_PERCENT,
            "data_classification": "PROTOTYPE",
            "is_bangladesh_data": False,
            "is_current": False,
            "usable_for_dispatch": True,
        },
        "flexible_demand": {
            "status": "PROTOTYPE",
            "capacity_mw":
                FLEXIBLE_DEMAND_MW,
            "data_classification": "PROTOTYPE",
            "is_bangladesh_data": False,
            "is_current": False,
            "usable_for_dispatch": True,
        },
    }


# =========================================================
# LOADSHIELD
# =========================================================

@router.get("/live")
def loadshield_live():

    # =====================================================
    # 1. FETCH REAL GRID DATA
    # =====================================================
    logger.info("LOADSHIELD_STAGE=grid START")

    grid_data = get_grid_live()

    if grid_data is None:
        logger.error("LOADSHIELD_STAGE=grid FAILED result=None")
        raise HTTPException(
            status_code=502,
            detail=(
                "Grid service returned no data."
            ),
        )

    logger.info("LOADSHIELD_STAGE=grid SUCCESS connected=%s live=%s", grid_data.get("connected"), grid_data.get("live"))

    # =====================================================
    # PGCB CHECK
    # =====================================================

    if not grid_data.get("live"):

        return {

            "project":
                "PowerFlex BD",

            "module":
                "LoadShield",

            "status":
                "WAITING_FOR_GRID_DATA",

            "current_situation": {
                "grid": {
                    "demand_mw": None,
                    "supply_mw": None,
                    "deficit_mw": None,
                    "load_shedding_mw": None,
                    "source": "PGCB / NLDC",
                    "data_classification":
                        "NOT_CONNECTED",
                },
            },

            "forecast_situation": None,

            "resource_analysis": None,
            "zone_analysis": [],

            "current_recommendation": None,
            "forecast_preparation": None,

            "message":
                (
                    "Official PGCB/NLDC data required "
                    "before making a real grid decision. "
                    "LoadShield will not use hardcoded "
                    "demand or supply values."
                ),

            "data_source": {
                "grid":
                    "PGCB / NLDC (not connected)",
                "solar":
                    "Open-Meteo + PowerFlex Solar AI",
                "wind":
                    "Open-Meteo + PowerFlex Wind AI",
                "demand_forecast":
                    "MODEL_FORECAST",
                "hydro": "PGCB ERP",
                "biomass":
                    "FAOSTAT / DLS / BBS / SREDA",
                "waste":
                    "DNCC / DSCC / AIIB / NDB",
                "battery": "PROTOTYPE - assumption",
                "flexible_demand":
                    "PROTOTYPE - assumption",
            },
        }

    # =====================================================
    # 2. EXTRACT DEMAND / SUPPLY
    # =====================================================
    logger.info("LOADSHIELD_STAGE=extract START")

    grid = grid_data.get("data")

    if not grid:
        logger.error("LOADSHIELD_STAGE=extract FAILED grid_data=%s", list(grid_data.keys()) if grid_data else None)

        raise HTTPException(
            status_code=502,
            detail="PGCB grid snapshot is missing.",
        )

    demand_mw = safe_float(
        grid.get("current_demand_mw")
    )

    supply_mw = safe_float(
        grid.get("supply_mw")
    )

    load_shedding_mw = safe_float(
        grid.get("load_shedding_mw")
    )

    logger.info("LOADSHIELD_STAGE=extract SUCCESS demand=%s supply=%s load_shed=%s", demand_mw, supply_mw, load_shedding_mw)

    # =====================================================
    # DATA VALIDATION
    # =====================================================

    if demand_mw is None:

        return {
            "project": "PowerFlex BD",
            "module": "LoadShield",
            "status": "DATA_INCOMPLETE",

            "current_situation": {
                "grid": {
                    "demand_mw": None,
                    "supply_mw": (
                        round(supply_mw, 3)
                        if supply_mw
                        else None
                    ),
                    "deficit_mw": None,
                    "load_shedding_mw": None,
                    "source": "PGCB / NLDC",
                    "data_classification":
                        "OFFICIAL_PGCB",
                },
            },

            "forecast_situation": None,

            "resource_analysis": None,
            "zone_analysis": [],

            "current_recommendation": None,
            "forecast_preparation": None,

            "message": (
                "PGCB demand data is unavailable."
            ),
        }

    if supply_mw is None:

        return {
            "project": "PowerFlex BD",
            "module": "LoadShield",
            "status": "DATA_INCOMPLETE",

            "current_situation": {
                "grid": {
                    "demand_mw": round(
                        demand_mw, 3
                    ),
                    "supply_mw": None,
                    "deficit_mw": None,
                    "load_shedding_mw": None,
                    "source": "PGCB / NLDC",
                    "data_classification":
                        "OFFICIAL_PGCB",
                },
            },

            "forecast_situation": None,

            "resource_analysis": None,
            "zone_analysis": [],

            "current_recommendation": None,
            "forecast_preparation": None,

            "message": (
                "PGCB supply data is unavailable."
            ),
        }

    # =====================================================
    # 3. CALCULATE DEFICIT
    # =====================================================

    deficit_mw = max(
        demand_mw - supply_mw, 0.0
    )

    # =====================================================
    # 4. FETCH SOLAR + WIND AI FORECASTS
    # =====================================================
    logger.info("LOADSHIELD_STAGE=solar START")

    try:
        solar_raw = get_solar_live()
        solar_data = solar_raw if solar_raw and solar_raw.get("status") != "ERROR" else {}
        logger.info("LOADSHIELD_STAGE=solar SUCCESS keys=%s", list(solar_data.keys())[:5])
    except Exception:
        logger.exception("LOADSHIELD_STAGE=solar FAILED")
        solar_data = {}

    logger.info("LOADSHIELD_STAGE=wind START")

    try:
        wind_raw = get_wind_live()
        wind_data = wind_raw if wind_raw and wind_raw.get("status") != "ERROR" else {}
        logger.info("LOADSHIELD_STAGE=wind SUCCESS keys=%s", list(wind_data.keys())[:5])
    except Exception:
        logger.exception("LOADSHIELD_STAGE=wind FAILED")
        wind_data = {}

    # =====================================================
    # 4b. FETCH UNIFIED RESOURCE DATA
    #     Reuse already-fetched grid/solar/wind to avoid
    #     duplicate external requests.
    # =====================================================
    logger.info("LOADSHIELD_STAGE=resources START")

    try:
        resource_data = fetch_all_resources(
            prefetched_grid_data=grid_data,
            prefetched_solar_data=solar_data,
            prefetched_wind_data=wind_data,
        )
        logger.info("LOADSHIELD_STAGE=resources SUCCESS keys=%s", list(resource_data.keys())[:8])
    except Exception:
        logger.exception("LOADSHIELD_STAGE=resources FAILED")
        resource_data = {}

    # =====================================================
    # 4c. FETCH BIOMASS POTENTIAL DATA
    # =====================================================
    logger.info("LOADSHIELD_STAGE=biomass START")

    biomass_divisions = None

    try:
        biomass_result = calculate_all_divisions(
            use_fallback=True
        )
        biomass_divisions = biomass_result.get(
            "divisions", {}
        )
        logger.info("LOADSHIELD_STAGE=biomass SUCCESS divisions=%s", len(biomass_divisions) if biomass_divisions else 0)
    except Exception:
        logger.exception("LOADSHIELD_STAGE=biomass FAILED")
        biomass_divisions = None

    # =====================================================
    # 4d. FETCH WASTE-TO-ENERGY POTENTIAL DATA
    # =====================================================
    logger.info("LOADSHIELD_STAGE=waste START")

    waste_zones = None

    try:
        waste_cities = calculate_all_cities()
        waste_zones = map_waste_to_zones(
            waste_cities.get("cities", {})
        )
        logger.info("LOADSHIELD_STAGE=waste SUCCESS zones=%s", len(waste_zones) if waste_zones else 0)
    except Exception:
        logger.exception("LOADSHIELD_STAGE=waste FAILED")
        waste_zones = None

    # =====================================================
    # 5. GENERATE DEMAND FORECAST
    # =====================================================
    logger.info("LOADSHIELD_STAGE=demand_forecast START")

    forecast_data = None
    forecast_peak_deficit = 0.0
    forecast_additional_requirement = 0.0

    try:
        model = train_demand_model()
        forecast_data = forecast_24h_demand(
            demand_mw, model
        )

        forecast_peak = safe_float(
            forecast_data.get("forecast_peak_mw")
        )

        if forecast_peak > supply_mw:
            forecast_peak_deficit = max(
                forecast_peak - supply_mw, 0.0
            )
            forecast_additional_requirement = max(
                forecast_peak - demand_mw, 0.0
            )

        logger.info("LOADSHIELD_STAGE=demand_forecast SUCCESS peak=%s", forecast_data.get("forecast_peak_mw"))
    except Exception:
        logger.exception("LOADSHIELD_STAGE=demand_forecast FAILED")
        forecast_data = None

    # =====================================================
    # 6. IF SUPPLY >= DEMAND
    # =====================================================

    if deficit_mw <= 0:

        forecast_preparation = None

        if (
            forecast_data
            and forecast_peak_deficit > 0
        ):

            forecast_prep_result = optimize(
                demand_mw=forecast_data[
                    "forecast_peak_mw"
                ],
                supply_mw=supply_mw,
                solar_data=solar_data,
                wind_data=wind_data,
                biomass_divisions=biomass_divisions,
                waste_zones=waste_zones,
            )

            forecast_preparation = {
                "status": "PREPARATION_RECOMMENDED",
                "forecast_peak_mw": round(
                    forecast_data["forecast_peak_mw"],
                    1,
                ),
                "peak_timestamp": forecast_data[
                    "peak_timestamp"
                ],
                "expected_additional_requirement_mw":
                    round(
                        forecast_additional_requirement,
                        1,
                    ),
                "expected_deficit_mw": round(
                    forecast_peak_deficit, 1
                ),
                "recommended_deployment":
                    forecast_prep_result[
                        "recommended_deployment"
                    ],
                "data_classification":
                    "MODEL_FORECAST",
            }

        elif forecast_data:

            forecast_preparation = {
                "status": "NO_ACTION_NEEDED",
                "forecast_peak_mw": round(
                    forecast_data["forecast_peak_mw"],
                    1,
                ),
                "peak_timestamp": forecast_data[
                    "peak_timestamp"
                ],
                "message": (
                    "Forecast peak demand is within "
                    "current supply capacity."
                ),
                "data_classification":
                    "MODEL_FORECAST",
            }

        return {
            "project": "PowerFlex BD",
            "module": "LoadShield",
            "status": "SUPPLY_SUFFICIENT",

            "current_situation": {
                "grid": {
                    "demand_mw": round(
                        demand_mw, 3
                    ),
                    "supply_mw": round(
                        supply_mw, 3
                    ),
                    "deficit_mw": 0.0,
                    "load_shedding_mw": round(
                        load_shedding_mw, 3
                    ) if load_shedding_mw else 0.0,
                    "source": "PGCB_OFFICIAL",
                    "data_classification":
                        "OFFICIAL_PGCB",
                },
            },

            "forecast_situation": (
                {
                    "forecast_peak_mw": round(
                        forecast_data[
                            "forecast_peak_mw"
                        ],
                        1,
                    ),
                    "peak_timestamp": forecast_data[
                        "peak_timestamp"
                    ],
                    "current_demand_mw": round(
                        forecast_data[
                            "current_pgcb_demand_mw"
                        ],
                        1,
                    ),
                    "data_classification":
                        "MODEL_FORECAST",
                }
                if forecast_data
                else None
            ),

            "resource_analysis":
                _build_resource_analysis(
                    resource_data,
                    solar_data,
                    wind_data,
                    biomass_divisions,
                    waste_zones,
                ),

            "zone_analysis": [],

            "current_recommendation": {
                "status": "SUPPLY_SUFFICIENT",
                "initial_deficit_mw": 0.0,
                "total_support_mw": 0.0,
                "remaining_gap_mw": 0.0,
                "recommended_deployment": [],
            },

            "forecast_preparation":
                forecast_preparation,

            "message": (
                "Current PGCB supply is sufficient "
                "for the reported demand. "
                "No emergency dispatch is required."
            ),

            "data_source": {
                "grid":
                    "PGCB_OFFICIAL (live)",
                "solar":
                    "Open-Meteo + PowerFlex Solar AI",
                "wind":
                    "Open-Meteo + PowerFlex Wind AI",
                "demand_forecast":
                    "MODEL_FORECAST",
                "hydro": "PGCB ERP",
                "biomass":
                    "FAOSTAT / DLS / BBS / SREDA",
                "waste":
                    "DNCC / DSCC / AIIB / NDB",
                "battery": "PROTOTYPE - assumption",
                "flexible_demand":
                    "PROTOTYPE - assumption",
            },
        }

    # =====================================================
    # 7. RUN OPTIMIZER (CURRENT)
    # =====================================================
    logger.info("LOADSHIELD_STAGE=optimizer START demand=%s supply=%s deficit=%s", demand_mw, supply_mw, deficit_mw)

    try:
        result = optimize(
            demand_mw=demand_mw,
            supply_mw=supply_mw,
            solar_data=solar_data,
            wind_data=wind_data,
            biomass_divisions=biomass_divisions,
            waste_zones=waste_zones,
        )
        logger.info("LOADSHIELD_STAGE=optimizer SUCCESS status=%s remaining_gap=%s", result.get("status"), result.get("remaining_gap_mw"))
    except Exception:
        logger.exception("LOADSHIELD_STAGE=optimizer FAILED")
        raise

    # =====================================================
    # 8. RISK + STATUS
    # =====================================================

    remaining_gap = result["remaining_gap_mw"]

    risk_level = calculate_risk(
        remaining_gap,
        demand_mw,
    )

    if remaining_gap <= 0:
        system_status = "BALANCED"
    elif risk_level == "MODERATE":
        system_status = "WATCH"
    elif risk_level == "HIGH":
        system_status = "STRESSED"
    else:
        system_status = "CRITICAL"

    # =====================================================
    # 9. FORECAST PREPARATION
    # =====================================================

    forecast_preparation = None

    if (
        forecast_data
        and forecast_peak_deficit > 0
    ):

        forecast_prep_result = optimize(
            demand_mw=forecast_data[
                "forecast_peak_mw"
            ],
            supply_mw=supply_mw,
            solar_data=solar_data,
            wind_data=wind_data,
            biomass_divisions=biomass_divisions,
            waste_zones=waste_zones,
        )

        prep_remaining = forecast_prep_result[
            "remaining_gap_mw"
        ]

        prep_risk = calculate_risk(
            prep_remaining,
            forecast_data["forecast_peak_mw"],
        )

        forecast_preparation = {
            "status": "PREPARATION_RECOMMENDED",
            "forecast_peak_mw": round(
                forecast_data["forecast_peak_mw"], 1
            ),
            "peak_timestamp": forecast_data[
                "peak_timestamp"
            ],
            "expected_additional_requirement_mw":
                round(
                    forecast_additional_requirement, 1
                ),
            "expected_deficit_mw": round(
                forecast_peak_deficit, 1
            ),
            "remaining_gap_after_dispatch_mw":
                round(prep_remaining, 1),
            "risk_level": prep_risk,
            "recommended_deployment":
                forecast_prep_result[
                    "recommended_deployment"
                ],
            "data_classification": "MODEL_FORECAST",
        }

    elif forecast_data:

        forecast_preparation = {
            "status": "NO_ACTION_NEEDED",
            "forecast_peak_mw": round(
                forecast_data["forecast_peak_mw"], 1
            ),
            "peak_timestamp": forecast_data[
                "peak_timestamp"
            ],
            "message": (
                "Forecast peak demand is within "
                "current supply capacity."
            ),
            "data_classification": "MODEL_FORECAST",
        }

    # =====================================================
    # 10. RESPONSE
    # =====================================================
    logger.info("LOADSHIELD_STAGE=response status=%s deficit=%s", result.get("status"), deficit_mw)

    return {
        "project": "PowerFlex BD",
        "module": "LoadShield",
        "status": result["status"],

        "current_situation": {
            "grid": {
                "demand_mw": round(demand_mw, 3),
                "supply_mw": round(supply_mw, 3),
                "deficit_mw": round(deficit_mw, 3),
                "load_shedding_mw": round(
                    load_shedding_mw, 3
                ) if load_shedding_mw else 0.0,
                "source": "PGCB_OFFICIAL",
                "data_classification":
                    "OFFICIAL_PGCB",
            },
            "risk_level": risk_level,
            "system_status": system_status,
        },

        "forecast_situation": (
            {
                "forecast_peak_mw": round(
                    forecast_data[
                        "forecast_peak_mw"
                    ],
                    1,
                ),
                "peak_timestamp": forecast_data[
                    "peak_timestamp"
                ],
                "current_demand_mw": round(
                    forecast_data[
                        "current_pgcb_demand_mw"
                    ],
                    1,
                ),
                "data_classification":
                    "MODEL_FORECAST",
            }
            if forecast_data
            else None
        ),

        "resource_analysis":
            _build_resource_analysis(
                resource_data,
                solar_data,
                wind_data,
                biomass_divisions,
                waste_zones,
            ),

        "zone_analysis": result["zone_analysis"],

        "current_recommendation": {
            "status": result["status"],
            "initial_deficit_mw": result[
                "initial_deficit_mw"
            ],
            "total_support_mw": result[
                "total_support_mw"
            ],
            "remaining_gap_mw": result[
                "remaining_gap_mw"
            ],
            "risk_level": risk_level,
            "system_status": system_status,
            "recommended_deployment": result[
                "recommended_deployment"
            ],
        },

        "forecast_preparation":
            forecast_preparation,

            "data_source": {
                "grid": "PGCB / NLDC",
                "solar":
                    "Open-Meteo + PowerFlex Solar AI",
                "wind":
                    "Open-Meteo + PowerFlex Wind AI",
                "demand_forecast": "MODEL_FORECAST",
                "hydro": "PGCB ERP",
                "gas": "PGCB ERP",
                "liquid_fuel": "PGCB ERP",
                "coal": "PGCB ERP",
                "biomass":
                    "FAOSTAT / DLS / BBS / SREDA",
                "waste":
                    "DNCC / DSCC / AIIB / NDB",
                "nuclear": "DATA_UNAVAILABLE",
                "battery": "PROTOTYPE",
                "flexible_demand": "PROTOTYPE",
            },
    }
