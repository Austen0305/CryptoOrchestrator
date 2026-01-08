"""
Copy Trading Service
Enables users to copy trades from other traders.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..repositories.copy_trading_repository import CopyTradingRepository
    from ..repositories.follow_repository import FollowRepository
    from ..repositories.trade_repository import TradeRepository
    from ..repositories.user_repository import UserRepository
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.copy_trading_repository import CopyTradingRepository
from ..repositories.follow_repository import FollowRepository
from ..repositories.trade_repository import TradeRepository
from ..repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class CopyTradingService:
    """Service for copy trading functionality"""

    def __init__(
        self,
        db: AsyncSession,
        follow_repository: FollowRepository | None = None,
        copy_trading_repository: CopyTradingRepository | None = None,
        trade_repository: TradeRepository | None = None,
        user_repository: UserRepository | None = None,
    ):
        # ✅ Repository injected via dependency injection (Service Layer Pattern)
        self.follow_repository = follow_repository or FollowRepository()
        self.copy_trading_repository = (
            copy_trading_repository or CopyTradingRepository()
        )
        self.trade_repository = trade_repository or TradeRepository()
        self.user_repository = user_repository or UserRepository()
        self.db = db  # Keep db for transaction handling

    async def follow_trader(
        self,
        follower_id: int,
        trader_id: int,
        allocation_percentage: float = 100.0,
        max_position_size: float | None = None,
    ) -> dict[str, any]:
        """
        Follow a trader to copy their trades.

        Args:
            follower_id: User ID of the follower
            trader_id: User ID of the trader to follow
            allocation_percentage: Percentage of capital to allocate (default: 100%)
            max_position_size: Maximum position size in USD (optional)

        Returns:
            Dict with follow relationship details
        """
        try:
            # ✅ Business logic: Validate allocation
            if allocation_percentage <= 0 or allocation_percentage > 100:
                raise ValueError("Allocation percentage must be between 0 and 100")

            # ✅ Data access delegated to repository
            trader = await self.user_repository.get_by_id(self.db, trader_id)
            if not trader:
                raise ValueError("Trader not found")

            # ✅ Data access delegated to repository
            existing = await self.follow_repository.get_by_follower_and_trader(
                self.db, follower_id, trader_id
            )

            if existing:
                # ✅ Business logic: Update existing follow
                updated = await self.follow_repository.update(
                    self.db,
                    existing.id,
                    {
                        "allocation_percentage": allocation_percentage,
                        "max_position_size": max_position_size,
                        "is_active": True,
                    },
                )
                if updated:
                    return {
                        "id": updated.id,
                        "follower_id": follower_id,
                        "trader_id": trader_id,
                        "allocation_percentage": allocation_percentage,
                        "max_position_size": max_position_size,
                        "created_at": (
                            updated.created_at.isoformat()
                            if updated.created_at
                            else datetime.now().isoformat()
                        ),
                        "status": "active",
                    }

            # ✅ Business logic: Create new follow relationship
            follow_data = {
                "follower_id": follower_id,
                "trader_id": trader_id,
                "allocation_percentage": allocation_percentage,
                "max_position_size": max_position_size,
                "is_active": True,
                "auto_copy_enabled": True,
            }

            # ✅ Data access delegated to repository
            follow = await self.follow_repository.create(self.db, follow_data)

            return {
                "id": follow.id,
                "follower_id": follower_id,
                "trader_id": trader_id,
                "allocation_percentage": allocation_percentage,
                "max_position_size": max_position_size,
                "created_at": (
                    follow.created_at.isoformat()
                    if follow.created_at
                    else datetime.now().isoformat()
                ),
                "status": "active",
            }

        except Exception as e:
            logger.error(
                f"Error following trader: {e}",
                exc_info=True,
                extra={"follower_id": follower_id, "trader_id": trader_id},
            )
            raise

    async def unfollow_trader(self, follower_id: int, trader_id: int) -> bool:
        """Unfollow a trader"""
        try:
            # ✅ Data access delegated to repository
            follow = await self.follow_repository.get_by_follower_and_trader(
                self.db, follower_id, trader_id
            )

            if follow:
                # ✅ Business logic: Deactivate follow
                # ✅ Data access delegated to repository
                updated = await self.follow_repository.update(
                    self.db, follow.id, {"is_active": False}
                )
                return updated is not None
            return False
        except Exception as e:
            logger.error(
                f"Error unfollowing trader: {e}",
                exc_info=True,
                extra={"follower_id": follower_id, "trader_id": trader_id},
            )
            await self.db.rollback()
            return False

    async def get_followed_traders(self, follower_id: int) -> list[dict]:
        """Get list of traders being followed"""
        try:
            # ✅ Data access delegated to repository (with eager loading)
            follows = await self.follow_repository.get_active_follows_by_follower(
                self.db, follower_id
            )

            traders = []
            for follow in follows:
                # ✅ Eager loaded trader relationship prevents N+1 queries
                trader = follow.trader
                traders.append(
                    {
                        "id": follow.id,
                        "trader_id": follow.trader_id,
                        "username": trader.username or trader.email if trader else None,
                        "email": trader.email if trader else None,
                        "allocation_percentage": follow.allocation_percentage,
                        "max_position_size": follow.max_position_size,
                        "auto_copy_enabled": follow.auto_copy_enabled,
                        "total_copied_trades": follow.total_copied_trades,
                        "total_profit": follow.total_profit,
                        "last_copied_at": (
                            follow.last_copied_at.isoformat()
                            if follow.last_copied_at
                            else None
                        ),
                        "created_at": (
                            follow.created_at.isoformat() if follow.created_at else None
                        ),
                        "status": "active" if follow.is_active else "inactive",
                    }
                )

            return traders
        except Exception as e:
            logger.error(
                f"Error getting followed traders: {e}",
                exc_info=True,
                extra={"follower_id": follower_id},
            )
            return []

    async def copy_trade(
        self,
        follower_id: int,
        trader_id: int,
        original_trade_id: str,
        allocation_percentage: float,
    ) -> dict[str, any]:
        """
        Copy a specific trade from a trader.

        Args:
            follower_id: User ID of the follower
            trader_id: User ID of the trader
            original_trade_id: ID of the original trade to copy
            allocation_percentage: Percentage of original trade size to copy

        Returns:
            Dict with copied trade details
        """
        try:
            # ✅ Data access delegated to repository
            try:
                original_trade_id_int = int(original_trade_id)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid trade ID: {original_trade_id}")

            original_trade = await self.trade_repository.get_by_id(
                self.db, original_trade_id_int
            )
            if not original_trade or original_trade.user_id != trader_id:
                raise ValueError("Original trade not found")

            # ✅ Data access delegated to repository
            follow = await self.follow_repository.get_by_follower_and_trader(
                self.db, follower_id, trader_id
            )
            if not follow or not follow.is_active:
                raise ValueError("Not following this trader")

            # Calculate copied trade size
            copied_amount = original_trade.amount * (allocation_percentage / 100.0)

            # Apply max position size limit if set
            if (
                follow.max_position_size
                and copied_amount * original_trade.price > follow.max_position_size
            ):
                copied_amount = follow.max_position_size / original_trade.price

            # Apply min/max trade size limits
            if (
                follow.min_trade_size
                and copied_amount * original_trade.price < follow.min_trade_size
            ):
                raise ValueError(f"Trade size below minimum: {follow.min_trade_size}")

            if (
                follow.max_trade_size
                and copied_amount * original_trade.price > follow.max_trade_size
            ):
                copied_amount = follow.max_trade_size / original_trade.price

            # ✅ Business logic: Create copied trade record
            # ✅ Data access delegated to repository
            copied_trade_record = (
                await self.copy_trading_repository.create_copied_trade(
                    self.db,
                    follower_id=follower_id,
                    trader_id=trader_id,
                    original_trade_id=original_trade.id,
                    allocation_percentage=allocation_percentage,
                    original_amount=original_trade.amount,
                    copied_amount=copied_amount,
                    original_price=original_trade.price,
                    copied_price=original_trade.price,  # Will be updated when executed
                    status="pending",
                )
            )

            # Execute the copied trade via trading service
            try:
                from ..services.trading.real_money_service import (
                    real_money_trading_service,
                )
                from ..services.trading.safe_trading_system import SafeTradingSystem

                safe_trading = SafeTradingSystem()

                # Validate trade
                trade_details = {
                    "symbol": original_trade.pair or original_trade.symbol,
                    "action": original_trade.side,
                    "quantity": copied_amount,
                    "price": original_trade.price,
                    "user_id": follower_id,
                    "mode": original_trade.mode,
                }

                validation = await safe_trading.validate_trade(trade_details)
                if not validation["valid"]:
                    # ✅ Data access delegated to repository
                    await self.copy_trading_repository.update_status(
                        self.db,
                        copied_trade_record.id,
                        "failed",
                        error_message="; ".join(validation["errors"]),
                    )
                    raise ValueError(
                        f"Trade validation failed: {'; '.join(validation['errors'])}"
                    )

                # Execute trade
                if original_trade.mode == "real":
                    executed_trade = await real_money_trading_service.execute_trade(
                        user_id=str(follower_id),
                        pair=original_trade.pair or original_trade.symbol,
                        side=original_trade.side,
                        amount=copied_amount,
                        order_type=original_trade.order_type or "market",
                        price=(
                            original_trade.price
                            if original_trade.order_type == "limit"
                            else None
                        ),
                    )
                else:
                    # Paper trading
                    from ..services.backtesting.paper_trading_service import (
                        PaperTradingService,
                    )

                    paper_service = PaperTradingService()
                    executed_trade = await paper_service.execute_paper_trade(
                        user_id=str(follower_id),
                        pair=original_trade.pair or original_trade.symbol,
                        side=original_trade.side,
                        amount=copied_amount,
                        price=original_trade.price,
                    )

                # ✅ Business logic: Update copied trade record
                if executed_trade and "id" in executed_trade:
                    # ✅ Data access delegated to repository
                    await self.copy_trading_repository.update(
                        self.db,
                        copied_trade_record.id,
                        {
                            "copied_trade_id": executed_trade.get("id"),
                            "copied_price": executed_trade.get(
                                "price", original_trade.price
                            ),
                            "status": "executed",
                        },
                    )

                    # ✅ Business logic: Update follow statistics
                    # ✅ Data access delegated to repository
                    await self.follow_repository.update(
                        self.db,
                        follow.id,
                        {
                            "total_copied_trades": follow.total_copied_trades + 1,
                            "last_copied_at": datetime.now(),
                        },
                    )

                    logger.info(
                        f"Trade copied successfully: {copied_trade_record.id}",
                        extra={"copied_trade_id": copied_trade_record.id},
                    )
                else:
                    # ✅ Data access delegated to repository
                    await self.copy_trading_repository.update_status(
                        self.db,
                        copied_trade_record.id,
                        "failed",
                        error_message="Trade execution returned no result",
                    )

            except Exception as e:
                logger.error(
                    f"Error executing copied trade: {e}",
                    exc_info=True,
                    extra={"copied_trade_id": copied_trade_record.id},
                )
                # ✅ Data access delegated to repository
                await self.copy_trading_repository.update_status(
                    self.db, copied_trade_record.id, "failed", error_message=str(e)
                )
                raise

            return {
                "id": copied_trade_record.id,
                "follower_id": follower_id,
                "trader_id": trader_id,
                "original_trade_id": original_trade_id,
                "copied_trade_id": copied_trade_record.copied_trade_id,
                "pair": original_trade.pair or original_trade.symbol,
                "side": original_trade.side,
                "amount": copied_amount,
                "price": copied_trade_record.copied_price,
                "allocation_percentage": allocation_percentage,
                "status": copied_trade_record.status,
                "created_at": (
                    copied_trade_record.created_at.isoformat()
                    if copied_trade_record.created_at
                    else datetime.now().isoformat()
                ),
            }

        except Exception as e:
            logger.error(f"Error copying trade: {e}", exc_info=True)
            raise

    async def get_copy_trading_stats(self, follower_id: int) -> dict[str, any]:
        """Get copy trading statistics for a follower"""
        try:
            # ✅ Data access delegated to repository
            follows = await self.follow_repository.get_active_follows_by_follower(
                self.db, follower_id
            )

            # ✅ Data access delegated to repository
            copied_trades = await self.copy_trading_repository.get_by_status(
                self.db, "executed", follower_id=follower_id
            )

            # ✅ Business logic: Calculate total profit from copied trades
            total_profit = 0.0
            for copied_trade in copied_trades:
                if copied_trade.copied_trade_id:
                    # ✅ Data access delegated to repository (with eager loading)
                    trade = await self.trade_repository.get_by_id(
                        self.db, copied_trade.copied_trade_id
                    )
                    if trade and trade.pnl:
                        total_profit += trade.pnl

            # ✅ Data access delegated to repository
            active_copies = await self.copy_trading_repository.get_by_follower(
                self.db, follower_id
            )
            # Filter by status
            active_copies = [
                c for c in active_copies if c.status in ["pending", "executed"]
            ]

            return {
                "total_copied_trades": len(copied_trades),
                "total_profit": round(total_profit, 2),
                "active_copies": len(
                    [c for c in active_copies if c.status == "pending"]
                ),
                "followed_traders": len(follows),
            }
        except Exception as e:
            logger.error(
                f"Error getting copy trading stats: {e}",
                exc_info=True,
                extra={"follower_id": follower_id},
            )
            return {
                "total_copied_trades": 0,
                "total_profit": 0.0,
                "active_copies": 0,
                "followed_traders": 0,
            }

    async def auto_copy_recent_trades(
        self, follower_id: int, trader_id: int, lookback_minutes: int = 5
    ) -> int:
        """
        Automatically copy recent trades from a trader.
        Called by Celery worker for auto-copy functionality.

        Args:
            follower_id: User ID of the follower
            trader_id: User ID of the trader
            lookback_minutes: How many minutes back to look for new trades

        Returns:
            Number of trades copied
        """
        try:
            from datetime import datetime, timedelta

            # ✅ Data access delegated to repository
            follow = await self.follow_repository.get_by_follower_and_trader(
                self.db, follower_id, trader_id
            )

            if not follow or not follow.is_active or not follow.auto_copy_enabled:
                return 0

            # ✅ Business logic: Get recent trades from trader that haven't been copied yet
            cutoff_time = datetime.utcnow() - timedelta(minutes=lookback_minutes)

            # ✅ Data access delegated to repository
            recent_trades = await self.trade_repository.get_by_user(
                self.db, trader_id, skip=0, limit=100
            )
            # Filter by cutoff time and status
            recent_trades = [
                t
                for t in recent_trades
                if t.created_at >= cutoff_time and t.status == "completed"
            ]

            # ✅ Data access delegated to repository
            copied_trades = (
                await self.copy_trading_repository.get_by_follower_and_trader(
                    self.db, follower_id, trader_id
                )
            )
            copied_trade_ids = {ct.original_trade_id for ct in copied_trades}

            # Filter out already copied trades
            new_trades = [t for t in recent_trades if str(t.id) not in copied_trade_ids]

            # Apply copy filters
            if follow.copy_buy_orders and follow.copy_sell_orders:
                trades_to_copy = new_trades
            elif follow.copy_buy_orders:
                trades_to_copy = [t for t in new_trades if t.side == "buy"]
            elif follow.copy_sell_orders:
                trades_to_copy = [t for t in new_trades if t.side == "sell"]
            else:
                trades_to_copy = []

            # Copy each trade
            copied_count = 0
            for trade in trades_to_copy:
                try:
                    # Use follow's allocation percentage
                    await self.copy_trade(
                        follower_id=follower_id,
                        trader_id=trader_id,
                        original_trade_id=str(trade.id),
                        allocation_percentage=follow.allocation_percentage,
                    )
                    copied_count += 1
                except Exception as e:
                    logger.error(
                        f"Error auto-copying trade {trade.id}: {e}", exc_info=True
                    )
                    # Continue with next trade
                    continue

            return copied_count

        except Exception as e:
            logger.error(f"Error in auto_copy_recent_trades: {e}", exc_info=True)
            return 0
