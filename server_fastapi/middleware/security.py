"""Security middleware for the FastAPI application."""
from typing import Callable, Optional

from fastapi import FastAPI, Request, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

def setup_security_middleware(app: FastAPI) -> None:
    """Configure security middleware for the FastAPI application."""
    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline';"
        )
        return response

    # IP whitelist middleware
    @app.middleware("http")
    async def ip_whitelist(request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else None
        if _is_sensitive_route(request.url.path) and not _is_whitelisted_ip(client_ip):
            return Response(status_code=403, content="Access denied")
        return await call_next(request)

def _is_sensitive_route(path: str) -> bool:
    """Check if the route is sensitive and requires IP whitelisting."""
    sensitive_routes = {
        "/api/v1/admin",
        "/api/v1/settings",
        "/api/v1/keys",
    }
    return any(path.startswith(route) for route in sensitive_routes)

def _is_whitelisted_ip(ip: Optional[str]) -> bool:
    """Check if the IP is in the whitelist."""
    # TODO: Implement IP whitelist configuration
    # This should be loaded from configuration and possibly cached
    whitelist = {"127.0.0.1", "::1"}  # Example whitelist
    return ip in whitelist if ip else False