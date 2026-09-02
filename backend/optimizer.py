from typing import Any, Dict, List, Optional
import logging

from backend.prototype_config import (
    SOLAR_INSTALLED_MW,
    WIND_INSTALLED_MW,
    BATTERY_POWER_MW,
    FLEXIBLE_DEMAND_MW,
)

logger = logging.getLogger("powerflex.optimizer")


# =========================================================
# POWERFLEX BD - LOADSHIELD OPTIMIZER
# =========================================================
#
# Multi-resource deficit optimization engine.
#
# Architecture:
#   PGCB/NLDC → Demand/Supply → Deficit Calculation
#   → Resource Analysis (Solar, Wind, Hydro, Biomass,
#     Waste-to-Energy, Battery, Flexible Demand)
#   → 9-Zone Evaluation → Best Combination
#   → LoadShield Recommendation
#
# IMPORTANT:
# Solar and Wind use LIVE AI forecast data.
# Biomass uses CALCULATED_FROM_OFFICIAL_DATA.
# Hydro uses OFFICIAL_PGCB (system-wide).
# Waste-to-Energy, Battery, Flexible Demand
# use PROTOTYPE assumptions.
# =========================================================


# =========================================================
# 9 BANGLADESH ZONES
# =========================================================

BANGLADESH_ZONES = [
    "Dhaka",
    "Chittagong",
    "Khulna",
    "Rajshahi",
    "Comilla",
    "Mymensingh",
    "Sylhet",
    "Barishal",
    "Rangpur",
]


# =========================================================
# DIVISION → 9-ZONE MAPPING
# =========================================================
#
# Bangladesh has 8 administrative divisions.
# PowerFlex has 9 zones.
#
# Comilla zone is within Chattogram division.
# For biomass, Comilla receives 30% of Chattogram
# division's calculated potential (based on population
# share: Comilla ~3.4M / Chattogram ~36.1M ≈ 9.4%;
# adjusted to 30% for Comilla district specifically
# within the wider Chattogram division).
#
# All other divisions map 1:1 to their zones.
# =========================================================

DIVISION_TO_ZONE = {
    "Dhaka": "Dhaka",
    "Chattogram": "Chittagong",
    "Rajshahi": "Rajshahi",
    "Khulna": "Khulna",
    "Barishal": "Barishal",
    "Sylhet": "Sylhet",
    "Rangpur": "Rangpur",
    "Mymensingh": "Mymensingh",
}

COMILLA_FRACTION_OF_CHATTOGRAM = 0.30


# =========================================================
# PROTOTYPE RESOURCE ASSUMPTIONS
# =========================================================
#
# These values are NOT official PGCB/NLDC data.
# They are placeholder assumptions for resources
# that do NOT yet have real data.
#
# Biomass has been REMOVED from here — it now uses
# calculated values from biomass_calculator.py.
#
# Waste has been REMOVED from here — it now uses
# calculated values from waste_calculator.py.
#
# Future official plant data should replace this config
# without changing the optimizer logic.
# =========================================================

ZONE_RESOURCE_ASSUMPTIONS = {
    "Dhaka": {
        "hydro_available_mw": 0.0,
    },
    "Chittagong": {
        "hydro_available_mw": 0.0,
    },
    "Khulna": {
        "hydro_available_mw": 0.0,
    },
    "Rajshahi": {
        "hydro_available_mw": 0.0,
    },
    "Comilla": {
        "hydro_available_mw": 0.0,
    },
    "Mymensingh": {
        "hydro_available_mw": 0.0,
    },
    "Sylhet": {
        "hydro_available_mw": 0.0,
    },
    "Barishal": {
        "hydro_available_mw": 0.0,
    },
    "Rangpur": {
        "hydro_available_mw": 0.0,
    },
}


BATTERY_SOC_PERCENT = 80.0

MAX_ZONE_ALLOCATION_PERCENT = 0.40


