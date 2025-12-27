"""
Wallet Broadcast Service
Handles broadcasting wallet updates via WebSocket
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Import WebSocket connections (circular import handled)
_active_connections = {}


def set_active_connections(connections: Dict):
    """Set active WebSocket connections (called from websocket_wallet route)"""
    global _active_connections
    _active_connections = connections


async def broadcast_wallet_update(user_id: int, wallet_data: Dict):
    """Broadcast wallet update to all connected clients for a user"""
    if user_id not in _active_connections:
        return

    try:
        from datetime import datetime

        message = {
            "type": "wallet_update",
            "data": wallet_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        disconnected = []
        for connection in _active_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send wallet update to user {user_id}: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for conn in disconnected:
            _active_connections[user_id].remove(conn)

        # Clean up empty lists
        if not _active_connections[user_id]:
            del _active_connections[user_id]
    except Exception as e:
        logger.error(f"Error broadcasting wallet update: {e}", exc_info=True)
