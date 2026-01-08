"""
Alerting Service
Implements alerting rules, channels, incident management integration,
alert escalation, and fatigue prevention.
"""

import asyncio
import logging
import uuid
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Alert notification channels"""

    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"


class AlertRule:
    """Alert rule definition"""

    def __init__(
        self,
        name: str,
        metric: str,
        threshold: float,
        operator: str,  # "gt", "lt", "eq"
        severity: AlertSeverity,
        channels: list[AlertChannel],
        duration: int = 60,  # Duration in seconds before alerting
        cooldown: int = 300,  # Cooldown period in seconds
    ):
        self.name = name
        self.metric = metric
        self.threshold = threshold
        self.operator = operator
        self.severity = severity
        self.channels = channels
        self.duration = duration
        self.cooldown = cooldown
        self.last_triggered: datetime | None = None
        self.trigger_count = 0


class Alert:
    """Alert instance"""

    def __init__(
        self,
        rule: AlertRule,
        current_value: float,
        message: str,
        metadata: dict[str, Any] | None = None,
    ):
        self.id = str(uuid.uuid4())
        self.rule = rule
        self.current_value = current_value
        self.message = message
        self.severity = rule.severity
        self.timestamp = datetime.utcnow()
        self.metadata = metadata or {}
        self.acknowledged = False
        self.acknowledged_by: str | None = None
        self.acknowledged_at: datetime | None = None
        self.resolved = False
        self.resolved_at: datetime | None = None
        self.escalation_level = 0  # 0 = initial, increases with escalation
        self.notification_count = 0  # Track notifications sent
        self.incident_id: str | None = None  # Link to incident


class Incident:
    """Incident instance - groups related alerts"""

    def __init__(
        self, title: str, severity: AlertSeverity, description: str | None = None
    ):
        self.id = str(uuid.uuid4())
        self.title = title
        self.severity = severity
        self.description = description
        self.status = "open"  # open, investigating, resolved, closed
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.resolved_at: datetime | None = None
        self.assigned_to: str | None = None
        self.related_alerts: list[str] = []  # Alert IDs
        self.metadata: dict[str, Any] = {}


class AlertingService:
    """Service for managing alerts, incidents, and notifications"""

    def __init__(self):
        self.rules: dict[str, AlertRule] = {}
        self.active_alerts: dict[str, Alert] = {}
        self.alert_history: list[Alert] = []
        self.channel_handlers: dict[AlertChannel, Callable] = {}
        self.max_history = 10000

        # Incident management
        self.active_incidents: dict[str, Incident] = {}
        self.incident_history: list[Incident] = []

        # Alert fatigue prevention
        self.alert_groups: dict[str, list[str]] = {}  # Group key -> alert IDs
        self.notification_timestamps: dict[str, list[datetime]] = defaultdict(list)
        self.max_notifications_per_hour = 10  # Per alert rule
        self.max_notifications_per_day = 50  # Per alert rule

        # Escalation policies
        self.escalation_policies: dict[AlertSeverity, dict[str, Any]] = {
            AlertSeverity.LOW: {
                "escalate_after_minutes": 60,
                "escalation_channels": [AlertChannel.EMAIL],
            },
            AlertSeverity.MEDIUM: {
                "escalate_after_minutes": 30,
                "escalation_channels": [AlertChannel.EMAIL, AlertChannel.SLACK],
            },
            AlertSeverity.HIGH: {
                "escalate_after_minutes": 15,
                "escalation_channels": [
                    AlertChannel.EMAIL,
                    AlertChannel.SLACK,
                    AlertChannel.SMS,
                ],
            },
            AlertSeverity.CRITICAL: {
                "escalate_after_minutes": 5,
                "escalation_channels": [
                    AlertChannel.EMAIL,
                    AlertChannel.SMS,
                    AlertChannel.PAGERDUTY,
                ],
            },
        }

    def register_rule(self, rule: AlertRule) -> None:
        """Register an alert rule"""
        self.rules[rule.name] = rule
        logger.info(f"Registered alert rule: {rule.name}")

    def get_alert_rules(self) -> list[AlertRule]:
        """Get all registered alert rules"""
        return list(self.rules.values())

    def register_channel_handler(
        self, channel: AlertChannel, handler: Callable[[Alert], None]
    ) -> None:
        """Register a handler for an alert channel"""
        self.channel_handlers[channel] = handler

    async def evaluate_rule(self, rule_name: str, current_value: float) -> Alert | None:
        """
        Evaluate an alert rule against current metric value

        Returns:
            Alert if rule triggered, None otherwise
        """
        if rule_name not in self.rules:
            logger.warning(f"Alert rule not found: {rule_name}")
            return None

        rule = self.rules[rule_name]

        # Check cooldown
        if rule.last_triggered:
            time_since_last = (datetime.utcnow() - rule.last_triggered).total_seconds()
            if time_since_last < rule.cooldown:
                return None  # Still in cooldown

        # Evaluate condition
        triggered = False
        if rule.operator == "gt":
            triggered = current_value > rule.threshold
        elif rule.operator == "lt":
            triggered = current_value < rule.threshold
        elif rule.operator == "eq":
            triggered = abs(current_value - rule.threshold) < 0.001

        if not triggered:
            return None

        # Check if alert already active
        if rule_name in self.active_alerts:
            # Update existing alert
            alert = self.active_alerts[rule_name]
            alert.current_value = current_value
            alert.timestamp = datetime.utcnow()
            return alert

        # Create new alert
        message = (
            f"{rule.name}: {rule.metric} = {current_value} "
            f"{rule.operator} {rule.threshold}"
        )

        alert = Alert(
            rule=rule,
            current_value=current_value,
            message=message,
            metadata={"rule_name": rule_name},
        )

        # Store alert
        self.active_alerts[rule_name] = alert
        self.alert_history.append(alert)

        # Keep history size manageable
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history :]

        # Update rule state
        rule.last_triggered = datetime.utcnow()
        rule.trigger_count += 1

        # Send notifications
        await self.send_alert(alert)

        # Create incident for critical/high severity alerts
        if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
            await self._create_or_update_incident(alert)

        logger.warning(
            f"Alert triggered: {rule.name} - {message}",
            extra={
                "alert_id": alert.id,
                "severity": alert.severity.value,
                "metric": rule.metric,
                "current_value": current_value,
                "threshold": rule.threshold,
            },
        )

        return alert

    def _check_alert_fatigue(self, alert: Alert) -> bool:
        """
        Check if alert should be suppressed due to fatigue prevention

        Returns:
            True if alert should be sent, False if suppressed
        """
        rule_name = alert.rule.name
        now = datetime.utcnow()

        # Get recent notifications for this rule
        recent_notifications = self.notification_timestamps[rule_name]

        # Clean old timestamps (older than 24 hours)
        cutoff = now - timedelta(hours=24)
        recent_notifications = [ts for ts in recent_notifications if ts > cutoff]
        self.notification_timestamps[rule_name] = recent_notifications

        # Check hourly limit
        hour_cutoff = now - timedelta(hours=1)
        hourly_count = sum(1 for ts in recent_notifications if ts > hour_cutoff)
        if hourly_count >= self.max_notifications_per_hour:
            logger.warning(
                f"Alert fatigue: {rule_name} exceeded hourly limit ({hourly_count}/{self.max_notifications_per_hour})"
            )
            return False

        # Check daily limit
        if len(recent_notifications) >= self.max_notifications_per_day:
            logger.warning(
                f"Alert fatigue: {rule_name} exceeded daily limit ({len(recent_notifications)}/{self.max_notifications_per_day})"
            )
            return False

        return True

    def _group_alerts(self, alert: Alert) -> str | None:
        """
        Group similar alerts to prevent duplicate notifications

        Returns:
            Group key if alert should be grouped, None otherwise
        """
        # Group by rule name and severity
        group_key = f"{alert.rule.name}:{alert.severity.value}"

        if group_key not in self.alert_groups:
            self.alert_groups[group_key] = []

        # Check if similar alert was sent recently (within 5 minutes)
        if self.alert_groups[group_key]:
            # Get most recent alert in group
            most_recent_alert_id = self.alert_groups[group_key][-1]
            most_recent_alert = self.active_alerts.get(most_recent_alert_id)

            if most_recent_alert:
                time_diff = (
                    alert.timestamp - most_recent_alert.timestamp
                ).total_seconds()
                if time_diff < 300:  # 5 minutes
                    # Group with existing alert
                    self.alert_groups[group_key].append(alert.id)
                    return group_key

        # New group
        self.alert_groups[group_key] = [alert.id]
        return None

    async def send_alert(self, alert: Alert, force: bool = False) -> None:
        """
        Send alert through configured channels with fatigue prevention

        Args:
            alert: Alert to send
            force: Force send even if fatigue prevention would block
        """
        # Check alert fatigue (unless forced)
        if not force and not self._check_alert_fatigue(alert):
            logger.info(f"Alert suppressed due to fatigue prevention: {alert.id}")
            return

        # Group alerts to prevent duplicates
        group_key = self._group_alerts(alert)
        if group_key and not force:
            logger.info(f"Alert grouped with existing alerts: {group_key}")
            # Still send but with grouped message
            alert.message = f"[Grouped] {alert.message}"

        # Determine channels based on escalation level
        channels = alert.rule.channels.copy()

        # Add escalation channels if alert has escalated
        if alert.escalation_level > 0:
            escalation_policy = self.escalation_policies.get(alert.severity, {})
            escalation_channels = escalation_policy.get("escalation_channels", [])
            channels.extend(escalation_channels)
            channels = list(set(channels))  # Remove duplicates

        # Send through each channel
        for channel in channels:
            handler = self.channel_handlers.get(channel)
            if handler:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(alert)
                    else:
                        handler(alert)

                    # Track notification
                    alert.notification_count += 1
                    self.notification_timestamps[alert.rule.name].append(
                        datetime.utcnow()
                    )

                except Exception as e:
                    logger.error(
                        f"Failed to send alert via {channel.value}: {e}", exc_info=True
                    )
            else:
                logger.warning(f"No handler registered for channel: {channel.value}")

    async def check_escalations(self) -> None:
        """Check and escalate unacknowledged alerts"""
        now = datetime.utcnow()

        for alert_id, alert in list(self.active_alerts.items()):
            if alert.acknowledged or alert.resolved:
                continue

            # Check if alert needs escalation
            escalation_policy = self.escalation_policies.get(alert.severity, {})
            escalate_after = escalation_policy.get("escalate_after_minutes", 60)

            time_since_alert = (now - alert.timestamp).total_seconds() / 60

            if time_since_alert >= escalate_after:
                # Escalate alert
                alert.escalation_level += 1
                logger.warning(
                    f"Alert escalated: {alert.id} (level {alert.escalation_level})",
                    extra={
                        "alert_id": alert.id,
                        "severity": alert.severity.value,
                        "escalation_level": alert.escalation_level,
                        "time_since_alert_minutes": time_since_alert,
                    },
                )

                # Send escalation notification
                await self.send_alert(alert, force=True)

                # Create or update incident if critical/high
                if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
                    await self._create_or_update_incident(alert)

    async def _create_or_update_incident(self, alert: Alert) -> Incident | None:
        """Create or update incident for critical/high severity alerts"""
        # Check if incident already exists for this alert
        if alert.incident_id and alert.incident_id in self.active_incidents:
            incident = self.active_incidents[alert.incident_id]
            if alert.id not in incident.related_alerts:
                incident.related_alerts.append(alert.id)
                incident.updated_at = datetime.utcnow()
            return incident

        # Create new incident
        incident = Incident(
            title=f"{alert.rule.name} - {alert.severity.value.upper()}",
            severity=alert.severity,
            description=alert.message,
        )
        incident.related_alerts = [alert.id]
        incident.metadata = {
            "rule_name": alert.rule.name,
            "metric": alert.rule.metric,
            "current_value": alert.current_value,
            "threshold": alert.rule.threshold,
        }

        self.active_incidents[incident.id] = incident
        alert.incident_id = incident.id

        logger.warning(
            f"Incident created: {incident.id} for alert {alert.id}",
            extra={
                "incident_id": incident.id,
                "alert_id": alert.id,
                "severity": alert.severity.value,
            },
        )

        return incident

    def acknowledge_alert(
        self, alert_id: str, acknowledged_by: str | None = None
    ) -> bool:
        """Acknowledge an alert"""
        for alert in self.active_alerts.values():
            if alert.id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_by = acknowledged_by
                alert.acknowledged_at = datetime.utcnow()
                logger.info(
                    f"Alert acknowledged: {alert_id} by {acknowledged_by}",
                    extra={"alert_id": alert_id, "acknowledged_by": acknowledged_by},
                )
                return True
        return False

    def resolve_alert(self, rule_name: str) -> bool:
        """Resolve an active alert"""
        if rule_name in self.active_alerts:
            alert = self.active_alerts[rule_name]
            alert.resolved = True
            del self.active_alerts[rule_name]
            logger.info(f"Alert resolved: {rule_name}")
            return True
        return False

    def get_active_alerts(self, severity: AlertSeverity | None = None) -> list[Alert]:
        """Get active alerts, optionally filtered by severity"""
        alerts = list(self.active_alerts.values())
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)

    def get_alert_history(
        self, limit: int = 100, severity: AlertSeverity | None = None
    ) -> list[Alert]:
        """Get alert history"""
        alerts = self.alert_history[-limit:] if limit else self.alert_history
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)

    def create_incident(
        self,
        title: str,
        severity: AlertSeverity,
        description: str | None = None,
        related_alert_ids: list[str] | None = None,
    ) -> Incident:
        """Manually create an incident"""
        incident = Incident(title=title, severity=severity, description=description)

        if related_alert_ids:
            incident.related_alerts = related_alert_ids
            # Link alerts to incident
            for alert_id in related_alert_ids:
                if alert_id in self.active_alerts:
                    self.active_alerts[alert_id].incident_id = incident.id

        self.active_incidents[incident.id] = incident
        logger.info(f"Incident created: {incident.id}")
        return incident

    def get_active_incidents(
        self, severity: AlertSeverity | None = None
    ) -> list[Incident]:
        """Get active incidents"""
        incidents = list(self.active_incidents.values())
        if severity:
            incidents = [i for i in incidents if i.severity == severity]
        return sorted(incidents, key=lambda i: i.created_at, reverse=True)

    def resolve_incident(
        self, incident_id: str, resolved_by: str | None = None
    ) -> bool:
        """Resolve an incident"""
        if incident_id in self.active_incidents:
            incident = self.active_incidents[incident_id]
            incident.status = "resolved"
            incident.resolved_at = datetime.utcnow()
            incident.updated_at = datetime.utcnow()

            if resolved_by:
                incident.metadata["resolved_by"] = resolved_by

            # Resolve related alerts
            for alert_id in incident.related_alerts:
                if alert_id in self.active_alerts:
                    self.resolve_alert_by_id(alert_id)

            # Move to history
            self.incident_history.append(incident)
            del self.active_incidents[incident_id]

            logger.info(
                f"Incident resolved: {incident_id} by {resolved_by}",
                extra={"incident_id": incident_id, "resolved_by": resolved_by},
            )
            return True
        return False

    def resolve_alert_by_id(self, alert_id: str) -> bool:
        """Resolve an alert by ID"""
        for rule_name, alert in list(self.active_alerts.items()):
            if alert.id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.utcnow()
                del self.active_alerts[rule_name]
                logger.info(f"Alert resolved: {alert_id}")
                return True
        return False

    def get_fatigue_stats(self) -> dict[str, Any]:
        """Get alert fatigue statistics"""
        stats = {}
        for rule_name, timestamps in self.notification_timestamps.items():
            now = datetime.utcnow()
            hour_cutoff = now - timedelta(hours=1)
            day_cutoff = now - timedelta(hours=24)

            hourly_count = sum(1 for ts in timestamps if ts > hour_cutoff)
            daily_count = sum(1 for ts in timestamps if ts > day_cutoff)

            stats[rule_name] = {
                "hourly_notifications": hourly_count,
                "daily_notifications": daily_count,
                "hourly_limit": self.max_notifications_per_hour,
                "daily_limit": self.max_notifications_per_day,
                "at_hourly_limit": hourly_count >= self.max_notifications_per_hour,
                "at_daily_limit": daily_count >= self.max_notifications_per_day,
            }

        return stats


# Default alert rules
def create_default_alert_rules() -> list[AlertRule]:
    """Create default alert rules"""
    return [
        AlertRule(
            name="high_error_rate",
            metric="error_rate",
            threshold=0.05,  # 5% error rate
            operator="gt",
            severity=AlertSeverity.HIGH,
            channels=[AlertChannel.EMAIL, AlertChannel.SLACK],
            duration=300,  # 5 minutes
            cooldown=600,  # 10 minutes
        ),
        AlertRule(
            name="slow_response_time",
            metric="p95_response_time_ms",
            threshold=200.0,  # 200ms p95
            operator="gt",
            severity=AlertSeverity.MEDIUM,
            channels=[AlertChannel.EMAIL],
            duration=300,
            cooldown=600,
        ),
        AlertRule(
            name="high_memory_usage",
            metric="memory_percent",
            threshold=90.0,  # 90% memory
            operator="gt",
            severity=AlertSeverity.CRITICAL,
            channels=[AlertChannel.EMAIL, AlertChannel.SMS, AlertChannel.PAGERDUTY],
            duration=60,
            cooldown=300,
        ),
        AlertRule(
            name="high_cpu_usage",
            metric="cpu_percent",
            threshold=80.0,  # 80% CPU
            operator="gt",
            severity=AlertSeverity.HIGH,
            channels=[AlertChannel.EMAIL, AlertChannel.SLACK],
            duration=300,
            cooldown=600,
        ),
    ]


# Singleton instance
_alerting_service: AlertingService | None = None


def get_alerting_service() -> AlertingService:
    """Get alerting service instance"""
    global _alerting_service
    if _alerting_service is None:
        _alerting_service = AlertingService()

        # Register default rules
        for rule in create_default_alert_rules():
            _alerting_service.register_rule(rule)

    return _alerting_service
