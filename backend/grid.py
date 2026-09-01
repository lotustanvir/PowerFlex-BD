import os
import re
from datetime import datetime, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException

from backend.demand_history import log_pgcb_observation


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/api/grid",
    tags=["Bangladesh Grid"],
)


# =========================================================
# ENVIRONMENT CONFIGURATION
# =========================================================

PGCB_GRID_PROVIDER = os.getenv(
    "PGCB_GRID_PROVIDER", ""
)

PGCB_GRID_API_URL = os.getenv(
    "PGCB_GRID_API_URL", ""
)

PGCB_GRID_API_KEY = os.getenv(
    "PGCB_GRID_API_KEY", ""
)


# =========================================================
# BANGLADESH DIGIT TRANSLATION
# =========================================================

BANGLA_DIGIT_MAP = str.maketrans(
    "০১২৩৪৫৬৭৮৯",
    "0123456789",
)


def translate_bangla_digits(value: str) -> str:
    return value.translate(BANGLA_DIGIT_MAP)


# =========================================================
# SAFE FLOAT
# =========================================================

def safe_float(
    value,
    default: float = None,
) -> Optional[float]:

    if value is None:
        return default

    try:

        cleaned = str(value).strip()
        cleaned = translate_bangla_digits(cleaned)
        cleaned = cleaned.replace(",", "")

        return float(cleaned)

    except (TypeError, ValueError):
        return default


# =========================================================
# PARSE TIMESTAMP
# =========================================================

def parse_pgcb_timestamp(
    date_str: str,
    time_str: str,
) -> str:

    combined = f"{date_str} {time_str}"
    combined = translate_bangla_digits(combined)

    for fmt in [

        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",

    ]:

        try:

            dt = datetime.strptime(combined, fmt)

            return dt.replace(
                tzinfo=timezone.utc,
            ).isoformat()

        except ValueError:

            continue

    return datetime.now(timezone.utc).isoformat()


# =========================================================
# PGCB OFFICIAL URLs
# =========================================================

PGCB_GENERATION_URL = (
    "https://erp.powergrid.gov.bd/w/generations/"
    "view_generations"
)

PGCB_DEMAND_SUPPLY_URL = (
    "https://erp.powergrid.gov.bd/web/generations/"
    "view_demand_supply_loadshed"
)


# =========================================================
# PGCB ERP: GENERATION DATA
# =========================================================

