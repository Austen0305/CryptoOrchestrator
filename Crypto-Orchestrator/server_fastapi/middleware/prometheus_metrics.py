"""
Prometheus Metrics Exporter
Exports application metrics in Prometheus format
"""

import logging
import time
from typing import Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
from collections import defaultdict, Counter
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from prometheus_client import (
        Counter as PromCounter,
        Histogram,
        Gauge,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client not installed, metrics disabled")


class PrometheusMetrics:
    """Prometheus metrics collector"""

    def __init__(self):
        if not PROMETHEUS_AVAILABLE:
            self.enabled = False
            return

        self.enabled = True

        # HTTP metrics
        self.http_requests_total = PromCounter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"],
        )

        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
        )

        self.http_request_size_bytes = Histogram(
            "http_request_size_bytes",
            "HTTP request size in bytes",
            ["method", "endpoint"],
            buckets=(100, 1000, 10000, 100000, 1000000),
        )

        self.http_response_size_bytes = Histogram(
            "http_response_size_bytes",
            "HTTP response size in bytes",
            ["method", "endpoint"],
            buckets=(100, 1000, 10000, 100000, 1000000),
        )

        # Database metrics
        self.db_queries_total = PromCounter(
            "db_queries_total",
            "Total database queries",
            ["operation", "status"],
        )

        self.db_query_duration_seconds = Histogram(
            "db_query_duration_seconds",
            "Database query duration in seconds",
            ["operation"],
            buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
        )

        self.db_connections_active = Gauge(
            "db_connections_active",
            "Active database connections",
        )

        # Cache metrics
        self.cache_hits_total = PromCounter(
            "cache_hits_total",
            "Total cache hits",
            ["cache_type"],
        )

        self.cache_misses_total = PromCounter(
            "cache_misses_total",
            "Total cache misses",
            ["cache_type"],
        )

        # Business metrics
        self.trades_total = PromCounter(
            "trades_total",
            "Total trades executed",
            ["status", "exchange"],
        )

        self.bots_active = Gauge(
            "bots_active",
            "Number of active trading bots",
        )

        self.users_total = Gauge(
            "users_total",
            "Total number of users",
        )

    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration: float,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None,
    ):
        """Record HTTP request metrics"""
        if not self.enabled:
            return

        self.http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
        self.http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(
            duration
        )

        if request_size is not None:
            self.http_request_size_bytes.labels(method=method, endpoint=endpoint).observe(
                request_size
            )

        if response_size is not None:
            self.http_response_size_bytes.labels(method=method, endpoint=endpoint).observe(
                response_size
            )

    def record_db_query(self, operation: str, duration: float, status: str = "success"):
        """Record database query metrics"""
        if not self.enabled:
            return

        self.db_queries_total.labels(operation=operation, status=status).inc()
        self.db_query_duration_seconds.labels(operation=operation).observe(duration)

    def set_db_connections(self, count: int):
        """Set active database connections"""
        if not self.enabled:
            return

        self.db_connections_active.set(count)

    def record_cache_hit(self, cache_type: str):
        """Record cache hit"""
        if not self.enabled:
            return

        self.cache_hits_total.labels(cache_type=cache_type).inc()

    def record_cache_miss(self, cache_type: str):
        """Record cache miss"""
        if not self.enabled:
            return

        self.cache_misses_total.labels(cache_type=cache_type).inc()

    def record_trade(self, status: str, exchange: str):
        """Record trade execution"""
        if not self.enabled:
            return

        self.trades_total.labels(status=status, exchange=exchange).inc()

    def set_bots_active(self, count: int):
        """Set active bots count"""
        if not self.enabled:
            return

        self.bots_active.set(count)

    def set_users_total(self, count: int):
        """Set total users count"""
        if not self.enabled:
            return

        self.users_total.set(count)


# Global metrics instance
prometheus_metrics = PrometheusMetrics() if PROMETHEUS_AVAILABLE else None


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics"""

    def __init__(self, app):
        super().__init__(app)
        self.metrics = prometheus_metrics

    async def dispatch(self, request: Request, call_next):
        """Process request and collect metrics"""
        if not self.metrics or not self.metrics.enabled:
            return await call_next(request)

        # Skip metrics endpoint
        if request.url.path == "/metrics":
            return await call_next(request)

        start_time = time.perf_counter()
        method = request.method
        endpoint = self._normalize_endpoint(request.url.path)

        # Get request size
        request_size = None
        if hasattr(request, "_body"):
            request_size = len(request._body) if request._body else None

        # Process request
        response = await call_next(request)

        # Calculate metrics
        duration = time.perf_counter() - start_time
        status = response.status_code

        # Get response size
        response_size = None
        if hasattr(response, "body"):
            response_size = len(response.body) if response.body else None

        # Record metrics
        self.metrics.record_http_request(
            method=method,
            endpoint=endpoint,
            status=status,
            duration=duration,
            request_size=request_size,
            response_size=response_size,
        )

        return response

    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path for metrics"""
        # Replace IDs with placeholders
        parts = path.split("/")
        normalized = []
        for part in parts:
            if part.isdigit() or (len(part) == 36 and "-" in part):  # UUID
                normalized.append("{id}")
            else:
                normalized.append(part)
        return "/".join(normalized)


def get_metrics_response() -> Response:
    """Get Prometheus metrics response"""
    if not PROMETHEUS_AVAILABLE or not prometheus_metrics or not prometheus_metrics.enabled:
        return StarletteResponse(
            content="Prometheus metrics not available",
            status_code=503,
        )

    return StarletteResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )

