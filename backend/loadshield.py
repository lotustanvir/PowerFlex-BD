from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
import json
import logging
import concurrent.futures
from typing import Any, Dict, Optional

from backend.services.grid_service import get_grid_live
from backend.services.solar_service import get_solar_live
from backend.services.wind_service import get_wind_live
from database.connection import get_session
from database.models import LoadshieldDispatch

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
from backend.risk_engine import compute_grid_risk, GridRiskResult


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

# Per-source timeout defaults (seconds)
TIMEOUT_GRID = 60
TIMEOUT_SOLAR = 30
TIMEOUT_WIND = 30
TIMEOUT_RESOURCES = 30
TIMEOUT_BIOMASS = 15
TIMEOUT_WASTE = 15
TIMEOUT_DEMAND_MODEL = 10
TIMEOUT_DEMAND_FORECAST = 30


def safe_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def fetch_with_timeout(
    func,
    *args,
    timeout: int = 30,
    default: Any = None,
    label: str = "unknown",
    **kwargs,
) -> Any:
    """Run *func* in a thread with a hard timeout.

    Returns *default* on timeout or any exception so that
    one slow data source never blocks the entire endpoint.
    """
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(func, *args, **kwargs)
            result = future.result(timeout=timeout)
            logger.info("FETCH_OK label=%s", label)
            return result
    except concurrent.futures.TimeoutError:
        logger.warning("FETCH_TIMEOUT label=%s timeout=%ss", label, timeout)
        return default
    except Exception:
        logger.exception("FETCH_FAILED label=%s", label)
        return default


def _fetch_pair_with_timeout(
    func_a,
    args_a,
    func_b,
    args_b,
    timeout: int = 30,
    default_a: Any = None,
    default_b: Any = None,
    label_a: str = "a",
    label_b: str = "b",
) -> tuple:
    """Run *func_a* and *func_b* concurrently in a shared pool.

    Both run with the same hard *timeout*. If one stalls, the
    other still completes. Returns ``(result_a, result_b)`` where
    a failed/timed-out slot gets its corresponding *default_*.

    The pool is NOT used as a context manager so that a slow
    background thread cannot block the endpoint return.
    """
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    try:
        future_a = pool.submit(func_a, *args_a)
        future_b = pool.submit(func_b, *args_b)

        result_a = default_a
        result_b = default_b

        try:
            result_a = future_a.result(timeout=timeout)
            logger.info("FETCH_OK label=%s", label_a)
        except concurrent.futures.TimeoutError:
            logger.warning("FETCH_TIMEOUT label=%s timeout=%ss", label_a, timeout)
        except Exception:
            logger.exception("FETCH_FAILED label=%s", label_a)

        try:
            result_b = future_b.result(timeout=timeout)
            logger.info("FETCH_OK label=%s", label_b)
        except concurrent.futures.TimeoutError:
            logger.warning("FETCH_TIMEOUT label=%s timeout=%ss", label_b, timeout)
        except Exception:
            logger.exception("FETCH_FAILED label=%s", label_b)

        return result_a, result_b
    finally:
        pool.shutdown(wait=False)


# =========================================================
# DATABASE LOGGING
# =========================================================

def log_dispatch(
    demand_mw, supply_mw, deficit_mw,
    solar_mw, wind_mw, hydro_mw, biomass_mw, waste_mw,
    battery_mw, flexible_mw, remaining_gap,
    status, risk_level, zone_breakdown,
):
    """Log a LoadShield dispatch decision to PostgreSQL."""
    try:
        session = get_session()
        with session:
            dispatch = LoadshieldDispatch(
                timestamp=datetime.now(timezone.utc),
                demand_mw=demand_mw,
                supply_mw=supply_mw,
                deficit_mw=deficit_mw,
                solar_mw=solar_mw,
                wind_mw=wind_mw,
                hydro_mw=hydro_mw,
                biomass_mw=biomass_mw,
                waste_mw=waste_mw,
                battery_mw=battery_mw,
                flexible_mw=flexible_mw,
                remaining_gap=remaining_gap,
                status=status,
                risk_level=risk_level,
                zone_breakdown=zone_breakdown,
            )
            session.add(dispatch)
            session.commit()
            logger.info(f"Dispatch logged: status={status}, risk={risk_level}, deficit={deficit_mw}")
    except Exception as e:
        logger.error(f"Failed to log dispatch: {e}")