# =========================================================
# SAFE FLOAT
# =========================================================

def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# =========================================================
# MAP DIVISION BIOMASS TO 9 ZONES
# =========================================================

def map_biomass_to_zones(
    biomass_divisions: Dict[str, Any],
) -> Dict[str, Dict[str, float]]:
    """
    Convert division-wise biomass data to zone-wise.

    Input: biomass_divisions from calculate_all_divisions()
    Output: {zone: {available_mw, dispatchable_mw,
            electricity_potential_mwh_year}}

    Mapping:
      7 divisions → 7 zones (1:1)
      Chattogram division → Chittagong zone (70%)
                        → Comilla zone (30%)
    """

    zone_biomass = {}

    for zone in BANGLADESH_ZONES:
        zone_biomass[zone] = {
            "available_mw": 0.0,
            "dispatchable_mw": 0.0,
            "electricity_potential_mwh_year": 0.0,
        }

    for div_name, div_data in biomass_divisions.items():

        zone = DIVISION_TO_ZONE.get(div_name)

        if zone is None:
            continue

        available = safe_float(
            div_data.get("average_potential_mw")
        )

        dispatchable = safe_float(
            div_data.get("dispatchable_mw")
        )

        electricity = safe_float(
            div_data.get(
                "electricity_potential_mwh_year"
            )
        )

        if div_name == "Chattogram":

            chattogram_share = (
                1.0 - COMILLA_FRACTION_OF_CHATTOGRAM
            )

            zone_biomass["Chittagong"] = {
                "available_mw": round(
                    available * chattogram_share, 2
                ),
                "dispatchable_mw": round(
                    dispatchable * chattogram_share, 2
                ),
                "electricity_potential_mwh_year":
                    round(
                        electricity
                        * chattogram_share,
                        1,
                    ),
            }

            zone_biomass["Comilla"] = {
                "available_mw": round(
                    available
                    * COMILLA_FRACTION_OF_CHATTOGRAM,
                    2,
                ),
                "dispatchable_mw": round(
                    dispatchable
                    * COMILLA_FRACTION_OF_CHATTOGRAM,
                    2,
                ),
                "electricity_potential_mwh_year":
                    round(
                        electricity
                        * COMILLA_FRACTION_OF_CHATTOGRAM,
                        1,
                    ),
            }

        else:

            zone_biomass[zone] = {
                "available_mw": round(available, 2),
                "dispatchable_mw": round(
                    dispatchable, 2
                ),
                "electricity_potential_mwh_year":
                    round(electricity, 1),
            }

    return zone_biomass


# =========================================================
# BUILD ZONE ANALYSIS
# =========================================================

