"""
P&L Calculation Service
Calculates profit and loss from trade history for portfolios and positions.
"""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..repositories.trade_repository import TradeRepository
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.trade_repository import TradeRepository

logger = logging.getLogger(__name__)


class PnLService:
    """Service for calculating profit and loss from trade history"""

    def __init__(
        self,
        db: AsyncSession,
        trade_repository: Optional["TradeRepository"] = None,
    ):
        # ✅ Repository injected via dependency injection (Service Layer Pattern)
        self.trade_repository = trade_repository or TradeRepository()
        self.db = db  # Keep db for transaction handling

    async def calculate_batch_position_pnl(
        self,
        user_id: int,
        symbols: list[str],
        current_prices: dict[str, float],
        mode: str = "paper",
    ) -> dict[str, dict[str, float]]:
        """
        Calculate P&L for multiple positions in batch.

        Args:
            user_id: User ID
            symbols: List of trading pair symbols
            current_prices: Dict mapping symbol to current market price
            mode: Trading mode ("paper" or "real")

        Returns:
            Dict mapping symbol to P&L data dict
        """
        try:
            # ✅ Fetch ALL trades for ALL symbols in parent query
            trades = await self.trade_repository.get_completed_trades_for_pnl(
                self.db, user_id=user_id, mode=mode, pairs=symbols
            )

            # Group trades by symbol
            trades_by_symbol: dict[str, list] = {symbol: [] for symbol in symbols}
            for trade in trades:
                if trade.pair in trades_by_symbol:
                    trades_by_symbol[trade.pair].append(trade)

            results = {}
            for symbol in symbols:
                symbol_trades = trades_by_symbol[symbol]
                price = current_prices.get(symbol, 0.0)
                results[symbol] = self._calculate_fifo_pnl(symbol_trades, price)

            return results

        except Exception as e:
            logger.error(
                f"Error in batch P&L calculation: {e}",
                exc_info=True,
                extra={"user_id": user_id, "symbols": symbols, "mode": mode},
            )
            return {symbol: self._empty_pnl_result() for symbol in symbols}

    def _calculate_fifo_pnl(
        self, trades: list, current_price: float
    ) -> dict[str, float]:
        """Helper to calculate FIFO P&L for a set of trades."""
        if not trades:
            return self._empty_pnl_result()

        # Calculate using FIFO method
        position_stats = {"quantity": 0.0, "cost_basis": 0.0}
        buy_queue: list[tuple[float, float]] = []  # (quantity, price)
        for trade in trades:
            if trade.side == "buy":
                self._process_buy_trade(trade, buy_queue, position_stats)
            elif trade.side == "sell":
                self._process_sell_trade(trade, buy_queue, position_stats)
        
        position_quantity = position_stats["quantity"]
        cost_basis = position_stats["cost_basis"]

        # Calculate current value and P&L
        current_value = position_quantity * current_price
        average_price = cost_basis / position_quantity if position_quantity > 0 else 0.0
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

    def _process_buy_trade(
        self, trade, buy_queue: list[tuple[float, float]], position_stats: dict[str, float]
    ) -> None:
        """Helper to process a buy trade."""
        buy_queue.append((trade.amount, trade.price))
        position_stats["quantity"] += trade.amount
        position_stats["cost_basis"] += trade.amount * trade.price

    def _process_sell_trade(
        self, trade, buy_queue: list[tuple[float, float]], position_stats: dict[str, float]
    ) -> None:
        """Helper to process a sell trade using FIFO."""
        remaining_sell = trade.amount

        # FIFO: sell from oldest buys first
        while remaining_sell > 0 and buy_queue:
            buy_qty, buy_price = buy_queue[0]

            if buy_qty <= remaining_sell:
                # Fully consumed this buy
                position_stats["cost_basis"] -= buy_qty * buy_price
                position_stats["quantity"] -= buy_qty
                remaining_sell -= buy_qty
                buy_queue.pop(0)
            else:
                # Partially consumed
                position_stats["cost_basis"] -= remaining_sell * buy_price
                position_stats["quantity"] -= remaining_sell
                buy_queue[0] = (buy_qty - remaining_sell, buy_price)
                remaining_sell = 0



    def _empty_pnl_result(self) -> dict[str, float]:
        """Returns default empty P&L structure."""
        return {
            "pnl": 0.0,
            "pnl_percent": 0.0,
            "cost_basis": 0.0,
            "current_value": 0.0,
            "quantity": 0.0,
            "average_price": 0.0,
        }

    async def calculate_position_pnl(
        self, user_id: int, symbol: str, current_price: float, mode: str = "paper"
    ) -> dict[str, float]:
        """
        Calculate P&L for a specific position.
        """
        try:
            trades = await self.trade_repository.get_completed_trades_for_pnl(
                self.db, user_id=user_id, mode=mode, pairs=[symbol]
            )
            return self._calculate_fifo_pnl(trades, current_price)
        except Exception as e:
            logger.error(f"Error calculating position P&L: {e}", exc_info=True)
            return self._empty_pnl_result()

    async def calculate_portfolio_pnl(
        self, user_id: int, mode: str = "paper", period_hours: int | None = None
    ) -> dict[str, float]:
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
                pairs=None,
                period_hours=period_hours,
            )

            # Calculate realized P&L from completed trades
            realized_pnl = 0.0
            total_fees = 0.0

            # Track positions for unrealized P&L
            positions: dict[str, dict[str, float]] = (
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
