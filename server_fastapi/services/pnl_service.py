"""
P&L Calculation Service
Calculates profit and loss from trade history for portfolios and positions.
"""

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ..repositories.trade_repository import TradeRepository
from datetime import datetime, timedelta
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.trade_repository import TradeRepository

logger = logging.getLogger(__name__)


class PnLService:
    """Service for calculating profit and loss from trade history"""

    def __init__(
        self,
        db: AsyncSession,
        trade_repository: Optional[TradeRepository] = None,
    ):
        # ✅ Repository injected via dependency injection (Service Layer Pattern)
        self.trade_repository = trade_repository or TradeRepository()
        self.db = db  # Keep db for transaction handling

    async def calculate_position_pnl(
        self, user_id: int, symbol: str, current_price: float, mode: str = "paper"
    ) -> Dict[str, float]:
        """
        Calculate P&L for a specific position.

        Args:
            user_id: User ID
            symbol: Trading pair symbol (e.g., "BTC/USD")
            current_price: Current market price
            mode: Trading mode ("paper" or "real")

        Returns:
            Dict with pnl, pnl_percent, cost_basis, current_value
        """
        try:
            # ✅ Data access delegated to repository
            trades = await self.trade_repository.get_completed_trades_for_pnl(
                self.db, user_id=user_id, mode=mode, pair=symbol
            )

            if not trades:
                return {
                    "pnl": 0.0,
                    "pnl_percent": 0.0,
                    "cost_basis": 0.0,
                    "current_value": 0.0,
                    "quantity": 0.0,
                    "average_price": 0.0,
                }

            # Calculate using FIFO method
            position_quantity = 0.0
            cost_basis = 0.0
            buy_queue: List[Tuple[float, float]] = []  # (quantity, price)

            for trade in trades:
                if trade.side == "buy":
                    buy_queue.append((trade.amount, trade.price))
                    position_quantity += trade.amount
                    cost_basis += trade.amount * trade.price
                elif trade.side == "sell":
                    sell_quantity = trade.amount
                    remaining_sell = sell_quantity

                    # FIFO: sell from oldest buys first
                    while remaining_sell > 0 and buy_queue:
                        buy_qty, buy_price = buy_queue[0]

                        if buy_qty <= remaining_sell:
                            # Fully consumed this buy
                            cost_basis -= buy_qty * buy_price
                            position_quantity -= buy_qty
                            remaining_sell -= buy_qty
                            buy_queue.pop(0)
                        else:
                            # Partially consumed
                            cost_basis -= remaining_sell * buy_price
                            position_quantity -= remaining_sell
                            buy_queue[0] = (buy_qty - remaining_sell, buy_price)
                            remaining_sell = 0

            # Calculate current value and P&L
            current_value = position_quantity * current_price
            average_price = (
                cost_basis / position_quantity if position_quantity > 0 else 0.0
            )
            pnl = current_value - cost_basis
            pnl_percent = (pnl / cost_basis * 100) if cost_basis > 0 else 0.0

            return {
                "pnl": round(pnl, 2),
                "pnl_percent": round(pnl_percent, 2),
                "cost_basis": round(cost_basis, 2),
                "current_value": round(current_value, 2),
                "quantity": round(position_quantity, 6),
                "average_price": round(average_price, 2),
            }

        except Exception as e:
            logger.error(
                f"Error calculating position P&L: {e}",
                exc_info=True,
                extra={"user_id": user_id, "symbol": symbol, "mode": mode},
            )
            return {
                "pnl": 0.0,
                "pnl_percent": 0.0,
                "cost_basis": 0.0,
                "current_value": 0.0,
                "quantity": 0.0,
                "average_price": 0.0,
            }

    async def calculate_portfolio_pnl(
        self, user_id: int, mode: str = "paper", period_hours: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Calculate total portfolio P&L.

        Args:
            user_id: User ID
            mode: Trading mode ("paper" or "real")
            period_hours: Optional time period in hours (e.g., 24 for 24h P&L)

        Returns:
            Dict with total_pnl, realized_pnl, unrealized_pnl, pnl_24h, etc.
        """
        try:
            # ✅ Data access delegated to repository
            trades = await self.trade_repository.get_completed_trades_for_pnl(
                self.db,
                user_id=user_id,
                mode=mode,
                pair=None,
                period_hours=period_hours,
            )

            # Calculate realized P&L from completed trades
            realized_pnl = 0.0
            total_fees = 0.0

            # Track positions for unrealized P&L
            positions: Dict[str, Dict[str, float]] = (
                {}
            )  # symbol -> {quantity, cost_basis}

            for trade in trades:
                symbol = trade.pair
                total_fees += trade.fee or 0.0

                if symbol not in positions:
                    positions[symbol] = {"quantity": 0.0, "cost_basis": 0.0}

                if trade.side == "buy":
                    positions[symbol]["quantity"] += trade.amount
                    positions[symbol]["cost_basis"] += trade.amount * trade.price
                elif trade.side == "sell":
                    # Calculate realized P&L for this sell
                    sell_value = trade.amount * trade.price
                    avg_cost = (
                        positions[symbol]["cost_basis"] / positions[symbol]["quantity"]
                        if positions[symbol]["quantity"] > 0
                        else 0.0
                    )
                    cost_basis_sold = trade.amount * avg_cost
                    trade_pnl = sell_value - cost_basis_sold - (trade.fee or 0.0)
                    realized_pnl += trade_pnl

                    # Update position
                    positions[symbol]["quantity"] -= trade.amount
                    positions[symbol]["cost_basis"] -= cost_basis_sold

            # Note: Unrealized P&L requires current prices, which should be fetched separately
            # This method returns realized P&L only

            return {
                "realized_pnl": round(realized_pnl, 2),
                "total_fees": round(total_fees, 2),
                "net_pnl": round(realized_pnl - total_fees, 2),
                "total_trades": len(trades),
            }

        except Exception as e:
            logger.error(
                f"Error calculating portfolio P&L: {e}",
                exc_info=True,
                extra={"user_id": user_id, "mode": mode, "period_hours": period_hours},
            )
            return {
                "realized_pnl": 0.0,
                "total_fees": 0.0,
                "net_pnl": 0.0,
                "total_trades": 0,
            }

    async def calculate_24h_pnl(self, user_id: int, mode: str = "paper") -> float:
        """Calculate 24-hour P&L"""
        result = await self.calculate_portfolio_pnl(user_id, mode, period_hours=24)
        return result.get("net_pnl", 0.0)

    async def calculate_total_pnl(self, user_id: int, mode: str = "paper") -> float:
        """Calculate total P&L (all time)"""
        result = await self.calculate_portfolio_pnl(user_id, mode, period_hours=None)
        return result.get("net_pnl", 0.0)
