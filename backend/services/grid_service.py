"""Grid data service.

Wraps the raw PGCB scraper functions with TTL caching, cache
metadata, and graceful stale-data fallback.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from backend.grid import (
    fetch_pgcb_demand_supply,
    fetch_pgcb_generation,
    fetch_pgcb_grid_data,
)

from backend.services.cache import get_grid_cache

logger = logging.getLogger(__name__)

# =========================================================
# CACHE KEYS
# =========================================================

_KEY_LIVE = "grid_live"
_KEY_OFFICIAL = "grid_official"
_KEY_GENERATION = "grid_generation"
_TTL_LIVE = 60
_TTL_OFFICIAL = 60


def _cache_metadata(cache, key: str) -> Dict[str, Any]:
    """Attach cache timing info to a response dict."""
    meta = cache.get_cache_metadata(key, ttl_seconds=_TTL_LIVE)
    return {
        "cached_at": meta["cached_at"],
        "cache_age_seconds": meta["cache_age_seconds"],
        "is_fresh": meta["is_fresh"],
    }


# =========================================================
# PUBLIC API
# =========================================================


def get_grid_live() -> Optional[Dict[str, Any]]:
    """Return cached or freshly-fetched live grid data.

    Returns None only when both cache and live fetch are empty.
    Never fabricates data.
    """
    cache = get_grid_cache()
    cached = cache.get(_KEY_LIVE, ttl_seconds=_TTL_LIVE)

    if cached is not None:
        result = dict(cached)
        result["live"] = result.get("connected", False)
        result["cache"] = _cache_metadata(cache, _KEY_LIVE)
        return result

    # Cache miss or stale — attempt live fetch
    logger.info("[grid_service] Fetching fresh live grid data")
    start = time.monotonic()

    try:
        fresh = fetch_pgcb_grid_data()
    except Exception as error:
        logger.error("[grid_service] Live fetch failed: %s", error)
        fresh = None

    elapsed = round(time.monotonic() - start, 3)
    logger.info("[grid_service] Live fetch completed in %.3fs", elapsed)

    if fresh is None:
        # Try stale cache as last resort
        stale = cache.get_stale(_KEY_LIVE)
        if stale is not None:
            stale["cache"] = _cache_metadata(cache, _KEY_LIVE)
            stale["live"] = stale.get("connected", False)
            stale["status"] = "STALE"
            return stale
        return None

    # Cache both successful and failed results to avoid hammering upstream
    cache.set(_KEY_LIVE, fresh)

    result = dict(fresh)
    result["live"] = result.get("connected", False)
    result["cache"] = _cache_metadata(cache, _KEY_LIVE)
    return result


def get_grid_official() -> Optional[Dict[str, Any]]:
    """Return cached or freshly-fetched official PGCB demand/supply data."""
    cache = get_grid_cache()
    cached = cache.get(_KEY_OFFICIAL, ttl_seconds=_TTL_OFFICIAL)

    if cached is not None:
        result = dict(cached)
        result["cache"] = cache.get_cache_metadata(
            _KEY_OFFICIAL, ttl_seconds=_TTL_OFFICIAL
        )
        return result

    logger.info("[grid_service] Fetching fresh official data")
    start = time.monotonic()

    try:
        fresh = fetch_pgcb_demand_supply()
    except Exception as error:
        logger.error("[grid_service] Official fetch failed: %s", error)
        fresh = None

    elapsed = round(time.monotonic() - start, 3)
    logger.info("[grid_service] Official fetch completed in %.3fs", elapsed)

    if fresh is None:
        stale = cache.get_stale(_KEY_OFFICIAL)
        if stale is not None:
            stale["cache"] = cache.get_cache_metadata(
                _KEY_OFFICIAL, ttl_seconds=_TTL_OFFICIAL
            )
            stale["status"] = "STALE"
            return stale
        return None

    if fresh.get("connected"):
        cache.set(_KEY_OFFICIAL, fresh)

    result = dict(fresh)
    result["cache"] = cache.get_cache_metadata(
        _KEY_OFFICIAL, ttl_seconds=_TTL_OFFICIAL
    )
    return result


def get_grid_status() -> Dict[str, Any]:
    """Return a lightweight status payload (no upstream call)."""
    cache = get_grid_cache()
    return {
        "service": "grid_service",
        "cache": cache.stats(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

