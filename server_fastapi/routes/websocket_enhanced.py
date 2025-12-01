"""
Enhanced Market Data WebSocket Endpoint
Real-time market data streaming with subscription management
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import asyncio
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ws", tags=["WebSocket"])


@router.websocket("/market-stream")
async def enhanced_market_stream(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None)
):
    """
    Enhanced WebSocket endpoint for real-time market data
    
    Features:
    - Subscribe to multiple trading pairs
    - Real-time price updates
    - Order book updates
    - Trade history stream
    - Automatic reconnection support
    
    Message format:
    Client -> Server:
    {
        "type": "subscribe",
        "channel": "market:BTC/USDT"
    }
    
    Server -> Client:
    {
        "type": "data",
        "channel": "market:BTC/USDT",
        "timestamp": "2025-11-13T...",
        "data": {...}
    }
    """
    from ..services.websocket_manager import connection_manager
    
    # Generate client ID if not provided
    if not client_id:
        client_id = f"client_{uuid.uuid4().hex[:8]}"
    
    try:
        # Connect client
        connection = await connection_manager.connect(websocket, client_id)
        
        # Start background tasks if not already running
        connection_manager.start_background_tasks()
        
        # Main message loop
        while True:
            try:
                # Receive message from client
                message = await websocket.receive_json()
                
                # Handle message
                await connection_manager.handle_message(client_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected normally")
                break
            except Exception as e:
                logger.error(f"Error processing message from {client_id}: {e}")
                await connection.send_message({
                    "type": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
    
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
    
    finally:
        # Clean up connection
        connection_manager.disconnect(client_id)


@router.websocket("/portfolio-updates")
async def portfolio_updates_stream(
    websocket: WebSocket,
    user_id: str = Query(...),
    client_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time portfolio updates
    
    Streams:
    - Balance changes
    - Position updates
    - Trade executions
    - P&L updates
    """
    from ..services.websocket_manager import connection_manager
    
    if not client_id:
        client_id = f"portfolio_{user_id}_{uuid.uuid4().hex[:6]}"
    
    try:
        connection = await connection_manager.connect(websocket, client_id)
        
        # Auto-subscribe to user's portfolio channel
        await connection_manager.subscribe(client_id, f"portfolio:{user_id}")
        
        # Main message loop
        while True:
            try:
                message = await websocket.receive_json()
                await connection_manager.handle_message(client_id, message)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                await connection.send_message({
                    "type": "error",
                    "error": str(e)
                })
    
    finally:
        connection_manager.disconnect(client_id)


@router.get("/ws/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics
    
    Returns information about:
    - Active connections
    - Channel subscriptions
    - Message throughput
    """
    from ..services.websocket_manager import connection_manager
    
    return connection_manager.get_stats()
