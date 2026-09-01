from typing import Any, Dict, List

from backend.biomass_sources import (
    BANGLADESH_DIVISIONS,
    CROP_RESIDUE_RATIOS,
    RECOVERABLE_FRACTION,
    ENERGY_CONTENT_MJ_KG,
    BIOMASS_ELECTRICITY_EFFICIENCY,
    KWH_PER_MJ,
    MANURE_PRODUCTION_KG_DAY,
    MANURE_RECOVERABLE_FRACTION,
    BIOGAS_YIELD_M3_PER_KG,
    METHANE_FRACTION,
    METHANE_ENERGY_MJ_PER_M3,
    BIOGAS_ELECTRICITY_EFFICIENCY,
    WASTE_GENERATION_KG_PERSON_DAY,
    ORGANIC_FRACTION,
    RECOVERABLE_WASTE_FRACTION,
    WTE_ELECTRICITY_EFFICIENCY,
    DIVISION_CROP_SHARE,
    DIVISION_LIVESTOCK_SHARE,
    DIVISION_POPULATION_2022,
    division_share,
)
from backend.biomass_fetcher import (
    fetch_all_biomass_data,
)


# =========================================================
# POWERFLEX BD - BIOMASS CALCULATOR
# =========================================================
#
# Division-wise biomass energy potential calculation.
#
# Methodology:
#   National data → Division distribution
#   → Residue calculation → Energy conversion
#   → Electricity potential → Dispatchable MW
# =========================================================


# =========================================================
# SAFE FLOAT
# =========================================================

def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


# =========================================================
# CROP RESIDUE CALCULATION
# =========================================================

