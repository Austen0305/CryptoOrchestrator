"""
Cache Utility Functions
Helper functions for caching strategies and cache management.
Includes versioning, analytics, and predictive preloading support.
"""

import asyncio
import gzip
import hashlib
import json
import logging
import time
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

import msgpack

logger = logging.getLogger(__name__)

# Import enhanced features (with try/except for optional dependencies)
try:
    from .cache_versioning import get_cache_version_manager

    VERSIONING_AVAILABLE = True
except ImportError:
    VERSIONING_AVAILABLE = False
    get_cache_version_manager = None

try:
    from ..services.cache.cache_analytics import get_cache_analytics

    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False
    get_cache_analytics = None

try:
    from ..services.cache.predictive_preloader import get_predictive_preloader

    PRELOADER_AVAILABLE = True
except ImportError:
    PRELOADER_AVAILABLE = False
    get_predictive_preloader = None

# Try to import Redis
try:
    import redis.asyncio as aioredis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None


class CacheKeyGenerator:
    """Generate consistent cache keys"""

    @staticmethod
    def generate_key(prefix: str, *args, **kwargs) -> str:
        """
        Generate a cache key from prefix and arguments.

        Args:
            prefix: Key prefix (e.g., 'user', 'bot')
            *args: Positional arguments to include in key
            **kwargs: Keyword arguments to include in key

        Returns:
            Cache key string
        """
        # Sort kwargs for consistent key generation
        sorted_kwargs = sorted(kwargs.items()) if kwargs else []

        # Create key components
        components = [prefix]
        components.extend(str(arg) for arg in args)
        components.extend(f"{k}:{v}" for k, v in sorted_kwargs)

        # Join and hash for shorter keys
        key_string = ":".join(components)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:16]

        return f"{prefix}:{key_hash}"

    @staticmethod
    def generate_tag_key(tag: str) -> str:
        """Generate a tag key for cache invalidation"""
        return f"tag:{tag}"


class CacheSerializer:
    """Serialize/deserialize cache values"""

    @staticmethod
    def serialize(value: Any, compress: bool = False) -> bytes:
        """
        Serialize a value for caching.

        Args:
            value: Value to serialize
            compress: Whether to compress the serialized value

        Returns:
            Serialized bytes
        """
        try:
            # Try msgpack first (faster, smaller)
            serialized = msgpack.packb(value, default=str)
        except (TypeError, ValueError):
            # Fallback to JSON
            serialized = json.dumps(value, default=str).encode("utf-8")

        if compress and len(serialized) > 1024:  # Compress if > 1KB
            serialized = gzip.compress(serialized)

        return serialized

    @staticmethod
    def deserialize(data: bytes, compressed: bool = False) -> Any:
        """
        Deserialize a cached value.

        Args:
            data: Serialized bytes
            compressed: Whether the data is compressed

        Returns:
            Deserialized value
        """
        try:
            if compressed:
                data = gzip.decompress(data)

            # Try msgpack first
            try:
                return msgpack.unpackb(data, raw=False)
            except (msgpack.exceptions.ExtraData, ValueError):
                # Fallback to JSON
                return json.loads(data.decode("utf-8"))
        except Exception as e:
            logger.error(f"Error deserializing cache value: {e}", exc_info=True)
            return None


