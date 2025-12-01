"""
Rate Limiting Middleware using Distributed Rate Limiter
Applies per-user and per-IP rate limits to all API requests
"""
from fastapi import Request, HTTPException, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for distributed rate limiting
    
    Features:
    - Different limits for authenticated vs anonymous users
    - Per-endpoint rate limiting
    - Proper HTTP 429 responses with Retry-After headers
    """
    
    def __init__(self, app, rate_limiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter
        
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
        }
        
        # Exempt paths (no rate limiting)
        self.exempt_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting"""
        
        # Skip rate limiting for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        # Skip if rate limiter not available
        if not self.rate_limiter:
            return await call_next(request)
        
        # Determine user identity
        user_id = self._get_user_id(request)
        client_ip = request.client.host if request.client else "unknown"
        
        # Create rate limit key
        if user_id:
            key = f"user:{user_id}"
            config = self.default_limits["authenticated"]
        else:
            key = f"ip:{client_ip}"
            config = self.default_limits["anonymous"]
        
        # Check for endpoint-specific limits
        for path, endpoint_config in self.endpoint_limits.items():
            if request.url.path.startswith(path):
                config = endpoint_config
                key = f"{key}:{path}"
                break
        
        # Check rate limit
        allowed, info = await self.rate_limiter.check_rate_limit(
            key,
            config["limit"],
            config["window"]
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
                    "reset_iso": info["reset_iso"]
                },
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(info["reset"]),
                    "Retry-After": str(max(1, retry_after)),
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit info to response headers
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])
        
        if info.get("fallback"):
            response.headers["X-RateLimit-Mode"] = "local"
        
        return response
    
    def _get_user_id(self, request: Request) -> str | None:
        """Extract user ID from request (JWT, session, etc.)"""
        # Check for user in request state (set by auth middleware)
        if hasattr(request.state, "user") and hasattr(request.state.user, "id"):
            return str(request.state.user.id)
        
        # Check for user_id in query params (for WebSocket, etc.)
        if "user_id" in request.query_params:
            return request.query_params["user_id"]
        
        # Could also check JWT token here
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # Extract user ID from JWT token
            # This would require JWT parsing logic
            pass
        
        return None


# Import datetime for timestamp calculations
from datetime import datetime
