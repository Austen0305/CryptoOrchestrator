"""
Performance Baselines and Trend Analysis Service
Baseline detection and trend analysis for performance metrics
"""

import logging
import statistics
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Baseline:
    """Performance baseline"""

    metric_name: str
    baseline_value: float
    std_dev: float
    min_value: float
    max_value: float
    percentile_50: float
    percentile_95: float
    percentile_99: float
    sample_count: int
    calculated_at: datetime
    time_window_hours: int


@dataclass
class Trend:
    """Trend analysis"""

    metric_name: str
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_strength: float  # 0-1, how strong the trend is
    rate_of_change: float  # Change per hour
    predicted_value_24h: float
    confidence: float  # 0-1
    analysis_period_hours: int


class PerformanceBaselinesService:
    """
    Performance baselines and trend analysis service

    Features:
    - Baseline calculation
    - Trend detection
    - Anomaly detection based on baselines
    - Performance regression detection
    - Predictive analysis
    """

    def __init__(self):
        self.baselines: dict[str, Baseline] = {}
        self.metric_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.trends: dict[str, Trend] = {}

    def record_metric(
        self,
        metric_name: str,
        value: float,
        timestamp: datetime | None = None,
    ):
        """
        Record a metric value

        Args:
            metric_name: Metric name
            value: Metric value
            timestamp: Optional timestamp
        """
        ts = timestamp or datetime.utcnow()
        self.metric_history[metric_name].append((ts, value))

    def calculate_baseline(
        self,
        metric_name: str,
        time_window_hours: int = 168,  # 7 days default
    ) -> Baseline | None:
        """
        Calculate baseline for a metric

        Args:
            metric_name: Metric name
            time_window_hours: Time window for baseline calculation

        Returns:
            Baseline if enough data
        """
        if metric_name not in self.metric_history:
            return None

        history = self.metric_history[metric_name]
        if len(history) < 10:  # Need at least 10 samples
            return None

        # Get values within time window
        cutoff = datetime.utcnow() - timedelta(hours=time_window_hours)
        recent_values = [v for t, v in history if t >= cutoff]

        if len(recent_values) < 10:
            return None

        # Calculate statistics
        baseline_value = statistics.mean(recent_values)
        std_dev = statistics.stdev(recent_values) if len(recent_values) > 1 else 0.0
        min_value = min(recent_values)
        max_value = max(recent_values)

        # Calculate percentiles
        sorted_values = sorted(recent_values)
        percentile_50 = sorted_values[int(len(sorted_values) * 0.50)]
        percentile_95 = (
            sorted_values[int(len(sorted_values) * 0.95)]
            if len(sorted_values) > 1
            else sorted_values[-1]
        )
        percentile_99 = (
            sorted_values[int(len(sorted_values) * 0.99)]
            if len(sorted_values) > 1
            else sorted_values[-1]
        )

        baseline = Baseline(
            metric_name=metric_name,
            baseline_value=baseline_value,
            std_dev=std_dev,
            min_value=min_value,
            max_value=max_value,
            percentile_50=percentile_50,
            percentile_95=percentile_95,
            percentile_99=percentile_99,
            sample_count=len(recent_values),
            calculated_at=datetime.utcnow(),
            time_window_hours=time_window_hours,
        )

        self.baselines[metric_name] = baseline

        logger.debug(f"Calculated baseline for {metric_name}: {baseline_value:.2f}")

        return baseline

    def analyze_trend(
        self,
        metric_name: str,
        analysis_period_hours: int = 24,
    ) -> Trend | None:
        """
        Analyze trend for a metric

        Args:
            metric_name: Metric name
            analysis_period_hours: Period to analyze

        Returns:
            Trend analysis
        """
        if metric_name not in self.metric_history:
            return None

        history = self.metric_history[metric_name]
        if len(history) < 2:
            return None

        # Get recent values
        cutoff = datetime.utcnow() - timedelta(hours=analysis_period_hours)
        recent_data = [(t, v) for t, v in history if t >= cutoff]

        if len(recent_data) < 2:
            return None

        # Sort by time
        recent_data.sort(key=lambda x: x[0])

        # Calculate linear regression (simplified)
        times = [
            (t - recent_data[0][0]).total_seconds() / 3600.0 for t, _ in recent_data
        ]
        values = [v for _, v in recent_data]

        # Simple linear regression
        n = len(times)
        sum_x = sum(times)
        sum_y = sum(values)
        sum_xy = sum(t * v for t, v in zip(times, values))
        sum_x2 = sum(t * t for t in times)

        if n * sum_x2 - sum_x * sum_x == 0:
            slope = 0.0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

        intercept = (sum_y - slope * sum_x) / n

        # Determine trend direction
        if abs(slope) < 0.01:
            trend_direction = "stable"
        elif slope > 0:
            trend_direction = "increasing"
        else:
            trend_direction = "decreasing"

        # Calculate trend strength (R-squared approximation)
        mean_y = sum_y / n
        ss_res = sum((v - (slope * t + intercept)) ** 2 for t, v in zip(times, values))
        ss_tot = sum((v - mean_y) ** 2 for v in values)

        if ss_tot > 0:
            r_squared = 1 - (ss_res / ss_tot)
            trend_strength = max(0.0, min(1.0, r_squared))
        else:
            trend_strength = 0.0

        # Predict value 24 hours ahead
        predicted_value_24h = slope * (times[-1] + 24) + intercept

        # Calculate confidence (based on data points and R-squared)
        confidence = min(1.0, (len(recent_data) / 100.0) * trend_strength)

        trend = Trend(
            metric_name=metric_name,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            rate_of_change=slope,  # Change per hour
            predicted_value_24h=predicted_value_24h,
            confidence=confidence,
            analysis_period_hours=analysis_period_hours,
        )

        self.trends[metric_name] = trend

        return trend

    def detect_regression(
        self,
        metric_name: str,
        current_value: float,
        threshold_std_devs: float = 2.0,
    ) -> dict[str, Any]:
        """
        Detect performance regression

        Args:
            metric_name: Metric name
            current_value: Current metric value
            threshold_std_devs: Number of standard deviations for threshold

        Returns:
            Regression detection result
        """
        baseline = self.baselines.get(metric_name)

        if not baseline:
            return {
                "regression_detected": False,
                "reason": "No baseline available",
            }

        # Check if current value deviates significantly
        deviation = abs(current_value - baseline.baseline_value)
        z_score = deviation / baseline.std_dev if baseline.std_dev > 0 else 0.0

        is_regression = z_score > threshold_std_devs

        result = {
            "regression_detected": is_regression,
            "metric_name": metric_name,
            "current_value": current_value,
            "baseline_value": baseline.baseline_value,
            "deviation": deviation,
            "z_score": z_score,
            "threshold": threshold_std_devs,
        }

        if is_regression:
            if current_value > baseline.baseline_value:
                result["regression_type"] = "performance_degradation"
            else:
                result["regression_type"] = "performance_improvement"

        return result

    def get_baseline(self, metric_name: str) -> Baseline | None:
        """Get baseline for a metric"""
        return self.baselines.get(metric_name)

    def get_trend(self, metric_name: str) -> Trend | None:
        """Get trend for a metric"""
        return self.trends.get(metric_name)

    def get_all_baselines(self) -> dict[str, Baseline]:
        """Get all baselines"""
        return self.baselines.copy()

    def get_all_trends(self) -> dict[str, Trend]:
        """Get all trends"""
        return self.trends.copy()


# Global instance
performance_baselines_service = PerformanceBaselinesService()
