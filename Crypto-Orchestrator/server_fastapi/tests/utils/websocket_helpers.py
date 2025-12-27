"""
WebSocket testing utilities for integration tests.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, List
from websockets.client import connect
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)


class WebSocketTestClient:
    """Test client for WebSocket connections"""

    def __init__(self, url: str, token: Optional[str] = None):
        self.url = url
        self.token = token
        self.websocket = None
        self.messages: List[Dict[str, Any]] = []
        self.connected = False

    async def connect(self) -> bool:
        """Connect to WebSocket server"""
        try:
            self.websocket = await connect(self.url)
            self.connected = True

            # Send authentication if token provided
            if self.token:
                await self.send({"type": "auth", "token": self.token})

                # Wait for auth confirmation
                response = await self.receive(timeout=5.0)
                if response and response.get("type") == "auth_success":
                    logger.info("WebSocket authenticated successfully")
                    return True
                else:
                    logger.warning("WebSocket authentication failed")
                    return False

            return True
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            self.connected = False
            return False

    async def send(self, message: Dict[str, Any]) -> None:
        """Send message to WebSocket server"""
        if not self.connected or not self.websocket:
            raise ConnectionError("WebSocket not connected")

        await self.websocket.send(json.dumps(message))

    async def receive(self, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """Receive message from WebSocket server"""
        if not self.connected or not self.websocket:
            raise ConnectionError("WebSocket not connected")

        try:
            message = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
            data = json.loads(message)
            self.messages.append(data)
            return data
        except asyncio.TimeoutError:
            return None
        except ConnectionClosed:
            self.connected = False
            return None
        except Exception as e:
            logger.error(f"Error receiving WebSocket message: {e}")
            return None

    async def receive_messages(
        self, count: int = 1, timeout: float = 5.0
    ) -> List[Dict[str, Any]]:
        """Receive multiple messages"""
        messages = []
        for _ in range(count):
            message = await self.receive(timeout=timeout)
            if message:
                messages.append(message)
            else:
                break
        return messages

    async def wait_for_message(
        self, message_type: str, timeout: float = 10.0
    ) -> Optional[Dict[str, Any]]:
        """Wait for a specific message type"""
        start_time = asyncio.get_event_loop().time()

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                return None

            message = await self.receive(timeout=1.0)
            if message and message.get("type") == message_type:
                return message

    async def close(self) -> None:
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


async def test_websocket_connection(
    url: str, token: Optional[str] = None, test_message: Optional[Dict[str, Any]] = None
) -> bool:
    """Test WebSocket connection and basic functionality"""
    async with WebSocketTestClient(url, token) as client:
        if not client.connected:
            return False

        if test_message:
            await client.send(test_message)
            response = await client.receive(timeout=5.0)
            return response is not None

        return True


async def test_websocket_subscription(
    url: str,
    token: str,
    subscription: Dict[str, Any],
    expected_message_type: str,
    timeout: float = 10.0,
) -> Optional[Dict[str, Any]]:
    """Test WebSocket subscription and wait for expected message"""
    async with WebSocketTestClient(url, token) as client:
        if not client.connected:
            return None

        await client.send(subscription)
        return await client.wait_for_message(expected_message_type, timeout=timeout)
