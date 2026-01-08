"""
Real-time Notification Service
Handles push notifications, email alerts, and in-app notifications.
"""

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..repositories.push_subscription_repository import PushSubscriptionRepository
    from ..repositories.user_repository import UserRepository
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.push_subscription_repository import PushSubscriptionRepository
from ..repositories.user_repository import UserRepository
from ..services.email_service import email_service
from ..services.expo_push_service import expo_push_service
from ..services.sms_service import sms_service

# Import websocket manager
try:
    from ..services.websocket_manager import connection_manager as websocket_manager
except ImportError:
    try:
        from ..routes.ws import manager as websocket_manager
    except ImportError:
        # Fallback: create a simple mock
        class MockWebSocketManager:
            async def broadcast(self, channel: str, message: dict):
                logger.warning("WebSocket manager not available, notification not sent")

            async def send_to_client(self, client_id: str, message: dict):
                return False

            async def broadcast_to_user(self, user_id: int, message: dict):
                return False

        websocket_manager = MockWebSocketManager()

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Notification types"""

    TRADE_EXECUTED = "trade_executed"
    TRADE_FAILED = "trade_failed"
    ORDER_FILLED = "order_filled"
    STOP_LOSS_TRIGGERED = "stop_loss_triggered"
    TAKE_PROFIT_TRIGGERED = "take_profit_triggered"
    RISK_ALERT = "risk_alert"
    PORTFOLIO_ALERT = "portfolio_alert"
    BOT_STARTED = "bot_started"
    BOT_STOPPED = "bot_stopped"
    COPY_TRADE_EXECUTED = "copy_trade_executed"
    PRICE_ALERT = "price_alert"
    SYSTEM_ALERT = "system_alert"


class NotificationCategory(str, Enum):
    """Notification categories for filtering"""

    TRADING = "trading"
    RISK = "risk"
    PORTFOLIO = "portfolio"
    BOT = "bot"
    SYSTEM = "system"
    ALERT = "alert"
    COPY_TRADING = "copy_trading"


class NotificationPriority(str, Enum):
    """Notification priority levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationService:
    """Service for sending real-time notifications"""

    # Class-level storage shared across all instances
    # In-memory storage for notifications (can be migrated to DB later)
    # Format: {user_id: [notification_dict, ...]}
    _notifications: dict[str, list[dict[str, Any]]] = {}
    # WebSocket listeners: {user_id: [callback_function, ...]}
    _listeners: dict[str, list[Callable]] = {}

    def __init__(
        self,
        db: AsyncSession,
        user_repository: UserRepository | None = None,
        push_subscription_repository: PushSubscriptionRepository | None = None,
    ):
        # ✅ Repository injected via dependency injection (Service Layer Pattern)
        self.user_repository = user_repository or UserRepository()
        # Note: PushSubscriptionRepository takes db in __init__
        self.push_subscription_repository = (
            push_subscription_repository or PushSubscriptionRepository(db)
        )
        self.db = db  # Keep db for transaction handling

    async def send_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        data: dict[str, Any] | None = None,
        send_email: bool = False,
    ) -> bool:
        """
        Send a notification to a user.

        Args:
            user_id: User ID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            priority: Notification priority
            data: Additional data
            send_email: Whether to send email notification

        Returns:
            True if notification sent successfully
        """
        try:
            # ✅ Data access delegated to repository
            user = await self.user_repository.get_by_id(self.db, user_id)

            if not user:
                logger.warning(
                    f"User {user_id} not found for notification",
                    extra={"user_id": user_id},
                )
                return False

            notification = {
                "id": f"notif_{datetime.now().timestamp()}",
                "user_id": user_id,
                "type": notification_type.value,
                "title": title,
                "message": message,
                "priority": priority.value,
                "data": data or {},
                "timestamp": datetime.now().isoformat(),
                "read": False,
            }

            # Send via WebSocket (real-time)
            try:
                # Try different WebSocket manager methods
                if hasattr(websocket_manager, "broadcast_to_user"):
                    # Use user-based broadcasting (from routes/ws.py)
                    await websocket_manager.broadcast_to_user(
                        user_id, {"type": "notification", **notification}
                    )
                elif hasattr(websocket_manager, "broadcast"):
                    # Use channel-based broadcasting (from services/websocket_manager.py)
                    await websocket_manager.broadcast(
                        channel=f"user:{user_id}",
                        message={"event": "notification", **notification},
                    )
                else:
                    logger.warning("WebSocket manager method not found")
            except Exception as e:
                logger.warning(f"WebSocket notification failed: {e}")

            # Send email if requested
            if send_email and user.email:
                try:
                    email_subject = f"[{priority.value.upper()}] {title}"
                    email_body = f"""
                    {message}
                    
                    {f"Additional Details: {data}" if data else ""}
                    
                    ---
                    CryptoOrchestrator
                    """
                    await email_service.send_email(
                        to=user.email, subject=email_subject, text_content=email_body
                    )
                except Exception as e:
                    logger.warning(f"Email notification failed: {e}")

            # Send SMS if requested and priority is high/critical
            if priority in [NotificationPriority.HIGH, NotificationPriority.CRITICAL]:
                try:
                    # Get user phone number from preferences or user model
                    # For now, check if phone is in metadata
                    phone_number = None
                    if data and data.get("phone_number"):
                        phone_number = data.get("phone_number")
                    elif hasattr(user, "phone_number") and user.phone_number:
                        phone_number = user.phone_number

                    if phone_number and sms_service.enabled:
                        sms_message = f"{title}: {message}"
                        sms_result = await sms_service.send_sms(
                            to_number=phone_number,
                            message=sms_message,
                            priority=priority.value,
                        )
                        if sms_result.get("success"):
                            logger.info(f"SMS notification sent to {phone_number}")
                except Exception as e:
                    logger.warning(f"SMS notification failed: {e}")

            # Send push notification to mobile devices
            try:
                # ✅ Business logic: Map notification type to subscription filter
                notification_type_map = {
                    NotificationType.TRADE_EXECUTED: "trade",
                    NotificationType.TRADE_FAILED: "trade",
                    NotificationType.ORDER_FILLED: "trade",
                    NotificationType.STOP_LOSS_TRIGGERED: "trade",
                    NotificationType.TAKE_PROFIT_TRIGGERED: "trade",
                    NotificationType.BOT_STARTED: "bot",
                    NotificationType.BOT_STOPPED: "bot",
                    NotificationType.RISK_ALERT: "risk",
                    NotificationType.PORTFOLIO_ALERT: "risk",
                    NotificationType.PRICE_ALERT: "price_alert",
                    NotificationType.SYSTEM_ALERT: "system",
                }

                filter_type = notification_type_map.get(notification_type, "system")
                # ✅ Data access delegated to repository
                subscriptions = await self.push_subscription_repository.get_active_subscriptions_for_notification_type(
                    user_id, filter_type
                )

                # ✅ Business logic: Send push notifications to all active subscriptions
                for subscription in subscriptions:
                    if subscription.expo_push_token:
                        # Send via Expo
                        push_result = await expo_push_service.send_push_notification(
                            expo_push_token=subscription.expo_push_token,
                            title=title,
                            body=message,
                            data={
                                "notification_id": notification["id"],
                                "type": notification_type.value,
                                "priority": priority.value,
                                **(data or {}),
                            },
                            priority=(
                                "high"
                                if priority
                                in [
                                    NotificationPriority.HIGH,
                                    NotificationPriority.CRITICAL,
                                ]
                                else "default"
                            ),
                        )

                        # ✅ Data access delegated to repository
                        if push_result.get("success"):
                            await self.push_subscription_repository.update_last_notification_sent(
                                subscription.id
                            )
                        else:
                            error = push_result.get("error", "Unknown error")
                            await self.push_subscription_repository.update_last_notification_sent(
                                subscription.id, error=error
                            )
                            logger.warning(
                                f"Push notification failed for subscription {subscription.id}: {error}",
                                extra={
                                    "subscription_id": subscription.id,
                                    "user_id": user_id,
                                    "error": error,
                                },
                            )
            except Exception as e:
                logger.warning(f"Push notification failed: {e}", exc_info=True)

            logger.info(
                f"Notification sent to user {user_id}: {title}",
                extra={
                    "user_id": user_id,
                    "notification_type": notification_type.value,
                    "priority": priority.value,
                },
            )
            return True

        except Exception as e:
            logger.error(
                f"Error sending notification: {e}",
                exc_info=True,
                extra={
                    "user_id": user_id,
                    "notification_type": notification_type.value,
                },
            )
            return False

    async def send_trade_notification(
        self,
        user_id: int,
        trade_id: int,
        trade_status: str,
        pair: str,
        side: str,
        amount: float,
        price: float,
    ):
        """Send trade execution notification"""
        if trade_status == "completed":
            await self.send_notification(
                user_id=user_id,
                notification_type=NotificationType.TRADE_EXECUTED,
                title="Trade Executed",
                message=f"Your {side} order for {amount} {pair} at {price} has been executed.",
                priority=NotificationPriority.HIGH,
                data={
                    "trade_id": trade_id,
                    "pair": pair,
                    "side": side,
                    "amount": amount,
                    "price": price,
                },
            )
        elif trade_status == "failed":
            await self.send_notification(
                user_id=user_id,
                notification_type=NotificationType.TRADE_FAILED,
                title="Trade Failed",
                message=f"Your {side} order for {amount} {pair} failed to execute.",
                priority=NotificationPriority.HIGH,
                data={"trade_id": trade_id},
            )

    async def send_risk_alert(
        self, user_id: int, alert_type: str, message: str, severity: str = "medium"
    ):
        """Send risk management alert"""
        priority_map = {
            "low": NotificationPriority.LOW,
            "medium": NotificationPriority.MEDIUM,
            "high": NotificationPriority.HIGH,
            "critical": NotificationPriority.CRITICAL,
        }

        await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.RISK_ALERT,
            title=f"Risk Alert: {alert_type}",
            message=message,
            priority=priority_map.get(severity, NotificationPriority.MEDIUM),
            data={"alert_type": alert_type, "severity": severity},
            send_email=(severity in ["high", "critical"]),
        )

    async def send_price_alert(
        self,
        user_id: int,
        pair: str,
        target_price: float,
        current_price: float,
        direction: str,  # "above" or "below"
    ):
        """Send price alert notification"""
        await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.PRICE_ALERT,
            title="Price Alert",
            message=f"{pair} price is now {direction} your target of {target_price} (current: {current_price})",
            priority=NotificationPriority.MEDIUM,
            data={
                "pair": pair,
                "target_price": target_price,
                "current_price": current_price,
                "direction": direction,
            },
        )

    async def create_notification(
        self,
        user_id: str,
        message: str,
        level: str = "info",
        title: str | None = None,
        category: NotificationCategory | None = None,
        priority: NotificationPriority | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create and store a notification"""
        notification_id = str(uuid.uuid4())
        notification = {
            "id": notification_id,
            "user_id": user_id,
            "type": level,
            "title": title or message[:50],
            "message": message,
            "category": (
                category.value if category else NotificationCategory.SYSTEM.value
            ),
            "priority": (
                priority.value if priority else NotificationPriority.MEDIUM.value
            ),
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
            "read": False,
            "created_at": datetime.now().timestamp(),
        }

        # Store in memory
        if user_id not in self._notifications:
            self._notifications[user_id] = []
        self._notifications[user_id].insert(0, notification)  # Most recent first

        # Keep only last 1000 notifications per user
        if len(self._notifications[user_id]) > 1000:
            self._notifications[user_id] = self._notifications[user_id][:1000]

        # Send via WebSocket if listeners exist
        if user_id in self._listeners:
            for listener in self._listeners[user_id]:
                try:
                    await listener(notification)
                except Exception as e:
                    logger.warning(f"Failed to notify listener: {e}")

        # Also send via send_notification for WebSocket broadcast
        try:
            user_id_int = int(user_id) if user_id.isdigit() else None
            if user_id_int:
                await self.send_notification(
                    user_id=user_id_int,
                    notification_type=NotificationType.SYSTEM_ALERT,
                    title=notification["title"],
                    message=message,
                    priority=priority or NotificationPriority.MEDIUM,
                    data=data,
                )
        except Exception as e:
            logger.warning(f"Failed to send notification via WebSocket: {e}")

        return notification

    async def get_recent_notifications(
        self,
        user_id: str,
        limit: int = 50,
        category: NotificationCategory | None = None,
        unread_only: bool = False,
        priority_filter: list[NotificationPriority] | None = None,
    ) -> list[dict[str, Any]]:
        """Get recent notifications for a user"""
        if user_id not in self._notifications:
            return []

        notifications = self._notifications[user_id].copy()

        # Apply filters
        if category:
            notifications = [
                n for n in notifications if n.get("category") == category.value
            ]
        if unread_only:
            notifications = [n for n in notifications if not n.get("read", False)]
        if priority_filter:
            priority_values = [p.value for p in priority_filter]
            notifications = [
                n for n in notifications if n.get("priority") in priority_values
            ]

        return notifications[:limit]

    async def mark_as_read(self, user_id: str, notification_id: int) -> bool:
        """Mark a notification as read"""
        if user_id not in self._notifications:
            return False

        # Find notification by ID (can be int or string)
        for notification in self._notifications[user_id]:
            if str(notification.get("id")) == str(notification_id):
                notification["read"] = True
                notification["read_at"] = datetime.now().isoformat()
                return True

        return False

    async def mark_all_as_read(
        self, user_id: str, category: NotificationCategory | None = None
    ) -> int:
        """Mark all notifications as read, optionally filtered by category"""
        if user_id not in self._notifications:
            return 0

        count = 0
        for notification in self._notifications[user_id]:
            if category and notification.get("category") != category.value:
                continue
            if not notification.get("read", False):
                notification["read"] = True
                notification["read_at"] = datetime.now().isoformat()
                count += 1

        return count

    async def delete_notification(self, user_id: str, notification_id: int) -> bool:
        """Delete a notification"""
        if user_id not in self._notifications:
            return False

        # Find and remove notification
        original_count = len(self._notifications[user_id])
        self._notifications[user_id] = [
            n
            for n in self._notifications[user_id]
            if str(n.get("id")) != str(notification_id)
        ]

        return len(self._notifications[user_id]) < original_count

    async def get_unread_count(
        self,
        user_id: str,
        category: NotificationCategory | None = None,
        priority_filter: list[NotificationPriority] | None = None,
    ) -> int:
        """Get count of unread notifications"""
        if user_id not in self._notifications:
            return 0

        notifications = [
            n for n in self._notifications[user_id] if not n.get("read", False)
        ]

        if category:
            notifications = [
                n for n in notifications if n.get("category") == category.value
            ]
        if priority_filter:
            priority_values = [p.value for p in priority_filter]
            notifications = [
                n for n in notifications if n.get("priority") in priority_values
            ]

        return len(notifications)

    async def get_notification_stats(self, user_id: str) -> dict[str, Any]:
        """Get notification statistics for a user"""
        if user_id not in self._notifications:
            return {
                "total": 0,
                "unread": 0,
                "by_category": {},
                "by_priority": {},
            }

        notifications = self._notifications[user_id]
        unread = [n for n in notifications if not n.get("read", False)]

        # Count by category
        by_category: dict[str, int] = {}
        by_priority: dict[str, int] = {}

        for notification in notifications:
            category = notification.get("category", "unknown")
            priority = notification.get("priority", "medium")
            by_category[category] = by_category.get(category, 0) + 1
            by_priority[priority] = by_priority.get(priority, 0) + 1

        return {
            "total": len(notifications),
            "unread": len(unread),
            "by_category": by_category,
            "by_priority": by_priority,
        }

    async def broadcast_notification(
        self,
        user_ids: list[str],
        message: str,
        level: str = "info",
        title: str | None = None,
        category: NotificationCategory | None = None,
        priority: NotificationPriority | None = None,
        data: dict[str, Any] | None = None,
    ) -> int:
        """Broadcast notification to multiple users"""
        count = 0
        for user_id in user_ids:
            try:
                await self.create_notification(
                    user_id=user_id,
                    message=message,
                    level=level,
                    title=title,
                    category=category,
                    priority=priority,
                    data=data,
                )
                count += 1
            except Exception as e:
                logger.warning(f"Failed to broadcast to user {user_id}: {e}")

        return count

    async def add_listener(self, user_id: str, callback: Callable) -> None:
        """Add a WebSocket listener for real-time notifications"""
        if user_id not in self._listeners:
            self._listeners[user_id] = []
        if callback not in self._listeners[user_id]:
            self._listeners[user_id].append(callback)

    async def remove_listener(self, user_id: str, callback: Callable) -> None:
        """Remove a WebSocket listener"""
        if user_id in self._listeners:
            if callback in self._listeners[user_id]:
                self._listeners[user_id].remove(callback)
            if not self._listeners[user_id]:
                del self._listeners[user_id]
