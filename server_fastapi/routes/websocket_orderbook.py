"""
WebSocket endpoint for real-time order book streaming.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Optional
import logging
import json
from datetime import datetime

from ..services.orderbook_streaming_service import orderbook_streaming_service
from ..dependencies.auth import get_optional_user

logger = logging.getLogger(__name__)

router = APIRouter()


class OrderBookConnectionManager:
    """Manages WebSocket connections for order book streaming"""
    
    def __init__(self):
        self.active_connections: Dict[str, set] = {}  # pair -> set of websockets
    
    async def connect(self, websocket: WebSocket, pair: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        if pair not in self.active_connections:
            self.active_connections[pair] = set()
        self.active_connections[pair].add(websocket)
        logger.info(f"Order book WebSocket connected for {pair}")
    
    def disconnect(self, websocket: WebSocket, pair: str):
        """Remove WebSocket connection"""
        if pair in self.active_connections:
            self.active_connections[pair].discard(websocket)
            if not self.active_connections[pair]:
                del self.active_connections[pair]
        logger.info(f"Order book WebSocket disconnected for {pair}")
    
    async def send_orderbook(self, pair: str, orderbook: Dict):
        """Send order book update to all connected clients"""
        if pair in self.active_connections:
            message = {
                "type": "orderbook",
                "pair": pair,
                "data": {
                    "bids": orderbook.get("bids", []),
                    "asks": orderbook.get("asks", []),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            disconnected = set()
            for websocket in self.active_connections[pair]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.warning(f"Error sending order book update: {e}")
                    disconnected.add(websocket)
            
            # Remove disconnected websockets
            for ws in disconnected:
                self.disconnect(ws, pair)


connection_manager = OrderBookConnectionManager()


async def orderbook_callback(pair: str, orderbook: Dict):
    """Callback for order book updates"""
    await connection_manager.send_orderbook(pair, orderbook)


@router.websocket("/ws/orderbook/{pair}")
async def websocket_orderbook(
    websocket: WebSocket,
    pair: str,
    token: Optional[str] = None
):
    """
    WebSocket endpoint for real-time order book updates.
    
    Args:
        pair: Trading pair (e.g., "BTC/USD")
        token: Optional JWT token for authentication
    """
    # Optional authentication
    user = None
    if token:
        try:
            user = await get_optional_user(token)
        except:
            pass
    
    await connection_manager.connect(websocket, pair)
    
    # Subscribe to order book updates
    subscription_id = await orderbook_streaming_service.subscribe(
        pair,
        lambda ob: orderbook_callback(pair, ob),
        update_interval=1.0
    )
    
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, pair)
        await orderbook_streaming_service.unsubscribe(pair, lambda ob: orderbook_callback(pair, ob))
        logger.info(f"Order book WebSocket disconnected for {pair}")
    except Exception as e:
        logger.error(f"Error in order book WebSocket: {e}")
        connection_manager.disconnect(websocket, pair)
        await orderbook_streaming_service.unsubscribe(pair, lambda ob: orderbook_callback(pair, ob))

