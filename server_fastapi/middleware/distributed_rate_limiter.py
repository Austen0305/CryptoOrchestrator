"""
Distributed Rate Limiting with Redis Backend
Sliding window algorithm for accurate rate limiting across multiple instances
"""
import asyncio
from datetime import datetime
from typing import Optional
import logging

try:
    from redis import asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None

logger = logging.getLogger(__name__)


class DistributedRateLimiter:
    """
    Redis-backed rate limiter using sliding window algorithm
    
    Features:
    - Accurate sliding window (not fixed window)
    - Distributed across multiple app instances
    - Per-user and per-IP rate limiting
    - Graceful degradation if Redis unavailable
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.connected = False
        
        # In-memory fallback for when Redis is unavailable
        self.local_cache: dict[str, list[float]] = {}
    
    async def connect(self):
        """Establish Redis connection"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, using in-memory rate limiting")
            return
        
        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2
            )
            await self.redis.ping()
            self.connected = True
            logger.info(f"✅ Distributed rate limiter connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.warning(f"Redis connection failed, using in-memory fallback: {e}")
            self.connected = False
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Distributed rate limiter closed")
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int = 60
    ) -> tuple[bool, dict]:
        """
        Check if request is within rate limit using sliding window
        
        Args:
            key: Unique identifier (user_id, IP, etc.)
            limit: Maximum requests allowed
            window: Time window in seconds
        
        Returns:
            tuple: (allowed: bool, info: dict)
        """
        if self.connected and self.redis:
            return await self._check_redis(key, limit, window)
        else:
            return await self._check_local(key, limit, window)
    
    async def _check_redis(self, key: str, limit: int, window: int) -> tuple[bool, dict]:
        """Redis-backed rate limit check"""
        now = datetime.now().timestamp()
        window_start = now - window
        redis_key = f"rate_limit:{key}"
        
        try:
            # Use Redis pipeline for atomicity
            pipe = self.redis.pipeline()
            
            # Remove old entries outside window
            pipe.zremrangebyscore(redis_key, 0, window_start)
            
            # Count requests in current window
            pipe.zcard(redis_key)
            
            # Add current request timestamp
            pipe.zadd(redis_key, {str(now): now})
            
            # Set expiry on key
            pipe.expire(redis_key, window + 10)
            
            # Get oldest request for reset calculation
            pipe.zrange(redis_key, 0, 0, withscores=True)
            
            results = await pipe.execute()
            current_count = results[1]  # Count before adding current request
            oldest = results[4]  # Oldest request timestamp
            
            # Calculate reset time
            reset_time = int(oldest[0][1] + window) if oldest else int(now + window)
            
            allowed = current_count < limit
            
            info = {
                "limit": limit,
                "remaining": max(0, limit - current_count - (1 if allowed else 0)),
                "reset": reset_time,
                "reset_iso": datetime.fromtimestamp(reset_time).isoformat(),
                "current": current_count + (1 if allowed else 0)
            }
            
            return allowed, info
            
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Fall back to local check
            return await self._check_local(key, limit, window)
    
    async def _check_local(self, key: str, limit: int, window: int) -> tuple[bool, dict]:
        """In-memory fallback rate limit check"""
        now = datetime.now().timestamp()
        window_start = now - window
        
        # Initialize or clean up old entries
        if key not in self.local_cache:
            self.local_cache[key] = []
        
        self.local_cache[key] = [
            ts for ts in self.local_cache[key]
            if ts > window_start
        ]
        
        current_count = len(self.local_cache[key])
        allowed = current_count < limit
        
        if allowed:
            self.local_cache[key].append(now)
        
        # Calculate reset time
        oldest = self.local_cache[key][0] if self.local_cache[key] else now
        reset_time = int(oldest + window)
        
        info = {
            "limit": limit,
            "remaining": max(0, limit - current_count - (1 if allowed else 0)),
            "reset": reset_time,
            "reset_iso": datetime.fromtimestamp(reset_time).isoformat(),
            "current": current_count + (1 if allowed else 0),
            "fallback": True  # Indicate using local cache
        }
        
        return allowed, info
    
    async def reset_limit(self, key: str):
        """Manually reset rate limit for a specific key"""
        if self.connected and self.redis:
            try:
                redis_key = f"rate_limit:{key}"
                await self.redis.delete(redis_key)
                logger.info(f"Rate limit reset for key: {key}")
            except Exception as e:
                logger.error(f"Failed to reset rate limit: {e}")
        
        # Also clear from local cache
        if key in self.local_cache:
            del self.local_cache[key]
    
    async def get_current_usage(self, key: str, window: int = 60) -> dict:
        """Get current usage statistics without incrementing counter"""
        if self.connected and self.redis:
            try:
                now = datetime.now().timestamp()
                window_start = now - window
                redis_key = f"rate_limit:{key}"
                
                # Clean old entries and count
                await self.redis.zremrangebyscore(redis_key, 0, window_start)
                current_count = await self.redis.zcard(redis_key)
                
                # Get oldest for reset calculation
                oldest = await self.redis.zrange(redis_key, 0, 0, withscores=True)
                reset_time = int(oldest[0][1] + window) if oldest else int(now + window)
                
                return {
                    "current": current_count,
                    "reset": reset_time,
                    "reset_iso": datetime.fromtimestamp(reset_time).isoformat()
                }
            except Exception as e:
                logger.error(f"Failed to get usage: {e}")
        
        # Local fallback
        now = datetime.now().timestamp()
        window_start = now - window
        
        if key in self.local_cache:
            self.local_cache[key] = [
                ts for ts in self.local_cache[key]
                if ts > window_start
            ]
            current_count = len(self.local_cache[key])
            oldest = self.local_cache[key][0] if self.local_cache[key] else now
            reset_time = int(oldest + window)
        else:
            current_count = 0
            reset_time = int(now + window)
        
        return {
            "current": current_count,
            "reset": reset_time,
            "reset_iso": datetime.fromtimestamp(reset_time).isoformat(),
            "fallback": True
        }


# Global rate limiter instance
rate_limiter: Optional[DistributedRateLimiter] = None


def get_rate_limiter() -> DistributedRateLimiter:
    """Get or create the global rate limiter instance"""
    global rate_limiter
    if rate_limiter is None:
        import os
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        rate_limiter = DistributedRateLimiter(redis_url)
    return rate_limiter
