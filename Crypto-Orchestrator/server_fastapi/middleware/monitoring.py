"""Comprehensive monitoring middleware with Prometheus metrics"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge
import time
import psutil
import logging

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds", "HTTP request duration", ["method", "endpoint"]
)

ACTIVE_REQUESTS = Gauge("http_requests_active", "Number of active HTTP requests")

MEMORY_USAGE = Gauge("process_memory_bytes", "Process memory usage in bytes")

CPU_USAGE = Gauge("process_cpu_percent", "Process CPU usage percentage")


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Comprehensive monitoring middleware"""

    async def dispatch(self, request: Request, call_next):
        # Track active requests
        ACTIVE_REQUESTS.inc()

        # Start timer
        start_time = time.time()

        # Extract endpoint path template
        endpoint = request.url.path
        method = request.method

        try:
            response = await call_next(request)
            status = response.status_code
        except Exception as e:
            status = 500
            logger.error(f"Request failed: {e}")
            raise
        finally:
            # Update metrics
            duration = time.time() - start_time

            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()

            REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

            ACTIVE_REQUESTS.dec()

            # Update system metrics
            try:
                process = psutil.Process()
                MEMORY_USAGE.set(process.memory_info().rss)
                CPU_USAGE.set(process.cpu_percent())
            except Exception as e:
                logger.warning(f"Failed to update system metrics: {e}")

            # Log slow requests
            if duration > 1.0:
                logger.warning(
                    f"Slow request: {method} {endpoint} took {duration:.2f}s"
                )

        return response
