"""
Portfolio WebSocket Streaming Endpoint

Real-time portfolio updates via WebSocket with:
- Delta-based updates for efficiency
- Heartbeat for connection health
- Price subscription management
"""

import asyncio
import contextlib
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..services.portfolio_analytics_service import (
    RealTimePortfolioAnalytics,
    create_portfolio_analytics,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/portfolio", tags=["portfolio-stream"])


class PortfolioStreamManager:
    """Manages WebSocket connections for portfolio streaming"""

    def __init__(self):
        self._connections: dict[int, list[WebSocket]] = {}
        self._analytics: dict[int, RealTimePortfolioAnalytics] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        """Accept and register a WebSocket connection"""
        await websocket.accept()

        if user_id not in self._connections:
            self._connections[user_id] = []
            self._analytics[user_id] = create_portfolio_analytics(user_id)

        self._connections[user_id].append(websocket)
        logger.info(f"Portfolio WebSocket connected: user {user_id}")

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        """Remove a WebSocket connection"""
        if user_id in self._connections:
            self._connections[user_id] = [
                ws for ws in self._connections[user_id] if ws != websocket
            ]
            if not self._connections[user_id]:
                del self._connections[user_id]
                if user_id in self._analytics:
                    del self._analytics[user_id]

        logger.info(f"Portfolio WebSocket disconnected: user {user_id}")

    async def send_snapshot(self, user_id: int) -> None:
        """Send full portfolio snapshot to all user's connections"""
        if user_id not in self._connections:
            return

        analytics = self._analytics.get(user_id)
        if not analytics:
            return

        snapshot = analytics.get_snapshot()
        message = {
            "type": "snapshot",
            "data": snapshot.model_dump(mode="json"),
        }

        await self._broadcast(user_id, message)

    async def send_delta(self, user_id: int) -> None:
        """Send delta update to all user's connections"""
        if user_id not in self._connections:
            return

        analytics = self._analytics.get(user_id)
        if not analytics:
            return

        delta = analytics.get_delta()
        if delta:
            message = {
                "type": "delta",
                "data": delta.model_dump(mode="json"),
            }
            await self._broadcast(user_id, message)

    async def send_heartbeat(self, user_id: int) -> None:
        """Send heartbeat to keep connection alive"""
        message = {
            "type": "heartbeat",
            "data": {"timestamp": datetime.now(UTC).isoformat()},
        }
        await self._broadcast(user_id, message)

    async def _broadcast(self, user_id: int, message: dict) -> None:
        """Broadcast message to all user's connections"""
        if user_id not in self._connections:
            return

        dead_connections = []
        for ws in self._connections[user_id]:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                dead_connections.append(ws)

        # Clean up dead connections
        for ws in dead_connections:
            self.disconnect(user_id, ws)

    def get_analytics(self, user_id: int) -> RealTimePortfolioAnalytics | None:
        """Get analytics instance for a user"""
        return self._analytics.get(user_id)

    def update_price(self, user_id: int, symbol: str, price: float) -> bool:
        """Update price for a user's position"""
        analytics = self._analytics.get(user_id)
        if analytics:
            analytics.update_price(symbol, price)
            return True
        return False


# Singleton manager
stream_manager = PortfolioStreamManager()


@router.websocket("/stream/{user_id}")
async def portfolio_websocket(websocket: WebSocket, user_id: int):
    """
    WebSocket endpoint for real-time portfolio streaming.

    Message Types:
    - snapshot: Full portfolio state
    - delta: Changes since last update
    - heartbeat: Connection health check
    - error: Error notification

    Client can send:
    - {"action": "subscribe", "symbols": ["BTC/USDT", ...]}
    - {"action": "unsubscribe", "symbols": [...]}
    """
    await stream_manager.connect(user_id, websocket)

    # Send initial snapshot
    await stream_manager.send_snapshot(user_id)

    # Start heartbeat task
    async def heartbeat_loop():
        while True:
            await asyncio.sleep(30)
            try:
                await stream_manager.send_heartbeat(user_id)
            except Exception:
                break

    heartbeat_task = asyncio.create_task(heartbeat_loop())

    try:
        while True:
            # Wait for client messages
            data = await websocket.receive_json()

            action = data.get("action")

            if action == "refresh":
                await stream_manager.send_snapshot(user_id)

            elif action == "subscribe":
                # Handle symbol subscription
                symbols = data.get("symbols", [])
                logger.info(f"User {user_id} subscribed to: {symbols}")

            elif action == "unsubscribe":
                symbols = data.get("symbols", [])
                logger.info(f"User {user_id} unsubscribed from: {symbols}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: user {user_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        with contextlib.suppress(Exception):
            await websocket.send_json(
                {
                    "type": "error",
                    "data": {"message": str(e)},
                }
            )

    finally:
        heartbeat_task.cancel()
        stream_manager.disconnect(user_id, websocket)


@router.post("/stream/{user_id}/price")
async def update_price(user_id: int, symbol: str, price: float):
    """
    Update price for a position (triggers delta broadcast).
    Used by market data service to push price updates.
    """
    if stream_manager.update_price(user_id, symbol, price):
        await stream_manager.send_delta(user_id)
        return {"status": "ok"}
    return {"status": "no_connection"}
