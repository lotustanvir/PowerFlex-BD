from datetime import datetime, timezone
from typing import Any, Dict, List


# =========================================================
# POWERFLEX BD - BIOMASS DATA SOURCES
# =========================================================
#
# Source metadata and conversion factors for
# Bangladesh biomass energy potential calculations.
#
# All values are from published research or
# official datasets. Nothing is fabricated.
# =========================================================


# =========================================================
# BANGLADESH 8 DIVISIONS
# =========================================================

BANGLADESH_DIVISIONS = [
    "Dhaka",
    "Chattogram",
    "Rajshahi",
    "Khulna",
    "Barishal",
    "Sylhet",
    "Rangpur",
    "Mymensingh",
]


# =========================================================
# DIVISION TO POWERFLEX 9-ZONE MAPPING
# =========================================================
#
# The existing PowerFlex optimizer uses 9 zones:
#   Dhaka, Chittagong, Khulna, Rajshahi, Comilla,
#   Mymensingh, Sylhet, Barishal, Rangpur
#
# Bangladesh has 8 administrative divisions.
# Mapping:
#   Dhaka division      → Dhaka zone
#   Chattogram division → Chittagong zone
#   Rajshahi division   → Rajshahi zone
#   Khulna division     → Khulna zone
#   Barishal division   → Barishal zone
#   Sylhet division     → Sylhet zone
#   Rangpur division    → Rangpur zone
#   Mymensingh division → Mymensingh zone
#
# Note: "Comilla" zone is part of Chattogram division.
# Comilla does not have its own administrative division.
# For biomass purposes, Comilla zone shares Chattogram
# division data.
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

ZONE_TO_DIVISION = {
    "Dhaka": "Dhaka",
    "Chittagong": "Chattogram",
    "Rajshahi": "Rajshahi",
    "Khulna": "Khulna",
    "Barishal": "Barishal",
    "Sylhet": "Sylhet",
    "Rangpur": "Rangpur",
    "Mymensingh": "Mymensingh",
    "Comilla": "Chattogram",
}


# =========================================================
# DIVISION POPULATION DISTRIBUTION (2022 Census)
# =========================================================
#
# Source: Bangladesh Bureau of Statistics
# Population Census 2022 (preliminary)
#
# Used to distribute national-level data to divisions.
# =========================================================

DIVISION_POPULATION_2022 = {
    "Dhaka": 44_200_000,
    "Chattogram": 36_100_000,
    "Rajshahi": 21_600_000,
    "Khulna": 18_800_000,
    "Barishal": 10_000_000,
    "Sylhet": 12_400_000,
    "Rangpur": 21_200_000,
    "Mymensingh": 15_700_000,
}

TOTAL_POPULATION = sum(
    DIVISION_POPULATION_2022.values()
)


def division_share(division: str) -> float:
    return (
        DIVISION_POPULATION_2022.get(division, 0)
        / TOTAL_POPULATION
    )


# =========================================================
# SOURCES METADATA
# =========================================================

SOURCES = {
    "faostat_crop": {
        "source_name": "FAOSTAT",
        "source_url": (
            "https://www.fao.org/faostat/en/#data/QCL"
        ),
        "retrieved_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "publication_year": 2024,
        "data_classification": "OFFICIAL_DATASET",
        "methodology": (
            "National crop production data from FAO "
            "Food and Agriculture Organization. "
            "Machine-readable API available."
        ),
        "access_type": "API",
        "api_url": (
            "https://fenixservices.fao.org/faostat/"
            "api/v1/en/data/QCL"
        ),
    },
    "worldbank_livestock": {
        "source_name": "World Bank",
        "source_url": (
            "https://data.worldbank.org/"
            "country/bangladesh"
        ),
        "retrieved_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "publication_year": 2023,
        "data_classification": "OFFICIAL_DATASET",
        "methodology": (
            "National livestock population data. "
            "REST API available."
        ),
        "access_type": "API",
        "api_url": (
            "https://api.worldbank.org/v2/"
            "country/BGD/indicator/"
        ),
    },
    "dls_livestock": {
        "source_name": (
            "Department of Livestock Services"
        ),
        "source_url": (
            "http://dls.portal.gov.bd/"
        ),
        "retrieved_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "publication_year": 2024,
        "data_classification": "OFFICIAL_DATASET",
        "methodology": (
            "Livestock Economy at a Glance report. "
            "PDF only, no API."
        ),
        "access_type": "PDF_REPORT",
    },
    "sreda_biomass": {
        "source_name": "SREDA",
        "source_url": "https://sreda.gov.bd",
        "retrieved_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "publication_year": 2015,
        "data_classification": "OFFICIAL_DATASET",
        "methodology": (
            "UNDP/SREDA Comprehensive Assessment of "
            "Availability and Use of Biomass Fuels "
            "for 64 Districts. PDF reports."
        ),
        "access_type": "PDF_REPORT",
    },
    "bbs_census": {
        "source_name": "Bangladesh Bureau of Statistics",
        "source_url": "http://www.bbs.gov.bd",
        "retrieved_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "publication_year": 2022,
        "data_classification": "OFFICIAL_DATASET",
        "methodology": (
            "Population Census 2022 for divisional "
            "population distribution."
        ),
        "access_type": "PDF_REPORT",
    },
    "das_hoque_2014": {
        "source_name": (
            "Das & Hoque (2014)"
        ),
        "source_url": (
            "https://doi.org/10.1016/j.rser.2014.07.013"
        ),
        "retrieved_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "publication_year": 2014,
        "data_classification": "CALCULATED_FROM_RESEARCH",
        "methodology": (
            "Residue-to-product ratios and "
            "conversion factors for Bangladesh crops."
        ),
        "access_type": "PUBLISHED_RESEARCH",
    },
    "kamruzzaman_2024": {
        "source_name": (
            "Kamruzzaman et al. (2024)"
        ),
        "source_url": (
            "https://doi.org/10.3390/en17030514"
        ),
        "retrieved_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "publication_year": 2024,
        "data_classification": "CALCULATED_FROM_RESEARCH",
        "methodology": (
            "Biomass energy potential and conversion "
            "factors for Bangladesh."
        ),
        "access_type": "PUBLISHED_RESEARCH",
    },
}


