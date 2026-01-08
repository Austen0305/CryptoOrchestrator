"""
API Key Authentication Middleware
Validates API keys and enforces rate limiting
"""

import logging

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from ..database import get_db_context
from ..services.api_key_service import APIKeyService

logger = logging.getLogger(__name__)


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication"""

    async def dispatch(self, request: Request, call_next):
        # Skip API key auth for certain paths
        skip_paths = [
            "/api/auth",
            "/api/health",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]

        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)

        # Check for API key in header
        api_key = request.headers.get("X-API-Key") or request.headers.get(
            "Authorization"
        )

        if api_key:
            # Remove "Bearer " prefix if present
            if api_key.startswith("Bearer "):
                api_key = api_key[7:]

            # Validate API key
            async with get_db_context() as db:
                service = APIKeyService(db)
                api_key_obj = await service.validate_api_key(api_key)

                if not api_key_obj:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid API key",
                    )

                # Check rate limit
                allowed, remaining = await service.check_rate_limit(api_key_obj.id)
                if not allowed:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded",
                        headers={"X-RateLimit-Remaining": "0"},
                    )

                # Add API key info to request state
                request.state.api_key = api_key_obj
                request.state.api_key_id = api_key_obj.id
                request.state.user_id = api_key_obj.user_id

                # Process request
                response = await call_next(request)

                # Log usage after response
                await service.log_api_usage(
                    api_key_id=api_key_obj.id,
                    endpoint=request.url.path,
                    method=request.method,
                    status_code=response.status_code,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                )

                # Add rate limit headers
                response.headers["X-RateLimit-Limit"] = str(api_key_obj.rate_limit)
                response.headers["X-RateLimit-Remaining"] = str(
                    remaining - 1 if remaining else 0
                )

                return response

        # No API key provided - continue with normal auth
        return await call_next(request)