# =========================================================
# RISK — delegated to risk_engine.py
# =========================================================

def calculate_risk(
    gap_mw,
    demand_mw,
):
    """Legacy helper kept for backward-compat callers."""
    if demand_mw is None or demand_mw <= 0:
        return "UNKNOWN"
    if gap_mw <= 0:
        return "LOW"
    gap_percent = (gap_mw / demand_mw) * 100
    if gap_percent <= 5:
        return "MODERATE"
    if gap_percent <= 15:
        return "HIGH"
    return "CRITICAL"


def _build_risk_assessment(
    demand_mw: float,
    supply_mw: float,
    solar_data: Dict[str, Any],
    wind_data: Dict[str, Any],
    biomass_divisions: Optional[Dict[str, Any]],
    waste_zones: Optional[Dict[str, Any]],
    load_shedding_mw: float = 0.0,
) -> GridRiskResult:
    """Run the full Grid Risk Score engine."""
    from backend.optimizer import SOLAR_INSTALLED_MW, WIND_INSTALLED_MW

    return compute_grid_risk(
        demand_mw=demand_mw,
        supply_mw=supply_mw,
        solar_data=solar_data,
        wind_data=wind_data,
        biomass_data=biomass_divisions,
        waste_data=waste_zones,
        load_shedding_mw=load_shedding_mw,
        solar_installed_mw=SOLAR_INSTALLED_MW,
        wind_installed_mw=WIND_INSTALLED_MW,
        include_scenarios=True,
    )


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
            "data_source": "PGCB ERP (generation) + Open-Meteo + Solar AI (forecast)",
            "data_classification":
                "OFFICIAL_PGCB (generation) / FORECAST (AI prediction)",
            "is_bangladesh_data": True,
            "is_current": True,
            "usable_for_dispatch": False,
            "note": (
                "Current generation from PGCB ERP is official. "
                "Zone forecasts are weather-driven model predictions, "
                "not measured plant output."
            ),
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
            "data_source": "PGCB ERP (generation) + Open-Meteo + Wind Power Curve (estimate)",
            "data_classification":
                "OFFICIAL_PGCB (generation) / CALCULATED (power curve estimate)",
            "is_bangladesh_data": True,
            "is_current": True,
            "usable_for_dispatch": False,
            "note": (
                "Current generation from PGCB ERP is official. "
                "Zone estimates are engineering model outputs, "
                "not measured turbine generation."
            ),
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
    # 1. FETCH REAL GRID DATA (per-source timeout)
    # =====================================================
    logger.info("LOADSHIELD_STAGE=grid START")

    grid_data = fetch_with_timeout(
        get_grid_live,
        timeout=TIMEOUT_GRID,
        default=None,
        label="grid_live",
    )

    if grid_data is None:
        logger.error("LOADSHIELD_STAGE=grid FAILED result=None")
        raise HTTPException(
            status_code=502,
            detail="Grid service returned no data.",
        )

    logger.info(
        "LOADSHIELD_STAGE=grid SUCCESS connected=%s live=%s",
        grid_data.get("connected"),
        grid_data.get("live"),
    )

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

            "grid_risk": None,

            "message":
                (
                    "Official PGCB/NLDC data required "
                    "before making a real grid decision. "
                    "LoadShield will not use hardcoded "
                    "demand or supply values. "
                    "Note: LoadShield provides scenario-based "
                    "recommendations, not real-time dispatch commands."
                ),

            "data_source": {
                "grid":
                    "PGCB / NLDC (not connected)",
                "solar":
                    "Open-Meteo + PowerFlex Solar AI (FORECAST)",
                "wind":
                    "Open-Meteo + PowerFlex Wind Power Curve (CALCULATED)",
                "demand_forecast":
                    "MODEL_FORECAST (synthetic training data)",
                "hydro": "PGCB ERP",
                "biomass":
                    "FAOSTAT / DLS / BBS / SREDA (CALCULATED)",
                "waste":
                    "DNCC / DSCC / AIIB / NDB (CALCULATED)",
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
        logger.error(
            "LOADSHIELD_STAGE=extract FAILED grid_data=%s",
            list(grid_data.keys()) if grid_data else None,
        )
        raise HTTPException(
            status_code=502,
            detail="PGCB grid snapshot is missing.",
        )

    demand_mw = safe_float(grid.get("current_demand_mw"))
    supply_mw = safe_float(grid.get("supply_mw"))
    load_shedding_mw = safe_float(grid.get("load_shedding_mw"))

    logger.info(
        "LOADSHIELD_STAGE=extract SUCCESS demand=%s supply=%s load_shed=%s",
        demand_mw, supply_mw, load_shedding_mw,
    )

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

            "grid_risk": None,

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

            "grid_risk": None,

            "message": (
                "PGCB supply data is unavailable."
            ),
        }

    # =====================================================
    # 3. CALCULATE DEFICIT
    # =====================================================

    deficit_mw = max(demand_mw - supply_mw, 0.0)

    # =====================================================
    # 4. FETCH SOLAR + WIND AI FORECASTS (concurrent, per-source timeout)
    # =====================================================
    logger.info("LOADSHIELD_STAGE=solar_wind START")

    solar_data, wind_data = _fetch_pair_with_timeout(
        func_a=get_solar_live,
        args_a=(),
        func_b=get_wind_live,
        args_b=(),
        timeout=max(TIMEOUT_SOLAR, TIMEOUT_WIND),
        default_a={},
        default_b={},
        label_a="solar_live",
        label_b="wind_live",
    )

    if solar_data and solar_data.get("status") in ("ERROR", "DATA_UNAVAILABLE"):
        solar_data = {}

    if wind_data and wind_data.get("status") in ("ERROR", "DATA_UNAVAILABLE"):
        wind_data = {}

    # =====================================================
    # 4b. FETCH UNIFIED RESOURCE DATA
    # =====================================================
    logger.info("LOADSHIELD_STAGE=resources START")

    resource_data = fetch_with_timeout(
        fetch_all_resources,
        prefetched_grid_data=grid_data,
        prefetched_solar_data=solar_data,
        prefetched_wind_data=wind_data,
        timeout=TIMEOUT_RESOURCES,
        default={},
        label="resources",
    )

    # =====================================================
    # 4c. FETCH BIOMASS POTENTIAL DATA (parallel)
    # =====================================================
    logger.info("LOADSHIELD_STAGE=biomass START")

    biomass_raw = fetch_with_timeout(
        calculate_all_divisions,
        True,
        timeout=TIMEOUT_BIOMASS,
        default=None,
        label="biomass",
    )
    biomass_divisions = biomass_raw.get("divisions", {}) if biomass_raw else None

    # =====================================================
    # 4d. FETCH WASTE-TO-ENERGY POTENTIAL DATA (parallel)
    # =====================================================
    logger.info("LOADSHIELD_STAGE=waste START")

    waste_cities = fetch_with_timeout(
        calculate_all_cities,
        timeout=TIMEOUT_WASTE,
        default=None,
        label="waste",
    )
    waste_zones = (
        map_waste_to_zones(waste_cities.get("cities", {}))
        if waste_cities
        else None
    )

    # =====================================================
    # 5. GENERATE DEMAND FORECAST
    # =====================================================
    logger.info("LOADSHIELD_STAGE=demand_forecast START")

    forecast_data = None
    forecast_peak_deficit = 0.0
    forecast_additional_requirement = 0.0

    model = fetch_with_timeout(
        train_demand_model,
        timeout=TIMEOUT_DEMAND_MODEL,
        default=None,
        label="demand_model",
    )
    if model is not None:
        forecast_data = fetch_with_timeout(
            forecast_24h_demand,
            demand_mw,
            model,
            timeout=TIMEOUT_DEMAND_FORECAST,
            default=None,
            label="demand_forecast",
        )

    if forecast_data:
        forecast_peak = safe_float(forecast_data.get("forecast_peak_mw"))
        if forecast_peak and forecast_peak > supply_mw:
            forecast_peak_deficit = max(forecast_peak - supply_mw, 0.0)
            forecast_additional_requirement = max(forecast_peak - demand_mw, 0.0)
        logger.info(
            "LOADSHIELD_STAGE=demand_forecast SUCCESS peak=%s",
            forecast_data.get("forecast_peak_mw"),
        )

    # =====================================================
    # 5b. COMPUTE GRID RISK SCORE
    # =====================================================
    logger.info("LOADSHIELD_STAGE=risk START")

    risk_result = _build_risk_assessment(
        demand_mw=demand_mw,
        supply_mw=supply_mw,
        solar_data=solar_data,
        wind_data=wind_data,
        biomass_divisions=biomass_divisions,
        waste_zones=waste_zones,
        load_shedding_mw=load_shedding_mw or 0.0,
    )

    risk_level = risk_result.risk_level
    grid_risk_dict = risk_result.to_dict()

    # =====================================================
    # 6. IF SUPPLY >= DEMAND
    # =====================================================

    if deficit_mw <= 0:

        forecast_preparation = None

        if forecast_data and forecast_peak_deficit > 0:

            forecast_prep_result = optimize(
                demand_mw=forecast_data["forecast_peak_mw"],
                supply_mw=supply_mw,
                solar_data=solar_data,
                wind_data=wind_data,
                biomass_divisions=biomass_divisions,
                waste_zones=waste_zones,
            )

            forecast_preparation = {
                "status": "PREPARATION_RECOMMENDED",
                "forecast_peak_mw": round(
                    forecast_data["forecast_peak_mw"], 1,
                ),
                "peak_timestamp": forecast_data["peak_timestamp"],
                "expected_additional_requirement_mw":
                    round(forecast_additional_requirement, 1),
                "expected_deficit_mw": round(forecast_peak_deficit, 1),
                "recommended_deployment":
                    forecast_prep_result["recommended_deployment"],
                "data_classification": "MODEL_FORECAST",
            }

        elif forecast_data:

            forecast_preparation = {
                "status": "NO_ACTION_NEEDED",
                "forecast_peak_mw": round(
                    forecast_data["forecast_peak_mw"], 1,
                ),
                "peak_timestamp": forecast_data["peak_timestamp"],
                "message": (
                    "Forecast peak demand is within "
                    "current supply capacity."
                ),
                "data_classification": "MODEL_FORECAST",
            }

        log_dispatch(
            demand_mw=demand_mw,
            supply_mw=supply_mw,
            deficit_mw=0.0,
            solar_mw=resource_data.get("solar", {}).get("generation_mw"),
            wind_mw=resource_data.get("wind", {}).get("generation_mw"),
            hydro_mw=resource_data.get("hydro", {}).get("generation_mw"),
            biomass_mw=resource_data.get("biomass", {}).get("generation_mw"),
            waste_mw=resource_data.get("waste", {}).get("generation_mw"),
            battery_mw=BATTERY_POWER_MW,
            flexible_mw=FLEXIBLE_DEMAND_MW,
            remaining_gap=0.0,
            status="SUPPLY_SUFFICIENT",
            risk_level=risk_level,
            zone_breakdown=json.dumps([]),
        )

        return {
            "project": "PowerFlex BD",
            "module": "LoadShield",
            "status": "SUPPLY_SUFFICIENT",

            "current_situation": {
                "grid": {
                    "demand_mw": round(demand_mw, 3),
                    "supply_mw": round(supply_mw, 3),
                    "deficit_mw": 0.0,
                    "load_shedding_mw": round(
                        load_shedding_mw, 3
                    ) if load_shedding_mw else 0.0,
                    "source": "PGCB_OFFICIAL",
                    "data_classification": "OFFICIAL_PGCB",
                },
                "risk_level": risk_level,
                "system_status": "BALANCED",
            },

            "forecast_situation": (
                {
                    "forecast_peak_mw": round(
                        forecast_data["forecast_peak_mw"], 1,
                    ),
                    "peak_timestamp": forecast_data["peak_timestamp"],
                    "current_demand_mw": round(
                        forecast_data["current_pgcb_demand_mw"], 1,
                    ),
                    "data_classification": "MODEL_FORECAST",
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

            "forecast_preparation": forecast_preparation,

            "grid_risk": grid_risk_dict,

            "message": (
                "Current PGCB supply is sufficient "
                "for the reported demand. "
                "No emergency dispatch is required. "
                "Note: This analysis provides scenario-based "
                "recommendations only."
            ),

            "data_source": {
                "grid": "PGCB_OFFICIAL (live)",
                "solar": "Open-Meteo + PowerFlex Solar AI",
                "wind": "Open-Meteo + PowerFlex Wind AI",
                "demand_forecast": "MODEL_FORECAST",
                "hydro": "PGCB ERP",
                "biomass": "FAOSTAT / DLS / BBS / SREDA",
                "waste": "DNCC / DSCC / AIIB / NDB",
                "battery": "PROTOTYPE - assumption",
                "flexible_demand": "PROTOTYPE - assumption",
            },
        }

    # =====================================================
    # 7. RUN OPTIMIZER (CURRENT)
    # =====================================================
    logger.info(
        "LOADSHIELD_STAGE=optimizer START demand=%s supply=%s deficit=%s",
        demand_mw, supply_mw, deficit_mw,
    )

    try:
        result = optimize(
            demand_mw=demand_mw,
            supply_mw=supply_mw,
            solar_data=solar_data,
            wind_data=wind_data,
            biomass_divisions=biomass_divisions,
            waste_zones=waste_zones,
        )
        logger.info(
            "LOADSHIELD_STAGE=optimizer SUCCESS status=%s remaining_gap=%s",
            result.get("status"), result.get("remaining_gap_mw"),
        )
    except Exception:
        logger.exception("LOADSHIELD_STAGE=optimizer FAILED")
        raise

    # =====================================================
    # 8. SYSTEM STATUS
    # =====================================================

    remaining_gap = result["remaining_gap_mw"]

    if remaining_gap <= 0:
        system_status = "BALANCED"
    elif risk_level == "MODERATE":
        system_status = "WATCH"
    elif risk_level == "ELEVATED":
        system_status = "STRESSED"
    else:
        system_status = "CRITICAL"

    # =====================================================
    # 9. FORECAST PREPARATION
    # =====================================================

    forecast_preparation = None

    if forecast_data and forecast_peak_deficit > 0:

        forecast_prep_result = optimize(
            demand_mw=forecast_data["forecast_peak_mw"],
            supply_mw=supply_mw,
            solar_data=solar_data,
            wind_data=wind_data,
            biomass_divisions=biomass_divisions,
            waste_zones=waste_zones,
        )

        prep_remaining = forecast_prep_result["remaining_gap_mw"]

        prep_risk = calculate_risk(
            prep_remaining,
            forecast_data["forecast_peak_mw"],
        )

        forecast_preparation = {
            "status": "PREPARATION_RECOMMENDED",
            "forecast_peak_mw": round(
                forecast_data["forecast_peak_mw"], 1,
            ),
            "peak_timestamp": forecast_data["peak_timestamp"],
            "expected_additional_requirement_mw":
                round(forecast_additional_requirement, 1),
            "expected_deficit_mw": round(forecast_peak_deficit, 1),
            "remaining_gap_after_dispatch_mw":
                round(prep_remaining, 1),
            "risk_level": prep_risk,
            "recommended_deployment":
                forecast_prep_result["recommended_deployment"],
            "data_classification": "MODEL_FORECAST",
        }

    elif forecast_data:

        forecast_preparation = {
            "status": "NO_ACTION_NEEDED",
            "forecast_peak_mw": round(
                forecast_data["forecast_peak_mw"], 1,
            ),
            "peak_timestamp": forecast_data["peak_timestamp"],
            "message": (
                "Forecast peak demand is within "
                "current supply capacity."
            ),
            "data_classification": "MODEL_FORECAST",
        }

    # =====================================================
    # 10. LOG DISPATCH + RESPONSE
    # =====================================================
    logger.info(
        "LOADSHIELD_STAGE=response status=%s deficit=%s",
        result.get("status"), deficit_mw,
    )

    log_dispatch(
        demand_mw=demand_mw,
        supply_mw=supply_mw,
        deficit_mw=deficit_mw,
        solar_mw=resource_data.get("solar", {}).get("generation_mw"),
        wind_mw=resource_data.get("wind", {}).get("generation_mw"),
        hydro_mw=resource_data.get("hydro", {}).get("generation_mw"),
        biomass_mw=resource_data.get("biomass", {}).get("generation_mw"),
        waste_mw=resource_data.get("waste", {}).get("generation_mw"),
        battery_mw=BATTERY_POWER_MW,
        flexible_mw=FLEXIBLE_DEMAND_MW,
        remaining_gap=remaining_gap,
        status=result["status"],
        risk_level=risk_level,
        zone_breakdown=json.dumps(result["zone_analysis"]),
    )

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
                "data_classification": "OFFICIAL_PGCB",
            },
            "risk_level": risk_level,
            "system_status": system_status,
        },

        "forecast_situation": (
            {
                "forecast_peak_mw": round(
                    forecast_data["forecast_peak_mw"], 1,
                ),
                "peak_timestamp": forecast_data["peak_timestamp"],
                "current_demand_mw": round(
                    forecast_data["current_pgcb_demand_mw"], 1,
                ),
                "data_classification": "MODEL_FORECAST",
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
            "initial_deficit_mw": result["initial_deficit_mw"],
            "total_support_mw": result["total_support_mw"],
            "remaining_gap_mw": result["remaining_gap_mw"],
            "risk_level": risk_level,
            "system_status": system_status,
            "recommended_deployment": result["recommended_deployment"],
        },

        "forecast_preparation": forecast_preparation,

        "grid_risk": grid_risk_dict,

        "data_source": {
            "grid": "PGCB / NLDC (official)",
            "solar": "Open-Meteo + PowerFlex Solar AI (FORECAST)",
            "wind": "Open-Meteo + PowerFlex Wind Power Curve (CALCULATED)",
            "demand_forecast": "MODEL_FORECAST (synthetic training data)",
            "hydro": "PGCB ERP",
            "gas": "PGCB ERP",
            "liquid_fuel": "PGCB ERP",
            "coal": "PGCB ERP",
            "biomass": "FAOSTAT / DLS / BBS / SREDA (CALCULATED)",
            "waste": "DNCC / DSCC / AIIB / NDB (CALCULATED)",
            "nuclear": "DATA_UNAVAILABLE",
            "battery": "PROTOTYPE",
            "flexible_demand": "PROTOTYPE",
        },
    }
