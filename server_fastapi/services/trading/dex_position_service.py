"""
DEX Position Service
Manages open positions from DEX swaps for better P&L tracking.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...repositories.dex_position_repository import DEXPositionRepository
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ...models.dex_position import DEXPosition
from ...repositories.dex_position_repository import DEXPositionRepository
from ..blockchain.token_registry import get_token_registry
from ..market_data_service import get_market_data_service

logger = logging.getLogger(__name__)


class DEXPositionService:
    """Service for managing DEX positions"""

    def __init__(
        self,
        db_session: AsyncSession,
        position_repository: DEXPositionRepository | None = None,
    ):
        # ✅ Repository injected via dependency injection (Service Layer Pattern)
        self.position_repository = position_repository or DEXPositionRepository()
        self.db = db_session  # Keep db for transaction handling
        self.token_registry = get_token_registry()
        self.market_data = get_market_data_service()

    async def open_position(
        self,
        user_id: int,
        trade_id: int,
        chain_id: int,
        token_address: str,
        token_symbol: str,
        amount: float,
        entry_price: float,
        amount_usd: float,
    ) -> DEXPosition | None:
        """
        Open a new position from a DEX trade.

        Args:
            user_id: User ID
            trade_id: DEX trade ID that opened this position
            chain_id: Blockchain chain ID
            token_address: Token contract address
            token_symbol: Token symbol
            amount: Token amount
            entry_price: Entry price in USD
            amount_usd: USD value at entry

        Returns:
            DEXPosition instance or None if error
        """
        try:
            # ✅ Business logic: Create position data
            # ✅ Data access delegated to repository
            position = await self.position_repository.create_position(
                self.db,
                {
                    "user_id": user_id,
                    "chain_id": chain_id,
                    "token_address": token_address,
                    "token_symbol": token_symbol,
                    "amount": amount,
                    "amount_usd": amount_usd,
                    "entry_price": entry_price,
                    "entry_trade_id": trade_id,
                    "current_price": entry_price,  # Initially same as entry
                    "current_value_usd": amount_usd,  # Initially same as entry value
                    "unrealized_pnl": 0.0,
                    "unrealized_pnl_percent": 0.0,
                    "is_open": True,
                },
            )

            logger.info(
                f"Opened DEX position: {position.id} for user {user_id}",
                extra={
                    "position_id": position.id,
                    "user_id": user_id,
                    "token_symbol": token_symbol,
                    "amount": amount,
                },
            )

            return position
        except Exception as e:
            logger.error(f"Error opening position: {e}", exc_info=True)
            await self.db.rollback()
            return None

    async def update_position_pnl(
        self,
        position_id: int,
        current_price: float | None = None,
    ) -> DEXPosition | None:
        """
        Update position P&L with current price.

        Args:
            position_id: Position ID
            current_price: Current token price (fetched if not provided)

        Returns:
            Updated DEXPosition or None if error
        """
        try:
            # ✅ Data access delegated to repository
            position = await self.position_repository.get_by_id(self.db, position_id)

            if not position:
                return None

            if not position.is_open:
                return position  # Already closed

            # ✅ Business logic: Get current price if not provided
            if current_price is None:
                price_symbol = f"{position.token_symbol}/USD"
                current_price = (
                    await self.market_data.get_price(price_symbol)
                    or position.entry_price
                )

            # ✅ Business logic: Calculate current value and P&L
            current_value_usd = position.amount * current_price
            unrealized_pnl = current_value_usd - position.amount_usd
            unrealized_pnl_percent = (
                (unrealized_pnl / position.amount_usd * 100)
                if position.amount_usd > 0
                else 0.0
            )

            # ✅ Data access delegated to repository
            position = await self.position_repository.update_position(
                self.db,
                position_id,
                {
                    "current_price": current_price,
                    "current_value_usd": current_value_usd,
                    "unrealized_pnl": unrealized_pnl,
                    "unrealized_pnl_percent": unrealized_pnl_percent,
                    "last_updated_at": datetime.utcnow(),
                },
            )

            return position
        except Exception as e:
            logger.error(f"Error updating position P&L: {e}", exc_info=True)
            await self.db.rollback()
            return None

    async def close_position(
        self,
        position_id: int,
        exit_trade_id: int,
        exit_price: float,
    ) -> DEXPosition | None:
        """
        Close a position.

        Args:
            position_id: Position ID
            exit_trade_id: DEX trade ID that closed this position
            exit_price: Exit price in USD

        Returns:
            Closed DEXPosition or None if error
        """
        try:
            # ✅ Data access delegated to repository
            position = await self.position_repository.get_by_id(self.db, position_id)

            if not position:
                return None

            if not position.is_open:
                return position  # Already closed

            # ✅ Business logic: Calculate realized P&L
            exit_value_usd = position.amount * exit_price
            realized_pnl = exit_value_usd - position.amount_usd
            realized_pnl_percent = (
                (realized_pnl / position.amount_usd * 100)
                if position.amount_usd > 0
                else 0.0
            )

            # ✅ Data access delegated to repository
            position = await self.position_repository.update_position(
                self.db,
                position_id,
                {
                    "is_open": False,
                    "closed_at": datetime.utcnow(),
                    "exit_trade_id": exit_trade_id,
                    "exit_price": exit_price,
                    "realized_pnl": realized_pnl,
                    "realized_pnl_percent": realized_pnl_percent,
                    "current_price": exit_price,
                    "current_value_usd": exit_value_usd,
                    "unrealized_pnl": 0.0,
                    "unrealized_pnl_percent": 0.0,
                    "last_updated_at": datetime.utcnow(),
                },
            )

            logger.info(
                f"Closed DEX position: {position_id}",
                extra={
                    "position_id": position_id,
                    "realized_pnl": realized_pnl,
                    "realized_pnl_percent": realized_pnl_percent,
                },
            )

            return position
        except Exception as e:
            logger.error(f"Error closing position: {e}", exc_info=True)
            await self.db.rollback()
            return None

    async def get_user_positions(
        self,
        user_id: int,
        chain_id: int | None = None,
        is_open: bool | None = None,
    ) -> list[DEXPosition]:
        """
        Get user's positions.

        Args:
            user_id: User ID
            chain_id: Filter by chain ID (optional)
            is_open: Filter by open/closed status (optional)

        Returns:
            List of DEXPosition instances
        """
        try:
            # ✅ Data access delegated to repository
            return await self.position_repository.get_by_user(
                self.db, user_id, chain_id=chain_id, is_open=is_open
            )
        except Exception as e:
            logger.error(f"Error getting user positions: {e}", exc_info=True)
            return []

    async def update_all_positions_pnl(self, user_id: int | None = None) -> int:
        """
        Update P&L for all open positions (or user's positions).

        Args:
            user_id: User ID (optional, updates all if None)

        Returns:
            Number of positions updated
        """
        try:
            # ✅ Data access delegated to repository
            positions = await self.position_repository.get_open_positions(
                self.db, user_id=user_id
            )

            updated_count = 0
            for position in positions:
                updated = await self.update_position_pnl(position.id)
                if updated:
                    updated_count += 1

            logger.info(
                f"Updated P&L for {updated_count} positions",
                extra={"updated_count": updated_count, "user_id": user_id},
            )

            return updated_count
        except Exception as e:
            logger.error(f"Error updating all positions P&L: {e}", exc_info=True)
            return 0
