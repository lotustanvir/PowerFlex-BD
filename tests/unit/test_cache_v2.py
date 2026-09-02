import time
import pytest
from unittest.mock import patch, MagicMock

from backend.services.cache_v2 import (
    CacheBackend,
    MemoryCacheBackend,
    RedisCacheBackend,
    CacheManager,
    get_cache_manager,
)


class TestMemoryCacheBackend:
    def test_set_and_get(self):
        cache = MemoryCacheBackend(default_ttl=10)
        cache.set("key1", {"data": "value"})
        result = cache.get("key1")
        assert result == {"data": "value"}

    def test_get_missing_key(self):
        cache = MemoryCacheBackend()
        assert cache.get("nonexistent") is None

    def test_ttl_expiration(self):
        cache = MemoryCacheBackend(default_ttl=1)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_delete(self):
        cache = MemoryCacheBackend()
        cache.set("key1", "value1")
        cache.delete("key1")
        assert cache.get("key1") is None

    def test_delete_nonexistent(self):
        cache = MemoryCacheBackend()
        cache.delete("nonexistent")  # Should not raise

    def test_clear(self):
        cache = MemoryCacheBackend()
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        cache.clear()
        assert cache.get("k1") is None
        assert cache.get("k2") is None

    def test_stats(self):
        cache = MemoryCacheBackend(default_ttl=30)
        cache.set("k1", "v1")
        cache.get("k1")
        cache.get("missing")
        stats = cache.stats()
        assert stats["backend"] == "memory"
        assert stats["hit_count"] == 1
        assert stats["miss_count"] == 1
        assert stats["size"] == 1
        assert stats["default_ttl"] == 30

    def test_custom_ttl(self):
        cache = MemoryCacheBackend(default_ttl=1)
        cache.set("key1", "val", ttl=3)
        time.sleep(1.1)
        assert cache.get("key1") == "val"

    def test_thread_safety(self):
        cache = MemoryCacheBackend(default_ttl=10)
        errors = []

        def writer():
            for i in range(100):
                cache.set(f"key_{i}", i)

        def reader():
            for i in range(100):
                cache.get(f"key_{i}")

        threads = []
        for _ in range(5):
            threads.append(__import__("threading").Thread(target=writer))
            threads.append(__import__("threading").Thread(target=reader))
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0


class TestRedisCacheBackend:
    def test_unavailable_redis_returns_none(self):
        cache = RedisCacheBackend(redis_url="redis://invalid:9999")
        assert cache.is_available is False
        assert cache.get("key") is None

    def test_set_on_unavailable_is_noop(self):
        cache = RedisCacheBackend(redis_url="redis://invalid:9999")
        cache.set("key", "value")  # Should not raise

    def test_delete_on_unavailable_is_noop(self):
        cache = RedisCacheBackend(redis_url="redis://invalid:9999")
        cache.delete("key")  # Should not raise

    def test_clear_on_unavailable_is_noop(self):
        cache = RedisCacheBackend(redis_url="redis://invalid:9999")
        cache.clear()  # Should not raise

    def test_stats_when_unavailable(self):
        cache = RedisCacheBackend(redis_url="redis://invalid:9999")
        stats = cache.stats()
        assert stats["backend"] == "redis"
        assert stats["available"] is False

    @patch("backend.services.cache_v2.RedisCacheBackend.is_available", new_callable=lambda: property(lambda self: True))
    def test_get_returns_none_when_redis_fails(self, mock_avail):
        cache = RedisCacheBackend(redis_url="redis://invalid:9999")
        cache._redis = MagicMock()
        cache._redis.get.side_effect = Exception("connection lost")
        result = cache.get("key")
        assert result is None


class TestCacheManager:
    def test_defaults_to_memory(self):
        with patch("backend.services.cache_v2.CACHE_BACKEND", "memory"):
            manager = CacheManager()
            manager.set("k1", "v1")
            assert manager.get("k1") == "v1"

    def test_memory_fallback_on_redis_failure(self):
        with patch("backend.services.cache_v2.CACHE_BACKEND", "redis"):
            manager = CacheManager()
            manager._redis = RedisCacheBackend(redis_url="redis://invalid:9999")
            manager.set("k1", "v1")
            assert manager.get("k1") == "v1"
            assert manager.backend is manager._memory

    def test_set_and_get(self):
        manager = CacheManager()
        manager.set("test_key", {"a": 1})
        assert manager.get("test_key") == {"a": 1}

    def test_delete(self):
        manager = CacheManager()
        manager.set("k1", "v1")
        manager.delete("k1")
        assert manager.get("k1") is None

    def test_clear(self):
        manager = CacheManager()
        manager.set("k1", "v1")
        manager.set("k2", "v2")
        manager.clear()
        assert manager.get("k1") is None
        assert manager.get("k2") is None

    def test_stats(self):
        manager = CacheManager()
        manager.set("k1", "v1")
        stats = manager.stats()
        assert "preferred_backend" in stats
        assert "active_backend" in stats
        assert "memory" in stats
        assert "redis" in stats

    def test_ttl_propagation(self):
        manager = CacheManager()
        manager.set("k1", "v1", ttl=1)
        assert manager.get("k1") == "v1"
        time.sleep(1.1)
        assert manager.get("k1") is None

    def test_get_missing_returns_none(self):
        manager = CacheManager()
        assert manager.get("nonexistent") is None


class TestGetCacheManagerSingleton:
    def test_returns_same_instance(self):
        m1 = get_cache_manager()
        m2 = get_cache_manager()
        assert m1 is m2


class TestCacheBackendInterface:
    def test_memory_implements_interface(self):
        cache = MemoryCacheBackend()
        assert hasattr(cache, "get")
        assert hasattr(cache, "set")
        assert hasattr(cache, "delete")
        assert hasattr(cache, "clear")
        assert hasattr(cache, "stats")

    def test_redis_implements_interface(self):
        cache = RedisCacheBackend()
        assert hasattr(cache, "get")
        assert hasattr(cache, "set")
        assert hasattr(cache, "delete")
        assert hasattr(cache, "clear")
        assert hasattr(cache, "stats")
