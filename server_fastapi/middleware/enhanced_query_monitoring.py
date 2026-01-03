"""
Enhanced Query Performance Monitoring Middleware (2026)
Comprehensive database query monitoring with structured logging and metrics
"""

import logging
import time
from typing import Callable, Dict, Any, Optional
from datetime import datetime
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import event
from sqlalchemy.engine import Engine

from ..services.monitoring.performance_profiler import get_performance_profiler

logger = logging.getLogger(__name__)

# 2026 Best Practice: Configurable thresholds
SLOW_QUERY_THRESHOLD_MS = 100  # 100ms threshold for slow queries
VERY_SLOW_QUERY_THRESHOLD_MS = 1000  # 1 second for very slow queries
N_PLUS_ONE_THRESHOLD = 10  # Alert if more than 10 queries in a single request


class EnhancedQueryMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Enhanced query monitoring middleware (2026)
    
    Features:
    - Tracks all database queries per request
    - Detects N+1 query problems
    - Logs slow queries with full context
    - Tracks query patterns and statistics
    - Integrates with performance profiler
    """

    def __init__(self, app, slow_query_threshold_ms: int = SLOW_QUERY_THRESHOLD_MS):
        super().__init__(app)
        self.profiler = get_performance_profiler()
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.request_query_counts: Dict[str, int] = {}
        self._setup_query_listeners()

    def _setup_query_listeners(self):
        """Setup SQLAlchemy event listeners for comprehensive query monitoring"""
        try:
            from ..database import engine

            if engine:
                # Get sync engine for event listeners
                sync_engine = engine
                if hasattr(engine, "sync_engine"):
                    sync_engine = engine.sync_engine
                elif hasattr(engine, "_sync_engine"):
                    sync_engine = engine._sync_engine

                # Setup query profiling
                from ..services.monitoring.performance_profiler import (
                    setup_query_profiling,
                )

                setup_query_profiling(sync_engine)
                logger.info("Enhanced query monitoring listeners configured")
        except Exception as e:
            logger.warning(f"Could not setup enhanced query listeners: {e}")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Monitor request and track all database queries

        Tracks:
        - Total query count per request
        - Query execution times
        - N+1 query detection
        - Slow query logging
        """
        request_id = getattr(request.state, "request_id", None) or "unknown"
        query_count = 0
        query_times: List[float] = []
        start_time = time.time()

        # Track queries for this request
        def track_query(query_time_ms: float) -> None:
            nonlocal query_count
            query_count += 1
            query_times.append(query_time_ms)

        # Store tracking function in request state
        request.state.track_query = track_query

        try:
            response = await call_next(request)
            
            # Analyze query patterns after request completes
            total_request_time_ms = (time.time() - start_time) * 1000
            
            # Detect N+1 queries
            if query_count > N_PLUS_ONE_THRESHOLD:
                logger.warning(
                    f"Potential N+1 query problem detected: {query_count} queries in single request",
                    extra={
                        "request_id": request_id,
                        "path": request.url.path,
                        "method": request.method,
                        "query_count": query_count,
                        "total_time_ms": total_request_time_ms,
                        "avg_query_time_ms": sum(query_times) / len(query_times) if query_times else 0,
                    },
                )

            # Log request summary if queries were slow
            if query_times:
                max_query_time = max(query_times)
                avg_query_time = sum(query_times) / len(query_times)

                if max_query_time > self.slow_query_threshold_ms:
                    logger.info(
                        f"Request completed with {query_count} queries",
                        extra={
                            "request_id": request_id,
                            "path": request.url.path,
                            "method": request.method,
                            "query_count": query_count,
                            "max_query_time_ms": max_query_time,
                            "avg_query_time_ms": avg_query_time,
                            "total_request_time_ms": total_request_time_ms,
                            "status_code": response.status_code,
                        },
                    )

            return response
        except Exception as e:
            logger.error(
                f"Request failed after {query_count} queries: {e}",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "query_count": query_count,
                },
                exc_info=True,
            )
            raise


def setup_enhanced_query_monitoring(engine: Engine) -> None:
    """
    Setup enhanced SQLAlchemy query monitoring (2026)

    Monitors:
    - Query execution time
    - Query patterns
    - Slow queries
    - Query statistics
    """
    profiler = get_performance_profiler()

    # Get sync engine
    sync_engine = engine
    if hasattr(engine, "sync_engine"):
        sync_engine = engine.sync_engine
    elif hasattr(engine, "_sync_engine"):
        sync_engine = engine._sync_engine

    query_start_times: Dict[int, float] = {}  # Track query start times

    @event.listens_for(sync_engine, "before_cursor_execute")
    def before_cursor_execute(
        conn, cursor, statement, parameters, context, executemany
    ):
        """Record query start time"""
        query_id = id(cursor)
        query_start_times[query_id] = time.time()

    @event.listens_for(sync_engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Record query execution time and log slow queries"""
        query_id = id(cursor)
        start_time = query_start_times.pop(query_id, None)
        
        if start_time is None:
            return

        duration_ms = (time.time() - start_time) * 1000

        # Record in profiler
        profiler.record_query(
            query=statement,
            duration_ms=duration_ms,
            params=parameters if parameters else None,
        )

        # Enhanced logging for very slow queries
        if duration_ms > VERY_SLOW_QUERY_THRESHOLD_MS:
            logger.error(
                f"VERY SLOW QUERY: {duration_ms:.2f}ms",
                extra={
                    "query": statement[:500],  # First 500 chars
                    "duration_ms": duration_ms,
                    "parameters": str(parameters)[:200] if parameters else None,
                    "threshold_ms": VERY_SLOW_QUERY_THRESHOLD_MS,
                },
            )
        elif duration_ms > SLOW_QUERY_THRESHOLD_MS:
            logger.warning(
                f"Slow query: {duration_ms:.2f}ms",
                extra={
                    "query": statement[:300],  # First 300 chars
                    "duration_ms": duration_ms,
                    "threshold_ms": SLOW_QUERY_THRESHOLD_MS,
                },
            )

        # Track in request state if available
        if hasattr(conn, "info") and "request_state" in conn.info:
            request_state = conn.info["request_state"]
            if hasattr(request_state, "track_query"):
                request_state.track_query(duration_ms)

    logger.info("Enhanced query monitoring setup complete")
