import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import requests


# =========================================================
# POWERFLEX BD - BIOMASS DATA FETCHER
# =========================================================
#
# Fetches national-level crop and livestock data
# from FAOSTAT API and World Bank API.
#
# Caches results to avoid redundant API calls.
# =========================================================


# =========================================================
# CACHE CONFIGURATION
# =========================================================

CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

CACHE_EXPIRY_SECONDS = 86400  # 24 hours


# =========================================================
# CACHE HELPERS
# =========================================================

def cache_path(name: str) -> Path:
    return CACHE_DIR / f"biomass_{name}.json"


def load_cache(name: str) -> Optional[Dict]:
    path = cache_path(name)

    if not path.exists():
        return None

    try:

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        cached_at = data.get("cached_at", 0)

        if time.time() - cached_at > CACHE_EXPIRY_SECONDS:
            return None

        return data.get("payload")

    except Exception:
        return None


def save_cache(name: str, payload: Any):
    path = cache_path(name)

    try:

        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "cached_at": time.time(),
                "payload": payload,
            }, f, indent=2)

    except Exception:
        pass


# =========================================================
# FETCH FAOSTAT CROP DATA
# =========================================================

FAOSTAT_API = (
    "https://fenixservices.fao.org/faostat/api/v1/"
    "en/data/QCL"
)


def fetch_faostat_crops() -> Optional[Dict]:
    """
    Fetch Bangladesh crop production from FAOSTAT API.
    Returns national-level production in tonnes.
    Falls back to published data on any error.
    """

    cached = load_cache("faostat_crops")

    if cached is not None:
        return cached

    crops_to_fetch = {
        "Rice, paddy": "rice",
        "Wheat": "wheat",
        "Maize": "maize",
        "Sugar cane": "sugarcane",
        "Jute": "jute",
    }

    results = {}

    for fao_name, key in crops_to_fetch.items():

        try:

            params = {
                "area": "32",
                "item": fao_name,
                "element": "5510",
                "year": "2023",
                "output_type": "json",
            }

            response = requests.get(
                FAOSTAT_API,
                params=params,
                timeout=10,
                headers={
                    "Accept": "application/json",
                },
            )

            if response.status_code == 200:

                data = response.json()

                rows = data.get("data", [])

                if rows:

                    latest = rows[-1]

                    value = latest.get("value")

                    if value is not None:

                        results[key] = {
                            "production_tonnes": float(
                                value
                            ),
                            "year": latest.get(
                                "year", 2023
                            ),
                            "unit": "tonnes",
                        }

        except Exception:
            continue

    if results:

        save_cache("faostat_crops", results)

    return results if results else None


# =========================================================
# FETCH WORLD BANK LIVESTOCK DATA
# =========================================================

WB_API = (
    "https://api.worldbank.org/v2/"
    "country/BGD/indicator/"
)


def fetch_worldbank_livestock() -> Optional[Dict]:
    """
    Fetch Bangladesh livestock data from World Bank API.
    Falls back to published data on any error.
    """

    cached = load_cache("worldbank_livestock")

    if cached is not None:
        return cached

    indicators = {
        "AG.LIV.CATT.HD": "cattle",
        "AG.LIV BUFF.HD": "buffalo",
        "AG.LIV.GOAT.HD": "goat",
        "AG.LIV.SHEP.HD": "sheep",
    }

    results = {}

    for indicator, key in indicators.items():

        try:

            url = f"{WB_API}{indicator}"

            params = {
                "format": "json",
                "date": "2020:2023",
                "per_page": 5,
            }

            response = requests.get(
                url,
                params=params,
                timeout=10,
            )

            if response.status_code == 200:

                data = response.json()

                if (
                    isinstance(data, list)
                    and len(data) > 1
                ):

                    records = data[1]

                    if records:

                        latest = records[0]

                        value = latest.get("value")

                        if value is not None:

                            results[key] = {
                                "population": float(
                                    value
                                ),
                                "year": latest.get(
                                    "date", "2022"
                                ),
                                "unit": "head",
                            }

        except Exception:
            continue

    if results:

        save_cache(
            "worldbank_livestock", results
        )

    return results if results else None


# =========================================================
# FALLBACK: DLS NATIONAL LIVESTOCK DATA
# =========================================================
#
# From DLS "Livestock Economy at a Glance 2023-24"
# Used when World Bank API is unavailable.
# =========================================================

DLS_LIVESTOCK_NATIONAL = {
    "cattle": {
        "population": 2_501_300,
        "year": 2024,
        "unit": "head",
        "source": "DLS 2023-24",
    },
    "buffalo": {
        "population": 152_400,
        "year": 2024,
        "unit": "head",
        "source": "DLS 2023-24",
    },
    "goat": {
        "population": 2_711_700,
        "year": 2024,
        "unit": "head",
        "source": "DLS 2023-24",
    },
    "sheep": {
        "population": 390_300,
        "year": 2024,
        "unit": "head",
        "source": "DLS 2023-24",
    },
    "poultry": {
        "population": 39_603_800,
        "year": 2024,
        "unit": "head",
        "source": "DLS 2023-24",
    },
}


# =========================================================
# FALLBACK: BBS CROP PRODUCTION DATA
# =========================================================
#
# From BBS Yearbook and USDA/FAS.
# Used when FAOSTAT API is unavailable.
# =========================================================

BBS_CROP_NATIONAL = {
    "rice": {
        "production_tonnes": 56_347_851,
        "year": 2024,
        "unit": "tonnes",
        "source": "FAOSTAT/BBS",
    },
    "wheat": {
        "production_tonnes": 1_100_000,
        "year": 2024,
        "unit": "tonnes",
        "source": "USDA/FAS",
    },
    "maize": {
        "production_tonnes": 5_640_000,
        "year": 2024,
        "unit": "tonnes",
        "source": "USDA/FAS",
    },
    "sugarcane": {
        "production_tonnes": 2_930_000,
        "year": 2024,
        "unit": "tonnes",
        "source": "FAOSTAT",
    },
    "jute": {
        "production_tonnes": 1_600_000,
        "year": 2024,
        "unit": "tonnes",
        "source": "BBS estimate",
    },
}


# =========================================================
# UNIFIED FETCH
# =========================================================

def fetch_all_biomass_data(
    use_fallback: bool = False
) -> Dict[str, Any]:
    """
    Fetch all available biomass data sources.
    Uses cache. Falls back to published defaults.
    If use_fallback=True, skip APIs entirely.
    """

    if use_fallback:

        return {
            "crops": BBS_CROP_NATIONAL,
            "livestock": DLS_LIVESTOCK_NATIONAL,
            "crop_source": "BBS/USDA fallback",
            "livestock_source": "DLS fallback",
            "retrieved_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

    faostat = fetch_faostat_crops()
    worldbank = fetch_worldbank_livestock()

    crop_data = faostat if faostat else BBS_CROP_NATIONAL
    livestock_data = (
        worldbank
        if worldbank
        else DLS_LIVESTOCK_NATIONAL
    )

    crop_source = (
        "FAOSTAT API"
        if faostat
        else "BBS/USDA fallback"
    )
    livestock_source = (
        "World Bank API"
        if worldbank
        else "DLS fallback"
    )

    return {
        "crops": crop_data,
        "livestock": livestock_data,
        "crop_source": crop_source,
        "livestock_source": livestock_source,
        "retrieved_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }
