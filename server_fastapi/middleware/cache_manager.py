"""
Intelligent Request Caching with Redis Backend
Reduces load and improves response times
"""
import json
import hashlib
from typing import Optional, Any, Callable
from functools import wraps
import asyncio
import logging

logger = logging.getLogger(__name__)

# Redis connection will be initialized in main.py
redis_client = None


def init_redis(client):
    """Initialize Redis client"""
    global redis_client
    redis_client = client
    logger.info("Redis cache initialized")


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments"""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(
    ttl: int = 300,
    prefix: str = "",
    key_builder: Optional[Callable] = None
):
    """
    Decorator for caching function results
    
    Args:
        ttl: Time to live in seconds (default 5 minutes)
        prefix: Cache key prefix
        key_builder: Custom function to build cache key
    
    Example:
        @cached(ttl=60, prefix="market_data")
        async def get_market_data(symbol: str):
            return await fetch_from_exchange(symbol)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # If Redis not available, just call function
            if redis_client is None:
                logger.debug("Redis not available, skipping cache")
                return await func(*args, **kwargs)
            
            # Build cache key
            if key_builder:
                key = key_builder(*args, **kwargs)
            else:
                key = cache_key(*args, **kwargs)
            
            full_key = f"{prefix}:{func.__name__}:{key}" if prefix else f"{func.__name__}:{key}"
            
            try:
                # Try to get from cache
                cached_value = await redis_client.get(full_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit: {full_key}")
                    return json.loads(cached_value)
                
                # Cache miss - call function
                logger.debug(f"Cache miss: {full_key}")
                result = await func(*args, **kwargs)
                
                # Store in cache
                await redis_client.setex(
                    full_key,
                    ttl,
                    json.dumps(result, default=str)
                )
                
                return result
                
            except Exception as e:
                logger.error(f"Cache error: {e}")
                # On error, just call function
                return await func(*args, **kwargs)
        
        # Add cache invalidation method
        async def invalidate(*args, **kwargs):
            if redis_client is None:
                return
            
            if key_builder:
                key = key_builder(*args, **kwargs)
            else:
                key = cache_key(*args, **kwargs)
            
            full_key = f"{prefix}:{func.__name__}:{key}" if prefix else f"{func.__name__}:{key}"
            
            try:
                await redis_client.delete(full_key)
                logger.debug(f"Cache invalidated: {full_key}")
            except Exception as e:
                logger.error(f"Cache invalidation error: {e}")
        
        wrapper.invalidate = invalidate
        wrapper.cache_prefix = prefix
        
        return wrapper
    
    return decorator


async def invalidate_pattern(pattern: str):
    """Invalidate all cache keys matching pattern"""
    if redis_client is None:
        return
    
    try:
        keys = []
        async for key in redis_client.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            await redis_client.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache entries matching {pattern}")
    except Exception as e:
        logger.error(f"Pattern invalidation error: {e}")


async def clear_all_cache():
    """Clear all cache entries"""
    if redis_client is None:
        return
    
    try:
        await redis_client.flushdb()
        logger.info("All cache cleared")
    except Exception as e:
        logger.error(f"Cache clear error: {e}")


class CacheStats:
    """Track cache hit/miss statistics"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.errors = 0
    
    def record_hit(self):
        self.hits += 1
    
    def record_miss(self):
        self.misses += 1
    
    def record_error(self):
        self.errors += 1
    
    def get_stats(self) -> dict:
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
            "total_requests": total,
            "hit_rate_percentage": round(hit_rate, 2)
        }
    
    def reset(self):
        self.hits = 0
        self.misses = 0
        self.errors = 0


cache_stats = CacheStats()


class CacheWarmer:
    """
    Proactively warm cache entries before they expire
    Prevents cache stampede and improves response times
    """
    
    def __init__(self):
        self.warming_tasks: dict[str, asyncio.Task] = {}
        self.running = False
    
    async def warm_cache(
        self,
        func: Callable,
        args: tuple,
        kwargs: dict,
        ttl: int,
        prefix: str = ""
    ):
        """
        Continuously warm a cache entry
        Refreshes at 80% of TTL to prevent expiration
        """
        if redis_client is None:
            return
        
        cache_key_val = cache_key(*args, **kwargs)
        full_key = f"{prefix}:{func.__name__}:{cache_key_val}" if prefix else f"{func.__name__}:{cache_key_val}"
        
        try:
            while self.running:
                # Initial population
                result = await func(*args, **kwargs)
                await redis_client.setex(
                    full_key,
                    ttl,
                    json.dumps(result, default=str)
                )
                logger.debug(f"Cache warmed: {full_key}")
                
                # Wait 80% of TTL before refreshing
                await asyncio.sleep(ttl * 0.8)
                
        except asyncio.CancelledError:
            logger.debug(f"Cache warming cancelled for {full_key}")
        except Exception as e:
            logger.error(f"Cache warming error for {full_key}: {e}")
    
    def start_warming(
        self,
        name: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        ttl: int = 300,
        prefix: str = ""
    ):
        """Start warming a specific cache entry"""
        if name in self.warming_tasks:
            logger.warning(f"Cache warming already active for {name}")
            return
        
        self.running = True
        kwargs = kwargs or {}
        
        task = asyncio.create_task(
            self.warm_cache(func, args, kwargs, ttl, prefix)
        )
        self.warming_tasks[name] = task
        logger.info(f"Started cache warming for {name}")
    
    def stop_warming(self, name: str):
        """Stop warming a specific cache entry"""
        if name in self.warming_tasks:
            self.warming_tasks[name].cancel()
            del self.warming_tasks[name]
            logger.info(f"Stopped cache warming for {name}")
    
    def stop_all(self):
        """Stop all cache warming tasks"""
        self.running = False
        for name, task in list(self.warming_tasks.items()):
            task.cancel()
        self.warming_tasks.clear()
        logger.info("Stopped all cache warming tasks")
    
    def get_status(self) -> dict:
        """Get status of all warming tasks"""
        return {
            "running": self.running,
            "active_warmers": len(self.warming_tasks),
            "tasks": list(self.warming_tasks.keys())
        }


cache_warmer = CacheWarmer()


def cached_with_warming(
    ttl: int = 300,
    prefix: str = "",
    warm: bool = False,
    warm_name: Optional[str] = None
):
    """
    Enhanced caching decorator with optional cache warming
    
    Args:
        ttl: Time to live in seconds
        prefix: Cache key prefix
        warm: Enable cache warming
        warm_name: Unique name for the warming task
    
    Example:
        @cached_with_warming(ttl=60, prefix="market", warm=True, warm_name="btc_price")
        async def get_btc_price():
            return await fetch_price("BTC/USDT")
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Use regular caching logic
            if redis_client is None:
                return await func(*args, **kwargs)
            
            key = cache_key(*args, **kwargs)
            full_key = f"{prefix}:{func.__name__}:{key}" if prefix else f"{func.__name__}:{key}"
            
            try:
                cached_value = await redis_client.get(full_key)
                if cached_value is not None:
                    cache_stats.record_hit()
                    logger.debug(f"Cache hit: {full_key}")
                    return json.loads(cached_value)
                
                cache_stats.record_miss()
                logger.debug(f"Cache miss: {full_key}")
                result = await func(*args, **kwargs)
                
                await redis_client.setex(
                    full_key,
                    ttl,
                    json.dumps(result, default=str)
                )
                
                return result
                
            except Exception as e:
                cache_stats.record_error()
                logger.error(f"Cache error: {e}")
                return await func(*args, **kwargs)
        
        # Add cache warming control methods
        async def start_warming(*args, **kwargs):
            """Start cache warming for this function"""
            name = warm_name or f"{prefix}:{func.__name__}"
            cache_warmer.start_warming(name, func, args, kwargs, ttl, prefix)
        
        def stop_warming():
            """Stop cache warming for this function"""
            name = warm_name or f"{prefix}:{func.__name__}"
            cache_warmer.stop_warming(name)
        
        wrapper.start_warming = start_warming
        wrapper.stop_warming = stop_warming
        
        return wrapper
    
    return decorator


async def get_cache_info() -> dict:
    """Get comprehensive cache information"""
    if redis_client is None:
        return {"available": False}
    
    try:
        info = await redis_client.info("stats")
        memory_info = await redis_client.info("memory")
        
        return {
            "available": True,
            "stats": cache_stats.get_stats(),
            "redis": {
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
                "used_memory_human": memory_info.get("used_memory_human"),
                "used_memory_peak_human": memory_info.get("used_memory_peak_human")
            },
            "warming": cache_warmer.get_status()
        }
    except Exception as e:
        logger.error(f"Error getting cache info: {e}")
        return {"available": False, "error": str(e)}