def calculate_crop_residue(
    division: str,
    crop_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Calculate crop residue potential for a division.

    Method:
      national_production
      → division_share
      → residue_ratio
      → recoverable_fraction
      → energy_content
      → electricity_efficiency
      → MWh/year
      → average MW
    """

    division_crops = DIVISION_CROP_SHARE.get(
        division, {}
    )

    total_residue_tonnes = 0.0
    total_energy_gj = 0.0
    crop_details = {}

    residue_map = {
        "rice": [
            "rice_straw",
            "rice_husk",
        ],
        "wheat": ["wheat_straw"],
        "jute": ["jute_stick"],
        "sugarcane": ["sugarcane_bagasse"],
        "maize": [
            "maize_stalks",
            "maize_cobs",
        ],
    }

    for crop_key, crop_share in division_crops.items():

        crop_info = crop_data.get(crop_key, {})

        national_tonnes = safe_float(
            crop_info.get("production_tonnes")
        )

        division_tonnes = (
            national_tonnes * crop_share
        )

        residues = residue_map.get(crop_key, [])

        for residue_key in residues:

            ratio_info = CROP_RESIDUE_RATIOS.get(
                residue_key, {}
            )

            ratio = safe_float(
                ratio_info.get("ratio")
            )

            residue_tonnes = (
                division_tonnes * ratio
            )

            recoverable = safe_float(
                RECOVERABLE_FRACTION.get(
                    residue_key
                )
            )

            recoverable_tonnes = (
                residue_tonnes * recoverable
            )

            ljv = safe_float(
                ENERGY_CONTENT_MJ_KG.get(
                    residue_key
                )
            )

            energy_gj = (
                recoverable_tonnes * 1000 * ljv / 1000
            )

            total_residue_tonnes += residue_tonnes
            total_energy_gj += energy_gj

            crop_details[residue_key] = {
                "residue_tonnes": round(
                    residue_tonnes, 1
                ),
                "recoverable_tonnes": round(
                    recoverable_tonnes, 1
                ),
                "energy_gj": round(energy_gj, 1),
            }

    electricity_mwh = (
        total_energy_gj
        * 1000
        * KWH_PER_MJ
        * BIOMASS_ELECTRICITY_EFFICIENCY
        / 1000
    )

    average_mw = electricity_mwh / 8760

    dispatchable_mw = average_mw * 0.50

    return {
        "crop_residue_tonnes_year": round(
            total_residue_tonnes, 1
        ),
        "recoverable_residue_tonnes_year": round(
            sum(
                d["recoverable_tonnes"]
                for d in crop_details.values()
            ),
            1,
        ),
        "energy_potential_gj_year": round(
            total_energy_gj, 1
        ),
        "electricity_potential_mwh_year": round(
            electricity_mwh, 1
        ),
        "average_potential_mw": round(
            average_mw, 2
        ),
        "dispatchable_mw": round(
            dispatchable_mw, 2
        ),
        "crop_details": crop_details,
    }


# =========================================================
# ANIMAL MANURE CALCULATION
# =========================================================

def calculate_animal_manure(
    division: str,
    livestock_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Calculate animal manure energy potential.

    Method:
      national_population
      → division_share
      → manure_per_animal
      → recoverable_fraction
      → biogas_yield
      → methane_energy
      → electricity
      → MW
    """

    division_livestock = DIVISION_LIVESTOCK_SHARE.get(
        division, {}
    )

    total_manure_tonnes = 0.0
    total_biogas_m3 = 0.0
    total_electricity_mwh = 0.0
    animal_details = {}

    manure_map = {
        "cattle": "cattle",
        "buffalo": "buffalo",
        "goat": "goat",
        "sheep": "sheep",
        "poultry": "chicken",
    }

    for wb_key, div_key in manure_map.items():

        wb_info = livestock_data.get(wb_key, {})

        national_pop = safe_float(
            wb_info.get("population")
        )

        div_share = safe_float(
            division_livestock.get(div_key)
        )

        division_pop = national_pop * div_share

        kg_day = safe_float(
            MANURE_PRODUCTION_KG_DAY.get(div_key)
        )

        manure_kg_year = (
            division_pop * kg_day * 365
        )

        manure_tonnes = manure_kg_year / 1000

        recoverable_tonnes = (
            manure_tonnes
            * MANURE_RECOVERABLE_FRACTION
        )

        biogas_m3 = (
            recoverable_tonnes * 1000
            * BIOGAS_YIELD_M3_PER_KG
        )

        methane_m3 = biogas_m3 * METHANE_FRACTION

        energy_gj = (
            methane_m3
            * METHANE_ENERGY_MJ_PER_M3
            / 1000
        )

        electricity_mwh = (
            energy_gj
            * 1000
            * KWH_PER_MJ
            * BIOGAS_ELECTRICITY_EFFICIENCY
            / 1000
        )

        total_manure_tonnes += manure_tonnes
        total_biogas_m3 += biogas_m3
        total_electricity_mwh += electricity_mwh

        animal_details[wb_key] = {
            "population": round(division_pop, 0),
            "manure_tonnes_year": round(
                manure_tonnes, 1
            ),
            "recoverable_tonnes": round(
                recoverable_tonnes, 1
            ),
            "biogas_m3_year": round(biogas_m3, 1),
        }

    average_mw = total_electricity_mwh / 8760

    dispatchable_mw = average_mw * 0.40

    return {
        "animal_manure_tonnes_year": round(
            total_manure_tonnes, 1
        ),
        "biogas_m3_year": round(
            total_biogas_m3, 1
        ),
        "electricity_potential_mwh_year": round(
            total_electricity_mwh, 1
        ),
        "average_potential_mw": round(
            average_mw, 2
        ),
        "dispatchable_mw": round(
            dispatchable_mw, 2
        ),
        "animal_details": animal_details,
    }


# =========================================================
# ORGANIC WASTE CALCULATION
# =========================================================

def calculate_organic_waste(
    division: str,
) -> Dict[str, Any]:
    """
    Calculate organic municipal waste energy potential.

    Method:
      population
      → waste_per_capita
      → organic_fraction
      → recoverable_fraction
      → biogas/WtE conversion
      → electricity
      → MW
    """

    pop = safe_float(
        DIVISION_POPULATION_2022.get(division)
    )

    waste_tonnes = (
        pop
        * WASTE_GENERATION_KG_PERSON_DAY
        * 365
        / 1000
    )

    organic_tonnes = (
        waste_tonnes * ORGANIC_FRACTION
    )

    recoverable_tonnes = (
        organic_tonnes * RECOVERABLE_WASTE_FRACTION
    )

    biogas_m3 = (
        recoverable_tonnes * 1000
        * BIOGAS_YIELD_M3_PER_KG
    )

    electricity_mwh = (
        recoverable_tonnes * 1000
        * 10  # MJ per tonne (approximate)
        * KWH_PER_MJ
        * WTE_ELECTRICITY_EFFICIENCY
        / 1000
    )

    average_mw = electricity_mwh / 8760

    dispatchable_mw = average_mw * 0.30

    return {
        "organic_waste_tonnes_year": round(
            organic_tonnes, 1
        ),
        "recoverable_waste_tonnes_year": round(
            recoverable_tonnes, 1
        ),
        "biogas_m3_year": round(biogas_m3, 1),
        "electricity_potential_mwh_year": round(
            electricity_mwh, 1
        ),
        "average_potential_mw": round(
            average_mw, 2
        ),
        "dispatchable_mw": round(
            dispatchable_mw, 2
        ),
    }


# =========================================================
# DIVISION-WISE TOTAL
# =========================================================

def calculate_division_biomass(
    division: str,
    crop_data: Dict[str, Any],
    livestock_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Calculate total biomass potential for one division.
    """

    crop = calculate_crop_residue(
        division, crop_data
    )

    manure = calculate_animal_manure(
        division, livestock_data
    )

    waste = calculate_organic_waste(division)

    total_mwh = (
        crop["electricity_potential_mwh_year"]
        + manure["electricity_potential_mwh_year"]
        + waste["electricity_potential_mwh_year"]
    )

    total_average_mw = (
        crop["average_potential_mw"]
        + manure["average_potential_mw"]
        + waste["average_potential_mw"]
    )

    total_dispatchable_mw = (
        crop["dispatchable_mw"]
        + manure["dispatchable_mw"]
        + waste["dispatchable_mw"]
    )

    return {
        "division": division,
        "crop_residue": crop,
        "animal_manure": manure,
        "organic_waste": waste,
        "crop_residue_tonnes_year": crop[
            "crop_residue_tonnes_year"
        ],
        "animal_manure_tonnes_year": manure[
            "animal_manure_tonnes_year"
        ],
        "organic_waste_tonnes_year": waste[
            "organic_waste_tonnes_year"
        ],
        "biogas_m3_year": (
            manure["biogas_m3_year"]
            + waste["biogas_m3_year"]
        ),
        "electricity_potential_mwh_year": round(
            total_mwh, 1
        ),
        "average_potential_mw": round(
            total_average_mw, 2
        ),
        "dispatchable_mw": round(
            total_dispatchable_mw, 2
        ),
    }


# =========================================================
# ALL DIVISIONS
# =========================================================

def calculate_all_divisions(
    use_fallback: bool = False,
) -> Dict[str, Any]:
    """
    Calculate biomass potential for all 8 divisions.
    If use_fallback=True, use published defaults.
    """

    biomass_data = fetch_all_biomass_data(
        use_fallback=use_fallback
    )

    crop_data = biomass_data["crops"]
    livestock_data = biomass_data["livestock"]

    divisions = {}

    total_mwh = 0.0
    total_dispatchable = 0.0

    for div in BANGLADESH_DIVISIONS:

        result = calculate_division_biomass(
            div, crop_data, livestock_data
        )

        divisions[div] = result

        total_mwh += result[
            "electricity_potential_mwh_year"
        ]

        total_dispatchable += result[
            "dispatchable_mw"
        ]

    national_average_mw = total_mwh / 8760

    return {
        "divisions": divisions,
        "national": {
            "electricity_potential_mwh_year": round(
                total_mwh, 1
            ),
            "average_potential_mw": round(
                national_average_mw, 2
            ),
            "total_dispatchable_mw": round(
                total_dispatchable, 2
            ),
        },
        "data_sources": {
            "crop_data": biomass_data[
                "crop_source"
            ],
            "livestock_data": biomass_data[
                "livestock_source"
            ],
            "retrieved_at": biomass_data[
                "retrieved_at"
            ],
        },
    }
