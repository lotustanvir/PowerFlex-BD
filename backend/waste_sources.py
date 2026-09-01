from datetime import datetime, timezone
from typing import Any, Dict, List


# =========================================================
# POWERFLEX BD - WASTE-TO-ENERGY DATA SOURCES
# =========================================================
#
# Source metadata, project data, and conversion factors
# for Bangladesh Waste-to-Energy calculations.
#
# Key finding: Bangladesh has ZERO operational WtE plants
# as of August 2026. All projects are under construction
# or planned.
# =========================================================


# =========================================================
# BANGLADESH WtE PROJECTS (Documented)
# =========================================================
#
# Sources:
#   - AIIB Project Documents (P000617)
#   - NDB Project Documents
#   - BPDB PPA Data
#   - DNCC Official Statements
#   - The Business Standard (2026)
#   - Energy Tribune (2026)
#   - Mongabay (2024)
#   - Energy Transition Bangladesh
# =========================================================

WTE_PROJECTS: List[Dict[str, Any]] = [
    {
        "project_name": (
            "Aminbazar North Dhaka "
            "Waste-to-Energy Power Plant"
        ),
        "project_id": "AIIB-P000617",
        "alternate_names": [
            "Dhaka North WtE",
            "CMEC WtE Plant",
            "Aminbazar WtE",
        ],
        "location": {
            "site": "Aminbazar, Baliarpur",
            "upazila": "Savar",
            "district": "Dhaka",
            "division": "Dhaka",
            "coordinates": {
                "latitude": 23.7894,
                "longitude": 90.3278,
            },
            "zone": "Dhaka",
        },
        "developer": {
            "name": (
                "China Machinery Engineering "
                "Corporation (CMEC)"
            ),
            "parent": (
                "China National Machinery "
                "Industry Corporation (Sinomach)"
            ),
            "spv": (
                "WtE Power Plant North Dhaka "
                "Private Limited"
            ),
            "country": "China",
        },
        "capacity": {
            "installed_capacity_mw": 42.5,
            "gross_capacity_mw": 42.5,
            "net_capacity_mw": 35.0,
            "unit": "MW",
        },
        "waste_input": {
            "daily_waste_tonnes": 3000,
            "annual_waste_tonnes": 1_095_000,
            "waste_type": "Municipal Solid Waste",
            "source": "DNCC",
        },
        "technology": {
            "type": "Incineration",
            "description": (
                "4 x 750 tonnes/day incineration "
                "lines + 2 x 35 MW turbo-generator "
                "systems"
            ),
            "furnace": "Mechanical grate furnace",
            "boiler": (
                "Waste heat boilers from "
                "Wuxi Huaguang Environment "
                "& Energy Group Co., Ltd"
            ),
            "incinerator": (
                "Shanghai SUS Environment "
                "Co., Ltd"
            ),
            "flue_gas_temp_celsius": 850,
        },
        "timeline": {
            "approval_date": "2020-11-12",
            "agreement_signed": "2021-12-01",
            "ppa_signed": "2021-12-21",
            "construction_started": "2024-07",
            "expected_cod": "2028-08",
            "concessional_period_years": 25,
        },
        "financials": {
            "total_cost_usd": 467_000_000,
            "equity_usd": 157_000_000,
            "debt_usd": 310_000_000,
            "aiib_loan_usd": 100_000_000,
            "ndb_loan_usd": 100_000_000,
            "ppa_tariff_usd_kwh": 0.2178,
            "ppa_tariff_bdt_kwh": 25.0,
        },
        "annual_generation": {
            "expected_gwh": 309.01,
            "plant_load_factor_pct": 83.0,
        },
        "status": {
            "current": "UNDER_CONSTRUCTION",
            "operational": False,
            "generating": False,
            "environmental_clearance": True,
            "construction_progress": (
                "Piling works commenced July 2024. "
                "Target COD: August 2028."
            ),
        },
        "data_classification": (
            "OFFICIAL_PROJECT_DATA"
        ),
        "source": {
            "name": "AIIB Project Document",
            "url": (
                "https://www.aiib.org/en/projects/"
                "details/2025/approved/"
                "bangladesh-north-dhaka-waste-to-"
                "energy-project.html"
            ),
            "retrieved_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "publication_year": 2025,
        },
    },
    {
        "project_name": (
            "Matuail South Dhaka "
            "Waste-to-Energy Project"
        ),
        "project_id": "DSCC-MATUAIL-001",
        "alternate_names": [
            "Dhaka South WtE",
            "B&F Group WtE",
            "Matuail WtE",
        ],
        "location": {
            "site": "Matuail",
            "upazila": "Satarkanji",
            "district": "Dhaka",
            "division": "Dhaka",
            "coordinates": {
                "latitude": 23.7200,
                "longitude": 90.4300,
            },
            "zone": "Dhaka",
        },
        "developer": {
            "name": "B&F Group",
            "parent": None,
            "spv": None,
            "country": "South Korea",
        },
        "capacity": {
            "installed_capacity_mw": 9.1,
            "gross_capacity_mw": 9.1,
            "net_capacity_mw": 8.0,
            "unit": "MW",
            "note": (
                "81,000 MWh/year = ~9.25 MW average. "
                "Equivalent to ~221 MWh/day."
            ),
        },
        "waste_input": {
            "daily_waste_tonnes": 3250,
            "annual_waste_tonnes": 1_186_250,
            "waste_type": "Municipal Solid Waste",
            "source": "DSCC",
        },
        "technology": {
            "type": "Biogas from Waste",
            "description": (
                "Biogas capture from waste "
                "decomposition + solar + "
                "organic fertilizer production"
            ),
            "outputs": [
                "Electricity",
                "Methane gas",
                "Organic fertilizer",
                "Animal feed",
                "Eco-friendly bricks",
            ],
        },
        "timeline": {
            "approval_date": None,
            "agreement_signed": None,
            "ppa_signed": None,
            "construction_started": None,
            "expected_cod": None,
            "concessional_period_years": None,
        },
        "financials": {
            "total_cost_usd": None,
            "ppa_tariff_usd_kwh": None,
        },
        "annual_generation": {
            "expected_gwh": 81.0,
            "plant_load_factor_pct": None,
        },
        "status": {
            "current": "ANNOUNCED",
            "operational": False,
            "generating": False,
            "environmental_clearance": False,
            "construction_progress": (
                "Announced at PM meeting July 2026. "
                "Earlier stage than Aminbazar. "
                "No construction started."
            ),
        },
        "data_classification": (
            "OFFICIAL_PROJECT_DATA"
        ),
        "source": {
            "name": "The Business Standard",
            "url": (
                "https://www.tbsnews.net/bangladesh/"
                "pm-seeks-faster-progress-dhakas-"
                "two-waste-energy-projects-1486101"
            ),
            "retrieved_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "publication_year": 2026,
        },
    },
]


