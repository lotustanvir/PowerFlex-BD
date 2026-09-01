from typing import Any, Dict


# =========================================================
# POWERFLEX BD RESOURCE CONFIGURATION
# =========================================================
#
# IMPORTANT:
# These capacities are PROTOTYPE CONFIGURATION VALUES.
# They are NOT claimed to be current Bangladesh grid data.
#
# Once official plant/resource data becomes available,
# these values should be replaced by real connected capacity
# and availability data from approved sources.
#
# DATA SOURCE CLASSIFICATION:
#   LIVE:
#     - PGCB/NLDC grid demand/supply
#     - Open-Meteo weather forecast
#     - PowerFlex Solar AI
#     - PowerFlex Wind AI
#
#   PROTOTYPE:
#     - Hydro assumptions
#     - Biomass assumptions
#     - Waste-to-energy assumptions
#     - Battery assumptions
#     - Flexible demand assumptions
# =========================================================


RESOURCE_CONFIG = {
    "solar": {
        "installed_capacity_mw": 1000.0,
        "dispatchable": False,
        "source_type": "LIVE - AI forecast",
        "data_classification": "LIVE",
    },

    "wind": {
        "installed_capacity_mw": 500.0,
        "dispatchable": False,
        "source_type": "LIVE - AI forecast",
        "data_classification": "LIVE",
    },

    "hydro": {
        "installed_capacity_mw": 230.0,
        "available_capacity_mw": 230.0,
        "dispatchable": True,
        "source_type": "PROTOTYPE - configured resource capacity",
        "data_classification": "PROTOTYPE",
        "note": (
            "Awaiting official plant-level data from "
            "PGCB/BWDB. Do NOT present as live data."
        ),
    },

    "waste": {
        "installed_capacity_mw": 100.0,
        "available_capacity_mw": 100.0,
        "dispatchable": True,
        "source_type": "PROTOTYPE - configured resource capacity",
        "data_classification": "PROTOTYPE",
        "note": (
            "Awaiting official plant-level data. "
            "Do NOT present as live data."
        ),
    },

    "biomass": {
        "installed_capacity_mw": 100.0,
        "available_capacity_mw": 100.0,
        "dispatchable": True,
        "source_type": "PROTOTYPE - configured resource capacity",
        "data_classification": "PROTOTYPE",
        "note": (
            "Awaiting official plant-level data. "
            "Do NOT present as live data."
        ),
    },

    "battery": {
        "power_capacity_mw": 500.0,
        "soc_percent": 80.0,
        "dispatchable": True,
        "source_type": "PROTOTYPE - configured storage",
        "data_classification": "PROTOTYPE",
        "note": (
            "Battery dispatch is system-wide backup. "
            "Awaiting real storage asset data."
        ),
    },

    "flexible_demand": {
        "capacity_mw": 500.0,
        "dispatchable": True,
        "source_type": "PROTOTYPE - configured demand response",
        "data_classification": "PROTOTYPE",
        "note": (
            "Flexible demand is demand reduction, "
            "not generation. Awaiting real DR program data."
        ),
    },
}


# =========================================================
# ZONE-LEVEL RESOURCE ASSUMPTIONS
# =========================================================
#
# Per-zone prototype assumptions for Hydro, Biomass,
# Waste-to-Energy.
#
# Solar and Wind are NOT here because they use
# LIVE AI forecast data from the existing modules.
#
# These values are meant to be replaced by official
# plant-level data when available.
# =========================================================

