"""Unified resource service.

Wraps ``fetch_all_resources()`` from ``backend.resource_data`` with
TTL caching and accepts prefetched grid/solar/wind data to avoid
duplicate external requests.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from backend.resource_data import fetch_all_resources
from backend.services.cache import get_resource_cache

logger = logging.getLogger(__name__)

# =========================================================
# CACHE CONFIG
# =========================================================

_KEY_LIVE = "resources_all"
_TTL = 60  # seconds


# =========================================================
# PUBLIC API
# =========================================================


def get_all_resources(
    grid_data: Optional[Dict[str, Any]] = None,
    solar_data: Optional[Dict[str, Any]] = None,
    wind_data: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Return cached or freshly-built unified resource data.

    When prefetched data is supplied, those values are passed
    through to ``fetch_all_resources()`` so it skips its own
    HTTP calls.

    Returns None only when the underlying function fails completely.
    """
    cache = get_resource_cache()

    # When callers provide prefetched data the combined payload
    # differs from a plain cached hit, so bypass the cache in
    # that case and always build fresh.
    use_cache = (
        grid_data is None
        and solar_data is None
        and wind_data is None
    )

    if use_cache:
        cached = cache.get(_KEY_LIVE, ttl_seconds=_TTL)
        if cached is not None:
            result = dict(cached)
            result["cache"] = cache.get_cache_metadata(
                _KEY_LIVE, ttl_seconds=_TTL
            )
            return result

    logger.info("[resource_service] Building fresh resource data")
    start = time.monotonic()

    try:
        fresh = fetch_all_resources(
            prefetched_grid_data=grid_data,
            prefetched_solar_data=solar_data,
            prefetched_wind_data=wind_data,
        )
    except Exception as error:
        logger.error("[resource_service] Build failed: %s", error)
        elapsed = round(time.monotonic() - start, 3)
        return {
            "project": "PowerFlex BD",
            "module": "Unified Resource Data",
            "status": "ERROR",
            "message": f"Resource build failed: {error}",
            "resources": None,
            "fetch_duration_seconds": elapsed,
            "cache": cache.get_cache_metadata(
                _KEY_LIVE, ttl_seconds=_TTL
            ),
        }

    elapsed = round(time.monotonic() - start, 3)
    logger.info(
        "[resource_service] Build completed in %.3fs", elapsed
    )

    if fresh is None:
        return None

    # Only cache when no prefetched data was injected
    if use_cache:
        cache.set(_KEY_LIVE, fresh)

    result = dict(fresh)
    result["cache"] = cache.get_cache_metadata(
        _KEY_LIVE, ttl_seconds=_TTL
    )
    return result


def get_resource_status() -> Dict[str, Any]:
    """Return lightweight status for the resource service."""
    cache = get_resource_cache()
    return {
        "service": "resource_service",
        "cache": cache.stats(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