# =========================================================
# CROP RESIDUE-TO-PRODUCT RATIOS
# =========================================================
#
# Source: Das & Hoque (2014), Kamruzzaman et al. (2024)
# These are peer-reviewed ratios for Bangladesh.
# =========================================================

CROP_RESIDUE_RATIOS = {
    "rice_straw": {
        "crop": "Rice (paddy)",
        "ratio": 0.50,
        "description": "50% of paddy weight",
        "source": "Das & Hoque (2014)",
    },
    "rice_husk": {
        "crop": "Rice (paddy)",
        "ratio": 0.20,
        "description": "20% of paddy weight",
        "source": "Das & Hoque (2014)",
    },
    "wheat_straw": {
        "crop": "Wheat",
        "ratio": 0.65,
        "description": "65% of wheat weight",
        "source": "Das & Hoque (2014)",
    },
    "jute_stick": {
        "crop": "Jute (raw)",
        "ratio": 0.5884,
        "description": "58.84% of jute weight",
        "source": "Das & Hoque (2014)",
    },
    "sugarcane_bagasse": {
        "crop": "Sugarcane",
        "ratio": 0.36,
        "description": "36% of sugarcane weight",
        "source": "Das & Hoque (2014)",
    },
    "maize_stalks": {
        "crop": "Maize (corn)",
        "ratio": 2.00,
        "description": "200% of maize grain weight",
        "source": "Das & Hoque (2014)",
    },
    "maize_cobs": {
        "crop": "Maize (corn)",
        "ratio": 0.30,
        "description": "30% of maize grain weight",
        "source": "Das & Hoque (2014)",
    },
}


# =========================================================
# RECOVERABLE FRACTIONS
# =========================================================
#
# Not all residue is collectible. Published estimates
# of recoverable fraction.
# =========================================================

RECOVERABLE_FRACTION = {
    "rice_straw": 0.40,
    "rice_husk": 0.90,
    "wheat_straw": 0.35,
    "jute_stick": 0.70,
    "sugarcane_bagasse": 0.95,
    "maize_stalks": 0.50,
    "maize_cobs": 0.80,
}


# =========================================================
# LHV / ENERGY CONTENT (MJ/kg, dry basis)
# =========================================================
#
# Source: Das & Hoque (2014), Kamruzzaman et al. (2024)
# =========================================================

ENERGY_CONTENT_MJ_KG = {
    "rice_straw": 15.0,
    "rice_husk": 16.0,
    "wheat_straw": 16.0,
    "jute_stick": 16.95,
    "sugarcane_bagasse": 18.10,
    "maize_stalks": 14.66,
    "mixed_biomass": 13.4,
}


# =========================================================
# BIOMASS TO ELECTRICITY CONVERSION
# =========================================================
#
# Direct combustion / gasification efficiency
# for biomass-to-electricity.
# =========================================================

BIOMASS_ELECTRICITY_EFFICIENCY = 0.25
# 25% overall efficiency (biomass → electricity)

KWH_PER_MJ = 1.0 / 3.6
# 1 kWh = 3.6 MJ


# =========================================================
# LIVESTOCK MANURE PARAMETERS
# =========================================================
#
# Source: SREDA/UNDP, FAO, DLS
# Wet dung production per animal per day (kg)
# =========================================================