# =========================================================
# CALCULATED WASTE-TO-ELECTRICITY POTENTIAL
# =========================================================
#
# Based on:
#   - Bangladesh urban waste generation rates
#   - BBS population data
#   - Published waste composition studies
#   - International WtE conversion factors
#
# Sources:
#   - ADB Bangladesh Waste Statistics
#   - JICA Dhaka Waste Management Study
#   - World Bank Bangladesh Waste Data
#   - Das & Hoque (2014) - conversion factors
# =========================================================

CITY_WASTE_GENERATION = {
    "Dhaka": {
        "daily_waste_tonnes": 6500,
        "source": "DNCC + DSCC Official",
        "data_classification": "OFFICIAL_PROJECT_DATA",
    },
    "Chattogram": {
        "daily_waste_tonnes": 2800,
        "source": "CNCC Official",
        "data_classification": "OFFICIAL_PROJECT_DATA",
    },
    "Khulna": {
        "daily_waste_tonnes": 800,
        "source": "KNCC Estimate",
        "data_classification": "CALCULATED_FROM_OFFICIAL_DATA",
    },
    "Rajshahi": {
        "daily_waste_tonnes": 600,
        "source": "RNCC Estimate",
        "data_classification": "CALCULATED_FROM_OFFICIAL_DATA",
    },
    "Sylhet": {
        "daily_waste_tonnes": 500,
        "source": "SNCC Estimate",
        "data_classification": "CALCULATED_FROM_OFFICIAL_DATA",
    },
    "Barishal": {
        "daily_waste_tonnes": 400,
        "source": "BNCC Estimate",
        "data_classification": "CALCULATED_FROM_OFFICIAL_DATA",
    },
    "Rangpur": {
        "daily_waste_tonnes": 450,
        "source": "RNCC Estimate",
        "data_classification": "CALCULATED_FROM_OFFICIAL_DATA",
    },
    "Mymensingh": {
        "daily_waste_tonnes": 350,
        "source": "MNCC Estimate",
        "data_classification": "CALCULATED_FROM_OFFICIAL_DATA",
    },
    "Comilla": {
        "daily_waste_tonnes": 300,
        "source": "City Estimate",
        "data_classification": "CALCULATED_FROM_RESEARCH",
    },
}