def build_zone_analysis(
    solar_data: Dict[str, Any],
    wind_data: Dict[str, Any],
    biomass_divisions: Optional[
        Dict[str, Any]
    ] = None,
    waste_zones: Optional[
        Dict[str, Any]
    ] = None,
) -> List[Dict[str, Any]]:
    """
    Evaluate all 9 Bangladesh zones.

    For Solar and Wind, use LIVE forecast data
    from existing modules.

    For Biomass, use calculated division-wise data
    from biomass_calculator.py (CALCULATED_FROM_OFFICIAL_DATA).

    For Waste, use calculated city-wise data
    from waste_calculator.py (CALCULATED_FROM_OFFICIAL_DATA).

    For Hydro, use prototype assumptions.
    """

    solar_ranking = {}
    for item in solar_data.get("zone_ranking", []):
        zone = item.get("zone")
        energy = safe_float(
            item.get("expected_energy_mwh_per_1mw_24h")
        )
        if zone:
            solar_ranking[zone] = energy

    wind_ranking = {}
    for item in wind_data.get("zone_ranking", []):
        zone = item.get("zone")
        energy = safe_float(
            item.get("expected_energy_mwh_per_1mw_24h")
        )
        if zone:
            wind_ranking[zone] = energy

    # Extract current-hour generation (more accurate for dispatch)
    solar_current_hour = safe_float(
        solar_data.get("current_hour_generation", {})
        .get("mw_per_1mw_installed", 0.0)
    )
    wind_current_hour = safe_float(
        wind_data.get("current_hour_generation", {})
        .get("mw_per_1mw_installed", 0.0)
    )

    # Map biomass divisions to zones
    zone_biomass = {}
    if biomass_divisions:
        zone_biomass = map_biomass_to_zones(
            biomass_divisions
        )

    # Use pre-mapped waste zone data
    zone_waste = waste_zones or {}

    zone_analysis = []

    for zone in BANGLADESH_ZONES:

        solar_score = solar_ranking.get(zone, 0.0)
        wind_score = wind_ranking.get(zone, 0.0)
        combined_score = solar_score + wind_score

        assumptions = ZONE_RESOURCE_ASSUMPTIONS.get(
            zone, {}
        )

        # Biomass from calculated data
        biomass_info = zone_biomass.get(zone, {})
        biomass_mw = safe_float(
            biomass_info.get("dispatchable_mw")
        )
        biomass_source_label = (
            "CALCULATED - FAOSTAT / DLS / BBS"
            if biomass_mw > 0
            else "CALCULATED - FAOSTAT / DLS / BBS"
        )

        # Waste from calculated data
        waste_info = zone_waste.get(zone, {})
        waste_mw = safe_float(
            waste_info.get("dispatchable_mw")
        )
        waste_source_label = (
            "CALCULATED - City Corporation / "
            "Project Data"
            if waste_mw > 0
            else "CALCULATED - City Corporation / "
            "Project Data"
        )

        zone_entry = {
            "zone": zone,
            "solar_available_mwh_per_1mw_24h": round(
                solar_score, 4
            ),
            "wind_available_mwh_per_1mw_24h": round(
                wind_score, 4
            ),
            "solar_current_hour_mw_per_1mw": round(
                solar_current_hour, 4
            ),
            "wind_current_hour_mw_per_1mw": round(
                wind_current_hour, 4
            ),
            "combined_renewable_score": round(
                combined_score, 4
            ),
            "hydro_available_mw": round(
                assumptions.get(
                    "hydro_available_mw", 0.0
                ),
                2,
            ),
            "biomass_available_mw": round(
                biomass_mw, 2
            ),
            "biomass_electricity_potential_mwh_year":
                round(
                    safe_float(
                        biomass_info.get(
                            "electricity_potential_mwh_year"
                        )
                    ),
                    1,
                ),
            "waste_available_mw": round(
                waste_mw, 2
            ),
            "waste_electricity_potential_mwh_year":
                round(
                    safe_float(
                        waste_info.get(
                            "electricity_mwh_year"
                        )
                    ),
                    1,
                ),
            "resource_source": {
                "solar": (
                    "FORECAST - Open-Meteo "
                    "+ PowerFlex Solar AI (current-hour forecast)"
                ),
                "wind": (
                    "CALCULATED - Open-Meteo "
                    "+ PowerFlex Wind Power Curve (current-hour estimate)"
                ),
                "hydro": "PROTOTYPE - assumption",
                "biomass": biomass_source_label,
                "waste": waste_source_label,
            },
        }

        zone_analysis.append(zone_entry)

    zone_analysis.sort(
        key=lambda z: z["combined_renewable_score"],
        reverse=True,
    )

    for rank, entry in enumerate(
        zone_analysis, start=1
    ):
        entry["rank"] = rank

    return zone_analysis


# =========================================================
# CALCULATE INSTALLED CAPACITY REQUIRED
# =========================================================

