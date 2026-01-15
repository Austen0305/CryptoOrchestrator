"""
Advanced Caching Strategies
Provides sophisticated caching strategies beyond basic caching
"""

import asyncio
import json
import logging
import time
from collections import OrderedDict
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class CacheStrategy:
    """Base cache strategy interface"""

    async def get(self, key: str) -> Any | None:
        """Get value from cache"""
        raise NotImplementedError

    async def set(self, key: str, value: Any, ttl: int | None = None):
        """Set value in cache"""
        raise NotImplementedError

    async def delete(self, key: str):
        """Delete value from cache"""
        raise NotImplementedError

    async def clear(self):
        """Clear all cache"""
        raise NotImplementedError


class MultiLevelCache(CacheStrategy):
    """
    Multi-level cache with L1 (memory) and L2 (Redis)

    Features:
    - Fast memory cache (L1)
    - Persistent Redis cache (L2)
    - Automatic promotion
    - Write-through strategy
    """

    def __init__(
        self,
        redis_client: redis.Redis | None = None,
        l1_size: int = 1000,
        l1_ttl: int = 60,
        l2_ttl: int = 3600,
    ):
        self.redis = redis_client
        self.redis_available = redis_client is not None and REDIS_AVAILABLE
        self.l1_cache: OrderedDict = OrderedDict()
        self.l1_size = l1_size
        self.l1_ttl = l1_ttl
        self.l2_ttl = l2_ttl
        self.stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "misses": 0,
            "sets": 0,
        }

    async def get(self, key: str) -> Any | None:
        """Get from L1 first, then L2"""
        # Check L1
        if key in self.l1_cache:
            entry = self.l1_cache[key]
            if time.time() < entry["expires"]:
                self.l1_cache.move_to_end(key)  # Move to end (LRU)
                self.stats["l1_hits"] += 1
                return entry["value"]
            else:
                del self.l1_cache[key]

        # Check L2 (Redis)
        if self.redis_available:
            try:
                cached = await self.redis.get(f"cache:{key}")
                if cached:
                    value = json.loads(cached)
                    # Promote to L1
                    await self._set_l1(key, value)
                    self.stats["l2_hits"] += 1
                    return value
            except Exception as e:
                logger.debug(f"Redis get error: {e}")

        self.stats["misses"] += 1
        return None

    async def set(self, key: str, value: Any, ttl: int | None = None):
        """Set in both L1 and L2"""
        # Set L1
        await self._set_l1(key, value, ttl or self.l1_ttl)

        # Set L2 (Redis)
        if self.redis_available:
            try:
                await self.redis.setex(
                    f"cache:{key}",
                    ttl or self.l2_ttl,
                    json.dumps(value),
                )
            except Exception as e:
                logger.debug(f"Redis set error: {e}")

        self.stats["sets"] += 1

    async def _set_l1(self, key: str, value: Any, ttl: int | None = None):
        """Set in L1 cache"""
        # Remove oldest if at capacity
        if len(self.l1_cache) >= self.l1_size:
            self.l1_cache.popitem(last=False)

        self.l1_cache[key] = {
            "value": value,
            "expires": time.time() + (ttl or self.l1_ttl),
        }

    async def delete(self, key: str):
        """Delete from both levels"""
        if key in self.l1_cache:
            del self.l1_cache[key]

        if self.redis_available:
            try:
                await self.redis.delete(f"cache:{key}")
            except Exception as e:
                logger.debug(f"Redis delete error: {e}")

    async def clear(self):
        """Clear both levels"""
        self.l1_cache.clear()

        if self.redis_available:
            try:
                # Clear all cache keys
                keys = await self.redis.keys("cache:*")
                if keys:
                    await self.redis.delete(*keys)
            except Exception as e:
                logger.debug(f"Redis clear error: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        total_requests = (
            self.stats["l1_hits"] + self.stats["l2_hits"] + self.stats["misses"]
        )
        hit_rate = (
            (self.stats["l1_hits"] + self.stats["l2_hits"]) / total_requests * 100
            if total_requests > 0
            else 0
        )

        return {
            **self.stats,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "l1_size": len(self.l1_cache),
            "l1_capacity": self.l1_size,
        }


class CacheWarmer:
    """Cache warming utility"""

    def __init__(self, cache: CacheStrategy):
        self.cache = cache
        self.warming_tasks: list[Callable] = []

    def register_warming_task(self, task: Callable, key_pattern: str):
        """Register a cache warming task"""
        self.warming_tasks.append((task, key_pattern))

    async def warm_cache(self):
        """Execute all warming tasks"""
        for task, _key_pattern in self.warming_tasks:
            try:
                if asyncio.iscoroutinefunction(task):
                    await task(self.cache)
                else:
                    task(self.cache)
            except Exception as e:
                logger.error(f"Cache warming task failed: {e}")


# Global cache instances
multi_level_cache: MultiLevelCache | None = None
cache_warmer: CacheWarmer | None = None


def get_multi_level_cache(redis_client: redis.Redis | None = None) -> MultiLevelCache:
    """Get or create multi-level cache"""
    global multi_level_cache

    if multi_level_cache is None:
        multi_level_cache = MultiLevelCache(redis_client=redis_client)
    return multi_level_cache
