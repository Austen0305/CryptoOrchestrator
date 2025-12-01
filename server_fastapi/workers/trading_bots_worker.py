"""
Celery Worker Tasks for Competitive Trading Bots
Handles scheduled execution for DCA, Grid, Infinity Grid, Trailing, and Futures bots
"""

import os
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any
from celery import Celery
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from ..database import DATABASE_URL
from ..services.trading.dca_trading_service import DCATradingService
from ..services.trading.grid_trading_service import GridTradingService
from ..services.trading.infinity_grid_service import InfinityGridService
from ..services.trading.trailing_bot_service import TrailingBotService
from ..services.trading.futures_trading_service import FuturesTradingService

logger = logging.getLogger(__name__)

# Get Celery app from main celery_app
try:
    from ..celery_app import celery_app
except ImportError:
    # Fallback if celery_app not available
    celery_app = Celery(
        "trading_bots_worker",
        broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
        backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    )

# Create async database session for worker
engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session():
    """Get database session for async operations."""
    async with async_session() as session:
        try:
            yield session
        finally:
            pass


@celery_app.task(name='trading_bots.process_dca_orders')
def process_dca_orders():
    """
    Process all DCA bots that are due for their next order.
    Runs every minute to check for bots ready to execute orders.
    """
    async def run():
        try:
            async with async_session() as session:
                service = DCATradingService(session=session)
                result = await service.process_all_due_orders()
                return result
        except Exception as e:
            logger.error(f"Error processing DCA orders: {e}", exc_info=True)
            return {"processed": 0, "skipped": 0, "errors": 1}
    
    return asyncio.run(run())


@celery_app.task(name='trading_bots.process_grid_cycles')
def process_grid_cycles():
    """
    Process grid trading bot cycles.
    Checks for filled orders and rebalances grids.
    Runs every 30 seconds.
    """
    async def run():
        try:
            async with async_session() as session:
                from ..repositories.grid_bot_repository import GridBotRepository
                repository = GridBotRepository()
                
                # Get all active grid bots
                active_bots = await repository.get_active_grid_bots(session)
                
                service = GridTradingService(session=session)
                results = []
                
                for bot in active_bots:
                    try:
                        result = await service.process_grid_cycle(bot.id, bot.user_id)
                        results.append({
                            "bot_id": bot.id,
                            "user_id": bot.user_id,
                            **result
                        })
                    except Exception as e:
                        logger.error(f"Error processing grid cycle for bot {bot.id}: {e}", exc_info=True)
                        results.append({
                            "bot_id": bot.id,
                            "user_id": bot.user_id,
                            "action": "error",
                            "error": str(e)
                        })
                
                return {
                    "processed": len([r for r in results if r.get("action") == "processed"]),
                    "errors": len([r for r in results if r.get("action") == "error"]),
                    "results": results
                }
        except Exception as e:
            logger.error(f"Error processing grid cycles: {e}", exc_info=True)
            return {"processed": 0, "errors": 1}
    
    return asyncio.run(run())


@celery_app.task(name='trading_bots.process_infinity_grids')
def process_infinity_grids():
    """
    Process infinity grid bot cycles.
    Checks price movements and adjusts grid bounds.
    Runs every minute.
    """
    async def run():
        try:
            async with async_session() as session:
                from ..repositories.infinity_grid_repository import InfinityGridRepository
                repository = InfinityGridRepository()
                
                # Get all active infinity grids
                active_bots = await repository.get_active_infinity_grids(session)
                
                service = InfinityGridService(session=session)
                results = []
                
                for bot in active_bots:
                    try:
                        result = await service.process_infinity_grid_cycle(bot.id, bot.user_id)
                        results.append({
                            "bot_id": bot.id,
                            "user_id": bot.user_id,
                            **result
                        })
                    except Exception as e:
                        logger.error(f"Error processing infinity grid cycle for bot {bot.id}: {e}", exc_info=True)
                        results.append({
                            "bot_id": bot.id,
                            "user_id": bot.user_id,
                            "action": "error",
                            "error": str(e)
                        })
                
                return {
                    "processed": len([r for r in results if r.get("action") == "processed"]),
                    "errors": len([r for r in results if r.get("action") == "error"]),
                    "results": results
                }
        except Exception as e:
            logger.error(f"Error processing infinity grids: {e}", exc_info=True)
            return {"processed": 0, "errors": 1}
    
    return asyncio.run(run())


