"""
Copy Trading Worker
Automatically copies trades from followed traders in real-time.
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from ..models.trade import Trade
from ..models.follow import Follow, CopiedTrade
from ..services.copy_trading_service import CopyTradingService

logger = logging.getLogger(__name__)


class CopyTradingWorker:
    """Background worker for automatic copy trading"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.copy_service = CopyTradingService(db)
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self.last_check_time: Dict[int, datetime] = {}  # trader_id -> last check time

    async def start(self):
        """Start the copy trading worker"""
        if self.running:
            logger.warning("Copy trading worker already running")
            return

        self.running = True
        self._task = asyncio.create_task(self._worker_loop())
        logger.info("Copy trading worker started")

    async def stop(self):
        """Stop the copy trading worker"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Copy trading worker stopped")

    async def _worker_loop(self):
        """Main worker loop"""
        while self.running:
            try:
                await self._process_new_trades()
                await asyncio.sleep(5)  # Check every 5 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in copy trading worker: {e}", exc_info=True)
                await asyncio.sleep(10)  # Wait longer on error

    async def _process_new_trades(self):
        """Process new trades from followed traders"""
        try:
            # Get all active follow relationships
            follows_stmt = select(Follow).where(Follow.is_active == True)
            follows_result = await self.db.execute(follows_stmt)
            follows = follows_result.scalars().all()

            for follow in follows:
                if not follow.auto_copy_enabled:
                    continue

                try:
                    # Get last check time for this trader
                    last_check = self.last_check_time.get(follow.trader_id)
                    if not last_check:
                        last_check = datetime.utcnow() - timedelta(minutes=1)

                    # Get new trades from this trader since last check
                    trades_stmt = (
                        select(Trade)
                        .where(
                            and_(
                                Trade.user_id == follow.trader_id,
                                Trade.mode
                                == "paper",  # Only copy paper trades by default
                                Trade.status == "completed",
                                Trade.timestamp > last_check,
                            )
                        )
                        .order_by(Trade.timestamp)
                    )

                    trades_result = await self.db.execute(trades_stmt)
                    new_trades = trades_result.scalars().all()

                    # Process each new trade
                    for trade in new_trades:
                        # Check if we should copy this trade
                        if not self._should_copy_trade(follow, trade):
                            continue

                        # Copy the trade
                        try:
                            await self._copy_trade_automatically(follow, trade)
                        except Exception as e:
                            logger.error(
                                f"Error copying trade {trade.id}: {e}", exc_info=True
                            )

                    # Update last check time
                    if new_trades:
                        self.last_check_time[follow.trader_id] = new_trades[
                            -1
                        ].timestamp
                    else:
                        self.last_check_time[follow.trader_id] = datetime.utcnow()

                except Exception as e:
                    logger.error(
                        f"Error processing trades for trader {follow.trader_id}: {e}",
                        exc_info=True,
                    )
                    continue

        except Exception as e:
            logger.error(f"Error in _process_new_trades: {e}", exc_info=True)

    def _should_copy_trade(self, follow: Follow, trade: Trade) -> bool:
        """Determine if a trade should be copied"""
        # Check if trade type is enabled
        if trade.side == "buy" and not follow.copy_buy_orders:
            return False
        if trade.side == "sell" and not follow.copy_sell_orders:
            return False

        # Check trade size limits
        trade_value = trade.amount * trade.price
        if follow.min_trade_size and trade_value < follow.min_trade_size:
            return False
        if follow.max_trade_size and trade_value > follow.max_trade_size:
            return False
        if follow.max_position_size:
            copied_value = trade_value * (follow.allocation_percentage / 100.0)
            if copied_value > follow.max_position_size:
                return False

        # Check if already copied
        # (Would check CopiedTrade table in production)

        return True

    async def _copy_trade_automatically(self, follow: Follow, trade: Trade):
        """Automatically copy a trade"""
        try:
            # Use copy service to execute the copy
            copied_trade = await self.copy_service.copy_trade(
                follower_id=follow.follower_id,
                trader_id=follow.trader_id,
                original_trade_id=str(trade.id),
                allocation_percentage=follow.allocation_percentage,
            )

            logger.info(
                f"Automatically copied trade {trade.id} for follower {follow.follower_id}"
            )
            return copied_trade

        except Exception as e:
            logger.error(
                f"Error automatically copying trade {trade.id}: {e}", exc_info=True
            )
            raise


# Global worker instance (will be initialized in main.py)
copy_trading_worker: Optional[CopyTradingWorker] = None
