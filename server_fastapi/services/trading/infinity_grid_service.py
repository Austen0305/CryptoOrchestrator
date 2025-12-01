"""
Infinity Grid Trading Service
Implements infinity grid bot functionality - dynamic grid that follows price movements.
"""

import logging
import uuid
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.infinity_grid import InfinityGrid
from ...repositories.infinity_grid_repository import InfinityGridRepository
from ...services.exchange_service import ExchangeService
from ...services.advanced_risk_manager import AdvancedRiskManager
from ...database import get_db_context
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class InfinityGridService:
    """
    Service for Infinity Grid bot operations.
    Dynamic grid that adjusts upper/lower bounds as price moves.
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        self.repository = InfinityGridRepository()
        self._session = session
        self.risk_manager = AdvancedRiskManager.get_instance()

    @asynccontextmanager
    async def _get_session(self):
        if self._session is not None:
            yield self._session
        else:
            async with get_db_context() as session:
                yield session

    async def create_infinity_grid(
        self,
        user_id: int,
        name: str,
        symbol: str,
        exchange: str,
        grid_count: int,
        grid_spacing_percent: float,
        order_amount: float,
        trading_mode: str = "paper",
        upper_adjustment_percent: float = 5.0,
        lower_adjustment_percent: float = 5.0,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Create a new infinity grid bot."""
        try:
            # Validate inputs
            if grid_count < 2:
                raise ValueError("Grid count must be at least 2")
            if grid_spacing_percent <= 0:
                raise ValueError("Grid spacing must be positive")
            if order_amount <= 0:
                raise ValueError("Order amount must be positive")

            bot_id = f"infinity-{user_id}-{uuid.uuid4().hex[:12]}"

            async with self._get_session() as session:
                # Get current market price to set initial bounds
                exchange_service = ExchangeService(exchange)
                current_price = await exchange_service.get_market_price(symbol)
                
                if not current_price:
                    raise ValueError(f"Could not get market price for {symbol}")

                # Calculate initial bounds based on grid spacing
                price_range = current_price * (grid_spacing_percent / 100) * (grid_count - 1)
                initial_upper = current_price + (price_range / 2)
                initial_lower = current_price - (price_range / 2)

                # Create infinity grid bot
                infinity_grid = InfinityGrid(
                    id=bot_id,
                    user_id=user_id,
                    name=name,
                    symbol=symbol,
                    exchange=exchange,
                    trading_mode=trading_mode,
                    grid_count=grid_count,
                    grid_spacing_percent=grid_spacing_percent,
                    order_amount=order_amount,
                    current_upper_price=initial_upper,
                    current_lower_price=initial_lower,
                    initial_price=current_price,
                    upper_adjustment_percent=upper_adjustment_percent,
                    lower_adjustment_percent=lower_adjustment_percent,
                    active=False,
                    status="stopped",
                    grid_state=json.dumps({
                        "orders": [],
                        "filled_orders": [],
                        "current_price": current_price
                    }),
                    config=json.dumps(config or {})
                )

                session.add(infinity_grid)
                await session.commit()
                await session.refresh(infinity_grid)

                logger.info(f"Created infinity grid {bot_id} for user {user_id}")
                return bot_id

        except Exception as e:
            logger.error(f"Error creating infinity grid for user {user_id}: {str(e)}", exc_info=True)
            raise

    async def start_infinity_grid(self, bot_id: str, user_id: int) -> bool:
        """Start an infinity grid bot."""
        try:
            async with self._get_session() as session:
                bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not bot:
                    return False

                if bot.active:
                    return True

                # Place initial grid orders
                await self._place_initial_grid_orders(bot, session)

                # Update bot status
                updated_bot = await self.repository.update_bot_status(
                    session, bot_id, user_id, True, "running"
                )

                return updated_bot is not None

        except Exception as e:
            logger.error(f"Error starting infinity grid {bot_id}: {str(e)}", exc_info=True)
            return False

    async def stop_infinity_grid(self, bot_id: str, user_id: int) -> bool:
        """Stop an infinity grid bot."""
        try:
            async with self._get_session() as session:
                bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not bot:
                    return False

                # Cancel all orders
                await self._cancel_all_orders(bot, session)

                # Update bot status
                updated_bot = await self.repository.update_bot_status(
                    session, bot_id, user_id, False, "stopped"
                )

                return updated_bot is not None

        except Exception as e:
            logger.error(f"Error stopping infinity grid {bot_id}: {str(e)}", exc_info=True)
            return False

    async def process_infinity_grid_cycle(self, bot_id: str, user_id: int) -> Dict[str, Any]:
        """Process one infinity grid cycle: check price and adjust bounds if needed."""
        try:
            async with self._get_session() as session:
                bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not bot or not bot.active:
                    return {"action": "skipped", "reason": "bot_inactive"}

                # Get current market price
                exchange_service = ExchangeService(bot.exchange)
                current_price = await exchange_service.get_market_price(bot.symbol)

                if not current_price:
                    return {"action": "skipped", "reason": "no_price_data"}

                # Check if bounds need adjustment
                adjustment_needed = await self._check_bound_adjustment(bot, current_price)

                if adjustment_needed["adjust"]:
                    # Adjust grid bounds
                    await self._adjust_grid_bounds(bot, current_price, adjustment_needed, session)

                # Check for filled orders and rebalance
                grid_state = json.loads(bot.grid_state) if bot.grid_state else {"orders": [], "filled_orders": []}
                filled_orders = await self._check_filled_orders(bot, grid_state, current_price, session)

                if filled_orders:
                    await self._rebalance_grid(bot, filled_orders, grid_state, current_price, session)

                return {"action": "processed", "current_price": current_price}

        except Exception as e:
            logger.error(f"Error processing infinity grid cycle: {str(e)}", exc_info=True)
            return {"action": "error", "error": str(e)}

    async def _check_bound_adjustment(self, bot: InfinityGrid, current_price: float) -> Dict[str, Any]:
        """Check if grid bounds need adjustment."""
        upper_threshold = bot.current_upper_price * (1 - bot.upper_adjustment_percent / 100)
        lower_threshold = bot.current_lower_price * (1 + bot.lower_adjustment_percent / 100)

        if current_price >= upper_threshold:
            # Price moved up significantly - adjust upper bound
            new_upper = current_price * (1 + bot.upper_adjustment_percent / 100)
            return {"adjust": True, "direction": "up", "new_upper": new_upper, "new_lower": bot.current_lower_price}
        elif current_price <= lower_threshold:
            # Price moved down significantly - adjust lower bound
            new_lower = current_price * (1 - bot.lower_adjustment_percent / 100)
            return {"adjust": True, "direction": "down", "new_upper": bot.current_upper_price, "new_lower": new_lower}

        return {"adjust": False}

    async def _adjust_grid_bounds(
        self,
        bot: InfinityGrid,
        current_price: float,
        adjustment: Dict[str, Any],
        session: AsyncSession
    ) -> None:
        """Adjust grid bounds and rebalance orders."""
        # Update bounds
        await self.repository.update_grid_bounds(
            session, bot.id, bot.user_id,
            adjustment["new_upper"], adjustment["new_lower"]
        )

        # Cancel old orders outside new bounds
        # Place new orders within new bounds
        # This is simplified - real implementation would be more complex

    async def _place_initial_grid_orders(self, bot: InfinityGrid, session: AsyncSession) -> List[Dict[str, Any]]:
        """Place initial grid orders."""
        # Similar to grid trading service
        # Calculate grid prices within current bounds
        # Place buy/sell orders
        return []

    async def _check_filled_orders(
        self,
        bot: InfinityGrid,
        grid_state: Dict[str, Any],
        current_price: float,
        session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Check which orders have been filled."""
        filled = []
        for order in grid_state.get("orders", []):
            if order.get("status") == "open":
                order_price = order.get("price")
                order_side = order.get("side")
                if (order_side == "buy" and current_price <= order_price) or \
                   (order_side == "sell" and current_price >= order_price):
                    filled.append(order)
        return filled

    async def _rebalance_grid(
        self,
        bot: InfinityGrid,
        filled_orders: List[Dict[str, Any]],
        grid_state: Dict[str, Any],
        current_price: float,
        session: AsyncSession
    ) -> None:
        """Rebalance grid after orders are filled."""
        # Similar to grid trading rebalance
        # Remove filled orders, place new orders
        pass

    async def _cancel_all_orders(self, bot: InfinityGrid, session: AsyncSession) -> None:
        """Cancel all open orders."""
        grid_state = json.loads(bot.grid_state) if bot.grid_state else {"orders": []}
        for order in grid_state.get("orders", []):
            order["status"] = "cancelled"
        # Update grid state
        pass

    async def get_infinity_grid(self, bot_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Get infinity grid details."""
        try:
            async with self._get_session() as session:
                bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not bot:
                    return None
                return bot.to_dict()
        except Exception as e:
            logger.error(f"Error getting infinity grid {bot_id}: {str(e)}", exc_info=True)
            return None

    async def list_user_infinity_grids(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List all infinity grids for a user."""
        try:
            async with self._get_session() as session:
                bots = await self.repository.get_user_infinity_grids(session, user_id, skip, limit)
                return [bot.to_dict() for bot in bots]
        except Exception as e:
            logger.error(f"Error listing infinity grids: {str(e)}", exc_info=True)
            return []

