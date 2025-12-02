"""
Real-time Performance Monitoring & Alerting
Tracks application metrics and triggers alerts
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import deque

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    severity: AlertSeverity
    component: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


@dataclass
class MetricThreshold:
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    comparison: str = "greater"  # "greater", "less", "equal"


class PerformanceMonitor:
    """
    Monitor application performance and trigger alerts
    """
    
    def __init__(self, alert_callback: Optional[Callable] = None):
        self.metrics: Dict[str, deque] = {}
        self.thresholds: Dict[str, MetricThreshold] = {}
        self.alerts: List[Alert] = []
        self.alert_callback = alert_callback
        self.max_metric_history = 1000
        
        # Default thresholds
        self.register_threshold(MetricThreshold(
            metric_name="response_time_ms",
            warning_threshold=1000,
            critical_threshold=3000,
            comparison="greater"
        ))
        
        self.register_threshold(MetricThreshold(
            metric_name="error_rate",
            warning_threshold=0.05,  # 5%
            critical_threshold=0.10,  # 10%
            comparison="greater"
        ))
        
        self.register_threshold(MetricThreshold(
            metric_name="cpu_percent",
            warning_threshold=70,
            critical_threshold=90,
            comparison="greater"
        ))
        
        self.register_threshold(MetricThreshold(
            metric_name="memory_percent",
            warning_threshold=80,
            critical_threshold=95,
            comparison="greater"
        ))
    
    def register_threshold(self, threshold: MetricThreshold):
        """Register a new metric threshold"""
        self.thresholds[threshold.metric_name] = threshold
        logger.info(f"Registered threshold for {threshold.metric_name}")
    
    def record_metric(self, metric_name: str, value: float, metadata: Optional[Dict] = None):
        """Record a metric value and check thresholds"""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = deque(maxlen=self.max_metric_history)
        
        self.metrics[metric_name].append({
            "value": value,
            "timestamp": datetime.now(),
            "metadata": metadata or {}
        })
        
        # Check thresholds
        self._check_threshold(metric_name, value, metadata)
    
    def _check_threshold(self, metric_name: str, value: float, metadata: Optional[Dict]):
        """Check if metric exceeds thresholds"""
        if metric_name not in self.thresholds:
            return
        
        threshold = self.thresholds[metric_name]
        severity = None
        
        if threshold.comparison == "greater":
            if value >= threshold.critical_threshold:
                severity = AlertSeverity.CRITICAL
            elif value >= threshold.warning_threshold:
                severity = AlertSeverity.WARNING
        elif threshold.comparison == "less":
            if value <= threshold.critical_threshold:
                severity = AlertSeverity.CRITICAL
            elif value <= threshold.warning_threshold:
                severity = AlertSeverity.WARNING
        
        if severity:
            alert = Alert(
                severity=severity,
                component=metric_name,
                message=f"{metric_name} is {value} (threshold: {threshold.warning_threshold}/{threshold.critical_threshold})",
                metadata=metadata or {}
            )
            
            self.alerts.append(alert)
            logger.warning(f"Alert triggered: {alert.message}")
            
            if self.alert_callback:
                asyncio.create_task(self.alert_callback(alert))
    
    def get_metric_stats(self, metric_name: str, window_minutes: int = 5) -> Dict:
        """Get statistics for a metric over a time window"""
        if metric_name not in self.metrics:
            return {}
        
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        recent_values = [
            m["value"] for m in self.metrics[metric_name]
            if m["timestamp"] >= cutoff_time
        ]
        
        if not recent_values:
            return {}
        
        return {
            "count": len(recent_values),
            "min": min(recent_values),
            "max": max(recent_values),
            "avg": sum(recent_values) / len(recent_values),
            "latest": recent_values[-1] if recent_values else None
        }
    
    def get_recent_alerts(self, severity: Optional[AlertSeverity] = None, limit: int = 50) -> List[Dict]:
        """Get recent alerts"""
        alerts = self.alerts[-limit:]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return [
            {
                "severity": a.severity.value,
                "component": a.component,
                "message": a.message,
                "timestamp": a.timestamp.isoformat(),
                "metadata": a.metadata
            }
            for a in alerts
        ]
    
    def clear_old_alerts(self, hours: int = 24):
        """Clear alerts older than specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        self.alerts = [a for a in self.alerts if a.timestamp >= cutoff_time]


# Global performance monitor
performance_monitor = PerformanceMonitor()


async def send_alert_notification(alert: Alert):
    """Send alert notification (email, Slack, etc.)"""
    # Implement your notification logic here
    logger.info(f"Alert notification: [{alert.severity.value}] {alert.message}")
    
    # Example: Send to Slack webhook
    # await send_slack_message(alert)
    
    # Example: Send email
    # await send_email_alert(alert)


# Set alert callback
performance_monitor.alert_callback = send_alert_notification
