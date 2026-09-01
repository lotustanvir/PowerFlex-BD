"""Thread-safe TTL cache with named instances.

Provides in-memory caching with configurable per-entry TTL,
hit/miss statistics, and thread safety via threading.Lock.
"""

import logging
import threading
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class Cache:
    """Named, thread-safe TTL cache instance.

    Each entry is stored as ``{key: (insert_timestamp, data)}``.
    Expired entries are lazily evicted on access.
    """

    def __init__(self, name: str, default_ttl: int = 60) -> None:
        self.name = name
        self.default_ttl = default_ttl
        self._store: Dict[str, tuple] = {}
        self._lock = threading.Lock()
        self._hit_count: int = 0
        self._miss_count: int = 0

    def get(self, key: str, ttl_seconds: Optional[int] = None) -> Optional[Any]:
        """Return cached data if present and not expired, else None."""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        now = time.time()

        with self._lock:
            if key in self._store:
                timestamp, data = self._store[key]
                if (now - timestamp) < ttl:
                    self._hit_count += 1
                    logger.debug(
                        "[%s] Cache HIT for key=%s (age=%.1fs)",
                        self.name,
                        key,
                        now - timestamp,
                    )
                    return data
                # Entry expired — evict lazily
                del self._store[key]

            self._miss_count += 1
            logger.debug(
                "[%s] Cache MISS for key=%s",
                self.name,
                key,
            )
            return None

    def set(self, key: str, data: Any) -> None:
        """Store data with current timestamp."""
        with self._lock:
            self._store[key] = (time.time(), data)
            logger.debug(
                "[%s] Cache SET key=%s",
                self.name,
                key,
            )

    def clear(self) -> None:
        """Remove all entries."""
        with self._lock:
            self._store.clear()
            logger.debug("[%s] Cache CLEARED", self.name)

    def stats(self) -> Dict[str, Any]:
        """Return cache statistics."""
        with self._lock:
            return {
                "name": self.name,
                "hit_count": self._hit_count,
                "miss_count": self._miss_count,
                "size": len(self._store),
                "default_ttl": self.default_ttl,
            }

    def get_stale(self, key: str) -> Optional[Any]:
        """Return raw expired entry without TTL check, or None.

        Used as last-resort when a fresh fetch fails but
        we still have older valid data to serve.
        """
        with self._lock:
            if key in self._store:
                _ts, data = self._store[key]
                return dict(data) if isinstance(data, dict) else data
        return None

    def get_cache_metadata(
        self,
        key: str,
        ttl_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Return metadata about a cached entry without retrieving it.

        Useful for attaching ``cached_at``, ``cache_age_seconds``,
        and ``is_fresh`` to API responses.
        """
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        now = time.time()

        with self._lock:
            if key in self._store:
                timestamp, _data = self._store[key]
                age = now - timestamp
                return {
                    "cached_at": timestamp,
                    "cache_age_seconds": round(age, 2),
                    "is_fresh": age < ttl,
                }

        return {
            "cached_at": None,
            "cache_age_seconds": None,
            "is_fresh": False,
        }


# =========================================================
# NAMED CACHE INSTANCES
# =========================================================

_grid_cache = Cache("grid", default_ttl=60)
_solar_cache = Cache("solar", default_ttl=300)
_wind_cache = Cache("wind", default_ttl=300)
_resource_cache = Cache("resource", default_ttl=60)


def get_grid_cache() -> Cache:
    """Return the shared grid cache instance."""
    return _grid_cache


def get_solar_cache() -> Cache:
    """Return the shared solar cache instance."""
    return _solar_cache


def get_wind_cache() -> Cache:
    """Return the shared wind cache instance."""
    return _wind_cache


def get_resource_cache() -> Cache:
    """Return the shared resource cache instance."""
    return _resource_cache
