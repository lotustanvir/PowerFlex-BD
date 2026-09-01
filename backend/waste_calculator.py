from typing import Any, Dict

from backend.waste_sources import (
    WTE_PROJECTS,
    CITY_WASTE_GENERATION,
    WASTE_CONVERSION,
    DIVISION_TO_ZONE,
    COMILLA_FRACTION_OF_CHATTOGRAM,
)


# =========================================================
# POWERFLEX BD - WASTE CALCULATOR
# =========================================================
#
# Calculates waste-to-electricity potential from:
#   1. Documented project capacity (if under construction)
#   2. City waste generation data (calculated potential)
#
# Methodology:
#   waste_tonnes/day
#   → recovery_fraction
#   → LHV (MJ/kg)
#   → electricity_efficiency
#   → MWh/day
#   → MW average
# =========================================================


# =========================================================
# SAFE FLOAT
# =========================================================

def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


# =========================================================
# CALCULATE PROJECT CAPACITY
# =========================================================

def calculate_project_capacity() -> Dict[str, Any]:
    """
    Return documented project capacities.
    Only projects with actual/planned capacity included.
    """

    total_operational_mw = 0.0
    total_planned_mw = 0.0
    projects = []

    for proj in WTE_PROJECTS:

        status = proj.get("status", {})
        capacity = proj.get("capacity", {})
        mw = safe_float(
            capacity.get("installed_capacity_mw")
        )

        is_operational = status.get(
            "operational", False
        )
        is_generating = status.get(
            "generating", False
        )

        if is_operational and is_generating:
            total_operational_mw += mw
        else:
            total_planned_mw += mw

        projects.append({
            "project_name": proj["project_name"],
            "project_id": proj["project_id"],
            "location": proj["location"],
            "installed_capacity_mw": mw,
            "waste_input_tonnes_day": safe_float(
                proj.get("waste_input", {}).get(
                    "daily_waste_tonnes"
                )
            ),
            "status": status.get(
                "current", "UNKNOWN"
            ),
            "operational": is_operational,
            "generating": is_generating,
            "expected_cod": proj.get(
                "timeline", {}
            ).get("expected_cod"),
            "technology": proj.get(
                "technology", {}
            ).get("type"),
            "data_classification": proj.get(
                "data_classification"
            ),
            "source": proj.get("source", {}).get(
                "name"
            ),
        })

    return {
        "total_operational_mw": round(
            total_operational_mw, 2
        ),
        "total_planned_mw": round(
            total_planned_mw, 2
        ),
        "projects": projects,
    }


# =========================================================
# CALCULATE CITY WASTE POTENTIAL
# =========================================================

def calculate_city_waste_potential(
    city: str,
    daily_waste_tonnes: float,
) -> Dict[str, Any]:
    """
    Calculate waste-to-electricity potential for a city.

    Method:
      daily_waste × recovery_fraction × LHV
      × efficiency × kwh_per_mj / 1000
      = MWh/day
      = MW average
    """

    conv = WASTE_CONVERSION

    recovery = safe_float(
        conv.get("recovery_fraction", 0.50)
    )

    lhv = safe_float(
        conv.get("lhv_mj_kg", 7.0)
    )

    efficiency = safe_float(
        conv.get("incineration_efficiency_pct", 0.22)
    )

    kwh_per_mj = safe_float(
        conv.get("kwh_per_mj", 1.0 / 3.6)
    )

    recoverable_tonnes = (
        daily_waste_tonnes * recovery
    )

    recoverable_kg = recoverable_tonnes * 1000

    energy_mj = recoverable_kg * lhv

    electricity_kwh = (
        energy_mj * kwh_per_mj * efficiency
    )

    electricity_mwh_day = electricity_kwh / 1000

    electricity_mwh_year = electricity_mwh_day * 365

    average_mw = electricity_mwh_day / 24

    dispatchable_mw = average_mw * 0.80

    return {
        "city": city,
        "daily_waste_tonnes": round(
            daily_waste_tonnes, 1
        ),
        "recoverable_tonnes_day": round(
            recoverable_tonnes, 1
        ),
        "energy_potential_gj_day": round(
            energy_mj / 1000, 1
        ),
        "electricity_mwh_day": round(
            electricity_mwh_day, 1
        ),
        "electricity_mwh_year": round(
            electricity_mwh_year, 1
        ),
        "average_potential_mw": round(
            average_mw, 2
        ),
        "dispatchable_mw": round(
            dispatchable_mw, 2
        ),
    }


