"""
Marketplace Threshold Service
Monitors analytics metrics and triggers notifications when thresholds are exceeded.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from ..models.analytics_threshold import (
    AnalyticsThreshold,
    ThresholdType,
    ThresholdMetric,
    ThresholdOperator,
)
from ..models.signal_provider import SignalProvider
from ..models.indicator import Indicator
from ..services.marketplace_analytics_service import MarketplaceAnalyticsService
from ..services.notification_service import (
    NotificationService,
    NotificationType,
    NotificationPriority,
)

logger = logging.getLogger(__name__)


class MarketplaceThresholdService:
    """Service for monitoring and checking analytics thresholds"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.analytics_service = MarketplaceAnalyticsService(db)
        self.notification_service = NotificationService(db)

    async def check_all_thresholds(self) -> List[Dict[str, Any]]:
        """
        Check all enabled thresholds and trigger notifications if needed.
        
        Returns:
            List of triggered threshold alerts
        """
        try:
            # Get all enabled thresholds
            result = await self.db.execute(
                select(AnalyticsThreshold).where(
                    AnalyticsThreshold.enabled == True
                )
            )
            thresholds = result.scalars().all()
            
            triggered_alerts = []
            
            for threshold in thresholds:
                try:
                    alert = await self._check_threshold(threshold)
                    if alert:
                        triggered_alerts.append(alert)
                        logger.info(
                            f"Threshold {threshold.id} triggered: {threshold.metric} = {alert.get('current_value')}",
                            extra={
                                "threshold_id": threshold.id,
                                "metric": threshold.metric,
                                "current_value": alert.get("current_value"),
                                "threshold_value": threshold.threshold_value,
                            }
                        )
                except Exception as e:
                    logger.error(
                        f"Error checking threshold {threshold.id}: {e}",
                        exc_info=True,
                        extra={
                            "threshold_id": threshold.id,
                            "threshold_type": threshold.threshold_type,
                            "metric": threshold.metric,
                        }
                    )
                    continue
            
            return triggered_alerts
        except Exception as e:
            logger.error(f"Error checking thresholds: {e}", exc_info=True)
            raise

    async def _check_threshold(
        self, threshold: AnalyticsThreshold
    ) -> Optional[Dict[str, Any]]:
        """Check a single threshold and trigger alert if needed"""
        
        # Check cooldown
        if threshold.last_triggered_at:
            time_since_last = datetime.utcnow() - threshold.last_triggered_at
            if time_since_last.total_seconds() < (threshold.cooldown_minutes * 60):
                return None  # Still in cooldown
        
        # Get current metric value
        current_value = await self._get_metric_value(threshold)
        
        if current_value is None:
            logger.warning(
                f"Could not get metric value for threshold {threshold.id}, metric: {threshold.metric}"
            )
            return None
        
        # Check if threshold is exceeded
        triggered = self._evaluate_threshold(
            current_value, threshold.operator, threshold.threshold_value
        )
        
        if not triggered:
            return None
        
        # Threshold exceeded - trigger notification
        alert = await self._trigger_alert(threshold, current_value)
        
        # Update last triggered timestamp
        threshold.last_triggered_at = datetime.utcnow()
        await self.db.commit()
        
        return alert

    async def _get_metric_value(
        self, threshold: AnalyticsThreshold
    ) -> Optional[float]:
        """Get current value for a metric"""
        try:
            metric = threshold.metric
            threshold_type = threshold.threshold_type
            context = threshold.context or {}
            
            if threshold_type == ThresholdType.PROVIDER.value:
                provider_id = context.get("provider_id")
                if not provider_id:
                    return None
                
                analytics = await self.analytics_service.get_provider_analytics(
                    provider_id
                )
                
                metric_map = {
                    ThresholdMetric.TOTAL_RETURN.value: analytics.get("total_return"),
                    ThresholdMetric.SHARPE_RATIO.value: analytics.get("sharpe_ratio"),
                    ThresholdMetric.WIN_RATE.value: analytics.get("win_rate"),
                    ThresholdMetric.MAX_DRAWDOWN.value: analytics.get("max_drawdown"),
                    ThresholdMetric.PROFIT_FACTOR.value: analytics.get("profit_factor"),
                    ThresholdMetric.AVERAGE_RATING.value: analytics.get("average_rating"),
                    ThresholdMetric.FOLLOWER_COUNT_CHANGE.value: analytics.get("follower_count"),
                }
                
                value = metric_map.get(metric)
                # Ensure value is numeric
                if value is not None:
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        logger.warning(
                            f"Metric value for {metric} is not numeric: {value}",
                            extra={"threshold_id": threshold.id, "metric": metric}
                        )
                        return None
                return None
            
            elif threshold_type == ThresholdType.DEVELOPER.value:
                developer_id = context.get("developer_id")
                if not developer_id:
                    return None
                
                analytics = await self.analytics_service.get_developer_analytics(
                    developer_id
                )
                
                metric_map = {
                    ThresholdMetric.INDICATOR_REVENUE_DROP_PERCENT.value: analytics.get("total_revenue"),
                    ThresholdMetric.INDICATOR_PURCHASE_COUNT_CHANGE.value: analytics.get("total_purchases"),
                    ThresholdMetric.INDICATOR_AVERAGE_RATING.value: analytics.get("average_rating"),
                }
                
                value = metric_map.get(metric)
                if value is not None:
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        logger.warning(
                            f"Metric value for {metric} is not numeric: {value}",
                            extra={"threshold_id": threshold.id, "metric": metric}
                        )
                        return None
                return None
            
            elif threshold_type == ThresholdType.MARKETPLACE_OVERVIEW.value:
                overview = await self.analytics_service.get_marketplace_overview()
                
                if metric == ThresholdMetric.PLATFORM_REVENUE_DROP_PERCENT.value:
                    # Calculate revenue change (would need historical data)
                    copy_trading = overview.get("copy_trading", {})
                    value = copy_trading.get("platform_revenue", 0.0)
                    return float(value) if value is not None else None
                
                elif metric == ThresholdMetric.TOTAL_PROVIDERS_CHANGE.value:
                    copy_trading = overview.get("copy_trading", {})
                    value = copy_trading.get("total_providers", 0)
                    return float(value) if value is not None else None
                
                elif metric == ThresholdMetric.TOTAL_INDICATORS_CHANGE.value:
                    indicators = overview.get("indicators", {})
                    value = indicators.get("total_indicators", 0)
                    return float(value) if value is not None else None
            
            elif threshold_type == ThresholdType.COPY_TRADING.value:
                # For copy trading marketplace-wide metrics
                overview = await self.analytics_service.get_marketplace_overview()
                copy_trading = overview.get("copy_trading", {})
                
                metric_map = {
                    ThresholdMetric.REVENUE_DROP_PERCENT.value: copy_trading.get("platform_revenue", 0.0),
                    ThresholdMetric.TOTAL_PROVIDERS_CHANGE.value: copy_trading.get("total_providers", 0),
                }
                
                value = metric_map.get(metric)
                if value is not None:
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        logger.warning(
                            f"Metric value for {metric} is not numeric: {value}",
                            extra={"threshold_id": threshold.id, "metric": metric}
                        )
                        return None
                return None
            
            elif threshold_type == ThresholdType.INDICATOR_MARKETPLACE.value:
                # For indicator marketplace-wide metrics
                overview = await self.analytics_service.get_marketplace_overview()
                indicators = overview.get("indicators", {})
                
                metric_map = {
                    ThresholdMetric.INDICATOR_REVENUE_DROP_PERCENT.value: indicators.get("platform_revenue", 0.0),
                    ThresholdMetric.TOTAL_INDICATORS_CHANGE.value: indicators.get("total_indicators", 0),
                }
                
                value = metric_map.get(metric)
                if value is not None:
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        logger.warning(
                            f"Metric value for {metric} is not numeric: {value}",
                            extra={"threshold_id": threshold.id, "metric": metric}
                        )
                        return None
                return None
            
            return None
        except Exception as e:
            logger.error(f"Error getting metric value: {e}", exc_info=True)
            return None

    def _evaluate_threshold(
        self, current_value: float, operator: str, threshold_value: float
    ) -> bool:
        """Evaluate if threshold condition is met"""
        if operator == ThresholdOperator.GREATER_THAN.value:
            return current_value > threshold_value
        elif operator == ThresholdOperator.LESS_THAN.value:
            return current_value < threshold_value
        elif operator == ThresholdOperator.EQUALS.value:
            return abs(current_value - threshold_value) < 0.001
        elif operator == ThresholdOperator.GREATER_THAN_OR_EQUAL.value:
            return current_value >= threshold_value
        elif operator == ThresholdOperator.LESS_THAN_OR_EQUAL.value:
            return current_value <= threshold_value
        elif operator == ThresholdOperator.PERCENT_CHANGE_DOWN.value:
            # For percent change, we'd need historical data
            # This is a simplified version
            return current_value < threshold_value
        elif operator == ThresholdOperator.PERCENT_CHANGE_UP.value:
            return current_value > threshold_value
        return False

    async def _trigger_alert(
        self, threshold: AnalyticsThreshold, current_value: float
    ) -> Dict[str, Any]:
        """Trigger notification for threshold alert"""
        try:
            # Determine notification channels
            channels = threshold.notification_channels or {
                "email": True,
                "push": True,
                "in_app": True,
            }
            
            # Build alert message
            title = threshold.name or f"Analytics Threshold Alert: {threshold.metric}"
            message = (
                f"Threshold '{threshold.metric}' has been exceeded. "
                f"Current value: {current_value:.2f}, Threshold: {threshold.threshold_value:.2f}"
            )
            
            if threshold.description:
                message = f"{threshold.description}\n\n{message}"
            
            # Determine priority based on threshold type
            priority = NotificationPriority.MEDIUM
            if threshold.threshold_type in [
                ThresholdType.PROVIDER.value,
                ThresholdType.DEVELOPER.value,
            ]:
                priority = NotificationPriority.HIGH
            
            # Send notification to user if threshold is user-specific
            if threshold.user_id:
                try:
                    notification_sent = await self.notification_service.send_notification(
                        user_id=threshold.user_id,
                        notification_type=NotificationType.SYSTEM_ALERT,
                        title=title,
                        message=message,
                        priority=priority,
                        data={
                            "threshold_id": threshold.id,
                            "metric": threshold.metric,
                            "current_value": current_value,
                            "threshold_value": threshold.threshold_value,
                            "threshold_type": threshold.threshold_type,
                        },
                        send_email=channels.get("email", False),
                    )
                    if notification_sent:
                        logger.info(
                            f"Notification sent for threshold {threshold.id} to user {threshold.user_id}",
                            extra={
                                "threshold_id": threshold.id,
                                "user_id": threshold.user_id,
                                "metric": threshold.metric,
                            }
                        )
                    else:
                        logger.warning(
                            f"Failed to send notification for threshold {threshold.id}",
                            extra={"threshold_id": threshold.id, "user_id": threshold.user_id}
                        )
                except Exception as e:
                    logger.error(
                        f"Error sending notification for threshold {threshold.id}: {e}",
                        exc_info=True,
                        extra={"threshold_id": threshold.id, "user_id": threshold.user_id}
                    )
                    # Don't fail the threshold check if notification fails
                    # The alert is still recorded
            
            # For global thresholds, could send to admins
            # This would require admin user lookup
            
            return {
                "threshold_id": threshold.id,
                "metric": threshold.metric,
                "current_value": current_value,
                "threshold_value": threshold.threshold_value,
                "triggered_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error triggering alert: {e}", exc_info=True)
            raise
