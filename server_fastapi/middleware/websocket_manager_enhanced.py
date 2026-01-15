"""
Enhanced WebSocket Connection Manager
Manages WebSocket connections with connection pooling and monitoring
"""

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


@dataclass
class WebSocketConnection:
    """WebSocket connection metadata"""

    websocket: WebSocket
    user_id: str | None = None
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    message_count: int = 0
    subscription_topics: set[str] = field(default_factory=set)


class EnhancedWebSocketManager:
    """
    Enhanced WebSocket connection manager with:
    - Connection pooling
    - Subscription management
    - Heartbeat/ping-pong
    - Connection monitoring
    - Automatic cleanup
    """

    def __init__(
        self,
        heartbeat_interval: int = 30,
        connection_timeout: int = 300,
        max_connections_per_user: int = 5,
    ):
        self.active_connections: dict[str, WebSocketConnection] = {}
        self.user_connections: dict[str, set[str]] = defaultdict(set)
        self.topic_subscriptions: dict[str, set[str]] = defaultdict(set)

        self.heartbeat_interval = heartbeat_interval
        self.connection_timeout = connection_timeout
        self.max_connections_per_user = max_connections_per_user

        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "disconnections": 0,
        }

        # Start background tasks
        self._heartbeat_task: asyncio.Task | None = None
        self._cleanup_task: asyncio.Task | None = None

    async def connect(
        self, websocket: WebSocket, connection_id: str, user_id: str | None = None
    ):
        """Accept and register WebSocket connection"""
        await websocket.accept()

        connection = WebSocketConnection(
            websocket=websocket,
            user_id=user_id,
        )

        self.active_connections[connection_id] = connection

        if user_id:
            self.user_connections[user_id].add(connection_id)

            # Check connection limit
            if len(self.user_connections[user_id]) > self.max_connections_per_user:
                # Close oldest connection
                oldest = min(
                    self.user_connections[user_id],
                    key=lambda cid: self.active_connections[cid].connected_at,
                )
                await self.disconnect(oldest)

        self.stats["total_connections"] += 1
        self.stats["active_connections"] = len(self.active_connections)

        logger.info(f"WebSocket connected: {connection_id} (user: {user_id})")

        # Start background tasks if not running
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def disconnect(self, connection_id: str):
        """Disconnect and cleanup WebSocket connection"""
        if connection_id not in self.active_connections:
            return

        connection = self.active_connections[connection_id]

        try:
            await connection.websocket.close()
        except Exception as e:
            logger.debug(f"Error closing WebSocket {connection_id}: {e}")

        # Remove from subscriptions
        for topic in connection.subscription_topics:
            self.topic_subscriptions[topic].discard(connection_id)

        # Remove from user connections
        if connection.user_id:
            self.user_connections[connection.user_id].discard(connection_id)

        del self.active_connections[connection_id]

        self.stats["active_connections"] = len(self.active_connections)
        self.stats["disconnections"] += 1

        logger.info(f"WebSocket disconnected: {connection_id}")

    async def send_personal_message(self, message: dict, connection_id: str):
        """Send message to specific connection"""
        if connection_id not in self.active_connections:
            logger.warning(f"Connection {connection_id} not found")
            return

        connection = self.active_connections[connection_id]

        try:
            await connection.websocket.send_json(message)
            connection.last_activity = datetime.now(UTC)
            connection.message_count += 1
            self.stats["messages_sent"] += 1
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            await self.disconnect(connection_id)

    async def broadcast(self, message: dict, topic: str | None = None):
        """Broadcast message to all connections or topic subscribers"""
        if topic:
            connection_ids = self.topic_subscriptions.get(topic, set()).copy()
        else:
            connection_ids = list(self.active_connections.keys())

        disconnected = []

        for connection_id in connection_ids:
            if connection_id in self.active_connections:
                try:
                    await self.send_personal_message(message, connection_id)
                except Exception:
                    disconnected.append(connection_id)

        # Cleanup disconnected
        for connection_id in disconnected:
            await self.disconnect(connection_id)

    async def subscribe(self, connection_id: str, topic: str):
        """Subscribe connection to a topic"""
        if connection_id in self.active_connections:
            self.active_connections[connection_id].subscription_topics.add(topic)
            self.topic_subscriptions[topic].add(connection_id)
            logger.debug(f"Connection {connection_id} subscribed to {topic}")

    async def unsubscribe(self, connection_id: str, topic: str):
        """Unsubscribe connection from a topic"""
        if connection_id in self.active_connections:
            self.active_connections[connection_id].subscription_topics.discard(topic)
            self.topic_subscriptions[topic].discard(connection_id)
            logger.debug(f"Connection {connection_id} unsubscribed from {topic}")

    async def _heartbeat_loop(self):
        """Send heartbeat/ping to all connections"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                # Send ping to all connections
                for connection_id, connection in list(self.active_connections.items()):
                    try:
                        await connection.websocket.send_json(
                            {"type": "ping", "timestamp": time.time()}
                        )
                    except Exception:
                        await self.disconnect(connection_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")

    async def _cleanup_loop(self):
        """Cleanup stale connections"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                cutoff = datetime.now(UTC) - timedelta(seconds=self.connection_timeout)
                stale = [
                    cid
                    for cid, conn in self.active_connections.items()
                    if conn.last_activity < cutoff
                ]

                for connection_id in stale:
                    logger.info(f"Cleaning up stale connection: {connection_id}")
                    await self.disconnect(connection_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get WebSocket statistics"""
        return {
            **self.stats,
            "topics": len(self.topic_subscriptions),
            "users_connected": len(self.user_connections),
        }

    def get_connection_info(self, connection_id: str) -> dict[str, Any] | None:
        """Get information about a connection"""
        if connection_id not in self.active_connections:
            return None

        conn = self.active_connections[connection_id]
        return {
            "connection_id": connection_id,
            "user_id": conn.user_id,
            "connected_at": conn.connected_at.isoformat(),
            "last_activity": conn.last_activity.isoformat(),
            "message_count": conn.message_count,
            "subscriptions": list(conn.subscription_topics),
        }


# Global WebSocket manager instance
websocket_manager = EnhancedWebSocketManager()