def fetch_pgcb_generation() -> dict:
    """
    Scrape official PGCB generation breakdown.

    Source: PGCB ERP Portal
    URL: view_generations
    Columns: Date, Time, Generation(MW), Gas,
      Liquid Fuel, Coal, Hydro, Solar, Wind,
      India (Bheramara HVDC, Tripura, Adani),
      Nepal, Remarks
    """

    import urllib3
    urllib3.disable_warnings(
        urllib3.exceptions.InsecureRequestWarning
    )

    try:

        response = requests.get(
            PGCB_GENERATION_URL,
            timeout=30,
            headers={
                "User-Agent": "PowerFlex-BD/1.0",
                "Accept": "text/html",
            },
            verify=False,
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        table = soup.find("table")

        if table is None:

            return {
                "connected": False,
                "source": "PGCB_GENERATION",
                "status": "PARSE_ERROR",
                "message": "No table found.",
                "data": None,
            }

        rows = table.find_all("tr")

        data_row_index = None

        for idx, row in enumerate(rows):

            cells = row.find_all("td")

            if len(cells) >= 14:

                first = cells[0].get_text(strip=True)
                first = translate_bangla_digits(first)

                if re.match(
                    r"\d{2}-\d{2}-\d{4}",
                    first,
                ):

                    data_row_index = idx

                    break

        if data_row_index is None:

            return {
                "connected": False,
                "source": "PGCB_GENERATION",
                "status": "PARSE_ERROR",
                "message": "No data row found.",
                "data": None,
            }

        cells = rows[data_row_index].find_all("td")

        values = []

        for cell in cells:

            text = cell.get_text(strip=True)
            text = translate_bangla_digits(text)
            values.append(text)

        if len(values) < 14:

            return {
                "connected": False,
                "source": "PGCB_GENERATION",
                "status": "PARSE_ERROR",
                "message": (
                    f"Expected 14 cells, got {len(values)}."
                ),
                "data": None,
            }

        row = {
            "Date": values[0],
            "Time": values[1],
            "Generation(MW)": values[2],
            "Gas": values[3],
            "Liquid Fuel": values[4],
            "Coal": values[5],
            "Hydro": values[6],
            "Solar": values[7],
            "Wind": values[8],
            "Bheramara HVDC": values[9],
            "Tripura": values[10],
            "Adani": values[11],
            "Nepal": values[12],
            "Remarks": values[13],
        }

        generation_mw = safe_float(
            row["Generation(MW)"]
        )

        gas_mw = safe_float(row["Gas"])
        liquid_fuel_mw = safe_float(row["Liquid Fuel"])
        coal_mw = safe_float(row["Coal"])
        hydro_mw = safe_float(row["Hydro"])
        solar_mw = safe_float(row["Solar"])
        wind_mw = safe_float(row["Wind"])

        india_bheramara = safe_float(
            row["Bheramara HVDC"]
        )
        india_tripura = safe_float(row["Tripura"])
        india_adani = safe_float(row["Adani"])
        nepal_mw = safe_float(row["Nepal"])

        total_imports = sum(
            v for v in [
                india_bheramara,
                india_tripura,
                india_adani,
                nepal_mw,
            ]
            if v is not None
        )

        timestamp = parse_pgcb_timestamp(
            row["Date"],
            row["Time"],
        )

        return {
            "connected": True,
            "source": "PGCB_GENERATION",
            "status": "LIVE",
            "data": {
                "timestamp": timestamp,
                "current_generation_mw": generation_mw,
                "generation_breakdown": {
                    "gas_mw": gas_mw,
                    "liquid_fuel_mw": liquid_fuel_mw,
                    "coal_mw": coal_mw,
                    "hydro_mw": hydro_mw,
                    "solar_mw": solar_mw,
                    "wind_mw": wind_mw,
                },
                "imports": {
                    "india_bheramara_hvdc_mw":
                        india_bheramara,
                    "india_tripura_mw": india_tripura,
                    "india_adani_mw": india_adani,
                    "nepal_mw": nepal_mw,
                    "total_imports_mw": total_imports,
                },
                "remarks": row.get("Remarks", ""),
            },
        }

    except requests.RequestException as error:

        return {
            "connected": False,
            "source": "PGCB_GENERATION",
            "status": "NETWORK_ERROR",
            "message": str(error),
            "data": None,
        }

    except Exception as error:

        return {
            "connected": False,
            "source": "PGCB_GENERATION",
            "status": "PARSE_ERROR",
            "message": str(error),
            "data": None,
        }


# =========================================================
# PGCB ERP: DEMAND / SUPPLY / LOAD-SHED DATA
# =========================================================

def fetch_pgcb_demand_supply() -> dict:
    """
    Scrape official PGCB demand/supply/load-shed page.

    Source: PGCB ERP Portal
    URL: view_demand_supply_loadshed
    Columns: Date, Time, Demand (MW), Supply (MW),
      Loadshed, Remarks

    This provides the REAL national demand and supply
    from PGCB official systems.
    """

    import urllib3
    urllib3.disable_warnings(
        urllib3.exceptions.InsecureRequestWarning
    )

    try:

        response = requests.get(
            PGCB_DEMAND_SUPPLY_URL,
            timeout=30,
            headers={
                "User-Agent": "PowerFlex-BD/1.0",
                "Accept": "text/html",
            },
            verify=False,
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        table = soup.find("table")

        if table is None:

            return {
                "connected": False,
                "source": "PGCB_DEMAND_SUPPLY",
                "status": "PARSE_ERROR",
                "message": "No table found.",
                "data": None,
            }

        rows = table.find_all("tr")

        data_row_index = None

        for idx, row in enumerate(rows):

            cells = row.find_all("td")

            if len(cells) >= 6:

                first = cells[0].get_text(strip=True)
                first = translate_bangla_digits(first)

                if re.match(
                    r"\d{2}-\d{2}-\d{4}",
                    first,
                ):

                    data_row_index = idx

                    break

        if data_row_index is None:

            return {
                "connected": False,
                "source": "PGCB_DEMAND_SUPPLY",
                "status": "PARSE_ERROR",
                "message": "No data row found.",
                "data": None,
            }

        cells = rows[data_row_index].find_all("td")

        values = []

        for cell in cells:

            text = cell.get_text(strip=True)
            text = translate_bangla_digits(text)
            values.append(text)

        if len(values) < 6:

            return {
                "connected": False,
                "source": "PGCB_DEMAND_SUPPLY",
                "status": "PARSE_ERROR",
                "message": (
                    f"Expected 6 cells, got {len(values)}."
                ),
                "data": None,
            }

        row = {
            "Date": values[0],
            "Time": values[1],
            "Demand (MW)": values[2],
            "Supply (MW)": values[3],
            "Loadshed": values[4],
            "Remarks": values[5],
        }

        demand_mw = safe_float(row["Demand (MW)"])
        supply_mw = safe_float(row["Supply (MW)"])
        load_shed_mw = safe_float(row["Loadshed"])

        deficit_mw = None

        if demand_mw is not None and supply_mw is not None:

            deficit_mw = demand_mw - supply_mw

        timestamp = parse_pgcb_timestamp(
            row["Date"],
            row["Time"],
        )

        return {
            "connected": True,
            "source": "PGCB_DEMAND_SUPPLY",
            "status": "LIVE",
            "data": {
                "timestamp": timestamp,
                "current_demand_mw": demand_mw,
                "current_supply_mw": supply_mw,
                "deficit_mw": deficit_mw,
                "load_shedding_mw": load_shed_mw,
                "remarks": row.get("Remarks", ""),
            },
        }

    except requests.RequestException as error:

        return {
            "connected": False,
            "source": "PGCB_DEMAND_SUPPLY",
            "status": "NETWORK_ERROR",
            "message": str(error),
            "data": None,
        }

    except Exception as error:

        return {
            "connected": False,
            "source": "PGCB_DEMAND_SUPPLY",
            "status": "PARSE_ERROR",
            "message": str(error),
            "data": None,
        }


# =========================================================
# COMBINED PGCB GRID DATA
# =========================================================

def fetch_pgcb_grid_data() -> dict:
    """
    Fetch and combine both PGCB data sources:
      1. Generation breakdown (fuel mix, imports)
      2. Demand / Supply / Load-shed

    Returns a unified grid snapshot.
    """

    gen_result = fetch_pgcb_generation()

    ds_result = fetch_pgcb_demand_supply()

    if not ds_result["connected"]:

        return {
            "connected": False,
            "source": "PGCB",
            "status": ds_result["status"],
            "message": (
                f"Demand/Supply page failed: "
                f"{ds_result['message']}"
            ),
            "data": None,
        }

    ds_data = ds_result["data"]

    gen_data = {}

    if gen_result["connected"]:

        gen_data = gen_result["data"]

    timestamp = ds_data.get("timestamp")

    demand_mw = ds_data.get("current_demand_mw")

    supply_from_ds = ds_data.get("current_supply_mw")

    load_shedding_mw = ds_data.get(
        "load_shedding_mw"
    )

    deficit_mw = ds_data.get("deficit_mw")

    generation_mw = gen_data.get(
        "current_generation_mw"
    )

    generation_breakdown = gen_data.get(
        "generation_breakdown",
        {},
    )

    imports = gen_data.get("imports", {})

    remarks = ds_data.get("remarks", "")

    if gen_result["connected"]:

        gen_remarks = gen_data.get("remarks", "")

        if gen_remarks:

            remarks = gen_remarks

    return {
        "connected": True,
        "source": "PGCB_OFFICIAL",
        "status": "LIVE",
        "message": (
            "Live official PGCB data received "
            "(demand + supply + load-shed + generation)."
        ),
        "data": {
            "timestamp": timestamp,

            "current_demand_mw": demand_mw,

            "current_generation_mw": generation_mw,

            "supply_mw": supply_from_ds,

            "demand_supply_gap_mw": deficit_mw,

            "load_shedding_mw": load_shedding_mw,

            "frequency_hz": None,

            "generation_breakdown":
                generation_breakdown,

            "imports": imports,

            "remarks": remarks,

            "data_availability": {
                "demand": "AVAILABLE",
                "supply": "AVAILABLE",
                "load_shedding": "AVAILABLE",
                "generation_breakdown":
                    "AVAILABLE" if gen_result["connected"]
                    else "UNAVAILABLE",
                "frequency": "NOT_AVAILABLE",
            },

            "data_classification": "OFFICIAL_PGCB",

            "source_urls": {
                "demand_supply":
                    PGCB_DEMAND_SUPPLY_URL,
                "generation":
                    PGCB_GENERATION_URL,
            },
        },
    }


# =========================================================
# JSON API FALLBACK
# =========================================================

def fetch_json_api_data() -> dict:

    if not PGCB_GRID_API_URL:

        return {
            "connected": False,
            "source": PGCB_GRID_PROVIDER or "API",
            "status": "NOT_CONFIGURED",
            "message": "API endpoint not configured.",
            "data": None,
        }

    headers = {
        "Accept": "application/json",
        "User-Agent": "PowerFlex-BD/1.0",
    }

    if PGCB_GRID_API_KEY:

        headers["Authorization"] = (
            f"Bearer {PGCB_GRID_API_KEY}"
        )

    try:

        response = requests.get(
            PGCB_GRID_API_URL,
            timeout=30,
            headers=headers,
        )

        response.raise_for_status()

        payload = response.json()

        return {
            "connected": True,
            "source": PGCB_GRID_PROVIDER or "API",
            "status": "LIVE",
            "data": payload,
        }

    except requests.RequestException as error:

        return {
            "connected": False,
            "source": PGCB_GRID_PROVIDER or "API",
            "status": "NETWORK_ERROR",
            "message": str(error),
            "data": None,
        }

    except ValueError as error:

        return {
            "connected": False,
            "source": PGCB_GRID_PROVIDER or "API",
            "status": "PARSE_ERROR",
            "message": str(error),
            "data": None,
        }


# =========================================================
# ENDPOINT: /api/grid/status
# =========================================================

@router.get("/status")
def pgcb_status():

    provider = PGCB_GRID_PROVIDER.strip().upper()

    return {
        "project": "PowerFlex BD",
        "provider": "PGCB / NLDC / BPDB",
        "adapter": "READY",
        "configured_provider": provider or None,
        "api_configured": bool(PGCB_GRID_API_URL),
        "supported_providers": [
            "PGCB_ERP",
            "PGCB_API",
            "BPDB_API",
            "OFFICIAL_FEED",
            "MANUAL_APPROVED",
        ],
        "pgcb_sources": {
            "generation": {
                "url": PGCB_GENERATION_URL,
                "data": "Fuel mix, imports",
                "auth_required": False,
            },
            "demand_supply_loadshed": {
                "url": PGCB_DEMAND_SUPPLY_URL,
                "data": "Demand, Supply, Load-shed",
                "auth_required": False,
            },
        },
        "message": (
            f"Provider: {provider or 'none'}. "
            f"PGCB ERP pages accessible."
        ),
    }


# =========================================================
# ENDPOINT: /api/grid/official
# =========================================================

@router.get("/official")
def official_pgcb_data():
    """
    Return only the latest official PGCB
    demand/supply/load-shed data.
    """

    result = fetch_pgcb_demand_supply()

    if not result["connected"]:

        return {
            "project": "PowerFlex BD",
            "status": result["status"],
            "live": False,
            "message": result["message"],
            "data": None,
        }

    data = result["data"]

    log_pgcb_observation(
        pgcb_timestamp=data["timestamp"],
        demand_mw=data["current_demand_mw"],
        supply_mw=data["current_supply_mw"],
        load_shedding_mw=data["load_shedding_mw"],
        deficit_mw=data["deficit_mw"],
        source="PGCB_ERP",
    )

    return {
        "project": "PowerFlex BD",
        "status": "LIVE",
        "live": True,
        "data_source": "PGCB_ERP",
        "data_classification": "OFFICIAL_PGCB",
        "source_url": PGCB_DEMAND_SUPPLY_URL,
        "data": {
            "timestamp": data["timestamp"],
            "demand_mw": data["current_demand_mw"],
            "supply_mw": data["current_supply_mw"],
            "deficit_mw": data["deficit_mw"],
            "load_shedding_mw": data[
                "load_shedding_mw"
            ],
            "remarks": data["remarks"],
        },
    }


# =========================================================
# ENDPOINT: /api/grid/live
# =========================================================

@router.get("/live")
def live_grid():
    """
    Combined grid snapshot with demand, supply,
    load-shedding, and generation breakdown.
    """

    pgcb = fetch_pgcb_grid_data()

    if not pgcb["connected"]:

        return {
            "project": "PowerFlex BD",
            "resource": "Bangladesh National Grid",
            "status": "PGCB_ADAPTER_READY",
            "data_source": "PGCB / NLDC",
            "live": False,
            "message": pgcb["message"],
            "grid_snapshot": None,
        }

    grid = pgcb["data"]

    demand = grid["current_demand_mw"]
    supply = grid["supply_mw"]
    load_shed = grid["load_shedding_mw"]

    log_pgcb_observation(
        pgcb_timestamp=grid.get("timestamp", ""),
        demand_mw=demand,
        supply_mw=supply,
        load_shedding_mw=load_shed,
        deficit_mw=grid.get(
            "demand_supply_gap_mw", 0.0
        ),
        source="PGCB_ERP",
    )

    if demand is not None and supply is not None:

        gap = demand - supply

        if gap > 0:

            grid_status = "DEFICIT"

            if gap >= demand * 0.10:
                risk_level = "CRITICAL"
            elif gap >= demand * 0.05:
                risk_level = "HIGH"
            else:
                risk_level = "MODERATE"

        else:

            grid_status = "BALANCED_OR_SURPLUS"
            risk_level = "LOW"

    else:

        grid_status = "DATA_INCOMPLETE"
        risk_level = "UNKNOWN"

    return {
        "project": "PowerFlex BD",
        "resource": "Bangladesh National Grid",
        "status": "LIVE",
        "data_source": "PGCB_OFFICIAL",
        "live": True,
        "grid_status": grid_status,
        "risk_level": risk_level,
        "data_classification": "OFFICIAL_PGCB",
        "grid_snapshot": grid,
        "adapter": {
            "provider": "PGCB_ERP",
            "mode": "official_erp_scraper",
            "data_classification": "OFFICIAL_PGCB",
            "source_urls": grid.get(
                "source_urls",
                {},
            ),
            "timestamp": datetime.now(
                timezone.utc,
            ).isoformat(),
        },
    }
