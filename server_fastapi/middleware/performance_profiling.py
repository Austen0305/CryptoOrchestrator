"""
Performance Profiling Middleware
Records endpoint execution times and identifies slow endpoints.
"""

import logging
import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..services.monitoring.performance_profiler import get_performance_profiler

logger = logging.getLogger(__name__)


class PerformanceProfilingMiddleware(BaseHTTPMiddleware):
    """Middleware for performance profiling"""

    def __init__(self, app):
        super().__init__(app)
        self.profiler = get_performance_profiler()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Profile request execution time"""
        start_time = time.time()

        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Record endpoint performance
            self.profiler.record_endpoint(
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                status_code=response.status_code,
            )

            # Add performance header
            response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

            return response

        except Exception:
            # Still record timing even on error
            duration_ms = (time.time() - start_time) * 1000
            self.profiler.record_endpoint(
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                status_code=500,
            )
            raise
