"""
Enhanced Security Headers Middleware
Adds comprehensive security headers for production
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
import os

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Enhanced security headers middleware
    Adds comprehensive security headers including CSP, HSTS, etc.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.is_production = os.getenv("NODE_ENV") == "production" or os.getenv("ENVIRONMENT") == "production"

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Allow inline scripts for development
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https: blob:",
            "connect-src 'self' ws://localhost:8000 wss://localhost:8000 https://api.sentry.io",
            "frame-src 'none'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
        ]

        if self.is_production:
            csp_directives.append("upgrade-insecure-requests")
        else:
            # More permissive CSP for development
            csp_directives = [
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
                "font-src 'self' https://fonts.gstatic.com",
                "img-src 'self' data: https: blob:",
                "connect-src 'self' ws://localhost:8000 wss://localhost:8000 http://localhost:8000 https://api.sentry.io",
                "frame-src 'none'",
                "object-src 'none'",
                "base-uri 'self'",
            ]

        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Strict Transport Security (HSTS) - Only in production with HTTPS
        if self.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options
        response.headers["X-Frame-Options"] = "DENY"

        # X-XSS-Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "speaker=()"
        )

        # Cross-Origin Embedder Policy (relaxed for development)
        if self.is_production:
            response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
            response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
            response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        # Remove server header (security through obscurity)
        response.headers.pop("server", None)

        return response