ZONE_RESOURCE_CONFIG = {
    "Dhaka": {
        "hydro_installed_mw": 0.0,
        "hydro_available_mw": 0.0,
        "biomass_installed_mw": 15.0,
        "biomass_available_mw": 10.0,
        "waste_installed_mw": 20.0,
        "waste_available_mw": 15.0,
        "classification": "PROTOTYPE",
    },
    "Chittagong": {
        "hydro_installed_mw": 0.0,
        "hydro_available_mw": 0.0,
        "biomass_installed_mw": 20.0,
        "biomass_available_mw": 15.0,
        "waste_installed_mw": 15.0,
        "waste_available_mw": 10.0,
        "classification": "PROTOTYPE",
    },
    "Khulna": {
        "hydro_installed_mw": 0.0,
        "hydro_available_mw": 0.0,
        "biomass_installed_mw": 20.0,
        "biomass_available_mw": 15.0,
        "waste_installed_mw": 15.0,
        "waste_available_mw": 10.0,
        "classification": "PROTOTYPE",
    },
    "Rajshahi": {
        "hydro_installed_mw": 0.0,
        "hydro_available_mw": 0.0,
        "biomass_installed_mw": 20.0,
        "biomass_available_mw": 15.0,
        "waste_installed_mw": 15.0,
        "waste_available_mw": 10.0,
        "classification": "PROTOTYPE",
    },
    "Comilla": {
        "hydro_installed_mw": 0.0,
        "hydro_available_mw": 0.0,
        "biomass_installed_mw": 15.0,
        "biomass_available_mw": 10.0,
        "waste_installed_mw": 10.0,
        "waste_available_mw": 5.0,
        "classification": "PROTOTYPE",
    },
    "Mymensingh": {
        "hydro_installed_mw": 0.0,
        "hydro_available_mw": 0.0,
        "biomass_installed_mw": 25.0,
        "biomass_available_mw": 20.0,
        "waste_installed_mw": 10.0,
        "waste_available_mw": 5.0,
        "classification": "PROTOTYPE",
    },
    "Sylhet": {
        "hydro_installed_mw": 0.0,
        "hydro_available_mw": 0.0,
        "biomass_installed_mw": 15.0,
        "biomass_available_mw": 10.0,
        "waste_installed_mw": 10.0,
        "waste_available_mw": 5.0,
        "classification": "PROTOTYPE",
    },
    "Barishal": {
        "hydro_installed_mw": 0.0,
        "hydro_available_mw": 0.0,
        "biomass_installed_mw": 15.0,
        "biomass_available_mw": 10.0,
        "waste_installed_mw": 10.0,
        "waste_available_mw": 5.0,
        "classification": "PROTOTYPE",
    },
    "Rangpur": {
        "hydro_installed_mw": 0.0,
        "hydro_available_mw": 0.0,
        "biomass_installed_mw": 20.0,
        "biomass_available_mw": 15.0,
        "waste_installed_mw": 10.0,
        "waste_available_mw": 5.0,
        "classification": "PROTOTYPE",
    },
}


# =========================================================
# SAFE FLOAT
# =========================================================

def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# =========================================================
# SOLAR AVAILABILITY
# =========================================================

def calculate_solar_available_mw(
    predicted_generation_per_mw: float,
) -> float:

    installed_capacity = safe_float(
        RESOURCE_CONFIG["solar"]["installed_capacity_mw"]
    )

    prediction = max(
        0.0,
        safe_float(predicted_generation_per_mw),
    )

    return min(
        installed_capacity,
        prediction * installed_capacity,
    )


# =========================================================
# WIND AVAILABILITY
# =========================================================

def calculate_wind_available_mw(
    predicted_generation_per_mw: float,
) -> float:

    installed_capacity = safe_float(
        RESOURCE_CONFIG["wind"]["installed_capacity_mw"]
    )

    prediction = max(
        0.0,
        safe_float(predicted_generation_per_mw),
    )

    return min(
        installed_capacity,
        prediction * installed_capacity,
    )


# =========================================================
# RESOURCE AVAILABILITY
# =========================================================

