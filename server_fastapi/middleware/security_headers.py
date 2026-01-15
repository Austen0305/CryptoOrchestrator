import secrets
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Applies strict security headers including CSP and Permissions-Policy
    aligned with 2026 standards.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate NONCE for this request (if needed for templating)
        # In a pure API, this is less critical but good for Swagger UI
        nonce = secrets.token_hex(16)
        request.state.csp_nonce = nonce

        response = await call_next(request)

        # 1. Content-Security-Policy (CSP)
        # Prevents XSS by restricting source of scripts.
        # 'strict-dynamic' is 2026 standard for modern apps.
        csp_policy = (
            f"default-src 'self'; "
            f"script-src 'self' 'nonce-{nonce}' 'strict-dynamic'; "
            f"style-src 'self' 'nonce-{nonce}'; "
            f"img-src 'self' data: https:; "
            f"font-src 'self' data: https:; "
            f"object-src 'none'; "
            f"base-uri 'none'; "
            f"frame-ancestors 'none'; "
            f"form-action 'self';"
        )
        response.headers["Content-Security-Policy"] = csp_policy

        # 2. Permissions-Policy
        # Blocks sensitive APIs by default.
        permissions_policy = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )
        response.headers["Permissions-Policy"] = permissions_policy

        # 3. Strict-Transport-Security (HSTS)
        # Enforce HTTPS for 1 year
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # 4. X-Content-Type-Options
        # Prevents MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 5. Referrer-Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response
