"""
Middleware Performance Metrics
Tracks and reports middleware performance metrics
"""

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import Request

logger = logging.getLogger(__name__)


@dataclass
class MiddlewareMetric:
    """Single middleware performance metric"""

    name: str
    duration_ms: float
    timestamp: datetime
    success: bool
    error: str | None = None


class MiddlewarePerformanceMonitor:
    """Monitor middleware performance metrics"""

    def __init__(self, max_samples: int = 1000, window_seconds: int = 60):
        self.max_samples = max_samples
        self.window_seconds = window_seconds
        self.metrics: dict[str, deque] = defaultdict(lambda: deque(maxlen=max_samples))
        self._lock = None  # Would use threading.Lock in production

    def record(
        self,
        middleware_name: str,
        duration_ms: float,
        success: bool = True,
        error: str | None = None,
    ):
        """Record a middleware performance metric"""
        metric = MiddlewareMetric(
            name=middleware_name,
            duration_ms=duration_ms,
            timestamp=datetime.now(UTC),
            success=success,
            error=error,
        )
        self.metrics[middleware_name].append(metric)

    def get_stats(self, middleware_name: str | None = None) -> dict:
        """Get performance statistics for middleware"""
        if middleware_name:
            metrics = list(self.metrics.get(middleware_name, []))
        else:
            # Aggregate all middleware
            metrics = []
            for mw_metrics in self.metrics.values():
                metrics.extend(list(mw_metrics))

        if not metrics:
            return {
                "count": 0,
                "avg_duration_ms": 0,
                "min_duration_ms": 0,
                "max_duration_ms": 0,
                "p95_duration_ms": 0,
                "p99_duration_ms": 0,
                "error_rate": 0,
            }

        # Filter by time window
        cutoff = datetime.now(UTC) - timedelta(seconds=self.window_seconds)
        recent_metrics = [m for m in metrics if m.timestamp > cutoff]

        if not recent_metrics:
            return {
                "count": 0,
                "avg_duration_ms": 0,
                "min_duration_ms": 0,
                "max_duration_ms": 0,
                "p95_duration_ms": 0,
                "p99_duration_ms": 0,
                "error_rate": 0,
            }

        durations = [m.duration_ms for m in recent_metrics]
        durations.sort()

        count = len(recent_metrics)
        error_count = sum(1 for m in recent_metrics if not m.success)

        return {
            "count": count,
            "avg_duration_ms": sum(durations) / count,
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "p95_duration_ms": durations[int(count * 0.95)] if count > 0 else 0,
            "p99_duration_ms": durations[int(count * 0.99)] if count > 0 else 0,
            "error_rate": error_count / count if count > 0 else 0,
        }

    def get_all_stats(self) -> dict[str, dict]:
        """Get statistics for all middleware"""
        all_stats = {}
        for middleware_name in self.metrics:
            all_stats[middleware_name] = self.get_stats(middleware_name)
        return all_stats

    def get_slow_middleware(self, threshold_ms: float = 100) -> list[dict]:
        """Get middleware that exceeds performance threshold"""
        slow = []
        for middleware_name, stats in self.get_all_stats().items():
            if stats["avg_duration_ms"] > threshold_ms:
                slow.append(
                    {
                        "middleware": middleware_name,
                        "avg_duration_ms": stats["avg_duration_ms"],
                        "count": stats["count"],
                    }
                )
        return sorted(slow, key=lambda x: x["avg_duration_ms"], reverse=True)


# Global performance monitor instance
performance_monitor = MiddlewarePerformanceMonitor()


class PerformanceTrackingMiddleware:
    """Middleware to track performance of other middleware"""

    def __init__(self, monitor: MiddlewarePerformanceMonitor | None = None):
        self.monitor = monitor or performance_monitor
        self.start_times: dict[str, float] = {}

    async def track_middleware(
        self,
        middleware_name: str,
        request: Request,
        call_next,
    ):
        """Track middleware execution time"""
        start_time = time.perf_counter()
        success = True
        error = None

        try:
            response = await call_next(request)
            return response
        except Exception as e:
            success = False
            error = str(e)
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.monitor.record(
                middleware_name=middleware_name,
                duration_ms=duration_ms,
                success=success,
                error=error,
            )
