"""
Futures Trading Service
Implements futures trading with leverage support.

NOTE: Futures trading on DEX requires perpetual swap protocols (e.g., GMX, dYdX, Perpetual Protocol).
This service currently supports paper trading and position tracking.
Real futures trading may need to be disabled or integrated with DEX perpetual protocols.
"""

import json
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db_context
from ...models.futures_position import FuturesPosition
from ...repositories.futures_position_repository import FuturesPositionRepository
from ...services.advanced_risk_manager import AdvancedRiskManager
from ...services.coingecko_service import CoinGeckoService

logger = logging.getLogger(__name__)


class FuturesTradingService:
    """
    Service for Futures Trading operations.
    Supports leverage trading with margin management and liquidation protection.
    """

    def __init__(self, session: AsyncSession | None = None):
        self.repository = FuturesPositionRepository()
        self._session = session
        self.risk_manager = AdvancedRiskManager.get_instance()
        self.coingecko = CoinGeckoService()

    @asynccontextmanager
    async def _get_session(self):
        if self._session is not None:
            yield self._session
        else:
            async with get_db_context() as session:
                yield session

    async def create_futures_position(
        self,
        user_id: int,
        symbol: str,
        exchange: str,
        side: str,
        quantity: float,
        leverage: int,
        trading_mode: str = "paper",
        entry_price: float | None = None,
        stop_loss_price: float | None = None,
        take_profit_price: float | None = None,
        trailing_stop_percent: float | None = None,
        name: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> str | None:
        """
        Create a new futures position.

        Args:
            user_id: User ID
            symbol: Trading symbol (e.g., "BTC/USD")
            exchange: Exchange name
            side: "long" or "short"
            quantity: Position size
            leverage: Leverage multiplier (e.g., 10 for 10x)
            trading_mode: "paper" or "real"
            entry_price: Entry price (None = market price)
            stop_loss_price: Stop loss price
            take_profit_price: Take profit price
            trailing_stop_percent: Trailing stop percentage
            name: Optional position name
            config: Additional configuration

        Returns:
            Position ID if successful, None otherwise
        """
        try:
            # Validate inputs
            if side not in ["long", "short"]:
                raise ValueError("Side must be 'long' or 'short'")
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
            if leverage < 1 or leverage > 125:
                raise ValueError("Leverage must be between 1 and 125")

            position_id = f"futures-{user_id}-{uuid.uuid4().hex[:12]}"

            async with self._get_session() as session:
                # Get current market price if entry price not provided
                if not entry_price:
                    entry_price = await self.coingecko.get_price(symbol)
                    if not entry_price:
                        raise ValueError(f"Could not get market price for {symbol}")

                # Extract chain_id from config or use default
                chain_id = 1  # Default to Ethereum
                if config and isinstance(config, dict):
                    chain_id = config.get("chain_id", 1)
                elif isinstance(exchange, str) and exchange.isdigit():
                    chain_id = int(exchange)

                # Calculate margin requirements
                position_value = quantity * entry_price
                margin_required = position_value / leverage
                maintenance_margin = (
                    margin_required * 0.5
                )  # Typically 50% of initial margin

                # Calculate liquidation price
                liquidation_price = self._calculate_liquidation_price(
                    entry_price, side, leverage, margin_required
                )

                # Create futures position
                # NOTE: Real futures trading requires DEX perpetual protocols (GMX, dYdX, etc.)
                # For now, only paper trading is fully supported
                if trading_mode == "real":
                    logger.warning(
                        f"Real futures trading not yet supported for DEX. "
                        f"Position {position_id} created but execution disabled. "
                        f"Consider using DEX perpetual protocols (GMX, dYdX) for real futures."
                    )

                futures_position = FuturesPosition(
                    id=position_id,
                    user_id=user_id,
                    name=name or f"{side.upper()} {symbol} {leverage}x",
                    symbol=symbol,
                    exchange=str(
                        chain_id
                    ),  # Store chain_id as string in exchange field (temporary)
                    trading_mode=trading_mode,
                    side=side,
                    leverage=leverage,
                    quantity=quantity,
                    entry_price=entry_price,
                    current_price=entry_price,
                    margin_used=margin_required,
                    margin_available=0.0,  # Would need to get from exchange
                    liquidation_price=liquidation_price,
                    maintenance_margin=maintenance_margin,
                    stop_loss_price=stop_loss_price,
                    take_profit_price=take_profit_price,
                    trailing_stop_percent=trailing_stop_percent,
                    is_open=True,
                    status="open",
                    unrealized_pnl=0.0,
                    realized_pnl=0.0,
                    total_pnl=0.0,
                    pnl_percent=0.0,
                    liquidation_risk=0.0,
                    margin_ratio=1.0,
                    config=json.dumps((config or {}) | {"chain_id": chain_id}),
                )

                session.add(futures_position)
                await session.commit()
                await session.refresh(futures_position)

                logger.info(
                    f"Created futures position {position_id} for user {user_id}"
                )
                return position_id

        except Exception as e:
            logger.error(
                f"Error creating futures position for user {user_id}: {str(e)}",
                exc_info=True,
            )
            raise

    def _calculate_liquidation_price(
        self, entry_price: float, side: str, leverage: int, margin: float
    ) -> float:
        """Calculate liquidation price for a futures position."""
        if side == "long":
            # Long position liquidates when price drops too much
            # Simplified calculation
            price_drop = entry_price * (1 / leverage)
            return entry_price - price_drop
        else:
            # Short position liquidates when price rises too much
            price_rise = entry_price * (1 / leverage)
            return entry_price + price_rise

    async def update_position_pnl(
        self, position_id: str, user_id: int
    ) -> dict[str, Any]:
        """Update P&L for a futures position based on current market price."""
        try:
            async with self._get_session() as session:
                position = await self.repository.get_by_user_and_id(
                    session, position_id, user_id
                )
                if not position or not position.is_open:
                    return {"action": "skipped", "reason": "position_not_open"}

                # Get current market price from CoinGecko
                current_price = await self.coingecko.get_price(position.symbol)

                if not current_price:
                    return {"action": "skipped", "reason": "no_price_data"}

                # Calculate unrealized P&L
                if position.side == "long":
                    unrealized_pnl = (
                        current_price - position.entry_price
                    ) * position.quantity
                else:
                    unrealized_pnl = (
                        position.entry_price - current_price
                    ) * position.quantity

                # Calculate total P&L
                total_pnl = position.realized_pnl + unrealized_pnl
                pnl_percent = (
                    (total_pnl / position.margin_used * 100)
                    if position.margin_used > 0
                    else 0.0
                )

                # Calculate liquidation risk
                price_distance_to_liquidation = abs(
                    current_price - position.liquidation_price
                )
                price_distance_percent = (
                    (price_distance_to_liquidation / position.entry_price * 100)
                    if position.entry_price > 0
                    else 0
                )
                liquidation_risk = max(0.0, min(100.0, 100.0 - price_distance_percent))

                # Calculate margin ratio
                margin_ratio = (
                    (position.margin_used / position.maintenance_margin)
                    if position.maintenance_margin > 0
                    else 0.0
                )

                # Check for liquidation
                if (
                    current_price <= position.liquidation_price
                    if position.side == "long"
                    else current_price >= position.liquidation_price
                ):
                    # Position would be liquidated
                    await self._liquidate_position(position, session)
                    return {"action": "liquidated", "price": current_price}

                # Check stop loss / take profit
                tp_sl_result = await self._check_stop_loss_take_profit(
                    position, current_price, session
                )
                if tp_sl_result["should_close"]:
                    return {
                        "action": "closed",
                        "reason": tp_sl_result["reason"],
                        "price": current_price,
                    }

                # Update position
                await self.repository.update_position_pnl(
                    session,
                    position_id,
                    user_id,
                    current_price,
                    unrealized_pnl,
                    position.realized_pnl,
                    total_pnl,
                    pnl_percent,
                    liquidation_risk,
                    margin_ratio,
                )

                return {
                    "action": "updated",
                    "current_price": current_price,
                    "unrealized_pnl": unrealized_pnl,
                    "total_pnl": total_pnl,
                    "liquidation_risk": liquidation_risk,
                }

        except Exception as e:
            logger.error(f"Error updating position P&L: {str(e)}", exc_info=True)
            return {"action": "error", "error": str(e)}

    async def close_futures_position(
        self, position_id: str, user_id: int, close_price: float | None = None
    ) -> dict[str, Any]:
        """Close a futures position."""
        try:
            async with self._get_session() as session:
                position = await self.repository.get_by_user_and_id(
                    session, position_id, user_id
                )
                if not position or not position.is_open:
                    return {"action": "skipped", "reason": "position_not_open"}

                # Get close price if not provided
                if not close_price:
                    close_price = await self.coingecko.get_price(position.symbol)
                    if not close_price:
                        return {
                            "action": "error",
                            "error": "Could not get market price",
                        }

                # Calculate realized P&L
                if position.side == "long":
                    realized_pnl = (
                        close_price - position.entry_price
                    ) * position.quantity
                else:
                    realized_pnl = (
                        position.entry_price - close_price
                    ) * position.quantity

                total_pnl = position.realized_pnl + realized_pnl

                # Close position
                updated_position = await self.repository.close_position(
                    session, position_id, user_id, realized_pnl, total_pnl
                )

                if updated_position:
                    return {
                        "action": "closed",
                        "close_price": close_price,
                        "realized_pnl": realized_pnl,
                        "total_pnl": total_pnl,
                    }
                else:
                    return {"action": "error", "error": "Failed to close position"}

        except Exception as e:
            logger.error(f"Error closing futures position: {str(e)}", exc_info=True)
            return {"action": "error", "error": str(e)}

    async def _check_stop_loss_take_profit(
        self, position: FuturesPosition, current_price: float, session: AsyncSession
    ) -> dict[str, Any]:
        """Check if stop loss or take profit conditions are met."""
        # Check stop loss
        if position.stop_loss_price:
            if (
                position.side == "long"
                and current_price <= position.stop_loss_price
                or position.side == "short"
                and current_price >= position.stop_loss_price
            ):
                await self.close_futures_position(
                    position.id, position.user_id, current_price
                )
                return {"should_close": True, "reason": "stop_loss_triggered"}

        # Check take profit
        if position.take_profit_price:
            if (
                position.side == "long"
                and current_price >= position.take_profit_price
                or (
                    position.side == "short"
                    and current_price <= position.take_profit_price
                )
            ):
                await self.close_futures_position(
                    position.id, position.user_id, current_price
                )
                return {"should_close": True, "reason": "take_profit_reached"}

        # Check trailing stop
        if position.trailing_stop_percent:
            # Simplified trailing stop logic
            if position.side == "long":
                # Update trailing stop for long position
                pass
            else:
                # Update trailing stop for short position
                pass

        return {"should_close": False, "reason": None}

    async def _liquidate_position(
        self, position: FuturesPosition, session: AsyncSession
    ) -> None:
        """Liquidate a futures position."""
        # Calculate final P&L at liquidation price
        if position.side == "long":
            realized_pnl = (
                position.liquidation_price - position.entry_price
            ) * position.quantity
        else:
            realized_pnl = (
                position.entry_price - position.liquidation_price
            ) * position.quantity

        total_pnl = position.realized_pnl + realized_pnl

        await self.repository.close_position(
            session, position.id, position.user_id, realized_pnl, total_pnl
        )

        # Update status to liquidated
        from sqlalchemy import update

        stmt = (
            update(FuturesPosition)
            .where(FuturesPosition.id == position.id)
            .values(status="liquidated")
        )
        await session.execute(stmt)
        await session.commit()

    async def get_futures_position(
        self, position_id: str, user_id: int
    ) -> dict[str, Any] | None:
        """Get futures position details."""
        try:
            async with self._get_session() as session:
                position = await self.repository.get_by_user_and_id(
                    session, position_id, user_id
                )
                if not position:
                    return None
                return position.to_dict()
        except Exception as e:
            logger.error(
                f"Error getting futures position {position_id}: {str(e)}", exc_info=True
            )
            return None

    async def list_user_futures_positions(
        self, user_id: int, skip: int = 0, limit: int = 100, open_only: bool = False
    ) -> tuple[list[dict[str, Any]], int]:
        """List all futures positions for a user with total count."""
        try:
            async with self._get_session() as session:
                if open_only:
                    positions = await self.repository.get_open_positions(
                        session, user_id
                    )
                    # For open_only, return all positions with total = length
                    return [position.to_dict() for position in positions], len(
                        positions
                    )
                else:
                    positions = await self.repository.get_user_futures_positions(
                        session, user_id, skip, limit
                    )
                    total = await self.repository.count_user_futures_positions(
                        session, user_id
                    )
                    return [position.to_dict() for position in positions], total
        except Exception as e:
            logger.error(f"Error listing futures positions: {str(e)}", exc_info=True)
            return [], 0
