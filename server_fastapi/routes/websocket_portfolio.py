"""
WebSocket Portfolio Updates Route
Real-time portfolio updates via WebSocket
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.security import HTTPBearer
import logging
import jwt
import os
import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime

from ..dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ws", tags=["WebSocket"])
security = HTTPBearer()

JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")

# Store active WebSocket connections
active_connections: Dict[str, Dict[str, Any]] = {}


class PortfolioWebSocketManager:
    """Manager for portfolio WebSocket connections"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, client_id: str):
        """Connect a WebSocket client"""
        await websocket.accept()
        self.connections[client_id] = {
            "websocket": websocket,
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
        }
        logger.info(f"Portfolio WebSocket connected: client={client_id}, user={user_id}")
    
    def disconnect(self, client_id: str):
        """Disconnect a WebSocket client"""
        if client_id in self.connections:
            del self.connections[client_id]
            logger.info(f"Portfolio WebSocket disconnected: client={client_id}")
    
    async def send_portfolio_update(self, user_id: str, portfolio_data: Dict[str, Any]):
        """Send portfolio update to all connections for a user"""
        disconnected = []
        for client_id, conn in self.connections.items():
            if conn["user_id"] == user_id:
                try:
                    await conn["websocket"].send_json({
                        "type": "portfolio_update",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": portfolio_data,
                    })
                except Exception as e:
                    logger.error(f"Failed to send portfolio update to {client_id}: {e}")
                    disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)
    
    async def broadcast_market_update(self, market_data: Dict[str, Any]):
        """Broadcast market data update to all connected clients"""
        disconnected = []
        for client_id, conn in self.connections.items():
            try:
                await conn["websocket"].send_json({
                    "type": "market_data",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": market_data,
                })
            except Exception as e:
                logger.error(f"Failed to send market update to {client_id}: {e}")
                disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)


# Global WebSocket manager instance
portfolio_ws_manager = PortfolioWebSocketManager()


