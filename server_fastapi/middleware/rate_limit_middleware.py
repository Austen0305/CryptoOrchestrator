"""
Rate Limiting Middleware using Distributed Rate Limiter
Applies per-user and per-IP rate limits to all API requests
"""

import logging
from collections.abc import Callable

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for distributed rate limiting

    Features:
    - Different limits for authenticated vs anonymous users
    - Per-endpoint rate limiting
    - Proper HTTP 429 responses with Retry-After headers
    """

    def __init__(self, app, rate_limiter=None):
        super().__init__(app)
        self.rate_limiter = (
            rate_limiter  # Can be None initially, will be set from app.state
        )

        # Rate limit configurations
        self.default_limits = {
            "authenticated": {"limit": 1000, "window": 3600},  # 1000/hour
            "anonymous": {"limit": 100, "window": 3600},  # 100/hour
        }

        # Endpoint-specific limits (more restrictive)
        self.endpoint_limits = {
            "/api/integrations/predict": {"limit": 20, "window": 60},  # 20/min
            "/api/backtesting/run": {"limit": 10, "window": 60},  # 10/min
            "/api/analytics/advanced": {"limit": 50, "window": 60},  # 50/min
            # Wallet operation limits
            "/api/wallets": {
                "limit": 100,
                "window": 3600,
            },  # 100/hour for wallet operations
            "/api/wallets/refresh-balances": {
                "limit": 20,
                "window": 3600,
            },  # 20/hour for balance refresh
            "/api/wallets/withdraw": {
                "limit": 10,
                "window": 3600,
            },  # 10/hour for withdrawals (security)
            # DEX operation limits
            "/api/dex/quote": {"limit": 60, "window": 60},  # 60/minute for quotes
            "/api/dex/swap": {
                "limit": 20,
                "window": 3600,
            },  # 20/hour for swaps (security)
            "/api/dex/trades": {
                "limit": 100,
                "window": 60,
            },  # 100/minute for status checks
        }

        # Tier-based rate limit multipliers
        self.tier_multipliers = {
            "free": 1.0,  # Base limits
            "basic": 1.5,  # 50% more
            "pro": 2.0,  # 2x limits
            "enterprise": 3.0,  # 3x limits
            "mega": 5.0,  # 5x limits
        }

        # Exempt paths (no rate limiting)
        self.exempt_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting"""

        # Skip rate limiting for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)

        # Skip if rate limiter not available
        if not self.rate_limiter:
            return await call_next(request)

        # Check if user is admin (bypass rate limits)
        if self._is_admin(request):
            response = await call_next(request)
            # Still add headers for admin
            response.headers["X-RateLimit-Limit"] = "unlimited"
            response.headers["X-RateLimit-Remaining"] = "unlimited"
            response.headers["X-RateLimit-Reset"] = str(
                int(datetime.now().timestamp()) + 3600
            )
            response.headers["X-RateLimit-Admin"] = "true"
            return response

        # Determine user identity
        user_id = self._get_user_id(request)
        client_ip = request.client.host if request.client else "unknown"
        user_tier = self._get_user_tier(request)

        # Create rate limit key
        if user_id:
            key = f"user:{user_id}"
            config = self.default_limits["authenticated"].copy()
        else:
            key = f"ip:{client_ip}"
            config = self.default_limits["anonymous"].copy()

        # Check for endpoint-specific limits
        endpoint_config = None
        for path, ep_config in self.endpoint_limits.items():
            if request.url.path.startswith(path):
                endpoint_config = ep_config.copy()
                key = f"{key}:{path}"
                break

        # Use endpoint config if found, otherwise use default
        if endpoint_config:
            config = endpoint_config
        else:
            # Apply tier-based multiplier to default limits
            multiplier = self.tier_multipliers.get(user_tier, 1.0)
            config["limit"] = int(config["limit"] * multiplier)

        # Check rate limit
        allowed, info = await rate_limiter.check_rate_limit(
            key, config["limit"], config["window"]
        )

        # Add rate limit headers to response
        if not allowed:
            retry_after = info["reset"] - int(datetime.now().timestamp())

            logger.warning(
                f"Rate limit exceeded for {key}: "
                f"{info['current']}/{info['limit']} requests"
            )

            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please try again in {retry_after} seconds.",
                    "limit": info["limit"],
                    "remaining": 0,
                    "reset": info["reset"],
                    "reset_iso": info["reset_iso"],
                },
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(info["reset"]),
                    "Retry-After": str(max(1, retry_after)),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit info to response headers (always add, even on success)
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])
        response.headers["X-RateLimit-Tier"] = user_tier

        if info.get("fallback"):
            response.headers["X-RateLimit-Mode"] = "local"

        # Log rate limit metrics for monitoring
        try:
            # Track rate limit usage (for monitoring dashboard)
            # In production, this would be sent to metrics service
            logger.debug(
                f"Rate limit check: {key} - {info['current']}/{info['limit']} (tier: {user_tier})",
                extra={
                    "rate_limit_key": key,
                    "current": info["current"],
                    "limit": info["limit"],
                    "remaining": info["remaining"],
                    "tier": user_tier,
                    "endpoint": request.url.path,
                },
            )
        except Exception:
            pass  # Don't fail request if metrics logging fails

        return response

    def _get_user_id(self, request: Request) -> str | None:
        """Extract user ID from request (JWT, session, etc.)"""
        # Check for user in request state (set by auth middleware)
        if hasattr(request.state, "user"):
            user = request.state.user
            if isinstance(user, dict):
                return str(user.get("id") or user.get("user_id") or user.get("sub"))
            elif hasattr(user, "id"):
                return str(user.id)

        # Check for user_id in query params (for WebSocket, etc.)
        if "user_id" in request.query_params:
            return request.query_params["user_id"]

        # Could also check JWT token here
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # Extract user ID from JWT token
            # This would require JWT parsing logic
            try:
                import jwt

                token = auth_header.replace("Bearer ", "")
                # Note: This requires JWT_SECRET - in production, use proper JWT validation
                # For now, just try to decode (without verification for rate limiting purposes)
                # In production, you'd want to verify the token properly
                payload = jwt.decode(token, options={"verify_signature": False})
                user_id = (
                    payload.get("sub") or payload.get("user_id") or payload.get("id")
                )
                if user_id:
                    return str(user_id)
            except Exception:
                pass

        return None

    def _get_user_tier(self, request: Request) -> str:
        """Get user subscription tier for tier-based rate limiting"""
        # Check for user tier in request state
        if hasattr(request.state, "user"):
            user = request.state.user
            if isinstance(user, dict):
                tier = (
                    user.get("tier")
                    or user.get("subscription_tier")
                    or user.get("user_tier")
                )
                if tier:
                    return str(tier).lower()

        # Default to free tier
        return "free"

    def _is_admin(self, request: Request) -> bool:
        """Check if user is admin (bypass rate limits)"""
        if hasattr(request.state, "user"):
            user = request.state.user
            if isinstance(user, dict):
                return user.get("is_admin", False) or user.get("role") == "admin"
            elif hasattr(user, "is_admin"):
                return user.is_admin
        return False


# Import datetime for timestamp calculations
from datetime import datetime
