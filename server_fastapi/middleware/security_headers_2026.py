"""
Enhanced Security Headers Middleware (2026 Best Practices)
Implements comprehensive security headers based on 2026 security standards
"""

import logging
import os
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware2026(BaseHTTPMiddleware):
    """
    Enhanced security headers middleware (2026 best practices)

    Implements:
    - Content Security Policy (CSP) with nonce support
    - Strict Transport Security (HSTS)
    - X-Frame-Options
    - X-Content-Type-Options
    - Referrer-Policy
    - Permissions-Policy
    - Cross-Origin policies
    - X-Permitted-Cross-Domain-Policies
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.is_production = os.getenv("NODE_ENV") == "production"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add comprehensive security headers to response"""
        response: Response = await call_next(request)

        # Generate nonce for CSP (2026 best practice)
        import secrets

        nonce = secrets.token_urlsafe(16)

        # Content Security Policy (CSP) - 2026 best practice
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'nonce-{nonce}' https://api.sentry.io",
            "style-src 'self' 'nonce-{nonce}' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https: blob:",
            "connect-src 'self' https://api.sentry.io wss: ws:",
            "frame-src 'none'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
            "upgrade-insecure-requests",
            "report-uri /api/security/csp-report",
        ]

        response.headers["Content-Security-Policy"] = "; ".join(
            directive.format(nonce=nonce) for directive in csp_directives
        )
        response.headers["X-CSP-Nonce"] = nonce

        # Strict Transport Security (HSTS) - 2026 best practice
        if self.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # X-Frame-Options - Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # X-Content-Type-Options - Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection (legacy, but still recommended)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy - Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy (formerly Feature-Policy) - 2026 best practice
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

        # Cross-Origin policies - 2026 best practice
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        # X-Permitted-Cross-Domain-Policies
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        return response
