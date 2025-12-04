import json
import os
import time
from typing import Any, Dict, Optional
from pydantic import BaseModel
import logging

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)

# Cache configuration
CACHE_CONFIG = {
    "default_ttl": 300,  # 5 minutes
    "market_data": 60,  # 1 minute
    "order_book": 30,  # 30 seconds
    "trading_pairs": 600,  # 10 minutes
    "user_info": 1800,  # 30 minutes
    "bot_status": 120,  # 2 minutes
    "portfolio": 300,  # 5 minutes
    "api_keys": 3600,  # 1 hour
    "max_memory_entries": 10000,
    "key_prefix": "co:",  # CryptoOrchestrator
}


class MemoryCache:
    """In-memory cache with TTL support as Redis fallback"""

    def __init__(self, max_size: int = CACHE_CONFIG["max_memory_entries"]):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size

    def set(self, key: str, value: Any, ttl: int = CACHE_CONFIG["default_ttl"]):
        """Set cache entry with TTL"""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(
                self.cache.keys(), key=lambda k: self.cache[k]["expires_at"]
            )
            del self.cache[oldest_key]

        expires_at = time.time() + ttl
        self.cache[key] = {"value": value, "expires_at": expires_at}

    def get(self, key: str) -> Optional[Any]:
        """Get cache entry if not expired"""
        entry = self.cache.get(key)
        if entry and time.time() < entry["expires_at"]:
            return entry["value"]
        elif entry:
            del self.cache[key]  # Remove expired entry
        return None

    def delete(self, key: str):
        """Delete cache entry"""
        self.cache.pop(key, None)

    def exists(self, key: str) -> bool:
        """Check if key exists and not expired"""
        entry = self.cache.get(key)
        return entry is not None and time.time() < entry["expires_at"]

    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()

    def cleanup(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            k for k, v in self.cache.items() if current_time >= v["expires_at"]
        ]
        for key in expired_keys:
            del self.cache[key]


class CacheKeyBuilder:
    """Cache key builder utility"""

    @staticmethod
    def market_data(pair: str, timeframe: str) -> str:
        return f"{CACHE_CONFIG['key_prefix']}market:{pair}:{timeframe}"

    @staticmethod
    def order_book(pair: str) -> str:
        return f"{CACHE_CONFIG['key_prefix']}orderbook:{pair}"

    @staticmethod
    def trading_pairs() -> str:
        return f"{CACHE_CONFIG['key_prefix']}trading_pairs"

    @staticmethod
    def user_info(user_id: str) -> str:
        return f"{CACHE_CONFIG['key_prefix']}user:{user_id}"

    @staticmethod
    def bot_status(bot_id: str) -> str:
        return f"{CACHE_CONFIG['key_prefix']}bot:{bot_id}:status"

    @staticmethod
    def portfolio(mode: str, user_id: Optional[str] = None) -> str:
        user_part = f":{user_id}" if user_id else ""
        return f"{CACHE_CONFIG['key_prefix']}portfolio:{mode}{user_part}"

    @staticmethod
    def api_keys(user_id: str) -> str:
        return f"{CACHE_CONFIG['key_prefix']}api_keys:{user_id}"

    @staticmethod
    def ml_model_state(bot_id: str) -> str:
        return f"{CACHE_CONFIG['key_prefix']}ml_model:{bot_id}"

    @staticmethod
    def backtest_results(bot_id: str) -> str:
        return f"{CACHE_CONFIG['key_prefix']}backtest:{bot_id}"


