"""
Metrics Service
Collects and exposes application metrics for observability
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MetricValue:
    """Single metric value with timestamp"""

    value: float
    timestamp: datetime
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class MetricSeries:
    """Time series of metric values"""

    name: str
    values: list[MetricValue] = field(default_factory=list)
    max_points: int = 1000  # Keep last 1000 points

    def add(self, value: float, tags: dict[str, str] | None = None):
        """Add a metric value"""
        metric_value = MetricValue(
            value=value, timestamp=datetime.utcnow(), tags=tags or {}
        )
        self.values.append(metric_value)

        # Keep only last max_points
        if len(self.values) > self.max_points:
            self.values = self.values[-self.max_points :]

    def get_recent(self, minutes: int = 60) -> list[MetricValue]:
        """Get recent metric values"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return [v for v in self.values if v.timestamp >= cutoff]

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics"""
        if not self.values:
            return {"count": 0}

        recent_values = [v.value for v in self.get_recent(60)]
        if not recent_values:
            return {"count": 0}

        return {
            "count": len(recent_values),
            "min": min(recent_values),
            "max": max(recent_values),
            "avg": sum(recent_values) / len(recent_values),
            "latest": recent_values[-1] if recent_values else None,
        }


class MetricsService:
    """
    Service for collecting and exposing application metrics

    Supports:
    - Counter metrics (increments)
    - Gauge metrics (current value)
    - Histogram metrics (distribution)
    - Timer metrics (duration)
    """

    def __init__(self):
        self.counters: dict[str, float] = defaultdict(float)
        self.gauges: dict[str, float] = {}
        self.histograms: dict[str, MetricSeries] = {}
        self.timers: dict[str, list[float]] = defaultdict(list)
        self.timer_start_times: dict[str, float] = {}

    def increment(
        self, name: str, value: float = 1.0, tags: dict[str, str] | None = None
    ):
        """Increment a counter metric"""
        key = self._make_key(name, tags)
        self.counters[key] += value

    def set_gauge(self, name: str, value: float, tags: dict[str, str] | None = None):
        """Set a gauge metric (current value)"""
        key = self._make_key(name, tags)
        self.gauges[key] = value

    def record_histogram(
        self, name: str, value: float, tags: dict[str, str] | None = None
    ):
        """Record a histogram value"""
        key = self._make_key(name, tags)
        if key not in self.histograms:
            self.histograms[key] = MetricSeries(name=name)
        self.histograms[key].add(value, tags)

    def start_timer(self, name: str, tags: dict[str, str] | None = None) -> str:
        """Start a timer, returns timer ID"""
        timer_id = f"{name}_{time.time_ns()}"
        key = self._make_key(name, tags)
        self.timer_start_times[timer_id] = time.time()
        return timer_id

    def stop_timer(self, timer_id: str, name: str, tags: dict[str, str] | None = None):
        """Stop a timer and record duration"""
        if timer_id not in self.timer_start_times:
            logger.warning(f"Timer {timer_id} not found")
            return

        duration = time.time() - self.timer_start_times[timer_id]
        del self.timer_start_times[timer_id]

        key = self._make_key(name, tags)
        self.timers[key].append(duration)

        # Keep only last 1000 timings
        if len(self.timers[key]) > 1000:
            self.timers[key] = self.timers[key][-1000:]

    def get_metrics(self) -> dict[str, Any]:
        """Get all metrics"""
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {k: v.get_summary() for k, v in self.histograms.items()},
            "timers": {k: self._get_timer_stats(v) for k, v in self.timers.items()},
        }

    def get_metric(self, name: str, metric_type: str = "counter") -> Any | None:
        """Get a specific metric"""
        if metric_type == "counter":
            return self.counters.get(name)
        elif metric_type == "gauge":
            return self.gauges.get(name)
        elif metric_type == "histogram":
            series = self.histograms.get(name)
            return series.get_summary() if series else None
        elif metric_type == "timer":
            timings = self.timers.get(name)
            return self._get_timer_stats(timings) if timings else None
        return None

    def _make_key(self, name: str, tags: dict[str, str] | None) -> str:
        """Create a key from name and tags"""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"

    def _get_timer_stats(self, timings: list[float]) -> dict[str, Any]:
        """Get statistics for timer values"""
        if not timings:
            return {"count": 0}

        sorted_timings = sorted(timings)
        count = len(sorted_timings)

        return {
            "count": count,
            "min": sorted_timings[0],
            "max": sorted_timings[-1],
            "avg": sum(sorted_timings) / count,
            "p50": sorted_timings[count // 2] if count > 0 else 0,
            "p95": sorted_timings[int(count * 0.95)] if count > 0 else 0,
            "p99": sorted_timings[int(count * 0.99)] if count > 0 else 0,
        }

    def reset(self):
        """Reset all metrics"""
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
        self.timers.clear()
        self.timer_start_times.clear()


# Global instance
metrics_service = MetricsService()
