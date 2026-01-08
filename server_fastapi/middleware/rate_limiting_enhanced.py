"""
Enhanced Rate Limiting Middleware
Advanced rate limiting with per-endpoint configuration, dynamic limits, and analytics
"""

import hashlib
import logging
import time
from collections import defaultdict

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class EnhancedRateLimiter:
    """
    Enhanced rate limiter with:
    - Per-endpoint configuration
    - Dynamic limit adjustment
    - User tier support
    - Analytics and reporting
    - Sliding window algorithm
    """

    def __init__(self, redis_client: redis.Redis | None = None):
        self.redis = redis_client
        self.redis_available = redis_client is not None

        # Default limits by user tier
        self.tier_limits = {
            "anonymous": {"requests": 60, "window": 60},
            "authenticated": {"requests": 300, "window": 60},
            "premium": {"requests": 1000, "window": 60},
            "enterprise": {"requests": 10000, "window": 60},
        }

        # Per-endpoint limits (overrides tier limits)
        self.endpoint_limits: dict[str, dict] = {
            "/api/auth/login": {"requests": 5, "window": 60},
            "/api/auth/register": {"requests": 3, "window": 60},
            "/api/auth/forgot-password": {"requests": 3, "window": 300},
            "/api/trades": {"requests": 100, "window": 60},
            "/api/bots": {"requests": 50, "window": 60},
            "/api/portfolio": {"requests": 200, "window": 60},
            "/api/markets": {"requests": 500, "window": 60},
        }

        # Analytics
        self.analytics = {
            "total_requests": 0,
            "rate_limited": 0,
            "by_endpoint": defaultdict(int),
            "by_tier": defaultdict(int),
        }

    def configure_endpoint(self, endpoint: str, requests: int, window: int):
        """Configure rate limit for specific endpoint"""
        self.endpoint_limits[endpoint] = {"requests": requests, "window": window}
        logger.info(f"Configured rate limit for {endpoint}: {requests}/{window}s")

    async def check_rate_limit(
        self, identifier: str, endpoint: str, user_tier: str = "anonymous"
    ) -> tuple[bool, int, int, dict[str, Any]]:
        """
        Check rate limit with enhanced analytics

        Returns:
            (allowed, remaining, reset_time, analytics)
        """
        # Get limit configuration
        limit_config = self.endpoint_limits.get(endpoint) or self.tier_limits.get(
            user_tier, self.tier_limits["anonymous"]
        )

        requests_limit = limit_config["requests"]
        window_seconds = limit_config["window"]

        # Update analytics
        self.analytics["total_requests"] += 1
        self.analytics["by_endpoint"][endpoint] += 1
        self.analytics["by_tier"][user_tier] += 1

        # Check limit
        if self.redis_available:
            allowed, remaining, reset_time = await self._check_redis_limit(
                identifier, endpoint, requests_limit, window_seconds
            )
        else:
            allowed, remaining, reset_time = self._check_memory_limit(
                identifier, endpoint, requests_limit, window_seconds
            )

        if not allowed:
            self.analytics["rate_limited"] += 1

        analytics = {
            "endpoint": endpoint,
            "tier": user_tier,
            "limit": requests_limit,
            "window": window_seconds,
        }

        return allowed, remaining, reset_time, analytics

    async def _check_redis_limit(
        self, identifier: str, endpoint: str, limit: int, window: int
    ) -> tuple[bool, int, int]:
        """Redis-based sliding window rate limiting"""
        key = self._get_limit_key(identifier, endpoint)
        current_time = time.time()
        window_start = current_time - window

        try:
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(current_time): current_time})
            pipe.expire(key, window)

            results = await pipe.execute()
            current_count = results[1]

            if current_count >= limit:
                oldest = await self.redis.zrange(key, 0, 0, withscores=True)
                reset_time = int((oldest[0][1] if oldest else current_time) + window)
                return False, 0, reset_time

            remaining = limit - current_count - 1
            return True, remaining, int(current_time + window)

        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            return True, limit, int(time.time() + window)

    def _check_memory_limit(
        self, identifier: str, endpoint: str, limit: int, window: int
    ) -> tuple[bool, int, int]:
        """In-memory rate limiting fallback"""
        if not hasattr(self, "_memory_limits"):
            self._memory_limits: dict[str, list] = {}

        key = f"{identifier}:{endpoint}"
        current_time = time.time()
        window_start = current_time - window

        if key not in self._memory_limits:
            self._memory_limits[key] = []

        self._memory_limits[key] = [
            t for t in self._memory_limits[key] if t > window_start
        ]

        if len(self._memory_limits[key]) >= limit:
            reset_time = int(self._memory_limits[key][0] + window)
            return False, 0, reset_time

        self._memory_limits[key].append(current_time)
        remaining = limit - len(self._memory_limits[key])
        return True, remaining, int(current_time + window)

    def _get_limit_key(self, identifier: str, endpoint: str) -> str:
        """Generate Redis key"""
        key_data = f"{identifier}:{endpoint}"
        return f"rate_limit:{hashlib.sha256(key_data.encode()).hexdigest()[:16]}"

    def get_analytics(self) -> dict[str, Any]:
        """Get rate limiting analytics"""
        total = self.analytics["total_requests"]
        return {
            **self.analytics,
            "rate_limit_percentage": (
                self.analytics["rate_limited"] / total * 100 if total > 0 else 0
            ),
        }


class EnhancedRateLimitMiddleware(BaseHTTPMiddleware):
    """Enhanced rate limiting middleware"""

    def __init__(self, app, redis_client: redis.Redis | None = None):
        super().__init__(app)
        self.rate_limiter = EnhancedRateLimiter(redis_client)
        self.skip_paths: set[str] = {
            "/health",
            "/healthz",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/redoc",
        }

    def _get_identifier(self, request: Request) -> str:
        """Get rate limit identifier"""
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        return f"ip:{request.client.host if request.client else 'unknown'}"

    def _get_user_tier(self, request: Request) -> str:
        """Get user tier"""
        user = getattr(request.state, "user", None)
        if not user:
            return "anonymous"

        subscription = getattr(user, "subscription", None)
        if subscription:
            tier = subscription.tier
            if tier in ["premium", "enterprise"]:
                return tier
        return "authenticated"

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        # Skip rate limiting for certain paths
        if request.url.path in self.skip_paths:
            return await call_next(request)

        identifier = self._get_identifier(request)
        endpoint = request.url.path
        user_tier = self._get_user_tier(request)

        (
            allowed,
            remaining,
            reset_time,
            analytics,
        ) = await self.rate_limiter.check_rate_limit(identifier, endpoint, user_tier)

        if not allowed:
            limit_config = self.rate_limiter.endpoint_limits.get(
                endpoint
            ) or self.rate_limiter.tier_limits.get(user_tier)

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests to {endpoint}",
                    "retry_after": reset_time,
                    "limit": limit_config["requests"],
                    "window": limit_config["window"],
                },
                headers={
                    "X-RateLimit-Limit": str(limit_config["requests"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(reset_time),
                },
            )

        response = await call_next(request)

        # Add rate limit headers
        limit_config = self.rate_limiter.endpoint_limits.get(
            endpoint
        ) or self.rate_limiter.tier_limits.get(user_tier)

        response.headers["X-RateLimit-Limit"] = str(limit_config["requests"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)

        return response
