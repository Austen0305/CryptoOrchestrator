from fastapi import WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.routing import APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import json
import asyncio
import jwt
import os
import logging
import time
from typing import List, Dict, Any, Optional
from ..services.market_data import MarketDataService
from ..services.trading_orchestrator import TradingOrchestrator
from ..services.notification_service import NotificationService
from ..services.monitoring.performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Environment variables
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[Dict[str, Any]] = []  # Store connection info with user_id

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections.append({
            'websocket': websocket,
            'user_id': user_id,
            'subscriptions': set()
        })
        logger.info(f"WebSocket connection established for user {user_id}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections = [
            conn for conn in self.active_connections
            if conn['websocket'] != websocket
        ]
        logger.info("WebSocket connection closed")

    def get_connection(self, websocket: WebSocket) -> Optional[Dict[str, Any]]:
        for conn in self.active_connections:
            if conn['websocket'] == websocket:
                return conn
        return None

    async def send_to_user(self, user_id: int, message: dict):
        """Send message to specific user"""
        for conn in self.active_connections:
            if conn['user_id'] == user_id:
                try:
                    await conn['websocket'].send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send message to user {user_id}: {e}")

    async def broadcast_to_user(self, user_id: int, message: dict):
        """Broadcast message to user across all their connections"""
        sent = False
        for conn in self.active_connections:
            if conn['user_id'] == user_id:
                try:
                    await conn['websocket'].send_json(message)
                    sent = True
                except Exception as e:
                    logger.error(f"Failed to send broadcast to user {user_id}: {e}")
        return sent

# Initialize managers and services
manager = ConnectionManager()
market_data_service = MarketDataService()
trading_orchestrator = TradingOrchestrator()
notification_service = NotificationService()
performance_monitor = PerformanceMonitor()

def get_current_user_ws(token: str = None) -> dict:
    """Get current user from JWT token for WebSocket connections"""
    try:
        if not token:
            raise HTTPException(status_code=401, detail="No token provided")

        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        # Mock user lookup - in real implementation, get from database
        user = {'id': user_id, 'email': f'user{user_id}@example.com'}
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.websocket("/ws/market-data")
async def websocket_market_data(websocket: WebSocket):
    """WebSocket endpoint for real-time market data"""
    token = None
    user = None

    try:
        # Accept connection to allow reading auth message
        await websocket.accept()
        # Wait for authentication message
        auth_data = await websocket.receive_json()
        if auth_data.get('type') != 'auth':
            await websocket.send_json({'error': 'Authentication required'})
            await websocket.close()
            return

        token = auth_data.get('token')
        user = get_current_user_ws(token)
        await manager.connect(websocket, user['id'])

        logger.info(f"User {user['id']} authenticated for market data")

        # Send initial confirmation
        await websocket.send_json({
            'type': 'auth_success',
            'message': 'Authenticated successfully'
        })

        while True:
            try:
                data = await websocket.receive_json()

                if data.get('action') == 'subscribe':
                    symbols = data.get('symbols', ['BTC/USD'])
                    logger.info(f"User {user['id']} subscribing to {symbols}")

                    # Start sending market data updates
                    async for update in market_data_service.stream_market_data():
                        if update['symbol'] in symbols:
                            await websocket.send_json(update)
                        await asyncio.sleep(0.1)  # Small delay to prevent overwhelming

                elif data.get('action') == 'backfill_request':
                    # Client provides { action: 'backfill_request', since: { 'BTC/USD': 1690000000000 } }
                    since_map = data.get('since', {})
                    for sym, since_ts in since_map.items():
                        try:
                            candles = await market_data_service.get_backfill(sym, int(since_ts))
                            if candles:
                                await websocket.send_json({
                                    'type': 'backfill',
                                    'symbol': sym,
                                    'timeframe': '1m',
                                    'candles': candles
                                })
                        except Exception as be:
                            logger.error(f"Backfill error for {sym}: {be}")
                            await websocket.send_json({'type': 'backfill_error', 'symbol': sym, 'error': str(be)})

                elif data.get('action') == 'unsubscribe':
                    logger.info(f"User {user['id']} unsubscribed from market data")
                    break

            except json.JSONDecodeError:
                await websocket.send_json({'error': 'Invalid JSON format'})
                continue

    except WebSocketDisconnect:
        logger.info("Market data WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in market data WebSocket: {e}")
        try:
            await websocket.send_json({'error': str(e)})
        except:
            pass
    finally:
        if websocket:
            manager.disconnect(websocket)

