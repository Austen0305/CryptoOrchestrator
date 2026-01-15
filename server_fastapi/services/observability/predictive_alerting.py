"""
Predictive Alerting Service
Predicts issues before they occur using time-series forecasting
"""

import logging
import statistics
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class Forecast:
    """Time-series forecast"""

    metric_name: str
    current_value: float
    predicted_value: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    trend: str  # "increasing", "decreasing", "stable"
    predicted_threshold_breach: datetime | None = None
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class PredictiveAlert:
    """Predictive alert"""

    metric_name: str
    current_value: float
    predicted_value: float
    threshold: float
    predicted_breach_time: datetime
    confidence: float
    severity: str
    message: str
    timestamp: datetime
    tags: dict[str, str] = field(default_factory=dict)


class PredictiveAlertingService:
    """
    Predictive alerting service using time-series forecasting

    Features:
    - Simple moving average forecasting
    - Linear trend detection
    - Threshold breach prediction
    - Confidence intervals
    """

    def __init__(self, forecast_window_minutes: int = 30, min_samples: int = 20):
        """
        Initialize predictive alerting service

        Args:
            forecast_window_minutes: Time window for prediction
            min_samples: Minimum samples needed for forecasting
        """
        self.forecast_window_minutes = forecast_window_minutes
        self.min_samples = min_samples
        self.metric_history: dict[str, deque] = {}
        self.forecasts: dict[str, Forecast] = {}
        self.predictive_alerts: list[PredictiveAlert] = []
        self.max_history = 1000

    def record_metric(
        self, metric_name: str, value: float, tags: dict[str, str] | None = None
    ):
        """
        Record a metric value and generate forecast

        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Optional tags
        """
        key = self._make_key(metric_name, tags)

        # Store in history
        if key not in self.metric_history:
            self.metric_history[key] = deque(maxlen=1000)

        timestamp = datetime.now(UTC)
        self.metric_history[key].append((timestamp, value))

        # Generate forecast
        forecast = self._generate_forecast(key, metric_name, tags)
        if forecast:
            self.forecasts[key] = forecast

        return forecast

    def _generate_forecast(
        self, key: str, metric_name: str, tags: dict[str, str] | None
    ) -> Forecast | None:
        """Generate forecast for a metric"""
        if key not in self.metric_history:
            return None

        history = self.metric_history[key]
        if len(history) < self.min_samples:
            return None

        # Get recent values
        recent_values = [v for _, v in history]
        current_value = recent_values[-1]

        # Simple moving average forecast
        window_size = min(10, len(recent_values))
        statistics.mean(recent_values[-window_size:])

        # Calculate trend
        if len(recent_values) >= 2:
            recent_trend = recent_values[-1] - recent_values[-2]
            if recent_trend > 0.01:
                trend = "increasing"
            elif recent_trend < -0.01:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # Simple linear projection
        if len(recent_values) >= 3:
            # Calculate average change rate
            changes = [
                recent_values[i] - recent_values[i - 1]
                for i in range(1, len(recent_values))
            ]
            avg_change = statistics.mean(changes) if changes else 0.0

            # Project forward
            forecast_minutes = self.forecast_window_minutes
            predicted_value = current_value + (avg_change * forecast_minutes)
        else:
            predicted_value = current_value

        # Calculate confidence interval (simplified)
        std_dev = statistics.stdev(recent_values) if len(recent_values) > 1 else 0.0
        confidence_interval_lower = predicted_value - (1.96 * std_dev)  # 95% CI
        confidence_interval_upper = predicted_value + (1.96 * std_dev)

        return Forecast(
            metric_name=metric_name,
            current_value=current_value,
            predicted_value=predicted_value,
            confidence_interval_lower=confidence_interval_lower,
            confidence_interval_upper=confidence_interval_upper,
            trend=trend,
            tags=tags or {},
        )

    def predict_threshold_breach(
        self,
        metric_name: str,
        threshold: float,
        condition: str = ">",
        tags: dict[str, str] | None = None,
    ) -> PredictiveAlert | None:
        """
        Predict when a metric will breach a threshold

        Args:
            metric_name: Name of the metric
            threshold: Threshold value
            condition: Condition (">", "<", ">=", "<=")
            tags: Optional tags
        """
        key = self._make_key(metric_name, tags)

        if key not in self.forecasts:
            return None

        forecast = self.forecasts[key]
        current_value = forecast.current_value
        predicted_value = forecast.predicted_value

        # Check if breach is predicted
        will_breach = False
        if condition == ">":
            will_breach = predicted_value > threshold and current_value <= threshold
        elif condition == "<":
            will_breach = predicted_value < threshold and current_value >= threshold
        elif condition == ">=":
            will_breach = predicted_value >= threshold and current_value < threshold
        elif condition == "<=":
            will_breach = predicted_value <= threshold and current_value > threshold

        if not will_breach:
            return None

        # Estimate breach time (simplified linear interpolation)
        if forecast.trend == "increasing" and condition in (">", ">="):
            if current_value < threshold:
                # Linear interpolation to find breach time
                rate = (predicted_value - current_value) / self.forecast_window_minutes
                if rate > 0:
                    time_to_breach = (threshold - current_value) / rate
                    predicted_breach_time = datetime.now(UTC) + timedelta(
                        minutes=time_to_breach
                    )
                else:
                    return None
            else:
                return None
        elif forecast.trend == "decreasing" and condition in ("<", "<="):
            if current_value > threshold:
                rate = (current_value - predicted_value) / self.forecast_window_minutes
                if rate > 0:
                    time_to_breach = (current_value - threshold) / rate
                    predicted_breach_time = datetime.now(UTC) + timedelta(
                        minutes=time_to_breach
                    )
                else:
                    return None
            else:
                return None
        else:
            return None

        # Calculate confidence (simplified)
        confidence = (
            0.7  # Base confidence, could be improved with more sophisticated models
        )

        # Determine severity based on time to breach
        minutes_to_breach = (
            predicted_breach_time - datetime.now(UTC)
        ).total_seconds() / 60
        if minutes_to_breach < 5:
            severity = "critical"
        elif minutes_to_breach < 15:
            severity = "high"
        elif minutes_to_breach < 30:
            severity = "medium"
        else:
            severity = "low"

        alert = PredictiveAlert(
            metric_name=metric_name,
            current_value=current_value,
            predicted_value=predicted_value,
            threshold=threshold,
            predicted_breach_time=predicted_breach_time,
            confidence=confidence,
            severity=severity,
            message=f"{metric_name} predicted to breach {condition} {threshold} in {minutes_to_breach:.1f} minutes",
            timestamp=datetime.now(UTC),
            tags=tags or {},
        )

        self.predictive_alerts.append(alert)
        if len(self.predictive_alerts) > self.max_history:
            self.predictive_alerts = self.predictive_alerts[-self.max_history :]

        return alert

    def get_forecast(
        self, metric_name: str, tags: dict[str, str] | None = None
    ) -> Forecast | None:
        """Get forecast for a metric"""
        key = self._make_key(metric_name, tags)
        return self.forecasts.get(key)

    def get_predictive_alerts(self, limit: int = 100) -> list[PredictiveAlert]:
        """Get recent predictive alerts"""
        return sorted(
            self.predictive_alerts[-limit:] if limit else self.predictive_alerts,
            key=lambda a: a.predicted_breach_time,
            reverse=True,
        )

    def _make_key(self, metric_name: str, tags: dict[str, str] | None) -> str:
        """Create a key from metric name and tags"""
        if not tags:
            return metric_name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{metric_name}[{tag_str}]"


# Global instance
predictive_alerting_service = PredictiveAlertingService()