def required_installed_capacity(
    support_mw: float,
    generation_per_1mw: float,
) -> float:
    """
    If AI predicts X MW per 1 MW installed,
    and we need Y MW of support:

        required_installed = Y / X

    Returns 0.0 if generation_per_1mw is zero.
    """
    if generation_per_1mw <= 0:
        return 0.0

    return support_mw / generation_per_1mw


# =========================================================
# OPTIMIZE - MAIN DISPATCH ENGINE
# =========================================================

def optimize(
    demand_mw: float,
    supply_mw: float,
    solar_data: Dict[str, Any],
    wind_data: Dict[str, Any],
    biomass_divisions: Optional[
        Dict[str, Any]
    ] = None,
    waste_zones: Optional[
        Dict[str, Any]
    ] = None,
    hydro_total_mw: float = 0.0,
    battery_mw: float = BATTERY_POWER_MW,
    flexible_demand_mw: float = FLEXIBLE_DEMAND_MW,
) -> Dict[str, Any]:
    """
    Multi-resource deficit optimization engine.

    Attempts mathematical (LP) optimization first.
    Falls back to heuristic greedy dispatch if the
    LP solver fails or is unavailable.

    1. Calculate deficit.
    2. If deficit <= 0 → SUPPLY_SUFFICIENT.
    3. If deficit > 0 → find optimal combination across
       9 zones to cover the deficit.
    4. Dispatch only what is needed.
    5. Spread across zones. Max 40% per zone.
    """

    # -----------------------------------------------------
    # TRY MATHEMATICAL OPTIMIZER FIRST
    # -----------------------------------------------------

    try:
        from backend.optimizer_math import (
            optimize_mathematical,
            math_result_to_dict,
        )

        math_result = optimize_mathematical(
            demand_mw=demand_mw,
            supply_mw=supply_mw,
            solar_data=solar_data,
            wind_data=wind_data,
            biomass_divisions=biomass_divisions,
            waste_zones=waste_zones,
            hydro_total_mw=hydro_total_mw,
            battery_mw=battery_mw,
            flexible_demand_mw=flexible_demand_mw,
        )

        if math_result is not None:
            logger.info(
                "Mathematical optimizer succeeded: "
                "status=%s remaining_gap=%.3f",
                math_result.status,
                math_result.remaining_gap,
            )
            return math_result_to_dict(
                math_result,
                solar_data,
                wind_data,
                biomass_divisions,
                waste_zones,
            )

    except ImportError:
        logger.info(
            "optimizer_math not available, "
            "using heuristic optimizer."
        )
    except Exception as e:
        logger.warning(
            "Mathematical optimizer failed (%s), "
            "falling back to heuristic.",
            e,
        )

    # -----------------------------------------------------
    # HEURISTIC FALLBACK
    # -----------------------------------------------------

    return _optimize_heuristic(
        demand_mw,
        supply_mw,
        solar_data,
        wind_data,
        biomass_divisions,
        waste_zones,
        hydro_total_mw,
        battery_mw,
        flexible_demand_mw,
    )