def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """Get user from JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


@router.websocket("/portfolio")
async def websocket_portfolio(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None),
):
    """WebSocket endpoint for real-time portfolio updates"""
    user_id = None
    client_id_str = client_id or f"client_{id(websocket)}"
    
    try:
        # Authenticate user
        if token:
            user = get_user_from_token(token)
            if user:
                user_id = user.get("sub") or user.get("user_id")
        else:
            # Try to get token from WebSocket message
            try:
                auth_message = await websocket.receive_json()
                if auth_message.get("type") == "auth":
                    token = auth_message.get("token")
                    if token:
                        user = get_user_from_token(token)
                        if user:
                            user_id = user.get("sub") or user.get("user_id")
            except:
                pass
        
        if not user_id:
            await websocket.close(code=1008, reason="Authentication required")
            return
        
        # Connect WebSocket
        await portfolio_ws_manager.connect(websocket, str(user_id), client_id_str)
        
        # Send initial portfolio data
        try:
            # Import portfolio route function
            from ..routes.portfolio import router as portfolio_router
            
            # Get portfolio data (paper mode by default)
            # We need to call the portfolio endpoint logic directly
            from ..routes.portfolio import get_portfolio
            from fastapi import Request
            from fastapi.security import HTTPAuthorizationCredentials
            
            # Create a mock request/dependency for get_portfolio
            # Since get_portfolio uses Depends(get_current_user), we need to pass user context
            class MockUser:
                def __init__(self, user_id):
                    self.user_id = user_id
                    self.sub = user_id
                    self.get = lambda key, default=None: user_id if key in ["user_id", "sub"] else default
            
            # Get portfolio data directly
            try:
                from ..services.analytics_engine import analytics_engine
                from ..routes.portfolio import Portfolio, Position
                
                # Get real portfolio data from portfolio route
                from ..routes.portfolio import get_portfolio
                from ..dependencies.auth import get_current_user
                
                # Create user context for portfolio route
                mock_user = MockUser(user_id)
                
                # Get real portfolio data
                try:
                    from ..database import get_db_context
                    from ..routes.portfolio import get_portfolio
                    async with get_db_context() as db:
                        portfolio = await get_portfolio(
                            mode="paper",  # Default to paper, can be made configurable
                            current_user={"user_id": user_id, "sub": user_id},
                            db=db
                        )
                        
                        # Convert portfolio to WebSocket format
                        portfolio_data = {
                            "totalBalance": portfolio.totalBalance,
                            "availableBalance": portfolio.availableBalance,
                            "positions": {
                                asset: {
                                    "asset": pos.asset,
                                    "amount": pos.amount,
                                    "averagePrice": pos.averagePrice,
                                    "currentPrice": pos.currentPrice,
                                    "totalValue": pos.totalValue,
                                    "profitLoss": pos.profitLoss,
                                    "profitLossPercent": pos.profitLossPercent,
                                }
                                for asset, pos in portfolio.positions.items()
                            },
                            "profitLoss24h": portfolio.profitLoss24h,
                            "profitLossTotal": portfolio.profitLossTotal,
                            "successfulTrades": portfolio.successfulTrades,
                            "failedTrades": portfolio.failedTrades,
                            "totalTrades": portfolio.totalTrades,
                            "winRate": portfolio.winRate,
                            "averageWin": portfolio.averageWin,
                            "averageLoss": portfolio.averageLoss,
                        }
                        
                        await websocket.send_json({
                            "type": "portfolio_update",
                            "timestamp": datetime.utcnow().isoformat(),
                            "data": portfolio_data,
                        })
                except Exception as e:
                    logger.error(f"Failed to fetch real portfolio data: {e}")
                    # Fallback to empty portfolio in production
                    from ..config.settings import get_settings
                    settings = get_settings()
                    if settings.production_mode or settings.is_production:
                        portfolio_data = {
                            "totalBalance": 0.0,
                            "availableBalance": 0.0,
                            "positions": {},
                            "profitLoss24h": 0.0,
                            "profitLossTotal": 0.0,
                            "successfulTrades": 0,
                            "failedTrades": 0,
                            "totalTrades": 0,
                            "winRate": 0.0,
                            "averageWin": 0.0,
                            "averageLoss": 0.0,
                        }
                    else:
                        # Development fallback
                        portfolio_data = {
                            "totalBalance": 100000.0,
                            "availableBalance": 95000.0,
                            "positions": {
                                "BTC": {
                                    "asset": "BTC",
                                    "amount": 1.2,
                                    "averagePrice": 48000.0,
                                    "currentPrice": 50000.0,
                                    "totalValue": 60000.0,
                                    "profitLoss": 4800.0,
                                    "profitLossPercent": 8.0,
                                }
                            },
                            "profitLoss24h": 1250.50,
                            "profitLossTotal": 7800.0,
                            "successfulTrades": 45,
                            "failedTrades": 12,
                            "totalTrades": 57,
                            "winRate": 0.789,
                            "averageWin": 215.50,
                            "averageLoss": -180.25,
                        }
                    
                    await websocket.send_json({
                        "type": "portfolio_update",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": portfolio_data,
                    })
            except Exception as e:
                logger.error(f"Failed to send initial portfolio data: {e}")
        except Exception as e:
            logger.error(f"Failed to send initial portfolio data: {e}")
        
        # Start periodic portfolio updates
        async def send_periodic_updates():
            while client_id_str in portfolio_ws_manager.connections:
                try:
                    await asyncio.sleep(10)  # Update every 10 seconds
                    
                    # Fetch real portfolio data
                    try:
                        from ..routes.portfolio import get_portfolio
                        from ..database import get_db_context
                        async with get_db_context() as db:
                            portfolio = await get_portfolio(
                                mode="paper",
                                current_user={"user_id": user_id, "sub": user_id},
                                db=db
                            )
                            portfolio_data = {
                                "totalBalance": portfolio.totalBalance,
                                "availableBalance": portfolio.availableBalance,
                                "positions": {
                                    asset: {
                                        "asset": pos.asset,
                                        "amount": pos.amount,
                                        "averagePrice": pos.averagePrice,
                                        "currentPrice": pos.currentPrice,
                                        "totalValue": pos.totalValue,
                                        "profitLoss": pos.profitLoss,
                                        "profitLossPercent": pos.profitLossPercent,
                                    }
                                    for asset, pos in portfolio.positions.items()
                                },
                                "profitLoss24h": portfolio.profitLoss24h,
                                "profitLossTotal": portfolio.profitLossTotal,
                            }
                    except Exception as e:
                        logger.error(f"Failed to fetch portfolio in periodic update: {e}")
                        # In production, return empty data
                        from ..config.settings import get_settings
                        settings = get_settings()
                        if settings.production_mode or settings.is_production:
                            portfolio_data = {
                                "totalBalance": 0.0,
                                "availableBalance": 0.0,
                                "positions": {},
                                "profitLoss24h": 0.0,
                                "profitLossTotal": 0.0,
                            }
                        else:
                            # Development fallback
                            portfolio_data = {
                                "totalBalance": 100000.0,
                                "availableBalance": 95000.0,
                                "positions": {},
                                "profitLoss24h": 0,
                                "profitLossTotal": 0,
                            }
                    
                    await websocket.send_json({
                        "type": "portfolio_update",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": portfolio_data,
                    })
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Failed to send periodic portfolio update: {e}")
                    break
        
        # Start background task for periodic updates
        update_task = asyncio.create_task(send_periodic_updates())
        
        # Handle incoming messages
        while True:
            try:
                message = await websocket.receive_json()
                
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif message.get("type") == "subscribe":
                    # Subscribe to specific mode or pair
                    mode = message.get("mode", "paper")
                    # Could add subscription logic here
                    await websocket.send_json({
                        "type": "subscribed",
                        "mode": mode,
                    })
                elif message.get("type") == "get_portfolio":
                    # Get current portfolio
                    mode = message.get("mode", "paper")
                    # Fetch real portfolio data
                    try:
                        from ..routes.portfolio import get_portfolio
                        from ..database import get_db_context
                        async with get_db_context() as db:
                            portfolio = await get_portfolio(
                                mode=mode,
                                current_user={"user_id": user_id, "sub": user_id},
                                db=db
                            )
                            portfolio_data = {
                                "totalBalance": portfolio.totalBalance,
                                "availableBalance": portfolio.availableBalance,
                                "positions": {
                                    asset: {
                                        "asset": pos.asset,
                                        "amount": pos.amount,
                                        "averagePrice": pos.averagePrice,
                                        "currentPrice": pos.currentPrice,
                                        "totalValue": pos.totalValue,
                                        "profitLoss": pos.profitLoss,
                                        "profitLossPercent": pos.profitLossPercent,
                                    }
                                    for asset, pos in portfolio.positions.items()
                                },
                                "profitLoss24h": portfolio.profitLoss24h,
                                "profitLossTotal": portfolio.profitLossTotal,
                            }
                    except Exception as e:
                        logger.error(f"Failed to fetch portfolio: {e}")
                        # In production, return empty data
                        from ..config.settings import get_settings
                        settings = get_settings()
                        if settings.production_mode or settings.is_production:
                            portfolio_data = {
                                "totalBalance": 0.0,
                                "availableBalance": 0.0,
                        "positions": {},
                        "profitLoss24h": 0,
                        "profitLossTotal": 0,
                    }
                    await websocket.send_json({
                        "type": "portfolio_update",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": portfolio_data,
                    })
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                })
        
        # Cancel update task
        update_task.cancel()
        
    except WebSocketDisconnect:
        logger.info(f"Portfolio WebSocket disconnected: {client_id_str}")
    except Exception as e:
        logger.error(f"Portfolio WebSocket error: {e}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass
    finally:
        portfolio_ws_manager.disconnect(client_id_str)


# Function to notify portfolio updates (can be called from other services)
async def notify_portfolio_update(user_id: str, portfolio_data: Dict[str, Any]):
    """Notify all WebSocket clients of portfolio update"""
    await portfolio_ws_manager.send_portfolio_update(user_id, portfolio_data)