@router.websocket("/ws/bot-status")
async def websocket_bot_status(websocket: WebSocket):
    """WebSocket endpoint for real-time bot status updates"""
    token = None
    user = None

    try:
        await websocket.accept()
        # Authentication
        auth_data = await websocket.receive_json()
        if auth_data.get('type') != 'auth':
            await websocket.send_json({'error': 'Authentication required'})
            await websocket.close()
            return

        token = auth_data.get('token')
        user = get_current_user_ws(token)
        await manager.connect(websocket, user['id'])

        await websocket.send_json({
            'type': 'auth_success',
            'message': 'Authenticated successfully'
        })

        logger.info(f"User {user['id']} connected to bot status updates")

        # Send initial bot statuses
        bots = await trading_orchestrator.get_user_bots(user['id'])
        for bot in bots:
            await websocket.send_json({
                'type': 'bot_status',
                'bot_id': bot['id'],
                'status': bot['status'],
                'last_update': bot.get('last_update')
            })

        # Listen for status updates (in real implementation, this would be event-driven)
        while True:
            try:
                data = await websocket.receive_json()

                if data.get('action') == 'ping':
                    await websocket.send_json({'type': 'pong'})

                elif data.get('action') == 'get_status':
                    bot_id = data.get('bot_id')
                    if bot_id:
                        bot = await trading_orchestrator.get_bot_status(user['id'], bot_id)
                        await websocket.send_json({
                            'type': 'bot_status',
                            'bot_id': bot_id,
                            'status': bot
                        })

            except json.JSONDecodeError:
                await websocket.send_json({'error': 'Invalid JSON format'})

    except WebSocketDisconnect:
        logger.info("Bot status WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in bot status WebSocket: {e}")
        try:
            await websocket.send_json({'error': str(e)})
        except:
            pass
    finally:
        if websocket:
            manager.disconnect(websocket)

@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    """WebSocket endpoint for real-time notifications"""
    token = None
    user = None

    async def notification_listener(notification: dict):
        """Callback for new notifications.

        Enhancement: If the notification wraps a risk scenario (notification['data']['type'] == 'risk_scenario'),
        emit a dedicated 'risk_scenario' event for clients that subscribe specifically to scenario updates.
        This keeps backward compatibility (standard 'notification' still sent) while enabling targeted handling.
        """
        try:
            # Always send the generic notification event
            await websocket.send_json({
                'type': 'notification',
                'data': notification
            })

            # Conditional second event for risk scenario broadcasts
            inner = notification.get('data') or {}
            if inner.get('type') == 'risk_scenario':
                await websocket.send_json({
                    'type': 'risk_scenario',
                    'data': notification  # mirror structure expected by frontend hook
                })
        except Exception as e:
            logger.error(f"Failed to send notification/risk_scenario to WebSocket: {e}")

    try:
        await websocket.accept()
        # Authentication
        auth_data = await websocket.receive_json()
        if auth_data.get('type') != 'auth':
            await websocket.send_json({'error': 'Authentication required'})
            await websocket.close()
            return

        token = auth_data.get('token')
        user = get_current_user_ws(token)
        await manager.connect(websocket, user['id'])

        # Add listener for real-time notifications
        await notification_service.add_listener(user['id'], notification_listener)

        await websocket.send_json({
            'type': 'auth_success',
            'message': 'Authenticated successfully'
        })

        logger.info(f"User {user['id']} connected to notifications")

        # Send recent notifications
        notifications = await notification_service.get_recent_notifications(user['id'], limit=20)
        await websocket.send_json({
            'type': 'initial_notifications',
            'data': notifications
        })

        # Send current unread count
        unread_count = await notification_service.get_unread_count(user['id'])
        await websocket.send_json({
            'type': 'unread_count_update',
            'count': unread_count
        })

        while True:
            try:
                data = await websocket.receive_json()

                if data.get('action') == 'ping':
                    await websocket.send_json({'type': 'pong'})

                elif data.get('action') == 'mark_read':
                    notification_id = data.get('notification_id')
                    if notification_id:
                        success = await notification_service.mark_as_read(user['id'], notification_id)
                        if success:
                            await websocket.send_json({
                                'type': 'notification_read',
                                'notification_id': notification_id
                            })
                            # Send updated unread count
                            unread_count = await notification_service.get_unread_count(user['id'])
                            await websocket.send_json({
                                'type': 'unread_count_update',
                                'count': unread_count
                            })

                elif data.get('action') == 'mark_all_read':
                    category = data.get('category')
                    from ..services.notification_service import NotificationCategory
                    category_enum = NotificationCategory(category) if category else None
                    count = await notification_service.mark_all_as_read(user['id'], category_enum)

                    await websocket.send_json({
                        'type': 'all_notifications_read',
                        'count': count,
                        'category': category
                    })
                    # Send updated unread count
                    unread_count = await notification_service.get_unread_count(user['id'])
                    await websocket.send_json({
                        'type': 'unread_count_update',
                        'count': unread_count
                    })

                elif data.get('action') == 'get_stats':
                    stats = await notification_service.get_notification_stats(user['id'])
                    await websocket.send_json({
                        'type': 'stats_update',
                        'data': stats
                    })

                elif data.get('action') == 'delete':
                    notification_id = data.get('notification_id')
                    if notification_id:
                        success = await notification_service.delete_notification(user['id'], notification_id)
                        if success:
                            await websocket.send_json({
                                'type': 'notification_deleted',
                                'notification_id': notification_id
                            })
                            # Send updated unread count
                            unread_count = await notification_service.get_unread_count(user['id'])
                            await websocket.send_json({
                                'type': 'unread_count_update',
                                'count': unread_count
                            })

            except json.JSONDecodeError:
                await websocket.send_json({'error': 'Invalid JSON format'})

    except WebSocketDisconnect:
        logger.info("Notifications WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in notifications WebSocket: {e}")
        try:
            await websocket.send_json({'error': str(e)})
        except:
            pass
    finally:
        # Remove listener when connection closes
        if user:
            await notification_service.remove_listener(user['id'], notification_listener)
        if websocket:
            manager.disconnect(websocket)