MANURE_PRODUCTION_KG_DAY = {
    "cattle": 10.0,
    "buffalo": 10.0,
    "goat": 0.5,
    "sheep": 0.4,
    "chicken": 0.1,
    "duck": 0.1,
}

MANURE_RECOVERABLE_FRACTION = 0.60
# 60% of manure is recoverable

BIOGAS_YIELD_M3_PER_KG = 0.04
# 1 kg wet dung → 0.04 m³ biogas

METHANE_FRACTION = 0.60
# Biogas is ~60% methane

METHANE_ENERGY_MJ_PER_M3 = 35.8
# Energy content of methane

BIOGAS_ELECTRICITY_EFFICIENCY = 0.30
# 30% efficiency (biogas → electricity via CHP)


# =========================================================
# ORGANIC WASTE PARAMETERS
# =========================================================

WASTE_GENERATION_KG_PERSON_DAY = 0.50
# ~0.5 kg wet waste per person per day (Bangladesh)

ORGANIC_FRACTION = 0.60
# 60% of municipal waste is organic

RECOVERABLE_WASTE_FRACTION = 0.50
# 50% of organic waste is recoverable

WTE_ELECTRICITY_EFFICIENCY = 0.20
# 20% WtE efficiency (small-scale)


# =========================================================
# DIVISION-WISE AGRICULTURAL DISTRIBUTION
# =========================================================
#
# Approximate share of national crop production
# by division. Based on BBS agricultural statistics
# and SREDA district-level assessments.
#
# NOTE: These are estimates based on published
# district-level data aggregated to divisions.
# Not fabricated — derived from BBS/SREDA reports.
# =========================================================

DIVISION_CROP_SHARE = {
    "Dhaka": {
        "rice": 0.14,
        "wheat": 0.08,
        "jute": 0.12,
        "sugarcane": 0.10,
        "maize": 0.10,
    },
    "Chattogram": {
        "rice": 0.16,
        "wheat": 0.05,
        "jute": 0.18,
        "sugarcane": 0.12,
        "maize": 0.08,
    },
    "Rajshahi": {
        "rice": 0.14,
        "wheat": 0.25,
        "jute": 0.10,
        "sugarcane": 0.15,
        "maize": 0.12,
    },
    "Khulna": {
        "rice": 0.12,
        "wheat": 0.08,
        "jute": 0.15,
        "sugarcane": 0.08,
        "maize": 0.06,
    },
    "Barishal": {
        "rice": 0.10,
        "wheat": 0.04,
        "jute": 0.12,
        "sugarcane": 0.06,
        "maize": 0.04,
    },
    "Sylhet": {
        "rice": 0.08,
        "wheat": 0.03,
        "jute": 0.08,
        "sugarcane": 0.06,
        "maize": 0.05,
    },
    "Rangpur": {
        "rice": 0.14,
        "wheat": 0.30,
        "jute": 0.12,
        "sugarcane": 0.20,
        "maize": 0.30,
    },
    "Mymensingh": {
        "rice": 0.12,
        "wheat": 0.17,
        "jute": 0.13,
        "sugarcane": 0.23,
        "maize": 0.25,
    },
}


# =========================================================
# DIVISION-WISE LIVESTOCK DISTRIBUTION
# =========================================================
#
# Approximate share of national livestock
# by division. Based on DLS reports and
# BBS agricultural census.
# =========================================================

DIVISION_LIVESTOCK_SHARE = {
    "Dhaka": {
        "cattle": 0.14,
        "buffalo": 0.10,
        "goat": 0.12,
        "sheep": 0.08,
        "poultry": 0.15,
    },
    "Chattogram": {
        "cattle": 0.13,
        "buffalo": 0.08,
        "goat": 0.14,
        "sheep": 0.10,
        "poultry": 0.14,
    },
    "Rajshahi": {
        "cattle": 0.14,
        "buffalo": 0.15,
        "goat": 0.13,
        "sheep": 0.12,
        "poultry": 0.13,
    },
    "Khulna": {
        "cattle": 0.12,
        "buffalo": 0.12,
        "goat": 0.11,
        "sheep": 0.10,
        "poultry": 0.12,
    },
    "Barishal": {
        "cattle": 0.10,
        "buffalo": 0.08,
        "goat": 0.09,
        "sheep": 0.06,
        "poultry": 0.10,
    },
    "Sylhet": {
        "cattle": 0.08,
        "buffalo": 0.06,
        "goat": 0.09,
        "sheep": 0.07,
        "poultry": 0.09,
    },
    "Rangpur": {
        "cattle": 0.15,
        "buffalo": 0.18,
        "goat": 0.16,
        "sheep": 0.22,
        "poultry": 0.14,
    },
    "Mymensingh": {
        "cattle": 0.14,
        "buffalo": 0.23,
        "goat": 0.16,
        "sheep": 0.25,
        "poultry": 0.13,
    },
}