def _optimize_heuristic(
    demand_mw: float,
    supply_mw: float,
    solar_data: Dict[str, Any],
    wind_data: Dict[str, Any],
    biomass_divisions: Optional[
        Dict[str, Any]
    ] = None,
    waste_zones: Optional[
        Dict[str, Any]
    ] = None,
    hydro_total_mw: float = 0.0,
    battery_mw: float = BATTERY_POWER_MW,
    flexible_demand_mw: float = FLEXIBLE_DEMAND_MW,
) -> Dict[str, Any]:
    """
    Heuristic greedy dispatch engine (original algorithm).

    Priority-ordered resource dispatch with zone caps.
    """

    demand = max(0.0, safe_float(demand_mw))
    supply = max(0.0, safe_float(supply_mw))
    deficit = max(demand - supply, 0.0)

    # -----------------------------------------------------
    # SUPPLY SUFFICIENT
    # -----------------------------------------------------

    if deficit <= 0:

        zone_analysis = build_zone_analysis(
            solar_data,
            wind_data,
            biomass_divisions,
            waste_zones,
        )

        return {
            "status": "SUPPLY_SUFFICIENT",
            "initial_deficit_mw": 0.0,
            "total_support_mw": 0.0,
            "remaining_gap_mw": 0.0,
            "zone_analysis": zone_analysis,
            "recommended_deployment": [],
        }

    # -----------------------------------------------------
    # BUILD ZONE ANALYSIS
    # -----------------------------------------------------

    zone_analysis = build_zone_analysis(
        solar_data,
        wind_data,
        biomass_divisions,
        waste_zones,
    )

    # -----------------------------------------------------
    # PREPARE PER-ZONE RESOURCE POOLS
    # -----------------------------------------------------
    #
    # For each zone, calculate how much each resource
    # can contribute based on AI forecast and assumptions.
    #
    # Solar/Wind: AI predicts generation per 1 MW
    # installed. We need an assumed installed capacity
    # per zone to convert to MW.
    #
    # For now we use prototype installed capacities
    # per zone derived from the global totals.
    # -----------------------------------------------------

    # -----------------------------------------------------
    # EXTRACT CURRENT-HOUR GENERATION
    # -----------------------------------------------------
    # Use current-hour generation per 1MW for dispatch.
    # This is more accurate than daily average / 24
    # because solar is zero at night and wind varies hourly.

    solar_current_hour = safe_float(
        solar_data.get("current_hour_generation", {})
        .get("mw_per_1mw_installed", 0.0)
    )
    wind_current_hour = safe_float(
        wind_data.get("current_hour_generation", {})
        .get("mw_per_1mw_installed", 0.0)
    )

    num_zones = len(BANGLADESH_ZONES)

    solar_per_zone_installed = (
        SOLAR_INSTALLED_MW / num_zones
    )
    wind_per_zone_installed = (
        WIND_INSTALLED_MW / num_zones
    )

    zone_pools = []

    for za in zone_analysis:

        zone = za["zone"]

        solar_gen_per_1mw = solar_current_hour
        wind_gen_per_1mw = wind_current_hour

        solar_available_mw = (
            solar_gen_per_1mw * solar_per_zone_installed
        )
        wind_available_mw = (
            wind_gen_per_1mw * wind_per_zone_installed
        )

        hydro_mw = safe_float(
            za.get("hydro_available_mw")
        )
        biomass_mw = safe_float(
            za.get("biomass_available_mw")
        )
        waste_mw = safe_float(
            za.get("waste_available_mw")
        )

        zone_pools.append({
            "zone": zone,
            "solar_available_mw": solar_available_mw,
            "solar_gen_per_1mw": solar_gen_per_1mw,
            "wind_available_mw": wind_available_mw,
            "wind_gen_per_1mw": wind_gen_per_1mw,
            "hydro_available_mw": hydro_mw,
            "biomass_available_mw": biomass_mw,
            "waste_available_mw": waste_mw,
            "combined_score": safe_float(
                za.get("combined_renewable_score")
            ),
        })

    zone_pools.sort(
        key=lambda z: z["combined_score"],
        reverse=True,
    )

    # -----------------------------------------------------
    # DISPATCH ACROSS ZONES
    # -----------------------------------------------------

    remaining_deficit = deficit
    max_per_zone = deficit * MAX_ZONE_ALLOCATION_PERCENT
    deployment = []

    resource_priority = [
        "solar",
        "wind",
        "hydro",
        "biomass",
        "waste",
    ]

    for pool in zone_pools:

        if remaining_deficit <= 0:
            break

        zone = pool["zone"]
        zone_cap = min(max_per_zone, remaining_deficit)
        zone_allocated = 0.0

        for resource in resource_priority:

            if remaining_deficit <= 0:
                break

            if zone_allocated >= zone_cap:
                break

            available_key = f"{resource}_available_mw"
            available_mw = pool.get(available_key, 0.0)

            if available_mw <= 0:
                continue

            room_in_zone = zone_cap - zone_allocated
            support = min(
                available_mw,
                room_in_zone,
                remaining_deficit,
            )

            if support <= 0:
                continue

            gen_key = f"{resource}_gen_per_1mw"
            gen_per_1mw = pool.get(gen_key, 0.0)

            installed_needed = required_installed_capacity(
                support,
                gen_per_1mw,
            )

            reason = _zone_resource_reason(
                resource,
                zone,
                gen_per_1mw,
            )

            deployment.append({
                "rank": len(deployment) + 1,
                "zone": zone,
                "resource": resource.capitalize(),
                "support_mw": round(support, 3),
                "recommended_installed_capacity_mw": round(
                    installed_needed, 2
                ),
                "reason": reason,
            })

            zone_allocated += support
            remaining_deficit -= support

    # -----------------------------------------------------
    # GLOBAL BACKUP: BATTERY
    # -----------------------------------------------------

    if remaining_deficit > 0 and battery_mw > 0:

        support = min(battery_mw, remaining_deficit)

        deployment.append({
            "rank": len(deployment) + 1,
            "zone": "System-wide",
            "resource": "Battery",
            "support_mw": round(support, 3),
            "recommended_installed_capacity_mw": round(
                support, 2
            ),
            "reason": (
                "Renewable resources across all zones "
                "cannot fully close the deficit. "
                "Battery dispatch as backup."
            ),
        })

        remaining_deficit -= support

    # -----------------------------------------------------
    # GLOBAL BACKUP: FLEXIBLE DEMAND
    # -----------------------------------------------------

    if remaining_deficit > 0 and flexible_demand_mw > 0:

        support = min(flexible_demand_mw, remaining_deficit)

        deployment.append({
            "rank": len(deployment) + 1,
            "zone": "System-wide",
            "resource": "Flexible Demand",
            "support_mw": round(support, 3),
            "recommended_installed_capacity_mw": round(
                support, 2
            ),
            "reason": (
                "Demand reduction / load shifting "
                "to cover remaining deficit."
            ),
        })

        remaining_deficit -= support

    # -----------------------------------------------------
    # TOTALS
    # -----------------------------------------------------

    total_support = sum(
        item["support_mw"] for item in deployment
    )

    remaining_gap = max(deficit - total_support, 0.0)

    if remaining_gap <= 0:
        status = "DEFICIT_COVERED"
    else:
        status = "DEFICIT_REMAINS"

    return {
        "status": status,
        "initial_deficit_mw": round(deficit, 3),
        "total_support_mw": round(total_support, 3),
        "remaining_gap_mw": round(remaining_gap, 3),
        "zone_analysis": zone_analysis,
        "recommended_deployment": deployment,
    }


# =========================================================
# REASON GENERATOR
# =========================================================

def _zone_resource_reason(
    resource: str,
    zone: str,
    gen_per_1mw: float,
) -> str:

    if resource == "solar":

        return (
            f"Solar AI forecasts "
            f"{gen_per_1mw:.4f} MW per 1 MW installed "
            f"in {zone}. Highest available solar "
            f"generation in zone pool."
        )

    if resource == "wind":

        return (
            f"Wind AI forecasts "
            f"{gen_per_1mw:.4f} MW per 1 MW installed "
            f"in {zone}. Available wind generation "
            f"in zone pool."
        )

    if resource == "hydro":

        return (
            f"Hydro prototype capacity available "
            f"in {zone}."
        )

    if resource == "biomass":

        return (
            f"Biomass dispatchable capacity from "
            f"calculated crop/livestock data "
            f"in {zone}."
        )

    if resource == "waste":

        return (
            f"Waste-to-Energy calculated capacity "
            f"from city waste data in {zone}."
        )

    return (
        f"{resource} resource available in {zone}."
    )