def get_resource_availability(
    solar_prediction_per_mw: float,
    wind_prediction_per_mw: float,
) -> Dict[str, Any]:

    solar_mw = calculate_solar_available_mw(
        solar_prediction_per_mw,
    )

    wind_mw = calculate_wind_available_mw(
        wind_prediction_per_mw,
    )

    hydro_mw = safe_float(
        RESOURCE_CONFIG["hydro"]["available_capacity_mw"]
    )

    waste_mw = safe_float(
        RESOURCE_CONFIG["waste"]["available_capacity_mw"]
    )

    biomass_mw = safe_float(
        RESOURCE_CONFIG["biomass"]["available_capacity_mw"]
    )

    battery_mw = safe_float(
        RESOURCE_CONFIG["battery"]["power_capacity_mw"]
    )

    flexible_demand_mw = safe_float(
        RESOURCE_CONFIG["flexible_demand"]["capacity_mw"]
    )

    renewable_mw = (
        solar_mw
        + wind_mw
        + hydro_mw
        + waste_mw
        + biomass_mw
    )

    total_support_mw = (
        renewable_mw
        + battery_mw
        + flexible_demand_mw
    )

    return {
        "solar_mw": round(solar_mw, 4),
        "wind_mw": round(wind_mw, 4),
        "hydro_mw": round(hydro_mw, 4),
        "waste_mw": round(waste_mw, 4),
        "biomass_mw": round(biomass_mw, 4),
        "battery_mw": round(battery_mw, 4),
        "flexible_demand_mw": round(
            flexible_demand_mw,
            4,
        ),
        "renewable_generation_mw": round(
            renewable_mw,
            4,
        ),
        "total_support_mw": round(
            total_support_mw,
            4,
        ),
        "data_classification": {
            "solar": "LIVE",
            "wind": "LIVE",
            "hydro": "PROTOTYPE",
            "biomass": "PROTOTYPE",
            "waste": "PROTOTYPE",
            "battery": "PROTOTYPE",
            "flexible_demand": "PROTOTYPE",
        },
    }


# =========================================================
# OPTIMIZER
# =========================================================

def optimize_resources(
    demand_mw: float,
    supply_mw: float,
    resources: Dict[str, Any],
) -> Dict[str, Any]:

    demand = max(
        0.0,
        safe_float(demand_mw),
    )

    supply = max(
        0.0,
        safe_float(supply_mw),
    )

    initial_gap = max(
        demand - supply,
        0.0,
    )

    remaining_gap = initial_gap

    dispatch = {}

    # -----------------------------------------------------
    # Renewable resources first
    # -----------------------------------------------------

    renewable_order = [
        "solar_mw",
        "wind_mw",
        "hydro_mw",
        "waste_mw",
        "biomass_mw",
    ]

    for resource in renewable_order:

        available = max(
            0.0,
            safe_float(
                resources.get(resource, 0)
            ),
        )

        dispatched = min(
            available,
            remaining_gap,
        )

        dispatch[resource] = round(
            dispatched,
            4,
        )

        remaining_gap -= dispatched

    # -----------------------------------------------------
    # Battery
    # -----------------------------------------------------

    battery_available = max(
        0.0,
        safe_float(
            resources.get("battery_mw", 0)
        ),
    )

    battery_dispatch = min(
        battery_available,
        remaining_gap,
    )

    dispatch["battery_mw"] = round(
        battery_dispatch,
        4,
    )

    remaining_gap -= battery_dispatch

    # -----------------------------------------------------
    # Flexible demand
    # -----------------------------------------------------

    flexible_available = max(
        0.0,
        safe_float(
            resources.get(
                "flexible_demand_mw",
                0,
            )
        ),
    )

    flexible_reduction = min(
        flexible_available,
        remaining_gap,
    )

    dispatch["flexible_demand_mw"] = round(
        flexible_reduction,
        4,
    )

    remaining_gap -= flexible_reduction

    # -----------------------------------------------------
    # Total support
    # -----------------------------------------------------

    total_support = (
        sum(
            dispatch.get(
                resource,
                0.0,
            )
            for resource in renewable_order
        )
        + dispatch["battery_mw"]
        + dispatch["flexible_demand_mw"]
    )

    adjusted_gap = max(
        initial_gap - total_support,
        0.0,
    )

    adjusted_demand = max(
        demand - total_support,
        0.0,
    )

    # -----------------------------------------------------
    # Result
    # -----------------------------------------------------

    if initial_gap <= 0:
        status = "SUPPLY_SUFFICIENT"

    elif adjusted_gap <= 0:
        status = "DEFICIT_COVERED"

    else:
        status = "DEFICIT_REMAINS"

    return {
        "initial_demand_mw": round(
            demand,
            4,
        ),
        "initial_supply_mw": round(
            supply,
            4,
        ),
        "initial_gap_mw": round(
            initial_gap,
            4,
        ),
        "dispatch": dispatch,
        "total_support_mw": round(
            total_support,
            4,
        ),
        "adjusted_demand_mw": round(
            adjusted_demand,
            4,
        ),
        "remaining_gap_mw": round(
            adjusted_gap,
            4,
        ),
        "status": status,
    }
