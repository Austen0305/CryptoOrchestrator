"""
Database Query Performance Monitoring Middleware
Logs slow queries (> 100ms) and tracks query performance.
"""

import logging
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import event
from sqlalchemy.engine import Engine

from ..services.monitoring.performance_profiler import get_performance_profiler

logger = logging.getLogger(__name__)


class QueryMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring database query performance"""

    def __init__(self, app):
        super().__init__(app)
        self.profiler = get_performance_profiler()
        self._setup_query_listeners()

    def _setup_query_listeners(self):
        """Setup SQLAlchemy event listeners for query monitoring"""
        try:
            from ..database import engine

            if engine:
                # Setup query profiling on engine
                from ..services.monitoring.performance_profiler import (
                    setup_query_profiling,
                )

                setup_query_profiling(engine.sync_engine)
        except Exception as e:
            logger.warning(f"Could not setup query listeners: {e}")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Monitor request and query performance"""
        response = await call_next(request)
        return response


# SQLAlchemy event listener setup
def setup_query_monitoring(engine: Engine) -> None:
    """Setup SQLAlchemy query monitoring"""
    profiler = get_performance_profiler()

    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(
        conn, cursor, statement, parameters, context, executemany
    ):
        conn.info.setdefault("query_start_time", []).append(time.time())

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total = time.time() - conn.info["query_start_time"].pop(-1)
        duration_ms = total * 1000

        # Record query performance
        profiler.record_query(
            query=statement, duration_ms=duration_ms, params=parameters
        )
