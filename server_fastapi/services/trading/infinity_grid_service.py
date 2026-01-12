"""
Infinity Grid Trading Service
Implements infinity grid bot functionality - dynamic grid that follows price movements.
"""

import json
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db_context
from ...models.infinity_grid import InfinityGrid
from ...repositories.infinity_grid_repository import InfinityGridRepository
from ...services.advanced_risk_manager import AdvancedRiskManager
from ...services.market_data_service import get_market_data_service
from ...services.trading.dex_trading_service import DEXTradingService

logger = logging.getLogger(__name__)


class InfinityGridService:
    """
    Service for Infinity Grid bot operations.
    Dynamic grid that adjusts upper/lower bounds as price moves.
    """

    def __init__(self, session: AsyncSession | None = None):
        self.repository = InfinityGridRepository()
        self._session = session
        self.risk_manager = AdvancedRiskManager.get_instance()
        self.market_data = get_market_data_service()
        self.dex_service = DEXTradingService()

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
        config: dict[str, Any] | None = None,
    ) -> str | None:
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
                current_price = await self.market_data.get_price(symbol)

                if not current_price:
                    raise ValueError(f"Could not get market price for {symbol}")

                # Calculate initial bounds based on grid spacing
                price_range = (
                    current_price * (grid_spacing_percent / 100) * (grid_count - 1)
                )
                initial_upper = current_price + (price_range / 2)
                initial_lower = current_price - (price_range / 2)

                # Extract chain_id from config or use default
                chain_id = 1  # Default to Ethereum
                if config and isinstance(config, dict):
                    chain_id = config.get("chain_id", 1)
                elif isinstance(exchange, str) and exchange.isdigit():
                    chain_id = int(exchange)

                # Create infinity grid bot (using exchange field for chain_id temporarily)
                infinity_grid = InfinityGrid(
                    id=bot_id,
                    user_id=user_id,
                    name=name,
                    symbol=symbol,
                    exchange=str(
                        chain_id
                    ),  # Store chain_id as string in exchange field (temporary)
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
                    grid_state=json.dumps(
                        {
                            "orders": [],
                            "filled_orders": [],
                            "current_price": current_price,
                        }
                    ),
                    config=json.dumps((config or {}) | {"chain_id": chain_id}),
                )

                session.add(infinity_grid)
                await session.commit()
                await session.refresh(infinity_grid)

                logger.info(f"Created infinity grid {bot_id} for user {user_id}")
                return bot_id

        except Exception as e:
            logger.error(
                f"Error creating infinity grid for user {user_id}: {str(e)}",
                exc_info=True,
            )
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
            logger.error(
                f"Error starting infinity grid {bot_id}: {str(e)}", exc_info=True
            )
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
            logger.error(
                f"Error stopping infinity grid {bot_id}: {str(e)}", exc_info=True
            )
            return False

    async def process_infinity_grid_cycle(
        self, bot_id: str, user_id: int
    ) -> dict[str, Any]:
        """Process one infinity grid cycle: check price and adjust bounds if needed."""
        try:
            async with self._get_session() as session:
                bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not bot or not bot.active:
                    return {"action": "skipped", "reason": "bot_inactive"}

                # Get current market price from Market Data Service
                current_price = await self.market_data.get_price(bot.symbol)

                if not current_price:
                    return {"action": "skipped", "reason": "no_price_data"}

                # Check if bounds need adjustment
                adjustment_needed = await self._check_bound_adjustment(
                    bot, current_price
                )

                if adjustment_needed["adjust"]:
                    # Adjust grid bounds
                    await self._adjust_grid_bounds(
                        bot, current_price, adjustment_needed, session
                    )

                # Check for filled orders and rebalance
                grid_state = (
                    json.loads(bot.grid_state)
                    if bot.grid_state
                    else {"orders": [], "filled_orders": []}
                )
                filled_orders = await self._check_filled_orders(
                    bot, grid_state, current_price, session
                )

                if filled_orders:
                    await self._rebalance_grid(
                        bot, filled_orders, grid_state, current_price, session
                    )

                return {"action": "processed", "current_price": current_price}

        except Exception as e:
            logger.error(
                f"Error processing infinity grid cycle: {str(e)}", exc_info=True
            )
            return {"action": "error", "error": str(e)}

    async def _check_bound_adjustment(
        self, bot: InfinityGrid, current_price: float
    ) -> dict[str, Any]:
        """Check if grid bounds need adjustment."""
        upper_threshold = bot.current_upper_price * (
            1 - bot.upper_adjustment_percent / 100
        )
        lower_threshold = bot.current_lower_price * (
            1 + bot.lower_adjustment_percent / 100
        )

        if current_price >= upper_threshold:
            # Price moved up significantly - adjust upper bound
            new_upper = current_price * (1 + bot.upper_adjustment_percent / 100)
            return {
                "adjust": True,
                "direction": "up",
                "new_upper": new_upper,
                "new_lower": bot.current_lower_price,
            }
        elif current_price <= lower_threshold:
            # Price moved down significantly - adjust lower bound
            new_lower = current_price * (1 - bot.lower_adjustment_percent / 100)
            return {
                "adjust": True,
                "direction": "down",
                "new_upper": bot.current_upper_price,
                "new_lower": new_lower,
            }

        return {"adjust": False}

    async def _adjust_grid_bounds(
        self,
        bot: InfinityGrid,
        current_price: float,
        adjustment: dict[str, Any],
        session: AsyncSession,
    ) -> None:
        """Adjust grid bounds and rebalance orders."""
        # Update bounds
        await self.repository.update_grid_bounds(
            session,
            bot.id,
            bot.user_id,
            adjustment["new_upper"],
            adjustment["new_lower"],
        )

        # Cancel old orders outside new bounds
        # Place new orders within new bounds
        # This is simplified - real implementation would be more complex

    async def _place_initial_grid_orders(
        self, bot: InfinityGrid, session: AsyncSession
    ) -> list[dict[str, Any]]:
        """Place initial grid orders."""
        # Calculate grid prices within current bounds
        price_range = bot.current_upper_price - bot.current_lower_price
        interval = price_range / (bot.grid_count - 1)
        grid_prices = [
            bot.current_lower_price + (i * interval) for i in range(bot.grid_count)
        ]

        current_price = bot.initial_price
        orders = []
        grid_state = (
            json.loads(bot.grid_state)
            if bot.grid_state
            else {"orders": [], "filled_orders": []}
        )

        # Place buy orders below current price
        buy_prices = [p for p in grid_prices if p < current_price]
        for price in buy_prices:
            order = await self._place_grid_order(
                bot, "buy", price, bot.order_amount, session
            )
            if order:
                orders.append(order)
                grid_state["orders"].append(
                    {
                        "order_id": order.get("id"),
                        "side": "buy",
                        "price": price,
                        "amount": bot.order_amount,
                        "status": "open",
                    }
                )

        # Place sell orders above current price
        sell_prices = [p for p in grid_prices if p > current_price]
        for price in sell_prices:
            order = await self._place_grid_order(
                bot, "sell", price, bot.order_amount, session
            )
            if order:
                orders.append(order)
                grid_state["orders"].append(
                    {
                        "order_id": order.get("id"),
                        "side": "sell",
                        "price": price,
                        "amount": bot.order_amount,
                        "status": "open",
                    }
                )

        # Update grid state
        await self.repository.update_grid_state(
            session, bot.id, bot.user_id, grid_state
        )

        return orders

    async def _place_grid_order(
        self,
        bot: InfinityGrid,
        side: str,
        price: float,
        amount: float,
        session: AsyncSession,
    ) -> dict[str, Any] | None:
        """Place a single grid order."""
        try:
            if bot.trading_mode == "paper":
                # Paper trading - simulate order
                return {
                    "id": f"paper-{uuid.uuid4().hex[:12]}",
                    "side": side,
                    "price": price,
                    "amount": amount,
                    "status": "open",
                    "symbol": bot.symbol,
                }
            else:
                # Real trading - execute DEX swap
                chain_id = 1  # Default to Ethereum
                if bot.config:
                    config = (
                        json.loads(bot.config)
                        if isinstance(bot.config, str)
                        else bot.config
                    )
                    chain_id = config.get(
                        "chain_id", int(bot.exchange) if bot.exchange.isdigit() else 1
                    )
                elif bot.exchange and bot.exchange.isdigit():
                    chain_id = int(bot.exchange)

                # Convert symbol to token addresses using token registry
                base_address, quote_address = await self._parse_symbol_to_tokens(
                    bot.symbol, chain_id
                )

                # Calculate sell amount based on side and price
                if side == "buy":
                    # Buying: sell quote token to get base token
                    sell_token = quote_address
                    buy_token = base_address
                    sell_amount = str(amount * price)
                else:
                    # Selling: sell base token to get quote token
                    sell_token = base_address
                    buy_token = quote_address
                    sell_amount = str(amount)

                # Execute DEX swap
                swap_result = await self.dex_service.execute_custodial_swap(
                    user_id=bot.user_id,
                    sell_token=sell_token,
                    buy_token=buy_token,
                    sell_amount=sell_amount,
                    chain_id=chain_id,
                    slippage_percentage=0.5,
                    db=session,
                    user_tier="free",
                )

                if swap_result and swap_result.get("success"):
                    return {
                        "id": swap_result.get("transaction_hash"),
                        "side": side,
                        "price": price,
                        "amount": amount,
                        "status": "open",
                        "symbol": bot.symbol,
                        "transaction_hash": swap_result.get("transaction_hash"),
                    }
                else:
                    logger.error(
                        f"DEX swap failed for infinity grid order: {swap_result}"
                    )
                    return None
        except Exception as e:
            logger.error(f"Error placing infinity grid order: {str(e)}", exc_info=True)
            return None

    async def _parse_symbol_to_tokens(
        self, symbol: str, chain_id: int = 1
    ) -> tuple[str, str]:
        """Parse trading symbol to token addresses using token registry."""
        from ..blockchain.token_registry import get_token_registry

        token_registry = get_token_registry()
        base_address, quote_address = await token_registry.parse_symbol_to_tokens(
            symbol, chain_id
        )
        return base_address, quote_address

    async def _check_filled_orders(
        self,
        bot: InfinityGrid,
        grid_state: dict[str, Any],
        current_price: float,
        session: AsyncSession,
    ) -> list[dict[str, Any]]:
        """Check which orders have been filled."""
        filled = []
        for order in grid_state.get("orders", []):
            if order.get("status") == "open":
                order_price = order.get("price")
                order_side = order.get("side")
                if (order_side == "buy" and current_price <= order_price) or (
                    order_side == "sell" and current_price >= order_price
                ):
                    filled.append(order)
        return filled

    async def _rebalance_grid(
        self,
        bot: InfinityGrid,
        filled_orders: list[dict[str, Any]],
        grid_state: dict[str, Any],
        current_price: float,
        session: AsyncSession,
    ) -> None:
        """Rebalance grid after orders are filled."""
        # Similar to grid trading rebalance
        # Remove filled orders, place new orders
        pass

    async def _cancel_all_orders(
        self, bot: InfinityGrid, session: AsyncSession
    ) -> None:
        """Cancel all open orders."""
        grid_state = json.loads(bot.grid_state) if bot.grid_state else {"orders": []}
        for order in grid_state.get("orders", []):
            order["status"] = "cancelled"
        # Update grid state
        pass

    async def get_infinity_grid(
        self, bot_id: str, user_id: int
    ) -> dict[str, Any] | None:
        """Get infinity grid details."""
        try:
            async with self._get_session() as session:
                bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not bot:
                    return None
                return bot.to_dict()
        except Exception as e:
            logger.error(
                f"Error getting infinity grid {bot_id}: {str(e)}", exc_info=True
            )
            return None

    async def list_user_infinity_grids(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> tuple[list[dict[str, Any]], int]:
        """List all infinity grids for a user with total count."""
        try:
            async with self._get_session() as session:
                bots = await self.repository.get_user_infinity_grids(
                    session, user_id, skip, limit
                )
                total = await self.repository.count_user_infinity_grids(
                    session, user_id
                )
                return [bot.to_dict() for bot in bots], total
        except Exception as e:
            logger.error(f"Error listing infinity grids: {str(e)}", exc_info=True)
            return [], 0
