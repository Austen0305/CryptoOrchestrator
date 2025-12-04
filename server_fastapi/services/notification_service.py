"""
Real-time Notification Service
Handles push notifications, email alerts, and in-app notifications.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..models.user import User
from ..services.email_service import email_service
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

    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        data: Optional[Dict[str, Any]] = None,
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
            # Get user
            user_stmt = select(User).where(User.id == user_id)
            user_result = await self.db.execute(user_stmt)
            user = user_result.scalar_one_or_none()

            if not user:
                logger.warning(f"User {user_id} not found for notification")
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
                    
                    {f'Additional Details: {data}' if data else ''}
                    
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

            logger.info(f"Notification sent to user {user_id}: {title}")
            return True

        except Exception as e:
            logger.error(f"Error sending notification: {e}", exc_info=True)
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
