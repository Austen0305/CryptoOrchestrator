"""
Enhanced WebSocket Connection Manager
Manages subscriptions, broadcasts, and reconnection logic
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set, List, Optional, Callable, Any
import asyncio
import json
import logging
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types"""
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    PING = "ping"
    PONG = "pong"
    DATA = "data"
    ERROR = "error"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


class WebSocketConnection:
    """Represents a single WebSocket connection with metadata"""
    
    def __init__(self, websocket: WebSocket, client_id: str):
        self.websocket = websocket
        self.client_id = client_id
        self.connected_at = datetime.now()
        self.last_activity = datetime.now()
        self.subscriptions: Set[str] = set()
        self.metadata: Dict[str, Any] = {}
    
    async def send_message(self, message: dict):
        """Send message and update activity timestamp"""
        try:
            await self.websocket.send_json(message)
            self.last_activity = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {self.client_id}: {e}")
            return False
    
    def is_idle(self, timeout_seconds: int = 300) -> bool:
        """Check if connection has been idle too long"""
        idle_time = (datetime.now() - self.last_activity).total_seconds()
        return idle_time > timeout_seconds


class ConnectionManager:
    """
    Advanced WebSocket connection manager with:
    - Channel-based subscriptions
    - Broadcast to multiple clients
    - Connection pooling and cleanup
    - Heartbeat/ping-pong for connection health
    """
    
    def __init__(self):
        # Active connections by client_id
        self.connections: Dict[str, WebSocketConnection] = {}
        
        # Channel subscriptions: channel_name -> set of client_ids
        self.subscriptions: Dict[str, Set[str]] = {}
        
        # Message handlers for different message types
        self.handlers: Dict[str, Callable] = {}
        
        # Background tasks
        self.cleanup_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
    
    async def connect(self, websocket: WebSocket, client_id: str) -> WebSocketConnection:
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        
        connection = WebSocketConnection(websocket, client_id)
        self.connections[client_id] = connection
        
        logger.info(f"✅ Client {client_id} connected (total: {len(self.connections)})")
        
        # Send welcome message
        await connection.send_message({
            "type": MessageType.CONNECTED.value,
            "client_id": client_id,
            "timestamp": datetime.now().isoformat(),
            "message": "Connected to WebSocket server"
        })
        
        return connection
    
    def disconnect(self, client_id: str):
        """Remove connection and clean up subscriptions"""
        if client_id not in self.connections:
            return
        
        connection = self.connections[client_id]
        
        # Remove from all subscriptions
        for channel in connection.subscriptions:
            if channel in self.subscriptions:
                self.subscriptions[channel].discard(client_id)
                # Clean up empty channels
                if not self.subscriptions[channel]:
                    del self.subscriptions[channel]
        
        # Remove connection
        del self.connections[client_id]
        
        logger.info(f"❌ Client {client_id} disconnected (remaining: {len(self.connections)})")
    
    async def subscribe(self, client_id: str, channel: str) -> bool:
        """Subscribe client to a channel"""
        if client_id not in self.connections:
            logger.warning(f"Cannot subscribe unknown client {client_id}")
            return False
        
        connection = self.connections[client_id]
        
        # Add to channel subscriptions
        if channel not in self.subscriptions:
            self.subscriptions[channel] = set()
        
        self.subscriptions[channel].add(client_id)
        connection.subscriptions.add(channel)
        
        logger.info(f"📡 Client {client_id} subscribed to {channel}")
        
        # Send confirmation
        await connection.send_message({
            "type": MessageType.SUBSCRIBE.value,
            "channel": channel,
            "status": "subscribed",
            "timestamp": datetime.now().isoformat()
        })
        
        return True
    
    async def unsubscribe(self, client_id: str, channel: str) -> bool:
        """Unsubscribe client from a channel"""
        if client_id not in self.connections:
            return False
        
        connection = self.connections[client_id]
        
        # Remove from channel
        if channel in self.subscriptions:
            self.subscriptions[channel].discard(client_id)
            if not self.subscriptions[channel]:
                del self.subscriptions[channel]
        
        connection.subscriptions.discard(channel)
        
        logger.info(f"📡 Client {client_id} unsubscribed from {channel}")
        
        # Send confirmation
        await connection.send_message({
            "type": MessageType.UNSUBSCRIBE.value,
            "channel": channel,
            "status": "unsubscribed",
            "timestamp": datetime.now().isoformat()
        })
        
        return True
    
    async def broadcast(self, channel: str, message: dict, exclude: Optional[Set[str]] = None):
        """Broadcast message to all subscribers of a channel"""
        if channel not in self.subscriptions:
            return
        
        exclude = exclude or set()
        subscribers = self.subscriptions[channel] - exclude
        
        if not subscribers:
            return
        
        # Add metadata to message
        broadcast_message = {
            "type": MessageType.DATA.value,
            "channel": channel,
            "timestamp": datetime.now().isoformat(),
            "data": message
        }
        
        # Send to all subscribers
        failed_clients = []
        for client_id in subscribers:
            if client_id in self.connections:
                success = await self.connections[client_id].send_message(broadcast_message)
                if not success:
                    failed_clients.append(client_id)
        
        # Clean up failed connections
        for client_id in failed_clients:
            logger.warning(f"Removing failed connection: {client_id}")
            self.disconnect(client_id)
        
        logger.debug(f"📢 Broadcast to {len(subscribers)} clients on channel '{channel}'")
    
    async def send_to_client(self, client_id: str, message: dict) -> bool:
        """Send message to a specific client"""
        if client_id not in self.connections:
            return False
        
        return await self.connections[client_id].send_message(message)
    
    async def handle_message(self, client_id: str, message: dict):
        """Handle incoming message from client"""
        try:
            msg_type = message.get("type")
            
            if msg_type == MessageType.SUBSCRIBE.value:
                channel = message.get("channel")
                if channel:
                    await self.subscribe(client_id, channel)
            
            elif msg_type == MessageType.UNSUBSCRIBE.value:
                channel = message.get("channel")
                if channel:
                    await self.unsubscribe(client_id, channel)
            
            elif msg_type == MessageType.PING.value:
                # Respond with pong
                await self.send_to_client(client_id, {
                    "type": MessageType.PONG.value,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Call custom handlers
            elif msg_type in self.handlers:
                await self.handlers[msg_type](client_id, message)
        
        except Exception as e:
            logger.error(f"Error handling message from {client_id}: {e}")
            await self.send_to_client(client_id, {
                "type": MessageType.ERROR.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    def register_handler(self, message_type: str, handler: Callable):
        """Register custom message handler"""
        self.handlers[message_type] = handler
        logger.info(f"Registered handler for message type: {message_type}")
    
    async def cleanup_idle_connections(self, interval: int = 60):
        """Background task to clean up idle connections"""
        while True:
            try:
                await asyncio.sleep(interval)
                
                idle_clients = [
                    client_id for client_id, conn in self.connections.items()
                    if conn.is_idle(timeout_seconds=300)
                ]
                
                for client_id in idle_clients:
                    logger.info(f"Cleaning up idle connection: {client_id}")
                    self.disconnect(client_id)
                    
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    async def heartbeat(self, interval: int = 30):
        """Send periodic heartbeat to all connections"""
        while True:
            try:
                await asyncio.sleep(interval)
                
                for client_id in list(self.connections.keys()):
                    await self.send_to_client(client_id, {
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat()
                    })
                    
            except Exception as e:
                logger.error(f"Error in heartbeat task: {e}")
    
    def start_background_tasks(self):
        """Start background cleanup and heartbeat tasks"""
        if not self.cleanup_task:
            self.cleanup_task = asyncio.create_task(self.cleanup_idle_connections())
            logger.info("Started connection cleanup task")
        
        if not self.heartbeat_task:
            self.heartbeat_task = asyncio.create_task(self.heartbeat())
            logger.info("Started heartbeat task")
    
    def stop_background_tasks(self):
        """Stop background tasks"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        logger.info("Stopped background tasks")
    
    def get_stats(self) -> dict:
        """Get connection manager statistics"""
        return {
            "total_connections": len(self.connections),
            "total_channels": len(self.subscriptions),
            "channels": {
                channel: len(subscribers)
                for channel, subscribers in self.subscriptions.items()
            },
            "connections": [
                {
                    "client_id": conn.client_id,
                    "connected_at": conn.connected_at.isoformat(),
                    "last_activity": conn.last_activity.isoformat(),
                    "subscriptions": list(conn.subscriptions)
                }
                for conn in self.connections.values()
            ]
        }


# Global connection manager instance
connection_manager = ConnectionManager()
