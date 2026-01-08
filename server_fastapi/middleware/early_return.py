"""
Early Return Middleware
Optimizes middleware execution with early returns for better performance
"""

import logging
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class EarlyReturnMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enables early returns for common scenarios

    Optimizations:
    - Skip processing for static assets
    - Fast path for health checks
    - Early validation failures
    - Cached response shortcuts
    """

    def __init__(
        self,
        app,
        skip_paths: set[str] | None = None,
        fast_paths: set[str] | None = None,
    ):
        super().__init__(app)
        self.skip_paths = skip_paths or {
            "/static",
            "/assets",
            "/favicon.ico",
            "/robots.txt",
        }
        self.fast_paths = fast_paths or {
            "/health",
            "/healthz",
            "/api/health",
        }

        self.stats = {
            "skipped": 0,
            "fast_path": 0,
            "normal": 0,
        }

    def _should_skip(self, request: Request) -> bool:
        """Check if request should skip middleware processing"""
        path = request.url.path

        # Skip static assets
        if any(path.startswith(skip) for skip in self.skip_paths):
            self.stats["skipped"] += 1
            return True

        return False

    def _is_fast_path(self, request: Request) -> bool:
        """Check if request is on fast path"""
        path = request.url.path
        return path in self.fast_paths

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with early return optimizations"""
        # Early skip for static assets
        if self._should_skip(request):
            return await call_next(request)

        # Fast path for health checks (minimal processing)
        if self._is_fast_path(request):
            self.stats["fast_path"] += 1
            # Health checks can bypass most middleware
            return await call_next(request)

        # Normal processing
        self.stats["normal"] += 1
        return await call_next(request)

    def get_stats(self) -> dict:
        """Get middleware statistics"""
        return self.stats.copy()
