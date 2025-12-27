"""
Smart Alerts Service - AI-powered alert system
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import logging
import asyncio

logger = logging.getLogger(__name__)


class AlertPriority(str, Enum):
    """Alert priority levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Alert types"""

    PRICE = "price"
    VOLUME = "volume"
    TECHNICAL = "technical"
    RISK = "risk"
    PERFORMANCE = "performance"
    MARKET = "market"
    PORTFOLIO = "portfolio"


class AlertRule(BaseModel):
    """Alert rule configuration"""

    id: str
    name: str
    type: AlertType
    priority: AlertPriority
    enabled: bool = True
    conditions: Dict[str, Any]
    actions: List[str]  # e.g., ["email", "sms", "webhook", "push"]
    cooldown_seconds: int = 3600  # Prevent duplicate alerts


class SmartAlert(BaseModel):
    """Smart alert"""

    id: str
    rule_id: str
    rule_name: str
    type: AlertType
    priority: AlertPriority
    message: str
    data: Dict[str, Any]
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None


class SmartAlertsService:
    """Smart alerts service with AI-powered alerting"""

    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, SmartAlert] = {}
        self.alert_history: List[SmartAlert] = []
        self.last_triggered: Dict[str, datetime] = {}
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        logger.info("Smart Alerts Service initialized")

    async def create_rule(self, rule: AlertRule) -> bool:
        """Create a new alert rule"""
        try:
            self.rules[rule.id] = rule

            # Start monitoring if enabled
            if rule.enabled:
                await self.start_monitoring(rule.id)

            logger.info(f"Created alert rule: {rule.name} (ID: {rule.id})")
            return True

        except Exception as e:
            logger.error(f"Error creating alert rule: {e}")
            return False

    async def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update an alert rule"""
        try:
            if rule_id not in self.rules:
                logger.warning(f"Alert rule not found: {rule_id}")
                return False

            rule = self.rules[rule_id]

            # Update rule fields
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)

            # Restart monitoring if enabled changed
            if "enabled" in updates:
                if updates["enabled"]:
                    await self.start_monitoring(rule_id)
                else:
                    await self.stop_monitoring(rule_id)

            logger.info(f"Updated alert rule: {rule_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating alert rule: {e}")
            return False

    async def delete_rule(self, rule_id: str) -> bool:
        """Delete an alert rule"""
        try:
            if rule_id not in self.rules:
                return False

            await self.stop_monitoring(rule_id)
            del self.rules[rule_id]

            logger.info(f"Deleted alert rule: {rule_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting alert rule: {e}")
            return False

    async def start_monitoring(self, rule_id: str) -> bool:
        """Start monitoring for an alert rule"""
        try:
            if rule_id in self.monitoring_tasks:
                return False

            rule = self.rules.get(rule_id)
            if not rule or not rule.enabled:
                return False

            self.monitoring_tasks[rule_id] = asyncio.create_task(
                self._monitor_rule(rule_id, rule)
            )

            logger.info(f"Started monitoring for alert rule: {rule_id}")
            return True

        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
            return False

    async def stop_monitoring(self, rule_id: str) -> bool:
        """Stop monitoring for an alert rule"""
        try:
            if rule_id in self.monitoring_tasks:
                self.monitoring_tasks[rule_id].cancel()
                try:
                    await self.monitoring_tasks[rule_id]
                except asyncio.CancelledError:
                    pass
                del self.monitoring_tasks[rule_id]

                logger.info(f"Stopped monitoring for alert rule: {rule_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}")
            return False

    async def _monitor_rule(self, rule_id: str, rule: AlertRule) -> None:
        """Monitor rule conditions and trigger alerts"""
        check_interval = 60  # Check every minute

        while True:
            try:
                if not rule.enabled:
                    await asyncio.sleep(check_interval)
                    continue

                # Check cooldown
                if rule_id in self.last_triggered:
                    time_since_last = (
                        datetime.utcnow() - self.last_triggered[rule_id]
                    ).total_seconds()
                    if time_since_last < rule.cooldown_seconds:
                        await asyncio.sleep(check_interval)
                        continue

                # Evaluate rule conditions
                should_alert = await self._evaluate_conditions(rule)

                if should_alert:
                    await self._trigger_alert(rule)
                    self.last_triggered[rule_id] = datetime.utcnow()

                await asyncio.sleep(check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring rule {rule_id}: {e}")
                await asyncio.sleep(check_interval)

    async def _evaluate_conditions(self, rule: AlertRule) -> bool:
        """Evaluate alert rule conditions"""
        conditions = rule.conditions
        alert_type = rule.type

        # Mock implementation - would evaluate actual conditions
        if alert_type == AlertType.PRICE:
            # Check price conditions
            threshold = conditions.get("threshold", 0)
            current_price = 50000  # Mock current price

            if conditions.get("operator") == "above" and current_price > threshold:
                return True
            elif conditions.get("operator") == "below" and current_price < threshold:
                return True

        elif alert_type == AlertType.TECHNICAL:
            # Check technical indicator conditions
            indicator = conditions.get("indicator")
            value = conditions.get("value", 0)

            # Mock indicator values
            if indicator == "RSI":
                rsi_value = 65  # Mock RSI
                if conditions.get("operator") == "above" and rsi_value > value:
                    return True
                elif conditions.get("operator") == "below" and rsi_value < value:
                    return True

        elif alert_type == AlertType.RISK:
            # Check risk conditions
            risk_metric = conditions.get("metric")
            threshold = conditions.get("threshold", 0)

            # Mock risk metrics
            if risk_metric == "drawdown":
                drawdown = 0.08  # Mock drawdown
                if drawdown > threshold:
                    return True

        elif alert_type == AlertType.PERFORMANCE:
            # Check performance conditions
            metric = conditions.get("metric")
            threshold = conditions.get("threshold", 0)

            # Mock performance metrics
            if metric == "returns":
                returns = 0.05  # Mock returns
                if returns < threshold:
                    return True

        return False

    async def _trigger_alert(self, rule: AlertRule) -> None:
        """Trigger an alert"""
        try:
            alert_id = f"alert_{rule.id}_{int(datetime.utcnow().timestamp())}"

            # Generate alert message
            message = self._generate_alert_message(rule)

            # Generate alert data
            data = await self._generate_alert_data(rule)

            alert = SmartAlert(
                id=alert_id,
                rule_id=rule.id,
                rule_name=rule.name,
                type=rule.type,
                priority=rule.priority,
                message=message,
                data=data,
            )

            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)

            # Keep only last 1000 alerts in history
            if len(self.alert_history) > 1000:
                self.alert_history = self.alert_history[-1000:]

            # Execute alert actions
            await self._execute_actions(alert, rule.actions)

            logger.warning(f"Alert triggered: {rule.name} ({alert_id})")

        except Exception as e:
            logger.error(f"Error triggering alert: {e}")

    def _generate_alert_message(self, rule: AlertRule) -> str:
        """Generate alert message"""
        alert_type = rule.type.value
        conditions = rule.conditions

        if alert_type == "price":
            operator = conditions.get("operator", "above")
            threshold = conditions.get("threshold", 0)
            return f"Price {operator} ${threshold:,.2f}"

        elif alert_type == "technical":
            indicator = conditions.get("indicator", "indicator")
            operator = conditions.get("operator", "above")
            value = conditions.get("value", 0)
            return f"{indicator} {operator} {value}"

        elif alert_type == "risk":
            metric = conditions.get("metric", "metric")
            threshold = conditions.get("threshold", 0)
            return f"{metric} exceeds threshold: {threshold}"

        elif alert_type == "performance":
            metric = conditions.get("metric", "metric")
            threshold = conditions.get("threshold", 0)
            return f"{metric} below threshold: {threshold}"

        return f"Alert: {rule.name}"

    async def _generate_alert_data(self, rule: AlertRule) -> Dict[str, Any]:
        """Generate alert data"""
        # Mock implementation - would gather actual data
        return {
            "rule_id": rule.id,
            "conditions": rule.conditions,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _execute_actions(self, alert: SmartAlert, actions: List[str]) -> None:
        """Execute alert actions"""
        for action in actions:
            try:
                if action == "email":
                    # Send email notification
                    logger.info(f"Sending email alert: {alert.id}")
                elif action == "sms":
                    # Send SMS notification
                    logger.info(f"Sending SMS alert: {alert.id}")
                elif action == "webhook":
                    # Send webhook notification
                    logger.info(f"Sending webhook alert: {alert.id}")
                elif action == "push":
                    # Send push notification
                    logger.info(f"Sending push alert: {alert.id}")
            except Exception as e:
                logger.error(
                    f"Error executing action {action} for alert {alert.id}: {e}"
                )

    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.acknowledged = True
                alert.acknowledged_at = datetime.utcnow()

                # Remove from active alerts
                del self.active_alerts[alert_id]

                logger.info(f"Alert acknowledged: {alert_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}")
            return False

    def get_active_alerts(
        self, priority: Optional[AlertPriority] = None
    ) -> List[SmartAlert]:
        """Get active alerts"""
        alerts = list(self.active_alerts.values())

        if priority:
            alerts = [a for a in alerts if a.priority == priority]

        return alerts

    def get_alert_history(
        self, rule_id: Optional[str] = None, limit: int = 100
    ) -> List[SmartAlert]:
        """Get alert history"""
        history = self.alert_history

        if rule_id:
            history = [a for a in history if a.rule_id == rule_id]

        return history[-limit:] if history else []


# Global service instance
smart_alerts_service = SmartAlertsService()
