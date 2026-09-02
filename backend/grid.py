import concurrent.futures
import logging
import os
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

import requests
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException

from backend.demand_history import log_pgcb_observation
from database.connection import get_session
from database.models import GridSnapshot

logger = logging.getLogger("powerflex.grid")

MAX_RESPONSE_BYTES = 5 * 1024 * 1024  # 5 MB
PGCB_STALE_THRESHOLD_HOURS = 2

# Endpoint-level timeout for PGCB operations (seconds).
# Chosen to be shorter than the inner HTTP timeout (30s) so
# the endpoint always returns within the budget, while still
# allowing a single normal PGCB request (typically <10s) to
# complete.  Under concurrent load this bounds the number of
# temporary executor threads to N (concurrent requests).
PGCB_ENDPOINT_TIMEOUT = 20


# =========================================================
# TIMEOUT HELPER
# =========================================================

def fetch_with_timeout(
    func: Callable,
    *args: Any,
    timeout: int = PGCB_ENDPOINT_TIMEOUT,
    default: Any = None,
    label: str = "pgcb",
    **kwargs: Any,
) -> Any:
    """Run *func* in a thread with a hard timeout.

    Returns *default* on timeout or any exception so that
    one slow upstream source never blocks the API server.

    Uses ``pool.shutdown(wait=False)`` so that a timed-out
    background thread never blocks the caller during cleanup.
    The abandoned thread will exit naturally when its inner
    HTTP timeout (30 s) expires.
    """
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        future = pool.submit(func, *args, **kwargs)
        result = future.result(timeout=timeout)
        logger.info("FETCH_OK label=%s", label)
        return result
    except concurrent.futures.TimeoutError:
        logger.warning(
            "FETCH_TIMEOUT label=%s timeout=%ss", label, timeout,
        )
        return default
    except Exception:
        logger.exception("FETCH_FAILED label=%s", label)
        return default
    finally:
        pool.shutdown(wait=False)


# =========================================================
# PGCB RESPONSE VALIDATION
# =========================================================

def validate_pgcb_response(
    response: requests.Response,
) -> Optional[str]:
    """Validate a PGCB HTTP response. Returns error message or None if valid."""
    if response.status_code != 200:
        return f"Unexpected status code: {response.status_code}"

    content_type = response.headers.get("Content-Type", "")
    if "html" not in content_type.lower():
        return f"Unexpected Content-Type: {content_type}"

    content_length = response.headers.get("Content-Length")
    if content_length and int(content_length) > MAX_RESPONSE_BYTES:
        return f"Response too large: {content_length} bytes"

    if len(response.content) > MAX_RESPONSE_BYTES:
        return f"Response body exceeds 5 MB limit"

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    if table is None:
        return "HTML does not contain expected table structure"

    return None


# =========================================================
# STALE DATA DETECTION
# =========================================================

def detect_stale_data(timestamp_str: str) -> bool:
    """Return True if PGCB timestamp is older than 2 hours."""
    if not timestamp_str:
        return False

    cleaned = translate_bangla_digits(str(timestamp_str))
    for fmt in [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%Y-%m-%d %H:%M",
    ]:
        try:
            dt = datetime.strptime(cleaned, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age = datetime.now(timezone.utc) - dt
            return age > timedelta(hours=PGCB_STALE_THRESHOLD_HOURS)
        except ValueError:
            continue

    return False


# =========================================================
# RETRY HELPER
# =========================================================

def _fetch_with_retry(
    url: str,
    max_retries: int = 3,
    timeout: int = 30,
    **kwargs,
) -> requests.Response:
    """Fetch URL with exponential backoff on network errors."""
    import os
    import urllib3

    # SSL verification enabled by default; allow explicit override via env var
    # for development environments with self-signed or broken server certificates.
    ssl_verify = os.getenv("GRID_SSL_VERIFY", "true").lower() != "false"
    if not ssl_verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        logger.warning(
            "SSL verification disabled for %s via GRID_SSL_VERIFY=false. "
            "This is insecure and should NOT be used in production.",
            url,
        )

    last_error = None
    for attempt in range(max_retries):
        try:
            response = requests.get(
                url,
                timeout=timeout,
                verify=ssl_verify,
                **kwargs,
            )
            return response
        except requests.ConnectionError as e:
            last_error = e
            wait = 2 ** attempt
            logger.warning(
                "Connection error on attempt %d/%d for %s, retrying in %ds",
                attempt + 1, max_retries, url, wait,
            )
            time.sleep(wait)
        except requests.Timeout as e:
            last_error = e
            wait = 2 ** attempt
            logger.warning(
                "Timeout on attempt %d/%d for %s, retrying in %ds",
                attempt + 1, max_retries, url, wait,
            )
            time.sleep(wait)
        except requests.RequestException as e:
            logger.error("Non-retryable request error for %s: %s", url, e)
            raise

    raise last_error


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/api/grid",
    tags=["Bangladesh Grid"],
)