class MultiLevelCache:
    """
    Multi-level cache with memory and Redis.
    Includes cache hit/miss metrics, versioning, analytics, and predictive preloading.
    """

    def __init__(
        self,
        redis_client: Any | None = None,
        enable_versioning: bool = True,
        enable_analytics: bool = True,
        enable_preloading: bool = True,
    ):
        self.memory_cache: dict = {}
        self.redis_client = redis_client
        self.memory_ttl: dict = {}  # Track TTL for memory cache

        # Cache metrics
        self.hits = 0
        self.misses = 0
        self.memory_hits = 0
        self.redis_hits = 0
        self.evictions = 0
        self.total_size_bytes = 0

        # Enhanced features
        self.enable_versioning = enable_versioning and VERSIONING_AVAILABLE
        self.enable_analytics = enable_analytics and ANALYTICS_AVAILABLE
        self.enable_preloading = enable_preloading and PRELOADER_AVAILABLE

        if self.enable_versioning and get_cache_version_manager:
            self.version_manager = get_cache_version_manager()
        else:
            self.version_manager = None

        if self.enable_analytics and get_cache_analytics:
            self.analytics = get_cache_analytics()
        else:
            self.analytics = None

        if self.enable_preloading and get_predictive_preloader:
            self.preloader = get_predictive_preloader()
        else:
            self.preloader = None

    async def get(
        self, key: str, default: Any = None, track_analytics: bool = True
    ) -> Any:
        """
        Get value from cache (memory first, then Redis).
        Includes analytics tracking and predictive preloading.

        Args:
            key: Cache key
            default: Default value if not found
            track_analytics: Whether to track this access in analytics

        Returns:
            Cached value or default
        """
        start_time = time.time()
        hit = False
        error = None
        size_bytes = None

        try:
            # Check memory cache first
            if key in self.memory_cache:
                # Check TTL
                if key in self.memory_ttl:
                    if datetime.now() < self.memory_ttl[key]:
                        value = self.memory_cache[key]
                        hit = True
                        self.hits += 1
                        self.memory_hits += 1
                        size_bytes = len(str(value).encode())

                        # Track analytics
                        if self.enable_analytics and track_analytics:
                            response_time = (time.time() - start_time) * 1000
                            self.analytics.record_operation(
                                "get",
                                key,
                                hit=True,
                                response_time_ms=response_time,
                                size_bytes=size_bytes,
                            )

                        # Record access for predictive preloading
                        if self.enable_preloading:
                            self.preloader.record_access(key)
                            # Trigger predictive preloading in background
                            asyncio.create_task(
                                self.preloader.preload_predicted_keys(key, self)
                            )

                        return value
                    else:
                        # Expired, remove from memory
                        del self.memory_cache[key]
                        del self.memory_ttl[key]
                else:
                    value = self.memory_cache[key]
                    hit = True
                    self.hits += 1
                    self.memory_hits += 1
                    size_bytes = len(str(value).encode())

                    if self.enable_analytics and track_analytics:
                        response_time = (time.time() - start_time) * 1000
                        self.analytics.record_operation(
                            "get",
                            key,
                            hit=True,
                            response_time_ms=response_time,
                            size_bytes=size_bytes,
                        )

                    if self.enable_preloading:
                        self.preloader.record_access(key)

                    return value

            # Check Redis if available
            if self.redis_client:
                try:
                    data = await self.redis_client.get(key)
                    if data:
                        value = CacheSerializer.deserialize(data, compressed=True)
                        # Store in memory cache for faster access
                        self.memory_cache[key] = value
                        hit = True
                        self.hits += 1
                        self.redis_hits += 1
                        size_bytes = len(data)

                        if self.enable_analytics and track_analytics:
                            response_time = (time.time() - start_time) * 1000
                            self.analytics.record_operation(
                                "get",
                                key,
                                hit=True,
                                response_time_ms=response_time,
                                size_bytes=size_bytes,
                            )

                        if self.enable_preloading:
                            self.preloader.record_access(key)
                            asyncio.create_task(
                                self.preloader.preload_predicted_keys(key, self)
                            )

                        return value
                except Exception as e:
                    error = str(e)
                    logger.warning(f"Redis get error: {e}", exc_info=True)

            # Cache miss
            self.misses += 1

            if self.enable_analytics and track_analytics:
                response_time = (time.time() - start_time) * 1000
                self.analytics.record_operation(
                    "get", key, hit=False, response_time_ms=response_time, error=error
                )

            if self.enable_preloading:
                self.preloader.record_access(key)

            return default

        except Exception as e:
            error = str(e)
            logger.error(f"Cache get error: {e}", exc_info=True)

            if self.enable_analytics and track_analytics:
                response_time = (time.time() - start_time) * 1000
                self.analytics.record_operation(
                    "get", key, hit=False, response_time_ms=response_time, error=error
                )

            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300,
        memory_only: bool = False,
        track_analytics: bool = True,
    ) -> bool:
        """
        Set value in cache (both memory and Redis).
        Includes analytics tracking.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            memory_only: Only cache in memory (skip Redis)
            track_analytics: Whether to track this operation in analytics

        Returns:
            True if successful
        """
        start_time = time.time()
        error = None
        size_bytes = None

        try:
            # Store in memory cache
            self.memory_cache[key] = value
            self.memory_ttl[key] = datetime.now() + timedelta(seconds=ttl)
            size_bytes = len(str(value).encode())

            # Store in Redis if available
            if not memory_only and self.redis_client:
                try:
                    serialized = CacheSerializer.serialize(value, compress=True)
                    size_bytes = len(serialized)
                    await self.redis_client.setex(key, ttl, serialized)
                except Exception as e:
                    error = str(e)
                    logger.warning(f"Redis set error: {e}", exc_info=True)

            if self.enable_analytics and track_analytics:
                response_time = (time.time() - start_time) * 1000
                self.analytics.record_operation(
                    "set",
                    key,
                    hit=False,
                    response_time_ms=response_time,
                    size_bytes=size_bytes,
                    error=error,
                )

            return True

        except Exception as e:
            error = str(e)
            logger.error(f"Cache set error: {e}", exc_info=True)

            if self.enable_analytics and track_analytics:
                response_time = (time.time() - start_time) * 1000
                self.analytics.record_operation(
                    "set", key, hit=False, response_time_ms=response_time, error=error
                )

            return False

    async def delete(self, key: str) -> bool:
        """Delete key from both caches"""
        self.memory_cache.pop(key, None)
        self.memory_ttl.pop(key, None)

        if self.redis_client:
            try:
                await self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete error: {e}", exc_info=True)

        return True

    async def invalidate_tag(self, tag: str) -> int:
        """
        Invalidate all keys with a specific tag.

        Args:
            tag: Tag to invalidate

        Returns:
            Number of keys invalidated
        """
        tag_key = CacheKeyGenerator.generate_tag_key(tag)

        if self.redis_client:
            try:
                # Get all keys with this tag
                pattern = f"{tag_key}:*"
                keys = []
                async for key in self.redis_client.scan_iter(match=pattern):
                    keys.append(key)

                # Delete all keys
                if keys:
                    await self.redis_client.delete(*keys)

                return len(keys)
            except Exception as e:
                logger.warning(f"Redis tag invalidation error: {e}", exc_info=True)

        return 0

    def clear_memory(self):
        """Clear memory cache"""
        self.memory_cache.clear()
        self.memory_ttl.clear()

    def get_metrics(self) -> dict[str, Any]:
        """Get cache metrics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        # Estimate memory usage
        memory_size = sum(len(str(v).encode()) for v in self.memory_cache.values())

        return {
            "hits": self.hits,
            "misses": self.misses,
            "memory_hits": self.memory_hits,
            "redis_hits": self.redis_hits,
            "hit_rate": round(hit_rate, 2),
            "memory_size_bytes": memory_size,
            "memory_entries": len(self.memory_cache),
            "evictions": self.evictions,
        }

    def reset_metrics(self) -> None:
        """Reset cache metrics"""
        self.hits = 0
        self.misses = 0
        self.memory_hits = 0
        self.redis_hits = 0
        self.evictions = 0


def cache_result(
    ttl: int = 300,
    key_prefix: str = "cache",
    include_user: bool = False,
    compress: bool = True,
):
    """
    Decorator to cache function results.

    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
        include_user: Include user ID in cache key
        compress: Compress cached values
    """

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_components = [key_prefix, func.__name__]

            if include_user and "current_user" in kwargs:
                user_id = kwargs["current_user"].get("id")
                if user_id:
                    key_components.append(f"user:{user_id}")

            # Include relevant args/kwargs in key
            for arg in args[:3]:  # First 3 args
                if isinstance(arg, (str, int, float)):
                    key_components.append(str(arg))

            cache_key = CacheKeyGenerator.generate_key(*key_components)

            # Try to get from cache
            # Note: This requires a cache instance to be available
            # For now, this is a template - actual implementation would need cache instance

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result (would need cache instance)

            return result

        return wrapper

    return decorator


# Global cache instance
_cache_instance: MultiLevelCache | None = None


def get_cache_instance() -> MultiLevelCache:
    """Get or create the global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = MultiLevelCache(
            use_l1_cache=True,
            use_l2_cache=True,
            use_redis=REDIS_AVAILABLE,
            redis_url="redis://localhost",
            l1_ttl_seconds=300,
            l2_ttl_seconds=3600,
        )
    return _cache_instance