@celery_app.task(name='trading_bots.process_trailing_bots')
def process_trailing_bots():
    """
    Process trailing bot cycles.
    Monitors price movements and executes orders when conditions are met.
    Runs every 10 seconds.
    """
    async def run():
        try:
            async with async_session() as session:
                from ..repositories.trailing_bot_repository import TrailingBotRepository
                repository = TrailingBotRepository()
                
                # Get all active trailing bots
                active_bots = await repository.get_active_trailing_bots(session)
                
                service = TrailingBotService(session=session)
                results = []
                
                for bot in active_bots:
                    try:
                        result = await service.process_trailing_bot_cycle(bot.id, bot.user_id)
                        results.append({
                            "bot_id": bot.id,
                            "user_id": bot.user_id,
                            **result
                        })
                    except Exception as e:
                        logger.error(f"Error processing trailing bot cycle for bot {bot.id}: {e}", exc_info=True)
                        results.append({
                            "bot_id": bot.id,
                            "user_id": bot.user_id,
                            "action": "error",
                            "error": str(e)
                        })
                
                return {
                    "processed": len([r for r in results if r.get("action") == "executed"]),
                    "monitoring": len([r for r in results if r.get("action") == "monitoring"]),
                    "errors": len([r for r in results if r.get("action") == "error"]),
                    "results": results
                }
        except Exception as e:
            logger.error(f"Error processing trailing bots: {e}", exc_info=True)
            return {"processed": 0, "errors": 1}
    
    return asyncio.run(run())


@celery_app.task(name='trading_bots.update_futures_pnl')
def update_futures_pnl():
    """
    Update P&L for all open futures positions.
    Runs every 5 seconds for real-time updates.
    """
    async def run():
        try:
            async with async_session() as session:
                from ..repositories.futures_position_repository import FuturesPositionRepository
                repository = FuturesPositionRepository()
                
                # Get all open positions
                open_positions = await repository.get_open_positions(session)
                
                service = FuturesTradingService(session=session)
                results = []
                
                for position in open_positions:
                    try:
                        result = await service.update_position_pnl(position.id, position.user_id)
                        results.append({
                            "position_id": position.id,
                            "user_id": position.user_id,
                            **result
                        })
                    except Exception as e:
                        logger.error(f"Error updating P&L for position {position.id}: {e}", exc_info=True)
                        results.append({
                            "position_id": position.id,
                            "user_id": position.user_id,
                            "action": "error",
                            "error": str(e)
                        })
                
                return {
                    "updated": len([r for r in results if r.get("action") == "updated"]),
                    "closed": len([r for r in results if r.get("action") == "closed"]),
                    "liquidated": len([r for r in results if r.get("action") == "liquidated"]),
                    "errors": len([r for r in results if r.get("action") == "error"]),
                    "results": results
                }
        except Exception as e:
            logger.error(f"Error updating futures P&L: {e}", exc_info=True)
            return {"updated": 0, "errors": 1}
    
    return asyncio.run(run())


@celery_app.task(name='trading_bots.process_copy_trades')
def process_copy_trades():
    """
    Process auto-copy trades for all active follow relationships.
    Automatically copies new trades from followed traders.
    Runs every 15 seconds.
    """
    async def run():
        try:
            async with async_session() as session:
                from ..services.copy_trading_service import CopyTradingService
                from ..repositories.follow_repository import FollowRepository
                
                service = CopyTradingService(session)
                repository = FollowRepository()
                
                # Get all active follow relationships with auto-copy enabled
                active_follows = await repository.get_active_auto_copy_follows(session)
                
                results = []
                for follow in active_follows:
                    try:
                        # Get recent trades from trader that haven't been copied yet
                        copied_count = await service.auto_copy_recent_trades(
                            follower_id=follow.follower_id,
                            trader_id=follow.trader_id
                        )
                        results.append({
                            "follow_id": follow.id,
                            "follower_id": follow.follower_id,
                            "trader_id": follow.trader_id,
                            "copied_trades": copied_count
                        })
                    except Exception as e:
                        logger.error(f"Error auto-copying trades for follow {follow.id}: {e}", exc_info=True)
                        results.append({
                            "follow_id": follow.id,
                            "error": str(e)
                        })
                
                return {
                    "processed": len([r for r in results if r.get("copied_trades", 0) > 0]),
                    "total_copied": sum(r.get("copied_trades", 0) for r in results),
                    "errors": len([r for r in results if "error" in r]),
                    "results": results
                }
        except Exception as e:
            logger.error(f"Error processing copy trades: {e}", exc_info=True)
            return {"processed": 0, "errors": 1}
    
    return asyncio.run(run())


# Register periodic tasks in beat schedule
celery_app.conf.beat_schedule.update({
    'process-dca-orders': {
        'task': 'trading_bots.process_dca_orders',
        'schedule': 60.0,  # Every minute
    },
    'process-grid-cycles': {
        'task': 'trading_bots.process_grid_cycles',
        'schedule': 30.0,  # Every 30 seconds
    },
    'process-infinity-grids': {
        'task': 'trading_bots.process_infinity_grids',
        'schedule': 60.0,  # Every minute
    },
    'process-trailing-bots': {
        'task': 'trading_bots.process_trailing_bots',
        'schedule': 10.0,  # Every 10 seconds
    },
    'update-futures-pnl': {
        'task': 'trading_bots.update_futures_pnl',
        'schedule': 5.0,  # Every 5 seconds
    },
    'process-copy-trades': {
        'task': 'trading_bots.process_copy_trades',
        'schedule': 15.0,  # Every 15 seconds
    },
})

