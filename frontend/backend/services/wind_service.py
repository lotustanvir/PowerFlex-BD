"""Wind forecast service.

Wraps the raw ``live_wind_forecast()`` endpoint with TTL caching
and graceful error handling.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from backend.services.cache import get_wind_cache

logger = logging.getLogger(__name__)

# =========================================================
# CACHE CONFIG
# =========================================================

_KEY_LIVE = "wind_live"
_TTL = 300  # 5 minutes


# =========================================================
# PUBLIC API
# =========================================================


def get_wind_live() -> Optional[Dict[str, Any]]:
    """Return cached or freshly-fetched wind forecast data.

    Stale-cache fallback: if the live fetch fails but we have
    an older cached entry, return it with status "STALE".
    If no cache exists at all, return a structured error dict.
    """
    cache = get_wind_cache()
    cached = cache.get(_KEY_LIVE, ttl_seconds=_TTL)

    if cached is not None:
        result = dict(cached)
        result["cache"] = cache.get_cache_metadata(_KEY_LIVE, ttl_seconds=_TTL)
        return result

    logger.info("[wind_service] Fetching fresh wind forecast")
    start = time.monotonic()

    try:
        from backend.wind import live_wind_forecast

        fresh = live_wind_forecast()
    except Exception as error:
        logger.error("[wind_service] Wind fetch failed: %s", error)
        elapsed = round(time.monotonic() - start, 3)

        # Attempt stale cache fallback
        stale = cache.get_stale(_KEY_LIVE)
        if stale is not None:
            logger.warning("[wind_service] Serving stale wind data after fetch failure")
            result = dict(stale)
            result["status"] = "STALE"
            result["live"] = False
            result["message"] = f"Wind data is stale: {error}"
            result["fetch_duration_seconds"] = elapsed
            result["cache"] = cache.get_cache_metadata(_KEY_LIVE, ttl_seconds=_TTL)
            return result

        return {
            "project": "PowerFlex BD",
            "resource": "Wind",
            "status": "ERROR",
            "live": False,
            "message": f"Wind forecast failed: {error}",
            "data": None,
            "fetch_duration_seconds": elapsed,
            "cache": cache.get_cache_metadata(_KEY_LIVE, ttl_seconds=_TTL),
        }

    elapsed = round(time.monotonic() - start, 3)
    logger.info("[wind_service] Wind fetch completed in %.3fs", elapsed)

    if fresh is None:
        return None

    if isinstance(fresh, dict):
        cache.set(_KEY_LIVE, fresh)

    result = dict(fresh)
    result["cache"] = cache.get_cache_metadata(_KEY_LIVE, ttl_seconds=_TTL)
    return result


def get_wind_status() -> Dict[str, Any]:
    """Return lightweight status for the wind service."""
    cache = get_wind_cache()
    return {
        "service": "wind_service",
        "cache": cache.stats(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