@router.websocket("/ws/performance-metrics")
async def websocket_performance_metrics(websocket: WebSocket):
    """WebSocket endpoint for real-time performance metrics"""
    token = None
    user = None

    try:
        await websocket.accept()
        # Authentication
        auth_data = await websocket.receive_json()
        if auth_data.get('type') != 'auth':
            await websocket.send_json({'error': 'Authentication required'})
            await websocket.close()
            return

        token = auth_data.get('token')
        user = get_current_user_ws(token)
        await manager.connect(websocket, user['id'])

        await websocket.send_json({
            'type': 'auth_success',
            'message': 'Authenticated successfully'
        })

        logger.info(f"User {user['id']} connected to performance metrics")

        # Send initial performance metrics
        trading_metrics = performance_monitor.get_trading_metrics()
        system_metrics = await performance_monitor.collect_system_metrics()

        await websocket.send_json({
            'type': 'initial_metrics',
            'trading': trading_metrics.dict(),
            'system': system_metrics.dict()
        })

        while True:
            try:
                data = await websocket.receive_json()

                if data.get('action') == 'ping':
                    await websocket.send_json({'type': 'pong'})

                elif data.get('action') == 'get_trading_metrics':
                    trading_metrics = performance_monitor.get_trading_metrics()
                    await websocket.send_json({
                        'type': 'trading_metrics_update',
                        'data': trading_metrics.dict()
                    })

                elif data.get('action') == 'get_system_metrics':
                    system_metrics = await performance_monitor.collect_system_metrics()
                    await websocket.send_json({
                        'type': 'system_metrics_update',
                        'data': system_metrics.dict()
                    })

                elif data.get('action') == 'get_metrics_history':
                    hours = data.get('hours', 24)
                    history = await performance_monitor.get_metrics_history(hours)
                    await websocket.send_json({
                        'type': 'metrics_history',
                        'data': [m.dict() for m in history]
                    })

                elif data.get('action') == 'get_system_health':
                    health = await performance_monitor.get_system_health()
                    await websocket.send_json({
                        'type': 'system_health',
                        'data': health
                    })

                elif data.get('action') == 'start_streaming':
                    # Start periodic streaming
                    interval = data.get('interval', 30)  # Default 30 seconds
                    logger.info(f"Starting metrics streaming for user {user['id']} with {interval}s interval")

                    while True:
                        try:
                            trading_metrics = performance_monitor.get_trading_metrics()
                            system_metrics = await performance_monitor.collect_system_metrics()

                            await websocket.send_json({
                                'type': 'metrics_stream',
                                'trading': trading_metrics.dict(),
                                'system': system_metrics.dict(),
                                'timestamp': int(time.time())
                            })

                            await asyncio.sleep(interval)
                        except asyncio.CancelledError:
                            break
                        except Exception as e:
                            logger.error(f"Error streaming metrics: {e}")
                            await asyncio.sleep(interval)

                elif data.get('action') == 'stop_streaming':
                    logger.info(f"Stopping metrics streaming for user {user['id']}")
                    break

            except json.JSONDecodeError:
                await websocket.send_json({'error': 'Invalid JSON format'})

    except WebSocketDisconnect:
        logger.info("Performance metrics WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in performance metrics WebSocket: {e}")
        try:
            await websocket.send_json({'error': str(e)})
        except:
            pass
    finally:
        if websocket:
            manager.disconnect(websocket)
