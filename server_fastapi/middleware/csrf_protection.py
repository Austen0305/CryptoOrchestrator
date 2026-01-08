"""
CSRF Protection Middleware
Implements CSRF token validation for state-changing operations (POST, PUT, DELETE, PATCH)
"""

import hashlib
import hmac
import logging
import secrets

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# CSRF token secret (should be in environment variable)
CSRF_SECRET = "csrf-secret-key-change-in-production"  # Should be from env


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection middleware

    Features:
    - Generates CSRF tokens
    - Validates CSRF tokens for state-changing operations
    - Exempts safe methods (GET, HEAD, OPTIONS)
    - Supports token in header (X-CSRF-Token) or cookie (csrf-token)
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.exempt_methods = {"GET", "HEAD", "OPTIONS"}
        self.exempt_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]

    async def dispatch(self, request: Request, call_next):
        """Process request with CSRF protection"""

        # Skip CSRF check for exempt methods
        if request.method in self.exempt_methods:
            return await call_next(request)

        # Skip CSRF check for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)

        # Get CSRF token from header or cookie
        csrf_token = request.headers.get("X-CSRF-Token") or request.cookies.get(
            "csrf-token"
        )

        # Get expected CSRF token from session/cookie
        expected_token = request.cookies.get("csrf-token")

        if not csrf_token:
            logger.warning(
                f"CSRF token missing for {request.method} {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "ip": request.client.host if request.client else None,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token missing. Please include X-CSRF-Token header or csrf-token cookie.",
            )

        # Validate CSRF token
        if not self._validate_csrf_token(csrf_token, expected_token):
            logger.warning(
                f"CSRF token validation failed for {request.method} {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "ip": request.client.host if request.client else None,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid CSRF token. Please refresh the page and try again.",
            )

        # Process request
        response = await call_next(request)

        # Set CSRF token in cookie if not present (for subsequent requests)
        if "csrf-token" not in request.cookies:
            token = self._generate_csrf_token()
            response.set_cookie(
                "csrf-token",
                token,
                httponly=False,  # Must be accessible to JavaScript
                samesite="strict",
                secure=True,  # Only over HTTPS in production
            )
            # Also set in header for convenience
            response.headers["X-CSRF-Token"] = token

        return response

    def _generate_csrf_token(self) -> str:
        """Generate a new CSRF token"""
        token = secrets.token_urlsafe(32)
        # Sign token with secret
        signature = hmac.new(
            CSRF_SECRET.encode(), token.encode(), hashlib.sha256
        ).hexdigest()
        return f"{token}.{signature}"

    def _validate_csrf_token(
        self, provided_token: str, expected_token: str | None
    ) -> bool:
        """Validate CSRF token"""
        if not provided_token or not expected_token:
            return False

        # Tokens should match exactly
        if provided_token == expected_token:
            # Verify signature
            if "." in provided_token:
                token, signature = provided_token.rsplit(".", 1)
                expected_signature = hmac.new(
                    CSRF_SECRET.encode(), token.encode(), hashlib.sha256
                ).hexdigest()
                return hmac.compare_digest(signature, expected_signature)
            return True

        return False


def get_csrf_token(request: Request) -> str:
    """Helper function to get CSRF token from request"""
    return request.cookies.get("csrf-token") or request.headers.get("X-CSRF-Token", "")
