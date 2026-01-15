"""
API Analytics Middleware
Tracks API usage, endpoint popularity, and client analytics
"""

import logging
import time
from collections import defaultdict, deque
from datetime import UTC, datetime
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class APIAnalyticsMiddleware(BaseHTTPMiddleware):
    """
    Tracks API analytics:
    - Endpoint usage
    - Response times
    - Error rates
    - Client information
    - Geographic data (if available)
    """

    def __init__(self, app=None, max_history: int = 10000):
        # Allow initialization without app for global instance
        if app:
            super().__init__(app)
        self.max_history = max_history

        # Analytics storage
        self.endpoint_stats: dict[str, dict] = defaultdict(
            lambda: {
                "count": 0,
                "total_time": 0.0,
                "errors": 0,
                "last_access": None,
            }
        )

        self.client_stats: dict[str, dict] = defaultdict(
            lambda: {
                "count": 0,
                "endpoints": set(),
                "last_access": None,
            }
        )

        self.hourly_stats: deque = deque(maxlen=24)  # Last 24 hours

        self.analytics = {
            "total_requests": 0,
            "total_errors": 0,
            "unique_clients": set(),
            "unique_endpoints": set(),
        }

    async def dispatch(self, request: Request, call_next) -> Response:
        """Track request analytics"""
        start_time = time.perf_counter()

        # Extract client info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        endpoint = request.url.path
        method = request.method

        # Track endpoint
        endpoint_key = f"{method} {endpoint}"
        self.endpoint_stats[endpoint_key]["count"] += 1
        self.endpoint_stats[endpoint_key]["last_access"] = datetime.now(UTC)

        # Track client
        client_key = f"{client_ip}:{user_agent[:50]}"
        self.client_stats[client_key]["count"] += 1
        self.client_stats[client_key]["endpoints"].add(endpoint_key)
        self.client_stats[client_key]["last_access"] = datetime.now(UTC)

        # Update analytics
        self.analytics["total_requests"] += 1
        self.analytics["unique_clients"].add(client_key)
        self.analytics["unique_endpoints"].add(endpoint_key)

        # Process request
        try:
            response = await call_next(request)
            duration = time.perf_counter() - start_time

            # Update stats
            self.endpoint_stats[endpoint_key]["total_time"] += duration

            if response.status_code >= 400:
                self.endpoint_stats[endpoint_key]["errors"] += 1
                self.analytics["total_errors"] += 1

            # Record hourly stats
            self._record_hourly_stats(endpoint_key, duration, response.status_code)

            return response

        except Exception:
            duration = time.perf_counter() - start_time
            self.endpoint_stats[endpoint_key]["errors"] += 1
            self.endpoint_stats[endpoint_key]["total_time"] += duration
            self.analytics["total_errors"] += 1
            raise

    def _record_hourly_stats(self, endpoint: str, duration: float, status_code: int):
        """Record statistics for current hour"""
        current_hour = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)

        if not self.hourly_stats or self.hourly_stats[-1]["hour"] != current_hour:
            self.hourly_stats.append(
                {
                    "hour": current_hour,
                    "requests": 0,
                    "errors": 0,
                    "avg_duration": 0.0,
                    "endpoints": defaultdict(int),
                }
            )

        hour_stats = self.hourly_stats[-1]
        hour_stats["requests"] += 1
        hour_stats["endpoints"][endpoint] += 1

        if status_code >= 400:
            hour_stats["errors"] += 1

        # Update average duration
        total_duration = (
            hour_stats["avg_duration"] * (hour_stats["requests"] - 1) + duration
        )
        hour_stats["avg_duration"] = total_duration / hour_stats["requests"]

    def get_endpoint_stats(self, endpoint: str | None = None) -> dict[str, Any]:
        """Get statistics for endpoint(s)"""
        if endpoint:
            stats = self.endpoint_stats.get(endpoint, {})
            count = stats.get("count", 0)
            return {
                **stats,
                "avg_time_ms": (stats.get("total_time", 0) / count * 1000)
                if count > 0
                else 0,
                "error_rate": (stats.get("errors", 0) / count * 100)
                if count > 0
                else 0,
            }

        # All endpoints
        result = {}
        for ep, stats in self.endpoint_stats.items():
            count = stats.get("count", 0)
            result[ep] = {
                **stats,
                "avg_time_ms": (stats.get("total_time", 0) / count * 1000)
                if count > 0
                else 0,
                "error_rate": (stats.get("errors", 0) / count * 100)
                if count > 0
                else 0,
            }
        return result

    def get_popular_endpoints(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get most popular endpoints"""
        endpoints = [
            {
                "endpoint": ep,
                "count": stats["count"],
                "avg_time_ms": (stats["total_time"] / stats["count"] * 1000)
                if stats["count"] > 0
                else 0,
                "error_rate": (stats["errors"] / stats["count"] * 100)
                if stats["count"] > 0
                else 0,
            }
            for ep, stats in self.endpoint_stats.items()
        ]
        return sorted(endpoints, key=lambda x: x["count"], reverse=True)[:limit]

    def get_analytics_summary(self) -> dict[str, Any]:
        """Get analytics summary"""
        return {
            "total_requests": self.analytics["total_requests"],
            "total_errors": self.analytics["total_errors"],
            "error_rate": (
                self.analytics["total_errors"] / self.analytics["total_requests"] * 100
                if self.analytics["total_requests"] > 0
                else 0
            ),
            "unique_clients": len(self.analytics["unique_clients"]),
            "unique_endpoints": len(self.analytics["unique_endpoints"]),
            "popular_endpoints": self.get_popular_endpoints(10),
            "hourly_stats": list(self.hourly_stats),
        }


# Global analytics instance (initialized without app)
api_analytics = APIAnalyticsMiddleware(max_history=10000)
