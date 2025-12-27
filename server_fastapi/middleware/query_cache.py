"""
Query Result Caching Middleware
Caches database query results to improve performance with multi-level caching
"""

import hashlib
import json
import logging
from functools import wraps
from typing import Any, Callable, Optional
from datetime import timedelta

logger = logging.getLogger(__name__)

# Try to import Redis cache service
try:
    from ..services.cache_service import cache_service

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    cache_service = None

# Try to import cache utilities
try:
    from ..utils.cache_utils import CacheKeyGenerator, CacheSerializer, MultiLevelCache

    CACHE_UTILS_AVAILABLE = True
except ImportError:
    CACHE_UTILS_AVAILABLE = False
    CacheKeyGenerator = None
    CacheSerializer = None
    MultiLevelCache = None

# Global multi-level cache instance
_multi_level_cache: Optional[MultiLevelCache] = None


def get_multi_level_cache(
    redis_client: Optional[Any] = None,
) -> Optional[MultiLevelCache]:
    """Get or create multi-level cache instance"""
    global _multi_level_cache
    if CACHE_UTILS_AVAILABLE and MultiLevelCache:
        if _multi_level_cache is None:
            _multi_level_cache = MultiLevelCache(redis_client=redis_client)
        return _multi_level_cache
    return None


def cache_query_result(
    ttl: int = 300,
    key_prefix: str = "query",
    include_user: bool = False,
    include_params: bool = True,
):
    """
    Decorator to cache database query results.

    Args:
        ttl: Time to live in seconds (default: 5 minutes)
        key_prefix: Prefix for cache key
        include_user: Include user ID in cache key
        include_params: Include function parameters in cache key

    Usage:
        @cache_query_result(ttl=600, key_prefix="bot_list")
        async def get_bots(user_id: str, db: AsyncSession):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Skip caching if Redis not available
            if not REDIS_AVAILABLE or not cache_service:
                logger.debug(
                    f"Cache not available, executing {func.__name__} without cache"
                )
                return await func(*args, **kwargs)

            # Build cache key using utility if available
            if CACHE_UTILS_AVAILABLE and CacheKeyGenerator:
                # Extract user_id if include_user is True
                user_id = None
                if include_user:
                    for arg in args:
                        if isinstance(arg, (int, str)):
                            user_id = str(arg)
                            break
                        elif isinstance(arg, dict):
                            user_id = str(arg.get("id") or arg.get("user_id") or "")
                            if user_id:
                                break

                # Build key components
                key_args = [func.__name__] + list(args[:3])  # First 3 args
                # Copy kwargs before mutating to avoid passing duplicate
                # arguments to the wrapped function (positional + kw)
                key_kwargs = dict(kwargs) if include_params else {}
                if user_id:
                    key_kwargs["user_id"] = user_id

                cache_key = CacheKeyGenerator.generate_key(
                    key_prefix, *key_args, **key_kwargs
                )
            else:
                # Fallback to original key generation
                cache_key_parts = [key_prefix, func.__name__]

                # Include user ID if requested
                if include_user:
                    user_id = None
                    # Check args for user_id or user dict
                    for arg in args:
                        if isinstance(arg, (int, str)):
                            # Direct user_id argument
                            user_id = str(arg)
                            break
                        elif isinstance(arg, dict):
                            # User dict with 'id' or 'user_id'
                            user_id = str(arg.get("id") or arg.get("user_id") or "")
                            if user_id:
                                break
                    if user_id:
                        cache_key_parts.append(f"user:{user_id}")

                # Include parameters if requested
                if include_params:
                    params_str = json.dumps(kwargs, sort_keys=True, default=str)
                    params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
                    cache_key_parts.append(params_hash)

                cache_key = ":".join(cache_key_parts)

            # Try to get from cache (multi-level: memory first, then Redis)
            multi_cache = get_multi_level_cache()
            if multi_cache:
                try:
                    cached_result = await multi_cache.get(cache_key)
                    if cached_result is not None:
                        logger.debug(f"Cache hit for {cache_key}")
                        return cached_result
                except Exception as e:
                    logger.warning(f"Multi-level cache get error for {cache_key}: {e}")

            # Fallback to original cache service
            if REDIS_AVAILABLE and cache_service:
                try:
                    cached_result = await cache_service.get(cache_key)
                    if cached_result is not None:
                        logger.debug(f"Cache hit for {cache_key}")
                        return cached_result
                except Exception as e:
                    logger.warning(f"Cache get error for {cache_key}: {e}")

            # Execute function and cache result
            try:
                result = await func(*args, **kwargs)

                # Cache the result (multi-level if available)
                if multi_cache:
                    try:
                        await multi_cache.set(cache_key, result, ttl=ttl)
                        logger.debug(f"Cached result for {cache_key} (TTL: {ttl}s)")
                    except Exception as e:
                        logger.warning(
                            f"Multi-level cache set error for {cache_key}: {e}"
                        )
                elif REDIS_AVAILABLE and cache_service:
                    try:
                        await cache_service.set(cache_key, result, ttl=ttl)
                        logger.debug(f"Cached result for {cache_key} (TTL: {ttl}s)")
                    except Exception as e:
                        logger.warning(f"Cache set error for {cache_key}: {e}")

                return result
            except Exception as e:
                logger.error(f"Error executing {func.__name__}: {e}", exc_info=True)
                raise

        return wrapper

    return decorator


def invalidate_cache_pattern(pattern: str):
    """
    Invalidate all cache keys matching a pattern.

    Args:
        pattern: Cache key pattern (supports wildcards)

    Usage:
        await invalidate_cache_pattern("bot_list:*")
    """
    if not REDIS_AVAILABLE or not cache_service:
        return

    try:
        # Pattern-based cache invalidation
        # Note: Full implementation would require cache_service to support pattern matching
        # Current implementation uses exact key invalidation via cache_service.delete()
        # For pattern-based invalidation, consider using Redis SCAN with pattern matching
        logger.info(f"Cache invalidation requested for pattern: {pattern}")
        # Future enhancement: Implement pattern-based cache invalidation in cache_service
        # This would allow invalidating all keys matching a pattern (e.g., "user:*:bots")
    except Exception as e:
        logger.error(f"Cache invalidation error for pattern {pattern}: {e}")
