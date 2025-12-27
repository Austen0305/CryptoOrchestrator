"""
Monitoring and Alerting System
Provides real-time monitoring, alerting, and notification capabilities
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert definition"""
    id: str
    level: AlertLevel
    title: str
    message: str
    source: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AlertRule:
    """Alert rule definition"""

    def __init__(
        self,
        name: str,
        condition: Callable,
        level: AlertLevel,
        message: str,
        cooldown: int = 300,  # 5 minutes
    ):
        self.name = name
        self.condition = condition
        self.level = level
        self.message = message
        self.cooldown = cooldown
        self.last_triggered: Optional[datetime] = None

    def should_trigger(self) -> bool:
        """Check if alert should trigger"""
        if self.last_triggered:
            elapsed = (datetime.utcnow() - self.last_triggered).total_seconds()
            if elapsed < self.cooldown:
                return False

        return self.condition()

    def trigger(self):
        """Mark alert as triggered"""
        self.last_triggered = datetime.utcnow()


class MonitoringAlertingSystem:
    """
    Monitoring and alerting system
    
    Features:
    - Real-time monitoring
    - Configurable alert rules
    - Multiple notification channels
    - Alert aggregation
    - Alert history
    - Auto-resolution
    """

    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=10000)
        self.rules: Dict[str, AlertRule] = {}
        self.notifiers: List[Callable] = []
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False

    def register_rule(self, rule: AlertRule):
        """Register an alert rule"""
        self.rules[rule.name] = rule
        logger.info(f"Alert rule registered: {rule.name}")

    def register_notifier(self, notifier: Callable):
        """Register a notification handler"""
        self.notifiers.append(notifier)
        logger.info("Notification handler registered")

    async def start_monitoring(self, interval: int = 60):
        """Start monitoring loop"""
        if self._running:
            return

        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitor_loop(interval))
        logger.info("Monitoring system started")

    async def stop_monitoring(self):
        """Stop monitoring loop"""
        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Monitoring system stopped")

    async def _monitor_loop(self, interval: int):
        """Main monitoring loop"""
        while self._running:
            try:
                # Check all rules
                for rule_name, rule in self.rules.items():
                    if rule.should_trigger():
                        await self._trigger_alert(rule)
                        rule.trigger()

                # Check metrics
                await self._check_metrics()

                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(interval)

    async def _trigger_alert(self, rule: AlertRule):
        """Trigger an alert"""
        import uuid

        alert = Alert(
            id=str(uuid.uuid4()),
            level=rule.level,
            title=rule.name,
            message=rule.message,
            source="monitoring_system",
            timestamp=datetime.utcnow(),
        )

        self.alerts[alert.id] = alert
        self.alert_history.append(alert)

        # Notify
        for notifier in self.notifiers:
            try:
                if asyncio.iscoroutinefunction(notifier):
                    await notifier(alert)
                else:
                    notifier(alert)
            except Exception as e:
                logger.error(f"Error in notifier: {e}")

        logger.warning(f"Alert triggered: {alert.title} - {alert.message}")

    async def _check_metrics(self):
        """Check metrics for anomalies"""
        # Check error rate
        error_rate = self._calculate_error_rate()
        if error_rate > 0.1:  # 10% error rate
            await self._create_metric_alert(
                "high_error_rate",
                AlertLevel.ERROR,
                f"Error rate is {error_rate*100:.1f}%",
            )

        # Check response time
        avg_response_time = self._calculate_avg_response_time()
        if avg_response_time > 1.0:  # 1 second
            await self._create_metric_alert(
                "slow_response_time",
                AlertLevel.WARNING,
                f"Average response time is {avg_response_time:.2f}s",
            )

    def _calculate_error_rate(self) -> float:
        """Calculate error rate from metrics"""
        errors = self.metrics.get("errors", deque())
        total = self.metrics.get("requests", deque())

        if not total:
            return 0.0

        error_count = len([m for m in errors if m.get("status", 200) >= 400])
        total_count = len(total)

        return error_count / total_count if total_count > 0 else 0.0

    def _calculate_avg_response_time(self) -> float:
        """Calculate average response time"""
        response_times = self.metrics.get("response_times", deque())
        if not response_times:
            return 0.0

        times = [m.get("duration", 0) for m in response_times]
        return sum(times) / len(times) if times else 0.0

    async def _create_metric_alert(self, name: str, level: AlertLevel, message: str):
        """Create alert from metric"""
        import uuid

        alert = Alert(
            id=str(uuid.uuid4()),
            level=level,
            title=name,
            message=message,
            source="metrics",
            timestamp=datetime.utcnow(),
        )

        self.alerts[alert.id] = alert
        self.alert_history.append(alert)

    def record_metric(self, name: str, value: Any, metadata: Optional[Dict[str, Any]] = None):
        """Record a metric"""
        self.metrics[name].append({
            "value": value,
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {},
        })

    def get_alerts(
        self,
        level: Optional[AlertLevel] = None,
        resolved: Optional[bool] = None,
        limit: int = 100,
    ) -> List[Alert]:
        """Get alerts"""
        alerts = list(self.alerts.values())

        if level:
            alerts = [a for a in alerts if a.level == level]

        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]

        alerts.sort(key=lambda a: a.timestamp, reverse=True)
        return alerts[:limit]

    def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        if alert_id in self.alerts:
            self.alerts[alert_id].resolved = True
            self.alerts[alert_id].resolved_at = datetime.utcnow()
            logger.info(f"Alert resolved: {alert_id}")

    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        total_alerts = len(self.alerts)
        unresolved = len([a for a in self.alerts.values() if not a.resolved])

        return {
            "total_alerts": total_alerts,
            "unresolved_alerts": unresolved,
            "resolved_alerts": total_alerts - unresolved,
            "alert_rules": len(self.rules),
            "notifiers": len(self.notifiers),
            "metrics_tracked": len(self.metrics),
        }


# Global monitoring system
monitoring_system = MonitoringAlertingSystem()

# Register default alert rules
monitoring_system.register_rule(
    AlertRule(
        name="high_error_rate",
        condition=lambda: False,  # Will be checked in metrics
        level=AlertLevel.ERROR,
        message="Error rate exceeds threshold",
    )
)

monitoring_system.register_rule(
    AlertRule(
        name="slow_response_time",
        condition=lambda: False,  # Will be checked in metrics
        level=AlertLevel.WARNING,
        message="Response time exceeds threshold",
    )
)

