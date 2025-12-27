"""
WebSocket Route for Real-Time Wallet Updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
import json
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.wallet_service import WalletService
from ..database import get_db_session
from ..services.wallet_broadcast import set_active_connections, broadcast_wallet_update

logger = logging.getLogger(__name__)

router = APIRouter()

# Store active WebSocket connections
active_connections: Dict[int, List[WebSocket]] = {}


async def broadcast_wallet_update(user_id: int, wallet_data: Dict):
    """Broadcast wallet update to all connected clients for a user"""
    if user_id in active_connections:
        message = {
            "type": "wallet_update",
            "data": wallet_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        disconnected = []
        for connection in active_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send wallet update to user {user_id}: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for conn in disconnected:
            active_connections[user_id].remove(conn)

        # Clean up empty lists
        if not active_connections[user_id]:
            del active_connections[user_id]


@router.websocket("/ws/wallet")
async def websocket_wallet(websocket: WebSocket):
    """WebSocket endpoint for real-time wallet updates"""
    await websocket.accept()

    try:
        # Authenticate user
        user = await get_current_user_websocket(websocket)
        if not user:
            await websocket.close(code=1008, reason="Unauthorized")
            return

        user_id = user.get("id")
        if not user_id:
            await websocket.close(code=1008, reason="Invalid user")
            return

        # Add connection to active connections
        if user_id not in active_connections:
            active_connections[user_id] = []
        active_connections[user_id].append(websocket)

        # Update broadcast service with active connections
        set_active_connections(active_connections)

        logger.info(f"Wallet WebSocket connected for user {user_id}")

        # Send initial wallet balance
        try:
            from ..database import get_db_context

            async with get_db_context() as db:
                service = WalletService(db)
                balance = await service.get_wallet_balance(user_id, "USD")
                await websocket.send_json(
                    {
                        "type": "initial_balance",
                        "data": balance,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
        except Exception as e:
            logger.error(f"Error sending initial balance: {e}")

        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for client messages (ping/pong or requests)
                data = await websocket.receive_text()
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif message.get("type") == "get_balance":
                    currency = message.get("currency", "USD")
                    from ..database import async_session

                    async with async_session() as db:
                        service = WalletService(db)
                        balance = await service.get_wallet_balance(user_id, currency)
                        await websocket.send_json(
                            {
                                "type": "balance_response",
                                "data": balance,
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json(
                    {"type": "error", "message": "Invalid JSON format"}
                )
            except Exception as e:
                logger.error(f"WebSocket error for user {user_id}: {e}")
                await websocket.send_json(
                    {"type": "error", "message": "Internal server error"}
                )

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}", exc_info=True)
    finally:
        # Remove connection from active connections
        if user_id in active_connections:
            if websocket in active_connections[user_id]:
                active_connections[user_id].remove(websocket)
            if not active_connections[user_id]:
                del active_connections[user_id]
        logger.info(f"Wallet WebSocket disconnected for user {user_id}")
