"""Solar forecast service.

Wraps the raw ``live_solar_forecast()`` endpoint with TTL caching
and graceful error handling.  If the AI model is unavailable the
service returns a structured error state instead of crashing.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from backend.services.cache import get_solar_cache

logger = logging.getLogger(__name__)

# =========================================================
# CACHE CONFIG
# =========================================================

_KEY_LIVE = "solar_live"
_TTL = 300  # 5 minutes


# =========================================================
# PUBLIC API
# =========================================================


def get_solar_live() -> Optional[Dict[str, Any]]:
    """Return cached or freshly-fetched solar forecast data.

    Stale-cache fallback: if the live fetch fails but we have
    an older cached entry, return it with status "STALE".
    If no cache exists at all, return a structured error dict.
    """
    cache = get_solar_cache()
    cached = cache.get(_KEY_LIVE, ttl_seconds=_TTL)

    if cached is not None:
        result = dict(cached)
        result["cache"] = cache.get_cache_metadata(_KEY_LIVE, ttl_seconds=_TTL)
        return result

    logger.info("[solar_service] Fetching fresh solar forecast")
    start = time.monotonic()

    try:
        from backend.solar import live_solar_forecast

        fresh = live_solar_forecast()
    except Exception as error:
        logger.error("[solar_service] Solar fetch failed: %s", error)
        elapsed = round(time.monotonic() - start, 3)

        # Attempt stale cache fallback
        stale = cache.get_stale(_KEY_LIVE)
        if stale is not None:
            logger.warning("[solar_service] Serving stale solar data after fetch failure")
            result = dict(stale)
            result["status"] = "STALE"
            result["live"] = False
            result["message"] = f"Solar data is stale: {error}"
            result["fetch_duration_seconds"] = elapsed
            result["cache"] = cache.get_cache_metadata(_KEY_LIVE, ttl_seconds=_TTL)
            return result

        return {
            "project": "PowerFlex BD",
            "resource": "Solar",
            "status": "ERROR",
            "live": False,
            "message": f"Solar forecast failed: {error}",
            "data": None,
            "fetch_duration_seconds": elapsed,
            "cache": cache.get_cache_metadata(_KEY_LIVE, ttl_seconds=_TTL),
        }

    elapsed = round(time.monotonic() - start, 3)
    logger.info("[solar_service] Solar fetch completed in %.3fs", elapsed)

    if fresh is None:
        return None

    # Cache only valid forecast data
    if isinstance(fresh, dict):
        cache.set(_KEY_LIVE, fresh)

    result = dict(fresh)
    result["cache"] = cache.get_cache_metadata(_KEY_LIVE, ttl_seconds=_TTL)
    return result


def get_solar_status() -> Dict[str, Any]:
    """Return lightweight status for the solar service."""
    cache = get_solar_cache()
    return {
        "service": "solar_service",
        "cache": cache.stats(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