class CacheService:
    """Advanced cache service with Redis and memory fallback"""

    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.memory_cache = MemoryCache()
        self.redis_available = False
        # Don't call async method from __init__ - will connect lazily when needed
        # self._connect_to_redis()  # Removed - async method cannot be called from sync __init__

    async def _connect_to_redis(self):
        """Connect to Redis if available"""
        if self.redis_available:
            return  # Already connected
        
        if not REDIS_AVAILABLE:
            logger.info("Redis library not available, using memory cache")
            return

        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            logger.info("Redis URL not configured, using memory cache")
            return

        try:
            self.redis = redis.from_url(redis_url, retry_on_timeout=True)
            await self.redis.ping()
            self.redis_available = True
            logger.info("Redis connection successful")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}, using memory cache")
            self.redis_available = False

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cache value with optional TTL"""
        # Connect to Redis lazily if not already connected
        if not self.redis_available:
            await self._connect_to_redis()
        
        effective_ttl = ttl or self._get_ttl_for_key(key)

        if self.redis_available and self.redis:
            try:
                await self.redis.setex(key, effective_ttl, json.dumps(value))
            except Exception as e:
                logger.error(f"Redis set failed: {e}, using memory cache")
                self.memory_cache.set(key, value, effective_ttl)
        else:
            self.memory_cache.set(key, value, effective_ttl)

    async def get(self, key: str) -> Optional[Any]:
        """Get cache value"""
        # Connect to Redis lazily if not already connected
        if not self.redis_available:
            await self._connect_to_redis()
        
        if self.redis_available and self.redis:
            try:
                value = await self.redis.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.error(f"Redis get failed: {e}, using memory cache")
                return self.memory_cache.get(key)
        return self.memory_cache.get(key)

    async def delete(self, key: str) -> None:
        """Delete cache entry"""
        # Connect to Redis lazily if not already connected
        if not self.redis_available:
            await self._connect_to_redis()
        
        if self.redis_available and self.redis:
            try:
                await self.redis.delete(key)
            except Exception as e:
                logger.error(f"Redis delete failed: {e}, using memory cache")
                self.memory_cache.delete(key)
        else:
            self.memory_cache.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        # Connect to Redis lazily if not already connected
        if not self.redis_available:
            await self._connect_to_redis()
        
        if self.redis_available and self.redis:
            try:
                return await self.redis.exists(key) == 1
            except Exception as e:
                logger.error(f"Redis exists failed: {e}, using memory cache")
                return self.memory_cache.exists(key)
        return self.memory_cache.exists(key)

    async def clear(self) -> None:
        """Clear all cache entries"""
        # Connect to Redis lazily if not already connected
        if not self.redis_available:
            await self._connect_to_redis()
        
        if self.redis_available and self.redis:
            try:
                keys = await self.redis.keys(f"{CACHE_CONFIG['key_prefix']}*")
                if keys:
                    await self.redis.delete(*keys)
            except Exception as e:
                logger.error(f"Redis clear failed: {e}, using memory cache")
                self.memory_cache.clear()
        else:
            self.memory_cache.clear()

    def _get_ttl_for_key(self, key: str) -> int:
        """Get appropriate TTL for key type"""
        if "market:" in key:
            return CACHE_CONFIG["market_data"]
        elif "orderbook:" in key:
            return CACHE_CONFIG["order_book"]
        elif "trading_pairs" in key:
            return CACHE_CONFIG["trading_pairs"]
        elif "user:" in key:
            return CACHE_CONFIG["user_info"]
        elif "bot:" in key and ":status" in key:
            return CACHE_CONFIG["bot_status"]
        elif "portfolio:" in key:
            return CACHE_CONFIG["portfolio"]
        elif "api_keys:" in key:
            return CACHE_CONFIG["api_keys"]
        return CACHE_CONFIG["default_ttl"]

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        memory_stats = {
            "size": len(self.memory_cache.cache),
            "max_size": self.memory_cache.max_size,
        }

        redis_stats = {"connected": False}
        if self.redis_available and self.redis:
            try:
                info = await self.redis.info("memory")
                redis_stats = {"connected": True, "memory": info}
            except Exception as e:
                redis_stats = {"connected": False, "error": str(e)}

        return {
            "memory": memory_stats,
            "redis": redis_stats,
            "redis_available": self.redis_available,
        }

    async def close(self) -> None:
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()


# Export singleton instance
cache_service = CacheService()
