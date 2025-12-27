"""
Response Standardizer Middleware
Ensures all API responses follow a consistent format
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp
import logging
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)


class ResponseStandardizerMiddleware(BaseHTTPMiddleware):
    """Middleware to standardize API responses"""

    # Paths that should not be standardized (binary, streaming, etc.)
    EXCLUDE_PATHS = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/metrics",
        "/healthz",
        "/health/live",
    ]

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # Skip standardization for excluded paths
        if any(request.url.path.startswith(path) for path in self.EXCLUDE_PATHS):
            return await call_next(request)

        # Process request
        response = await call_next(request)

        # Only standardize JSON responses
        if isinstance(response, JSONResponse):
            try:
                # Get response body
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk

                # Parse JSON
                try:
                    data = json.loads(body.decode())
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Not JSON, return as-is
                    return Response(
                        content=body,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        media_type=response.media_type,
                    )

                # Standardize response format
                standardized = self._standardize_response(
                    data, response.status_code, request
                )

                # Return standardized response
                return JSONResponse(
                    content=standardized,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                )
            except Exception as e:
                logger.warning(f"Error standardizing response: {e}")
                # Return original response on error
                return response

        return response

    def _standardize_response(
        self, data: Any, status_code: int, request: Request
    ) -> Dict[str, Any]:
        """Standardize response format"""

        # If already in standard format, return as-is
        if isinstance(data, dict) and ("success" in data or "error" in data):
            return data

        # Success responses (2xx)
        if 200 <= status_code < 300:
            return {
                "success": True,
                "data": data,
                "status_code": status_code,
                "request_id": getattr(request.state, "request_id", None),
            }

        # Error responses (4xx, 5xx)
        return {
            "success": False,
            "error": data if isinstance(data, dict) else {"message": str(data)},
            "status_code": status_code,
            "request_id": getattr(request.state, "request_id", None),
        }
