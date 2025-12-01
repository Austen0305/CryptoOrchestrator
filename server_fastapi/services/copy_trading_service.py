"""
Copy Trading Service
Enables users to copy trades from other traders.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from ..models.trade import Trade
from ..models.user import User
from ..models.follow import Follow, CopiedTrade

logger = logging.getLogger(__name__)


class CopyTradingService:
    """Service for copy trading functionality"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def follow_trader(
        self,
        follower_id: int,
        trader_id: int,
        allocation_percentage: float = 100.0,
        max_position_size: Optional[float] = None
    ) -> Dict[str, any]:
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
            # Validate allocation
            if allocation_percentage <= 0 or allocation_percentage > 100:
                raise ValueError("Allocation percentage must be between 0 and 100")
            
            # Check if trader exists and is public
            trader_stmt = select(User).where(User.id == trader_id)
            trader_result = await self.db.execute(trader_stmt)
            trader = trader_result.scalar_one_or_none()
            
            if not trader:
                raise ValueError("Trader not found")
            
            # Check if already following
            existing_stmt = select(Follow).where(
                and_(
                    Follow.follower_id == follower_id,
                    Follow.trader_id == trader_id
                )
            )
            existing_result = await self.db.execute(existing_stmt)
            existing = existing_result.scalar_one_or_none()
            
            if existing:
                # Update existing follow
                existing.allocation_percentage = allocation_percentage
                existing.max_position_size = max_position_size
                existing.is_active = True
                await self.db.commit()
                await self.db.refresh(existing)
                return {
                    "id": existing.id,
                    "follower_id": follower_id,
                    "trader_id": trader_id,
                    "allocation_percentage": allocation_percentage,
                    "max_position_size": max_position_size,
                    "created_at": existing.created_at.isoformat() if existing.created_at else datetime.now().isoformat(),
                    "status": "active"
                }
            
            # Create new follow relationship
            follow = Follow(
                follower_id=follower_id,
                trader_id=trader_id,
                allocation_percentage=allocation_percentage,
                max_position_size=max_position_size,
                is_active=True,
                auto_copy_enabled=True
            )
            self.db.add(follow)
            await self.db.commit()
            await self.db.refresh(follow)
            
            return {
                "id": follow.id,
                "follower_id": follower_id,
                "trader_id": trader_id,
                "allocation_percentage": allocation_percentage,
                "max_position_size": max_position_size,
                "created_at": follow.created_at.isoformat() if follow.created_at else datetime.now().isoformat(),
                "status": "active"
            }
            
        except Exception as e:
            logger.error(f"Error following trader: {e}", exc_info=True)
            raise
    
    async def unfollow_trader(
        self,
        follower_id: int,
        trader_id: int
    ) -> bool:
        """Unfollow a trader"""
        try:
            stmt = select(Follow).where(
                and_(
                    Follow.follower_id == follower_id,
                    Follow.trader_id == trader_id
                )
            )
            result = await self.db.execute(stmt)
            follow = result.scalar_one_or_none()
            
            if follow:
                follow.is_active = False
                await self.db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error unfollowing trader: {e}", exc_info=True)
            await self.db.rollback()
            return False
    
    async def get_followed_traders(self, follower_id: int) -> List[Dict]:
        """Get list of traders being followed"""
        try:
            stmt = select(Follow, User).join(
                User, Follow.trader_id == User.id
            ).where(
                and_(
                    Follow.follower_id == follower_id,
                    Follow.is_active == True
                )
            )
            result = await self.db.execute(stmt)
            follows = result.all()
            
            traders = []
            for follow, trader in follows:
                traders.append({
                    "id": follow.id,
                    "trader_id": follow.trader_id,
                    "username": trader.username or trader.email,
                    "email": trader.email,
                    "allocation_percentage": follow.allocation_percentage,
                    "max_position_size": follow.max_position_size,
                    "auto_copy_enabled": follow.auto_copy_enabled,
                    "total_copied_trades": follow.total_copied_trades,
                    "total_profit": follow.total_profit,
                    "last_copied_at": follow.last_copied_at.isoformat() if follow.last_copied_at else None,
                    "created_at": follow.created_at.isoformat() if follow.created_at else None,
                    "status": "active" if follow.is_active else "inactive"
                })
            
            return traders
        except Exception as e:
            logger.error(f"Error getting followed traders: {e}", exc_info=True)
            return []
    
    async def copy_trade(
        self,
        follower_id: int,
        trader_id: int,
        original_trade_id: str,
        allocation_percentage: float
    ) -> Dict[str, any]:
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
            # Get original trade
            trade_stmt = select(Trade).where(
                and_(
                    Trade.id == original_trade_id,
                    Trade.user_id == trader_id
                )
            )
            trade_result = await self.db.execute(trade_stmt)
            original_trade = trade_result.scalar_one_or_none()
            
            if not original_trade:
                raise ValueError("Original trade not found")
            
            # Get follow relationship
            follow_stmt = select(Follow).where(
                and_(
                    Follow.follower_id == follower_id,
                    Follow.trader_id == trader_id,
                    Follow.is_active == True
                )
            )
            follow_result = await self.db.execute(follow_stmt)
            follow = follow_result.scalar_one_or_none()
            
            if not follow:
                raise ValueError("Not following this trader")
            
            # Calculate copied trade size
            copied_amount = original_trade.amount * (allocation_percentage / 100.0)
            
            # Apply max position size limit if set
            if follow.max_position_size and copied_amount * original_trade.price > follow.max_position_size:
                copied_amount = follow.max_position_size / original_trade.price
            
            # Apply min/max trade size limits
            if follow.min_trade_size and copied_amount * original_trade.price < follow.min_trade_size:
                raise ValueError(f"Trade size below minimum: {follow.min_trade_size}")
            
            if follow.max_trade_size and copied_amount * original_trade.price > follow.max_trade_size:
                copied_amount = follow.max_trade_size / original_trade.price
            
            # Create copied trade record
            copied_trade_record = CopiedTrade(
                follower_id=follower_id,
                trader_id=trader_id,
                original_trade_id=original_trade.id,
                allocation_percentage=allocation_percentage,
                original_amount=original_trade.amount,
                copied_amount=copied_amount,
                original_price=original_trade.price,
                copied_price=original_trade.price,  # Will be updated when executed
                status="pending"
            )
            self.db.add(copied_trade_record)
            await self.db.commit()
            await self.db.refresh(copied_trade_record)
            
            # Execute the copied trade via trading service
            try:
                from ..services.trading.real_money_service import real_money_trading_service
                from ..services.trading.safe_trading_system import SafeTradingSystem
                
                safe_trading = SafeTradingSystem()
                
                # Validate trade
                trade_details = {
                    "symbol": original_trade.pair or original_trade.symbol,
                    "action": original_trade.side,
                    "quantity": copied_amount,
                    "price": original_trade.price,
                    "user_id": follower_id,
                    "mode": original_trade.mode
                }
                
                validation = await safe_trading.validate_trade(trade_details)
                if not validation["valid"]:
                    copied_trade_record.status = "failed"
                    copied_trade_record.error_message = "; ".join(validation["errors"])
                    await self.db.commit()
                    raise ValueError(f"Trade validation failed: {copied_trade_record.error_message}")
                
                # Execute trade
                if original_trade.mode == "real":
                    executed_trade = await real_money_trading_service.execute_trade(
                        user_id=str(follower_id),
                        pair=original_trade.pair or original_trade.symbol,
                        side=original_trade.side,
                        amount=copied_amount,
                        order_type=original_trade.order_type or "market",
                        price=original_trade.price if original_trade.order_type == "limit" else None
                    )
                else:
                    # Paper trading
                    from ..services.backtesting.paper_trading_service import PaperTradingService
                    paper_service = PaperTradingService()
                    executed_trade = await paper_service.execute_paper_trade(
                        user_id=str(follower_id),
                        pair=original_trade.pair or original_trade.symbol,
                        side=original_trade.side,
                        amount=copied_amount,
                        price=original_trade.price
                    )
                
                # Update copied trade record
                if executed_trade and "id" in executed_trade:
                    copied_trade_record.copied_trade_id = executed_trade.get("id")
                    copied_trade_record.copied_price = executed_trade.get("price", original_trade.price)
                    copied_trade_record.status = "executed"
                    
                    # Update follow statistics
                    follow.total_copied_trades += 1
                    follow.last_copied_at = datetime.now()
                    
                    await self.db.commit()
                    
                    logger.info(f"Trade copied successfully: {copied_trade_record.id}")
                else:
                    copied_trade_record.status = "failed"
                    copied_trade_record.error_message = "Trade execution returned no result"
                    await self.db.commit()
                    
            except Exception as e:
                logger.error(f"Error executing copied trade: {e}", exc_info=True)
                copied_trade_record.status = "failed"
                copied_trade_record.error_message = str(e)
                await self.db.commit()
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
                "created_at": copied_trade_record.created_at.isoformat() if copied_trade_record.created_at else datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error copying trade: {e}", exc_info=True)
            raise
    
    async def get_copy_trading_stats(
        self,
        follower_id: int
    ) -> Dict[str, any]:
        """Get copy trading statistics for a follower"""
        try:
            # Get all active follows
            follows_stmt = select(Follow).where(
                and_(
                    Follow.follower_id == follower_id,
                    Follow.is_active == True
                )
            )
            follows_result = await self.db.execute(follows_stmt)
            follows = follows_result.scalars().all()
            
            # Get all copied trades
            copied_trades_stmt = select(CopiedTrade).where(
                and_(
                    CopiedTrade.follower_id == follower_id,
                    CopiedTrade.status == "executed"
                )
            )
            copied_trades_result = await self.db.execute(copied_trades_stmt)
            copied_trades = copied_trades_result.scalars().all()
            
            # Calculate total profit from copied trades
            total_profit = 0.0
            for copied_trade in copied_trades:
                if copied_trade.copied_trade_id:
                    # Get the actual trade to calculate P&L
                    trade_stmt = select(Trade).where(Trade.id == copied_trade.copied_trade_id)
                    trade_result = await self.db.execute(trade_stmt)
                    trade = trade_result.scalar_one_or_none()
                    if trade and trade.pnl:
                        total_profit += trade.pnl
            
            # Count active copies (pending or open orders)
            active_copies_stmt = select(CopiedTrade).where(
                and_(
                    CopiedTrade.follower_id == follower_id,
                    CopiedTrade.status.in_(["pending", "executed"])
                )
            )
            active_copies_result = await self.db.execute(active_copies_stmt)
            active_copies = active_copies_result.scalars().all()
            
            return {
                "total_copied_trades": len(copied_trades),
                "total_profit": round(total_profit, 2),
                "active_copies": len([c for c in active_copies if c.status == "pending"]),
                "followed_traders": len(follows)
            }
        except Exception as e:
            logger.error(f"Error getting copy trading stats: {e}", exc_info=True)
            return {
                "total_copied_trades": 0,
                "total_profit": 0.0,
                "active_copies": 0,
                "followed_traders": 0
            }

    async def auto_copy_recent_trades(
        self,
        follower_id: int,
        trader_id: int,
        lookback_minutes: int = 5
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
            
            # Get follow relationship
            follow_stmt = select(Follow).where(
                and_(
                    Follow.follower_id == follower_id,
                    Follow.trader_id == trader_id,
                    Follow.is_active == True,
                    Follow.auto_copy_enabled == True
                )
            )
            follow_result = await self.db.execute(follow_stmt)
            follow = follow_result.scalar_one_or_none()
            
            if not follow:
                return 0
            
            # Get recent trades from trader that haven't been copied yet
            cutoff_time = datetime.utcnow() - timedelta(minutes=lookback_minutes)
            
            # Get trades from trader created after cutoff
            recent_trades_stmt = select(Trade).where(
                and_(
                    Trade.user_id == trader_id,
                    Trade.created_at >= cutoff_time,
                    Trade.status == "completed"
                )
            ).order_by(Trade.created_at.desc())
            
            recent_trades_result = await self.db.execute(recent_trades_stmt)
            recent_trades = recent_trades_result.scalars().all()
            
            # Get already copied trades to avoid duplicates
            copied_trade_ids_stmt = select(CopiedTrade.original_trade_id).where(
                and_(
                    CopiedTrade.follower_id == follower_id,
                    CopiedTrade.trader_id == trader_id
                )
            )
            copied_ids_result = await self.db.execute(copied_trade_ids_stmt)
            copied_trade_ids = {row[0] for row in copied_ids_result.all()}
            
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
                        allocation_percentage=follow.allocation_percentage
                    )
                    copied_count += 1
                except Exception as e:
                    logger.error(f"Error auto-copying trade {trade.id}: {e}", exc_info=True)
                    # Continue with next trade
                    continue
            
            return copied_count
            
        except Exception as e:
            logger.error(f"Error in auto_copy_recent_trades: {e}", exc_info=True)
            return 0

