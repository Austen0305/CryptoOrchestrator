"""
Real-time notification system for trading events.

Provides comprehensive notification infrastructure for trade executions,
bot status changes, performance alerts, and system events.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Set, Optional, Any
from datetime import datetime
from enum import Enum
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationType(str, Enum):
    """Types of notifications."""
    TRADE_EXECUTED = "trade_executed"
    BOT_STARTED = "bot_started"
    BOT_STOPPED = "bot_stopped"
    BOT_ERROR = "bot_error"
    PROFIT_ALERT = "profit_alert"
    LOSS_ALERT = "loss_alert"
    BALANCE_LOW = "balance_low"
    PRICE_ALERT = "price_alert"
    SYSTEM_ALERT = "system_alert"


class Notification(BaseModel):
    """Notification model."""
    id: str = Field(..., description="Unique notification ID")
    type: NotificationType
    priority: NotificationPriority
    title: str = Field(..., max_length=200)
    message: str = Field(..., max_length=1000)
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    read: bool = False
    user_id: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "notif_123",
                "type": "trade_executed",
                "priority": "high",
                "title": "Trade Executed",
                "message": "Buy order for 0.1 BTC/USDT filled at $45,000",
                "data": {
                    "symbol": "BTC/USDT",
                    "side": "buy",
                    "amount": 0.1,
                    "price": 45000
                },
                "timestamp": "2025-12-02T20:00:00Z",
                "read": False
            }
        }
    }


class NotificationManager:
    """
    Manages WebSocket connections and notification delivery.
    
    Handles user subscriptions, notification broadcasting, and
    connection lifecycle management.
    """
    
    def __init__(self):
        """Initialize the notification manager."""
        # user_id -> Set[WebSocket]
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
        # Store recent notifications for new connections
        self.recent_notifications: Dict[str, List[Notification]] = {}
        self.max_recent = 50
        
    async def connect(self, websocket: WebSocket, user_id: str):
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            user_id: User identifier
        """
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        logger.info(f"User {user_id} connected to notifications")
        
        # Send recent notifications to new connection
        if user_id in self.recent_notifications:
            for notification in self.recent_notifications[user_id][-10:]:
                await self._send_notification(websocket, notification)
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            user_id: User identifier
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
        logger.info(f"User {user_id} disconnected from notifications")
    
    async def broadcast_to_user(
        self,
        user_id: str,
        notification: Notification
    ):
        """
        Broadcast a notification to all of a user's connections.
        
        Args:
            user_id: User identifier
            notification: Notification to send
        """
        # Store in recent notifications
        if user_id not in self.recent_notifications:
            self.recent_notifications[user_id] = []
        
        self.recent_notifications[user_id].append(notification)
        
        # Keep only recent notifications
        if len(self.recent_notifications[user_id]) > self.max_recent:
            self.recent_notifications[user_id] = \
                self.recent_notifications[user_id][-self.max_recent:]
        
        # Send to all active connections
        if user_id in self.active_connections:
            disconnected = set()
            
            for connection in self.active_connections[user_id]:
                try:
                    await self._send_notification(connection, notification)
                except Exception as e:
                    logger.error(f"Error sending notification: {e}")
                    disconnected.add(connection)
            
            # Clean up disconnected clients
            for connection in disconnected:
                self.disconnect(connection, user_id)
    
    async def broadcast_to_all(self, notification: Notification):
        """
        Broadcast a notification to all connected users.
        
        Args:
            notification: Notification to send
        """
        for user_id in list(self.active_connections.keys()):
            await self.broadcast_to_user(user_id, notification)
    
    async def _send_notification(
        self,
        websocket: WebSocket,
        notification: Notification
    ):
        """
        Send a notification through a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            notification: Notification to send
        """
        await websocket.send_json({
            "type": "notification",
            "data": notification.model_dump()
        })
    
    def get_connection_count(self, user_id: Optional[str] = None) -> int:
        """
        Get the number of active connections.
        
        Args:
            user_id: Optional user ID to check specific user
            
        Returns:
            Connection count
        """
        if user_id:
            return len(self.active_connections.get(user_id, set()))
        return sum(len(conns) for conns in self.active_connections.values())


# Global notification manager instance
notification_manager = NotificationManager()