# =========================================================
# CALCULATE ALL CITIES
# =========================================================

def calculate_all_cities() -> Dict[str, Any]:
    """
    Calculate waste-to-electricity potential for all cities.
    """

    cities = {}

    total_daily_waste = 0.0
    total_mwh_day = 0.0
    total_dispatchable = 0.0

    for city, data in CITY_WASTE_GENERATION.items():

        daily = safe_float(
            data.get("daily_waste_tonnes")
        )

        result = calculate_city_waste_potential(
            city, daily
        )

        cities[city] = result

        total_daily_waste += daily
        total_mwh_day += safe_float(
            result.get("electricity_mwh_day")
        )
        total_dispatchable += safe_float(
            result.get("dispatchable_mw")
        )

    total_mwh_year = total_mwh_day * 365
    total_average_mw = total_mwh_day / 24

    return {
        "cities": cities,
        "national": {
            "total_daily_waste_tonnes": round(
                total_daily_waste, 1
            ),
            "total_mwh_day": round(
                total_mwh_day, 1
            ),
            "total_mwh_year": round(
                total_mwh_year, 1
            ),
            "total_average_mw": round(
                total_average_mw, 2
            ),
            "total_dispatchable_mw": round(
                total_dispatchable, 2
            ),
        },
        "conversion_factors": WASTE_CONVERSION,
    }


# =========================================================
# MAP TO 9 ZONES
# =========================================================

def map_waste_to_zones(
    city_potentials: Dict[str, Any],
) -> Dict[str, Dict[str, float]]:
    """
    Map city waste potentials to PowerFlex 9 zones.
    """

    zone_waste = {}

    zone_mapping = {
        "Dhaka": "Dhaka",
        "Chattogram": "Chittagong",
        "Rajshahi": "Rajshahi",
        "Khulna": "Khulna",
        "Barishal": "Barishal",
        "Sylhet": "Sylhet",
        "Rangpur": "Rangpur",
        "Mymensingh": "Mymensingh",
        "Comilla": "Chittagong",
    }

    for zone in [
        "Dhaka", "Chittagong", "Khulna",
        "Rajshahi", "Comilla", "Mymensingh",
        "Sylhet", "Barishal", "Rangpur",
    ]:
        zone_waste[zone] = {
            "available_mw": 0.0,
            "dispatchable_mw": 0.0,
            "electricity_mwh_year": 0.0,
        }

    for city, city_data in city_potentials.items():

        zone = zone_mapping.get(city)

        if zone is None:
            continue

        mw = safe_float(
            city_data.get("dispatchable_mw")
        )

        mwh_year = safe_float(
            city_data.get("electricity_mwh_year")
        )

        if city == "Chattogram":

            chattogram_share = (
                1.0 - COMILLA_FRACTION_OF_CHATTOGRAM
            )

            zone_waste["Chittagong"] = {
                "available_mw": round(
                    mw * chattogram_share, 2
                ),
                "dispatchable_mw": round(
                    mw * chattogram_share, 2
                ),
                "electricity_mwh_year": round(
                    mwh_year * chattogram_share, 1
                ),
            }

            zone_waste["Comilla"] = {
                "available_mw": round(
                    mw
                    * COMILLA_FRACTION_OF_CHATTOGRAM,
                    2,
                ),
                "dispatchable_mw": round(
                    mw
                    * COMILLA_FRACTION_OF_CHATTOGRAM,
                    2,
                ),
                "electricity_mwh_year": round(
                    mwh_year
                    * COMILLA_FRACTION_OF_CHATTOGRAM,
                    1,
                ),
            }

        else:

            zone_waste[zone] = {
                "available_mw": round(mw, 2),
                "dispatchable_mw": round(mw, 2),
                "electricity_mwh_year": round(
                    mwh_year, 1
                ),
            }

    return zone_waste
