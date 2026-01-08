"""
Enhanced Security Headers Middleware
Adds comprehensive security headers for production
Consolidated from security.py and security_headers.py
"""

import logging
import os
import secrets

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Enhanced security headers middleware
    Adds comprehensive security headers including CSP, HSTS, etc.

    Production CSP uses nonces to allow specific inline scripts/styles
    while maintaining security. Development mode uses permissive CSP.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.is_production = (
            os.getenv("NODE_ENV") == "production"
            or os.getenv("ENVIRONMENT") == "production"
        )
        # CSP reporting endpoint (set via environment variable)
        # Note: Endpoint is at /api/security/csp-report (mounted in security_audit router)
        self.csp_report_uri = os.getenv("CSP_REPORT_URI", "/api/security/csp-report")

    def _generate_nonce(self) -> str:
        """Generate a cryptographically secure nonce for CSP."""
        return secrets.token_urlsafe(16)

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Generate nonce for this request (used in production)
        nonce = self._generate_nonce()

        # Store nonce in request state for use in templates/response
        request.state.csp_nonce = nonce

        # Content Security Policy
        if self.is_production:
            # Production: Strict CSP with nonces (no unsafe-inline/unsafe-eval)
            # Note: Vite builds externalize most scripts, but React hydration may need nonces
            # Frontend should use: <script nonce={nonce}> for any required inline scripts
            csp_directives = [
                "default-src 'self'",
                f"script-src 'self' 'nonce-{nonce}' https://api.sentry.io",  # Nonce-based, no unsafe-inline/eval
                f"style-src 'self' 'nonce-{nonce}' https://fonts.googleapis.com",  # Nonce-based styles
                "font-src 'self' https://fonts.gstatic.com",
                "img-src 'self' data: https: blob:",
                "connect-src 'self' https://api.sentry.io",  # Production: no localhost
                "frame-src 'none'",
                "object-src 'none'",
                "base-uri 'self'",
                "form-action 'self'",
                "frame-ancestors 'none'",
                "upgrade-insecure-requests",
            ]

            # Add CSP reporting if enabled
            if os.getenv("ENABLE_CSP_REPORTING", "true").lower() == "true":
                csp_directives.append(f"report-uri {self.csp_report_uri}")
                # Also use report-to for newer browsers (requires Report-To header)
                # csp_directives.append("report-to csp-endpoint")
        else:
            # Development: More permissive CSP for development convenience
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

        # Add nonce to response headers for frontend access (if needed)
        # Frontend can read this via meta tag or API endpoint
        if self.is_production:
            response.headers["X-CSP-Nonce"] = nonce

        # Strict Transport Security (HSTS) - Only in production with HTTPS
        if self.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

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
        else:
            # More permissive for development
            response.headers["Cross-Origin-Embedder-Policy"] = "unsafe-none"
            response.headers["Cross-Origin-Opener-Policy"] = "unsafe-none"
            response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"

        # X-Permitted-Cross-Domain-Policies
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        # Remove server header (security through obscurity)
        # Use del instead of pop since MutableHeaders doesn't have pop method
        if "server" in response.headers:
            del response.headers["server"]

        return response