# =========================================================
# WASTE CONVERSION FACTORS
# =========================================================
#
# For mixed MSW (unsegregated) in Bangladesh:
#   - Lower heating value (LHV): 6-8 MJ/kg
#   - Average 7 MJ/kg for tropical MSW
#   - Recovery rate for WtE: 50-60%
#   - Incineration efficiency: 20-25%
#   - Biogas efficiency: 25-30%
#
# Sources:
#   - World Bank (2018) "What a Waste 2.0"
#   - ADB Technical Reports
#   - Kaza et al. (2018)
# =========================================================

WASTE_CONVERSION = {
    "lhv_mj_kg": 7.0,
    "recovery_fraction": 0.50,
    "incineration_efficiency_pct": 0.22,
    "biogas_efficiency_pct": 0.28,
    "kwh_per_mj": 1.0 / 3.6,
    "days_per_year": 365,
    "hours_per_day": 24,
    "note": (
        "Conservative estimate for unsegregated "
        "tropical MSW. Recovery fraction accounts "
        "for non-combustible and moisture content."
    ),
}


# =========================================================
# SOURCES METADATA
# =========================================================

SOURCES = {
    "aiib_project": {
        "source_name": "AIIB",
        "source_url": (
            "https://www.aiib.org/en/projects/"
            "details/2025/approved/"
            "bangladesh-north-dhaka-waste-to-"
            "energy-project.html"
        ),
        "retrieved_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "publication_year": 2025,
        "data_classification": "OFFICIAL_PROJECT_DATA",
        "methodology": (
            "AIIB project appraisal document "
            "for North Dhaka WtE project."
        ),
        "access_type": "PDF_REPORT",
    },
    "ndb_project": {
        "source_name": "New Development Bank",
        "source_url": (
            "https://www.ndb.int/project/"
            "north-dhaka-waste-to-energy-project/"
        ),
        "retrieved_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "publication_year": 2025,
        "data_classification": "OFFICIAL_PROJECT_DATA",
        "methodology": (
            "NDB project page for North Dhaka "
            "WtE project."
        ),
        "access_type": "WEB_PAGE",
    },
    "tbs_news": {
        "source_name": "The Business Standard",
        "source_url": (
            "https://www.tbsnews.net/bangladesh/"
            "pm-seeks-faster-progress-dhakas-"
            "two-waste-energy-projects-1486101"
        ),
        "retrieved_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "publication_year": 2026,
        "data_classification": "OFFICIAL_PROJECT_DATA",
        "methodology": (
            "News report on PM meeting about "
            "WtE projects."
        ),
        "access_type": "NEWS_ARTICLE",
    },
    "energy_tribune": {
        "source_name": "Energy Tribune",
        "source_url": (
            "https://www.theenergytribune.com/"
            "energy-power/2026/07/02/256794"
        ),
        "retrieved_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "publication_year": 2026,
        "data_classification": "OFFICIAL_PROJECT_DATA",
        "methodology": (
            "State Minister statement on "
            "Aminbazar WtE project."
        ),
        "access_type": "NEWS_ARTICLE",
    },
    "mongabay": {
        "source_name": "Mongabay",
        "source_url": (
            "https://news.mongabay.com/2024/06/"
            "bangladesh-incinerator-project-"
            "sparks-row-between-government-"
            "contractor/"
        ),
        "retrieved_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "publication_year": 2024,
        "data_classification": "OFFICIAL_PROJECT_DATA",
        "methodology": (
            "Investigative report on Aminbazar "
            "WtE project delays."
        ),
        "access_type": "NEWS_ARTICLE",
    },
    "energy_transition_bd": {
        "source_name": "Energy Transition BD",
        "source_url": (
            "https://www.energytransitionbd.org/"
            "infrastructure/"
            "aminbazar-42-5-mw-cmec-wte-"
            "power-plant-1"
        ),
        "retrieved_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "publication_year": 2023,
        "data_classification": "CALCULATED_FROM_RESEARCH",
        "methodology": (
            "Detailed project profile of "
            "Aminbazar WtE plant."
        ),
        "access_type": "WEB_PAGE",
    },
    "worldbank_waste": {
        "source_name": "World Bank",
        "source_url": (
            "https://datatopics.worldbank.org/"
            "what-a-waste/"
        ),
        "retrieved_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "publication_year": 2018,
        "data_classification": (
            "CALCULATED_FROM_RESEARCH"
        ),
        "methodology": (
            "What a Waste 2.0 - Global waste "
            "generation rates and composition."
        ),
        "access_type": "REPORT",
    },
}


# =========================================================
# DIVISION → 9-ZONE MAPPING (same as biomass)
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
