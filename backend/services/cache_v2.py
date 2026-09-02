import json
import logging
import os
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

CACHE_BACKEND = os.getenv("CACHE_BACKEND", "memory")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


class CacheBackend(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[Any]: ...

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def clear(self) -> None: ...

    @abstractmethod
    def stats(self) -> Dict[str, Any]: ...


class MemoryCacheBackend(CacheBackend):
    def __init__(self, default_ttl: int = 60) -> None:
        self.default_ttl = default_ttl
        self._store: Dict[str, tuple] = {}
        self._lock = threading.Lock()
        self._hit_count: int = 0
        self._miss_count: int = 0

    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        with self._lock:
            if key in self._store:
                timestamp, data, ttl = self._store[key]
                if (now - timestamp) < ttl:
                    self._hit_count += 1
                    return data
                del self._store[key]
            self._miss_count += 1
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        effective_ttl = ttl if ttl is not None else self.default_ttl
        with self._lock:
            self._store[key] = (time.time(), value, effective_ttl)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "backend": "memory",
                "hit_count": self._hit_count,
                "miss_count": self._miss_count,
                "size": len(self._store),
                "default_ttl": self.default_ttl,
            }


class RedisCacheBackend(CacheBackend):
    def __init__(self, redis_url: str = REDIS_URL, default_ttl: int = 60) -> None:
        self.default_ttl = default_ttl
        self._redis = None
        self._hit_count: int = 0
        self._miss_count: int = 0
        try:
            import redis
            self._redis = redis.Redis.from_url(
                redis_url, decode_responses=True, socket_timeout=2
            )
            self._redis.ping()
            logger.info("Redis connection established: %s", redis_url)
        except Exception as e:
            logger.warning("Redis unavailable, will fallback to memory: %s", e)
            self._redis = None

    @property
    def is_available(self) -> bool:
        if self._redis is None:
            return False
        try:
            self._redis.ping()
            return True
        except Exception:
            return False

    def get(self, key: str) -> Optional[Any]:
        if not self.is_available:
            self._miss_count += 1
            return None
        try:
            raw = self._redis.get(key)
            if raw is not None:
                self._hit_count += 1
                return json.loads(raw)
            self._miss_count += 1
            return None
        except Exception as e:
            logger.warning("Redis GET failed for key=%s: %s", key, e)
            self._miss_count += 1
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if not self.is_available:
            return
        try:
            ttl_seconds = ttl or self.default_ttl
            self._redis.setex(key, ttl_seconds, json.dumps(value))
        except Exception as e:
            logger.warning("Redis SET failed for key=%s: %s", key, e)

    def delete(self, key: str) -> None:
        if not self.is_available:
            return
        try:
            self._redis.delete(key)
        except Exception as e:
            logger.warning("Redis DELETE failed for key=%s: %s", key, e)

    def clear(self) -> None:
        if not self.is_available:
            return
        try:
            self._redis.flushdb()
        except Exception as e:
            logger.warning("Redis CLEAR failed: %s", e)

    def stats(self) -> Dict[str, Any]:
        return {
            "backend": "redis",
            "available": self.is_available,
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "default_ttl": self.default_ttl,
        }


class CacheManager:
    def __init__(self) -> None:
        self._memory = MemoryCacheBackend()
        self._redis = RedisCacheBackend()
        self._preferred = CACHE_BACKEND

    @property
    def backend(self) -> CacheBackend:
        if self._preferred == "redis" and self._redis.is_available:
            return self._redis
        return self._memory

    def get(self, key: str) -> Optional[Any]:
        result = self.backend.get(key)
        if result is not None:
            return result
        if self._preferred == "redis" and self.backend is self._redis:
            result = self._memory.get(key)
            if result is not None:
                self._redis.set(key, result)
            return result
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self._memory.set(key, value, ttl)
        if self._preferred == "redis" and self._redis.is_available:
            self._redis.set(key, value, ttl)

    def delete(self, key: str) -> None:
        self._memory.delete(key)
        if self._preferred == "redis" and self._redis.is_available:
            self._redis.delete(key)

    def clear(self) -> None:
        self._memory.clear()
        if self._preferred == "redis" and self._redis.is_available:
            self._redis.clear()

    def stats(self) -> Dict[str, Any]:
        return {
            "preferred_backend": self._preferred,
            "active_backend": self.backend.stats(),
            "memory": self._memory.stats(),
            "redis": self._redis.stats(),
        }


_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    global _manager
    if _manager is None:
        _manager = CacheManager()
    return _manager
