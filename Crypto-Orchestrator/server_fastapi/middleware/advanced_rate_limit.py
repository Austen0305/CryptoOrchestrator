"""
Advanced Rate Limiting Middleware
Redis-backed sliding window rate limiting with per-user and per-IP limits
"""

import time
import hashlib
from typing import Optional, Dict
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class AdvancedRateLimiter:
    """Advanced rate limiter with Redis-backed sliding window"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.redis_available = redis_client is not None

        # Default rate limits (requests per window)
        self.default_limits = {
            "anonymous": {"requests": 60, "window": 60},  # 60 req/min
            "authenticated": {"requests": 300, "window": 60},  # 300 req/min
            "premium": {"requests": 1000, "window": 60},  # 1000 req/min
        }

        # Per-endpoint limits
        self.endpoint_limits: Dict[str, Dict] = {
            "/api/auth/login": {"requests": 5, "window": 60},  # 5 login attempts/min
            "/api/auth/register": {"requests": 3, "window": 60},  # 3 registrations/min
            "/api/trades": {"requests": 100, "window": 60},  # 100 trades/min
            "/api/bots": {"requests": 50, "window": 60},  # 50 bot operations/min
        }

    def _get_limit_key(self, identifier: str, endpoint: str) -> str:
        """Generate Redis key for rate limit"""
        key_data = f"{identifier}:{endpoint}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"rate_limit:{key_hash}"

    async def check_rate_limit(
        self, identifier: str, endpoint: str, user_tier: str = "anonymous"
    ) -> tuple[bool, int, int]:
        """
        Check if request is within rate limit

        Returns:
            (allowed, remaining, reset_time)
        """
        # Get limit for endpoint or use default
        limit_config = self.endpoint_limits.get(endpoint)
        if not limit_config:
            limit_config = self.default_limits.get(
                user_tier, self.default_limits["anonymous"]
            )

        requests_limit = limit_config["requests"]
        window_seconds = limit_config["window"]

        # Use in-memory fallback if Redis not available
        if not self.redis_available:
            return self._check_memory_limit(
                identifier, endpoint, requests_limit, window_seconds
            )

        # Redis sliding window implementation
        key = self._get_limit_key(identifier, endpoint)
        current_time = time.time()
        window_start = current_time - window_seconds

        try:
            # Use sorted set for sliding window
            pipe = self.redis.pipeline()

            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)

            # Count current requests
            pipe.zcard(key)

            # Add current request
            pipe.zadd(key, {str(current_time): current_time})

            # Set expiration
            pipe.expire(key, window_seconds)

            results = await pipe.execute()
            current_count = results[1]

            if current_count >= requests_limit:
                # Get oldest entry to calculate reset time
                oldest = await self.redis.zrange(key, 0, 0, withscores=True)
                if oldest:
                    reset_time = int(oldest[0][1] + window_seconds)
                else:
                    reset_time = int(current_time + window_seconds)

                return False, 0, reset_time

            remaining = requests_limit - current_count - 1
            reset_time = int(current_time + window_seconds)

            return True, remaining, reset_time

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Allow request on error (fail open)
            return True, requests_limit, int(time.time() + window_seconds)

    def _check_memory_limit(
        self, identifier: str, endpoint: str, requests_limit: int, window_seconds: int
    ) -> tuple[bool, int, int]:
        """In-memory fallback rate limiting"""
        # Simple in-memory implementation (not thread-safe, but works for fallback)
        if not hasattr(self, "_memory_limits"):
            self._memory_limits: Dict[str, list] = {}

        key = f"{identifier}:{endpoint}"
        current_time = time.time()
        window_start = current_time - window_seconds

        if key not in self._memory_limits:
            self._memory_limits[key] = []

        # Remove old entries
        self._memory_limits[key] = [
            t for t in self._memory_limits[key] if t > window_start
        ]

        # Check limit
        if len(self._memory_limits[key]) >= requests_limit:
            reset_time = int(self._memory_limits[key][0] + window_seconds)
            return False, 0, reset_time

        # Add current request
        self._memory_limits[key].append(current_time)

        remaining = requests_limit - len(self._memory_limits[key])
        reset_time = int(current_time + window_seconds)

        return True, remaining, reset_time


class AdvancedRateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for advanced rate limiting"""

    def __init__(self, app: ASGIApp, redis_client: Optional[redis.Redis] = None):
        super().__init__(app)
        self.rate_limiter = AdvancedRateLimiter(redis_client)

    def _get_identifier(self, request: Request) -> str:
        """Get identifier for rate limiting (user ID or IP)"""
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    def _get_user_tier(self, request: Request) -> str:
        """Get user tier for rate limiting"""
        # Check if user is authenticated
        user = getattr(request.state, "user", None)
        if not user:
            return "anonymous"

        # Check subscription tier
        subscription = getattr(user, "subscription", None)
        if subscription and subscription.tier == "enterprise":
            return "premium"

        return "authenticated"

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and metrics
        if request.url.path in [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]:
            return await call_next(request)

        identifier = self._get_identifier(request)
        endpoint = request.url.path
        user_tier = self._get_user_tier(request)

        allowed, remaining, reset_time = await self.rate_limiter.check_rate_limit(
            identifier, endpoint, user_tier
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please try again after {reset_time}",
                    "retry_after": reset_time,
                    "limit": self.rate_limiter.endpoint_limits.get(
                        endpoint, self.rate_limiter.default_limits[user_tier]
                    )["requests"],
                },
                headers={
                    "X-RateLimit-Limit": str(
                        self.rate_limiter.endpoint_limits.get(
                            endpoint, self.rate_limiter.default_limits[user_tier]
                        )["requests"]
                    ),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(reset_time),
                },
            )

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(
            self.rate_limiter.endpoint_limits.get(
                endpoint, self.rate_limiter.default_limits[user_tier]
            )["requests"]
        )
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)

        return response
