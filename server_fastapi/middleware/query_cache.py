"""
Query Result Caching Middleware
Caches database query results to improve performance
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


def cache_query_result(
    ttl: int = 300,
    key_prefix: str = "query",
    include_user: bool = False,
    include_params: bool = True
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
                logger.debug(f"Cache not available, executing {func.__name__} without cache")
                return await func(*args, **kwargs)
            
            # Build cache key
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
            
            # Try to get from cache
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
                
                # Cache the result
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
        # This would need to be implemented in cache_service
        # For now, just log the intent
        logger.info(f"Cache invalidation requested for pattern: {pattern}")
        # TODO: Implement pattern-based cache invalidation in cache_service
    except Exception as e:
        logger.error(f"Cache invalidation error for pattern {pattern}: {e}")