@router.websocket("/ws/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    user_id: str  # In production, get from JWT token
):
    """
    WebSocket endpoint for real-time notifications.
    
    Args:
        websocket: WebSocket connection
        user_id: User identifier
    """
    await notification_manager.connect(websocket, user_id)
    
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            
            # Handle client messages (e.g., mark as read)
            try:
                message = json.loads(data)
                
                if message.get("action") == "mark_read":
                    notification_id = message.get("notification_id")
                    # TODO: Mark notification as read in database
                    logger.info(f"User {user_id} marked {notification_id} as read")
                    
                elif message.get("action") == "ping":
                    # Respond to ping
                    await websocket.send_json({"type": "pong"})
                    
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from user {user_id}: {data}")
                
    except WebSocketDisconnect:
        notification_manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        notification_manager.disconnect(websocket, user_id)


@router.get("/stats")
async def get_notification_stats():
    """
    Get notification system statistics.
    
    Returns:
        Statistics about active connections
    """
    return {
        "total_connections": notification_manager.get_connection_count(),
        "active_users": len(notification_manager.active_connections),
        "recent_notifications_cached": sum(
            len(notifs) 
            for notifs in notification_manager.recent_notifications.values()
        )
    }


# Helper functions for creating notifications

def create_trade_notification(
    user_id: str,
    symbol: str,
    side: str,
    amount: float,
    price: float,
    profit: Optional[float] = None
) -> Notification:
    """
    Create a trade execution notification.
    
    Args:
        user_id: User ID
        symbol: Trading symbol
        side: buy or sell
        amount: Trade amount
        price: Execution price
        profit: Profit/loss amount
        
    Returns:
        Notification object
    """
    message = f"{side.capitalize()} order for {amount} {symbol} filled at ${price:,.2f}"
    
    if profit is not None:
        profit_text = f"+${profit:,.2f}" if profit > 0 else f"-${abs(profit):,.2f}"
        message += f" ({profit_text})"
    
    return Notification(
        id=f"trade_{datetime.utcnow().timestamp()}",
        type=NotificationType.TRADE_EXECUTED,
        priority=NotificationPriority.HIGH,
        title="Trade Executed",
        message=message,
        data={
            "symbol": symbol,
            "side": side,
            "amount": amount,
            "price": price,
            "profit": profit
        },
        user_id=user_id
    )


def create_bot_notification(
    user_id: str,
    bot_id: str,
    bot_name: str,
    action: str,
    priority: NotificationPriority = NotificationPriority.MEDIUM
) -> Notification:
    """
    Create a bot status notification.
    
    Args:
        user_id: User ID
        bot_id: Bot ID
        bot_name: Bot name
        action: started, stopped, or error
        priority: Notification priority
        
    Returns:
        Notification object
    """
    notification_types = {
        "started": NotificationType.BOT_STARTED,
        "stopped": NotificationType.BOT_STOPPED,
        "error": NotificationType.BOT_ERROR
    }
    
    return Notification(
        id=f"bot_{bot_id}_{datetime.utcnow().timestamp()}",
        type=notification_types.get(action, NotificationType.SYSTEM_ALERT),
        priority=priority,
        title=f"Bot {action.capitalize()}",
        message=f"Bot '{bot_name}' has been {action}",
        data={
            "bot_id": bot_id,
            "bot_name": bot_name,
            "action": action
        },
        user_id=user_id
    )


def create_price_alert_notification(
    user_id: str,
    symbol: str,
    current_price: float,
    alert_price: float,
    condition: str
) -> Notification:
    """
    Create a price alert notification.
    
    Args:
        user_id: User ID
        symbol: Trading symbol
        current_price: Current price
        alert_price: Alert trigger price
        condition: above or below
        
    Returns:
        Notification object
    """
    return Notification(
        id=f"price_{symbol}_{datetime.utcnow().timestamp()}",
        type=NotificationType.PRICE_ALERT,
        priority=NotificationPriority.HIGH,
        title=f"Price Alert: {symbol}",
        message=f"{symbol} is now ${current_price:,.2f} ({condition} ${alert_price:,.2f})",
        data={
            "symbol": symbol,
            "current_price": current_price,
            "alert_price": alert_price,
            "condition": condition
        },
        user_id=user_id
    )


# Export the notification manager for use in other modules
__all__ = [
    'router',
    'notification_manager',
    'Notification',
    'NotificationPriority',
    'NotificationType',
    'create_trade_notification',
    'create_bot_notification',
    'create_price_alert_notification'
]
