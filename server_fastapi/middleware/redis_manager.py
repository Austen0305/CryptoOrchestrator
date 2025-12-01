"""
Redis Cache Manager with Automatic In-Memory Fallback
Provides resilient caching with graceful degradation
"""

import json
import logging
from typing import Optional, Any, Callable
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Try to import redis
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    logger.warning("redis package not installed, using in-memory cache fallback")
    REDIS_AVAILABLE = False


class RedisCacheManager:
    """Redis cache with automatic fallback to in-memory storage"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None
        self.available = False
        self._memory_cache = {}  # Fallback in-memory cache
        self._memory_ttl = {}  # TTL tracking for memory cache
        
    async def connect(self):
        """Connect to Redis with fallback to in-memory"""
        if not self.redis_url or not REDIS_AVAILABLE:
            logger.warning("Redis not configured or unavailable, using in-memory cache")
            self.available = False
            return
        
        try:
            self.client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            await self.client.ping()
            self.available = True
            logger.info("✅ Redis connected successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed, using in-memory cache: {e}")
            self.available = False
            self.client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (Redis or in-memory)"""
        # Try Redis first if available
        if self.available and self.client:
            try:
                value = await self.client.get(key)
                if value is not None:
                    return json.loads(value)
                return None
            except Exception as e:
                logger.error(f"Redis get error for key '{key}': {e}")
                # Fall through to memory cache
        
        # Use in-memory cache
        return self._get_from_memory(key)
    
    async def set(self, key: str, value: Any, expire: int = 300):
        """Set value in cache with expiration (seconds)"""
        # Try Redis first if available
        if self.available and self.client:
            try:
                await self.client.setex(key, expire, json.dumps(value))
                return True
            except Exception as e:
                logger.error(f"Redis set error for key '{key}': {e}")
                # Fall through to memory cache
        
        # Use in-memory cache
        self._set_in_memory(key, value, expire)
        return True
    
    async def delete(self, key: str):
        """Delete key from cache"""
        # Try Redis if available
        if self.available and self.client:
            try:
                await self.client.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error for key '{key}': {e}")
        
        # Also remove from memory cache
        self._memory_cache.pop(key, None)
        self._memory_ttl.pop(key, None)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if self.available and self.client:
            try:
                return await self.client.exists(key) > 0
            except Exception as e:
                logger.error(f"Redis exists error for key '{key}': {e}")
        
        # Check memory cache
        if key in self._memory_cache:
            if self._is_expired(key):
                self._memory_cache.pop(key, None)
                self._memory_ttl.pop(key, None)
                return False
            return True
        return False
    
    async def clear(self, pattern: Optional[str] = None):
        """Clear cache (all keys or matching pattern)"""
        if self.available and self.client:
            try:
                if pattern:
                    # Delete keys matching pattern
                    cursor = 0
                    while True:
                        cursor, keys = await self.client.scan(cursor, match=pattern, count=100)
                        if keys:
                            await self.client.delete(*keys)
                        if cursor == 0:
                            break
                else:
                    # Clear all keys
                    await self.client.flushdb()
            except Exception as e:
                logger.error(f"Redis clear error: {e}")
        
        # Clear memory cache
        if pattern:
            # Simple pattern matching for memory cache
            import fnmatch
            keys_to_delete = [k for k in self._memory_cache.keys() if fnmatch.fnmatch(k, pattern)]
            for key in keys_to_delete:
                self._memory_cache.pop(key, None)
                self._memory_ttl.pop(key, None)
        else:
            self._memory_cache.clear()
            self._memory_ttl.clear()
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            try:
                await self.client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
    
    # In-memory cache helpers
    def _get_from_memory(self, key: str) -> Optional[Any]:
        """Get value from in-memory cache"""
        if key not in self._memory_cache:
            return None
        
        # Check if expired
        if self._is_expired(key):
            self._memory_cache.pop(key, None)
            self._memory_ttl.pop(key, None)
            return None
        
        return self._memory_cache[key]
    
    def _set_in_memory(self, key: str, value: Any, expire: int):
        """Set value in in-memory cache"""
        self._memory_cache[key] = value
        self._memory_ttl[key] = datetime.utcnow() + timedelta(seconds=expire)
    
    def _is_expired(self, key: str) -> bool:
        """Check if memory cache key is expired"""
        if key not in self._memory_ttl:
            return True
        return datetime.utcnow() > self._memory_ttl[key]
    
    # Decorator for caching function results
    def cached(self, expire: int = 300, key_prefix: str = ""):
        """
        Decorator for caching function results
        
        Usage:
            @cache_manager.cached(expire=600, key_prefix="user")
            async def get_user_data(user_id: str):
                return {"id": user_id, "data": "..."}
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
                
                # Try to get from cache
                cached_value = await self.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return cached_value
                
                # Execute function
                logger.debug(f"Cache miss for key: {cache_key}")
                result = await func(*args, **kwargs)
                
                # Cache result
                await self.set(cache_key, result, expire)
                
                return result
            return wrapper
        return decorator


# Global cache manager instance
cache_manager = RedisCacheManager()


async def get_cache_manager() -> RedisCacheManager:
    """Dependency function for FastAPI"""
    return cache_manager
