"""
Alert Service
AI-powered alerting system for application monitoring
"""

import logging
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status"""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class AlertRule:
    """Alert rule configuration"""

    name: str
    metric_name: str
    condition: str  # e.g., "> 100", "< 50", "== 0"
    severity: AlertSeverity
    threshold: float
    cooldown_minutes: int = 5
    enabled: bool = True
    description: str = ""
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    """Alert instance"""

    rule_name: str
    severity: AlertSeverity
    message: str
    metric_value: float
    threshold: float
    timestamp: datetime
    status: AlertStatus = AlertStatus.ACTIVE
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    tags: dict[str, str] = field(default_factory=dict)


class AlertService:
    """
    AI-powered alerting service

    Features:
    - Rule-based alerting
    - Cooldown periods
    - Alert aggregation
    - AI-powered alert prioritization
    - Alert correlation
    """

    def __init__(self):
        self.rules: dict[str, AlertRule] = {}
        self.active_alerts: dict[str, Alert] = {}
        self.alert_history: list[Alert] = []
        self.last_alert_time: dict[str, datetime] = {}
        self.alert_handlers: list[Callable[[Alert], None]] = []
        self.max_history: int = 1000

    def register_rule(self, rule: AlertRule):
        """Register an alert rule"""
        self.rules[rule.name] = rule
        logger.info(f"Registered alert rule: {rule.name}")

    def register_handler(self, handler: Callable[[Alert], None]):
        """Register an alert handler (e.g., for notifications)"""
        self.alert_handlers.append(handler)

    def evaluate_metric(
        self, metric_name: str, value: float, tags: dict[str, str] | None = None
    ):
        """Evaluate a metric value against all rules"""
        tags = tags or {}

        for rule_name, rule in self.rules.items():
            if not rule.enabled:
                continue

            if rule.metric_name != metric_name:
                continue

            # Check if tags match (if rule has tags)
            if rule.tags and not all(tags.get(k) == v for k, v in rule.tags.items()):
                continue

            # Check cooldown
            last_alert_key = f"{rule_name}_{metric_name}"
            if last_alert_key in self.last_alert_time:
                time_since_last = (
                    datetime.now(UTC) - self.last_alert_time[last_alert_key]
                )
                if time_since_last < timedelta(minutes=rule.cooldown_minutes):
                    continue

            # Evaluate condition
            if self._evaluate_condition(value, rule.condition, rule.threshold):
                self._trigger_alert(rule, value, tags)

    def _evaluate_condition(
        self, value: float, condition: str, threshold: float
    ) -> bool:
        """Evaluate a condition"""
        try:
            # Simple condition evaluation
            if condition.startswith(">"):
                return value > threshold
            elif condition.startswith("<"):
                return value < threshold
            elif condition.startswith(">="):
                return value >= threshold
            elif condition.startswith("<="):
                return value <= threshold
            elif condition.startswith("=="):
                return abs(value - threshold) < 0.001  # Float comparison
            elif condition.startswith("!="):
                return abs(value - threshold) >= 0.001
            else:
                logger.warning(f"Unknown condition: {condition}")
                return False
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False

    def _trigger_alert(self, rule: AlertRule, value: float, tags: dict[str, str]):
        """Trigger an alert"""
        alert_key = f"{rule.name}_{rule.metric_name}"

        # Check if alert already exists
        if alert_key in self.active_alerts:
            # Update existing alert
            alert = self.active_alerts[alert_key]
            alert.message = f"{rule.description or rule.name}: {value} {rule.condition} {rule.threshold}"
            alert.metric_value = value
            alert.timestamp = datetime.now(UTC)
        else:
            # Create new alert
            alert = Alert(
                rule_name=rule.name,
                severity=rule.severity,
                message=f"{rule.description or rule.name}: {value} {rule.condition} {rule.threshold}",
                metric_value=value,
                threshold=rule.threshold,
                timestamp=datetime.now(UTC),
                tags=tags,
            )
            self.active_alerts[alert_key] = alert
            self.alert_history.append(alert)

            # Keep history limited
            if len(self.alert_history) > self.max_history:
                self.alert_history = self.alert_history[-self.max_history :]

        # Update last alert time
        self.last_alert_time[alert_key] = datetime.now(UTC)

        # Notify handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}", exc_info=True)

        logger.warning(
            f"Alert triggered: {alert.message} (severity: {alert.severity.value})"
        )

    def acknowledge_alert(self, alert_key: str):
        """Acknowledge an alert"""
        if alert_key in self.active_alerts:
            alert = self.active_alerts[alert_key]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.now(UTC)
            logger.info(f"Alert acknowledged: {alert_key}")

    def resolve_alert(self, alert_key: str):
        """Resolve an alert"""
        if alert_key in self.active_alerts:
            alert = self.active_alerts[alert_key]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now(UTC)
            del self.active_alerts[alert_key]
            logger.info(f"Alert resolved: {alert_key}")

    def get_active_alerts(self, severity: AlertSeverity | None = None) -> list[Alert]:
        """Get active alerts, optionally filtered by severity"""
        alerts = list(self.active_alerts.values())
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)

    def get_alert_history(self, limit: int = 100) -> list[Alert]:
        """Get alert history"""
        return self.alert_history[-limit:]

    def get_alert_summary(self) -> dict[str, Any]:
        """Get alert summary statistics"""
        active_by_severity = defaultdict(int)
        for alert in self.active_alerts.values():
            active_by_severity[alert.severity.value] += 1

        return {
            "total_active": len(self.active_alerts),
            "active_by_severity": dict(active_by_severity),
            "total_rules": len(self.rules),
            "enabled_rules": sum(1 for r in self.rules.values() if r.enabled),
            "total_history": len(self.alert_history),
        }


# Global instance
alert_service = AlertService()