# =========================================================
# LOG GRID SNAPSHOT TO POSTGRESQL
# =========================================================

def log_grid_snapshot(
    timestamp: str,
    demand_mw: float = None,
    supply_mw: float = None,
    load_shedding_mw: float = None,
    gas_mw: float = None,
    liquid_fuel_mw: float = None,
    coal_mw: float = None,
    hydro_mw: float = None,
    solar_mw: float = None,
    wind_mw: float = None,
    hvdc_mw: float = None,
    import_mw: float = None,
    grid_status: str = None,
    risk_level: str = None,
    raw_html: str = None,
    source: str = "PGCB_ERP",
    data_classification: str = "OFFICIAL_PGCB",
) -> bool:

    try:
        session = get_session()
        try:
            existing = (
                session.query(GridSnapshot)
                .filter(GridSnapshot.timestamp == timestamp)
                .first()
            )
            if existing:
                return False

            snapshot = GridSnapshot(
                timestamp=timestamp,
                demand_mw=round(demand_mw, 1)
                if demand_mw else None,
                supply_mw=round(supply_mw, 1)
                if supply_mw else None,
                load_shedding_mw=round(load_shedding_mw, 1)
                if load_shedding_mw else None,
                gas_mw=round(gas_mw, 1)
                if gas_mw else None,
                liquid_fuel_mw=round(liquid_fuel_mw, 1)
                if liquid_fuel_mw else None,
                coal_mw=round(coal_mw, 1)
                if coal_mw else None,
                hydro_mw=round(hydro_mw, 1)
                if hydro_mw else None,
                solar_mw=round(solar_mw, 1)
                if solar_mw else None,
                wind_mw=round(wind_mw, 1)
                if wind_mw else None,
                hvdc_mw=round(hvdc_mw, 1)
                if hvdc_mw else None,
                import_mw=round(import_mw, 1)
                if import_mw else None,
                grid_status=grid_status,
                risk_level=risk_level,
                source=source,
                data_classification=data_classification,
                raw_html=raw_html,
            )
            session.add(snapshot)
            session.commit()
            logger.info(
                "Grid snapshot recorded: %s", timestamp
            )
            return True

        except Exception as e:
            session.rollback()
            logger.error(
                "Failed to record grid snapshot: %s", e
            )
            return False

        finally:
            session.close()

    except Exception as e:
        logger.error(
            "Database unavailable for grid snapshot: %s", e
        )
        return False


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
    """Parse PGCB timestamp.
    
    IMPORTANT: PGCB ERP serves Bangladesh Standard Time (BST, UTC+6).
    We parse the datetime and stamp it as BST, then convert to UTC for storage.
    """
    from datetime import timedelta
    
    BST = timezone(timedelta(hours=6))
    
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
            
            # PGCB timestamps are in Bangladesh Standard Time (UTC+6)
            dt_bst = dt.replace(tzinfo=BST)
            
            # Convert to UTC for storage
            dt_utc = dt_bst.astimezone(timezone.utc)
            
            return dt_utc.isoformat()

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

    try:

        try:
            response = _fetch_with_retry(
                PGCB_GENERATION_URL,
                headers={
                    "User-Agent": "PowerFlex-BD/1.0",
                    "Accept": "text/html",
                },
            )
        except (requests.ConnectionError, requests.Timeout) as error:
            return {
                "connected": False,
                "source": "PGCB_GENERATION",
                "status": "NETWORK_ERROR",
                "message": f"Retry exhausted: {error}",
                "data": None,
            }

        validation_error = validate_pgcb_response(response)
        if validation_error:
            return {
                "connected": False,
                "source": "PGCB_GENERATION",
                "status": "PARSE_ERROR",
                "message": validation_error,
                "data": None,
            }

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

        stale = detect_stale_data(timestamp)
        if stale:
            logger.warning(
                "PGCB generation data is stale (>2h old): %s",
                timestamp,
            )

        return {
            "connected": True,
            "source": "PGCB_GENERATION",
            "status": "LIVE",
            "data": {
                "timestamp": timestamp,
                "current_generation_mw": generation_mw,
                "stale": stale,
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

    try:

        try:
            response = _fetch_with_retry(
                PGCB_DEMAND_SUPPLY_URL,
                headers={
                    "User-Agent": "PowerFlex-BD/1.0",
                    "Accept": "text/html",
                },
            )
        except (requests.ConnectionError, requests.Timeout) as error:
            return {
                "connected": False,
                "source": "PGCB_DEMAND_SUPPLY",
                "status": "NETWORK_ERROR",
                "message": f"Retry exhausted: {error}",
                "data": None,
            }

        validation_error = validate_pgcb_response(response)
        if validation_error:
            return {
                "connected": False,
                "source": "PGCB_DEMAND_SUPPLY",
                "status": "PARSE_ERROR",
                "message": validation_error,
                "data": None,
            }

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

        stale = detect_stale_data(timestamp)
        if stale:
            logger.warning(
                "PGCB demand/supply data is stale (>2h old): %s",
                timestamp,
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
                "stale": stale,
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

    result = fetch_with_timeout(
        fetch_pgcb_demand_supply,
        timeout=PGCB_ENDPOINT_TIMEOUT,
        default=None,
        label="grid_official",
    )

    if result is None or not result["connected"]:

        return {
            "project": "PowerFlex BD",
            "status": (
                result["status"]
                if result is not None
                else "PGCB_TIMEOUT"
            ),
            "live": False,
            "message": (
                result["message"]
                if result is not None
                else "PGCB upstream timed out"
            ),
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

    log_grid_snapshot(
        timestamp=data["timestamp"],
        demand_mw=data["current_demand_mw"],
        supply_mw=data["current_supply_mw"],
        load_shedding_mw=data["load_shedding_mw"],
        grid_status=None,
        risk_level=None,
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

    pgcb = fetch_with_timeout(
        fetch_pgcb_grid_data,
        timeout=PGCB_ENDPOINT_TIMEOUT,
        default=None,
        label="grid_live",
    )

    if pgcb is None or not pgcb["connected"]:

        return {
            "project": "PowerFlex BD",
            "resource": "Bangladesh National Grid",
            "status": "PGCB_ADAPTER_READY",
            "data_source": "PGCB / NLDC",
            "live": False,
            "message": (
                pgcb["message"]
                if pgcb is not None
                else "PGCB upstream timed out"
            ),
            "grid_snapshot": None,
        }

    grid = pgcb["data"]

    demand = grid["current_demand_mw"]
    supply = grid["supply_mw"]
    load_shed = grid["load_shedding_mw"]

    generation = grid.get("generation_breakdown", {})
    imports = grid.get("imports", {})

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

    log_grid_snapshot(
        timestamp=grid.get("timestamp", ""),
        demand_mw=demand,
        supply_mw=supply,
        load_shedding_mw=load_shed,
        gas_mw=generation.get("gas_mw"),
        liquid_fuel_mw=generation.get("liquid_fuel_mw"),
        coal_mw=generation.get("coal_mw"),
        hydro_mw=generation.get("hydro_mw"),
        solar_mw=generation.get("solar_mw"),
        wind_mw=generation.get("wind_mw"),
        hvdc_mw=imports.get("india_bheramara_hvdc_mw"),
        import_mw=imports.get("total_imports_mw"),
        grid_status=grid_status,
        risk_level=risk_level,
    )

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
