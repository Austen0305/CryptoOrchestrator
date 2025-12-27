"""
Grid Trading Service
Implements grid trading bot functionality - places buy/sell orders in a grid pattern.
"""

import logging
import uuid
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.grid_bot import GridBot
from ...repositories.grid_bot_repository import GridBotRepository
from ...services.coingecko_service import CoinGeckoService
from ...services.trading.dex_trading_service import DEXTradingService
from ...services.advanced_risk_manager import AdvancedRiskManager
from ...services.blockchain.transaction_service import get_transaction_service
from ...database import get_db_context
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class GridTradingService:
    """
    Service for grid trading bot operations.
    Places buy and sell orders in a grid pattern to profit from volatility.
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        self.repository = GridBotRepository()
        self._session = session
        self.risk_manager = AdvancedRiskManager.get_instance()
        self.coingecko = CoinGeckoService()
        self.dex_service = DEXTradingService()

    @asynccontextmanager
    async def _get_session(self):
        if self._session is not None:
            yield self._session
        else:
            async with get_db_context() as session:
                yield session

    async def create_grid_bot(
        self,
        user_id: int,
        name: str,
        symbol: str,
        chain_id: int = 1,  # Changed from exchange to chain_id
        upper_price: float = None,
        lower_price: float = None,
        grid_count: int = 10,
        order_amount: float = 100.0,
        trading_mode: str = "paper",
        grid_spacing_type: str = "arithmetic",
        config: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Create a new grid trading bot.

        Args:
            user_id: User ID
            name: Bot name
            symbol: Trading symbol (e.g., "ETH/USDC")
            chain_id: Blockchain chain ID (1 = Ethereum, 8453 = Base, etc.)
            upper_price: Upper bound of grid (auto-calculated if None)
            lower_price: Lower bound of grid (auto-calculated if None)
            grid_count: Number of grid levels
            order_amount: Amount per order
            trading_mode: "paper" or "real"
            grid_spacing_type: "arithmetic" or "geometric"
            config: Additional configuration (JSON)

        Returns:
            Bot ID if successful, None otherwise
        """
        try:
            # Validate inputs
            if upper_price <= lower_price:
                raise ValueError("Upper price must be greater than lower price")
            if grid_count < 2:
                raise ValueError("Grid count must be at least 2")
            if order_amount <= 0:
                raise ValueError("Order amount must be positive")
            if grid_spacing_type not in ["arithmetic", "geometric"]:
                raise ValueError(
                    "Grid spacing type must be 'arithmetic' or 'geometric'"
                )

            bot_id = f"grid-{user_id}-{uuid.uuid4().hex[:12]}"

            # Auto-calculate price bounds if not provided
            if upper_price is None or lower_price is None:
                current_price = await self.coingecko.get_price(symbol)
                if not current_price:
                    raise ValueError(f"Could not get market price for {symbol}")

                if upper_price is None:
                    upper_price = current_price * 1.1  # 10% above
                if lower_price is None:
                    lower_price = current_price * 0.9  # 10% below

            async with self._get_session() as session:
                # Create grid bot (using exchange field for chain_id temporarily for backward compatibility)
                # Note: Future schema update will add dedicated chain_id field to GridBot model
                grid_bot = GridBot(
                    id=bot_id,
                    user_id=user_id,
                    name=name,
                    symbol=symbol,
                    exchange=str(
                        chain_id
                    ),  # Store chain_id as string in exchange field (temporary)
                    trading_mode=trading_mode,
                    upper_price=upper_price,
                    lower_price=lower_price,
                    grid_count=grid_count,
                    grid_spacing_type=grid_spacing_type,
                    order_amount=order_amount,
                    active=False,
                    status="stopped",
                    grid_state=json.dumps(
                        {"orders": [], "filled_orders": [], "current_price": None}
                    ),
                    config=json.dumps((config or {}) | {"chain_id": chain_id}),
                )

                session.add(grid_bot)
                await session.commit()
                await session.refresh(grid_bot)

                logger.info(f"Created grid bot {bot_id} for user {user_id}")
                return bot_id

        except Exception as e:
            logger.error(
                f"Error creating grid bot for user {user_id}: {str(e)}", exc_info=True
            )
            raise

    async def start_grid_bot(self, bot_id: str, user_id: int) -> bool:
        """Start a grid trading bot."""
        try:
            async with self._get_session() as session:
                bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not bot:
                    logger.warning(f"Grid bot {bot_id} not found for user {user_id}")
                    return False

                if bot.active:
                    logger.info(f"Grid bot {bot_id} is already active")
                    return True

                # Validate start conditions
                validation = await self._validate_start_conditions(bot, session)
                if not validation["can_start"]:
                    logger.warning(
                        f"Cannot start grid bot {bot_id}: {validation['reason']}"
                    )
                    return False

                # Place initial grid orders
                await self._place_initial_grid_orders(bot, session)

                # Update bot status
                updated_bot = await self.repository.update_bot_status(
                    session, bot_id, user_id, True, "running"
                )

                if updated_bot:
                    logger.info(f"Started grid bot {bot_id} for user {user_id}")
                    return True
                else:
                    logger.error(f"Failed to start grid bot {bot_id}")
                    return False

        except Exception as e:
            logger.error(f"Error starting grid bot {bot_id}: {str(e)}", exc_info=True)
            return False

    async def stop_grid_bot(self, bot_id: str, user_id: int) -> bool:
        """Stop a grid trading bot."""
        try:
            async with self._get_session() as session:
                bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not bot:
                    logger.warning(f"Grid bot {bot_id} not found for user {user_id}")
                    return False

                if not bot.active:
                    logger.info(f"Grid bot {bot_id} is already stopped")
                    return True

                # Cancel all open orders
                await self._cancel_all_orders(bot, session)

                # Update bot status
                updated_bot = await self.repository.update_bot_status(
                    session, bot_id, user_id, False, "stopped"
                )

                if updated_bot:
                    logger.info(f"Stopped grid bot {bot_id} for user {user_id}")
                    return True
                else:
                    logger.error(f"Failed to stop grid bot {bot_id}")
                    return False

        except Exception as e:
            logger.error(f"Error stopping grid bot {bot_id}: {str(e)}", exc_info=True)
            return False

    async def process_grid_cycle(self, bot_id: str, user_id: int) -> Dict[str, Any]:
        """
        Process one grid trading cycle:
        1. Check for filled orders
        2. Rebalance grid if needed
        3. Update performance metrics
        """
        try:
            async with self._get_session() as session:
                bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not bot or not bot.active:
                    return {"action": "skipped", "reason": "bot_inactive"}

                # Get current grid state
                grid_state = (
                    json.loads(bot.grid_state)
                    if bot.grid_state
                    else {"orders": [], "filled_orders": []}
                )

                # Check for filled orders
                filled_orders = await self._check_filled_orders(
                    bot, grid_state, session
                )

                if filled_orders:
                    # Rebalance grid
                    await self._rebalance_grid(bot, filled_orders, grid_state, session)

                    # Update performance
                    await self._update_performance(bot, filled_orders, session)

                return {
                    "action": "processed",
                    "filled_orders": len(filled_orders),
                    "total_profit": bot.total_profit,
                }

        except Exception as e:
            logger.error(
                f"Error processing grid cycle for bot {bot_id}: {str(e)}", exc_info=True
            )
            return {"action": "error", "error": str(e)}

    async def _validate_start_conditions(
        self, bot: GridBot, session: AsyncSession
    ) -> Dict[str, Any]:
        """Validate that grid bot can start."""
        # Check if exchange is configured
        # Check if user has sufficient balance
        # Check risk limits
        return {"can_start": True, "reason": None}

    async def _place_initial_grid_orders(
        self, bot: GridBot, session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Place initial grid orders."""
        # Calculate grid prices
        grid_prices = self._calculate_grid_prices(
            bot.lower_price, bot.upper_price, bot.grid_count, bot.grid_spacing_type
        )

        # Get current market price from CoinGecko
        current_price = await self.coingecko.get_price(bot.symbol)

        if not current_price:
            logger.warning(f"Could not get market price for {bot.symbol}")
            current_price = (bot.lower_price + bot.upper_price) / 2

        orders = []
        grid_state = {"orders": [], "filled_orders": [], "current_price": current_price}

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

    def _calculate_grid_prices(
        self, lower_price: float, upper_price: float, grid_count: int, spacing_type: str
    ) -> List[float]:
        """Calculate grid price levels."""
        if spacing_type == "arithmetic":
            # Arithmetic spacing: equal price intervals
            price_range = upper_price - lower_price
            interval = price_range / (grid_count - 1)
            return [lower_price + (i * interval) for i in range(grid_count)]
        else:
            # Geometric spacing: equal percentage intervals
            ratio = (upper_price / lower_price) ** (1 / (grid_count - 1))
            return [lower_price * (ratio**i) for i in range(grid_count)]

    async def _place_grid_order(
        self,
        bot: GridBot,
        side: str,
        price: float,
        amount: float,
        session: AsyncSession,
    ) -> Optional[Dict[str, Any]]:
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
                # Get chain_id from bot config or exchange field (temporary)
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
                    # Buying: sell quote token (USDC) to get base token (ETH)
                    sell_token = quote_address
                    buy_token = base_address
                    sell_amount = str(amount * price)  # Amount of quote token to sell
                else:
                    # Selling: sell base token (ETH) to get quote token (USDC)
                    sell_token = base_address
                    buy_token = quote_address
                    sell_amount = str(amount)  # Amount of base token to sell

                # Execute DEX swap
                swap_result = await self.dex_service.execute_custodial_swap(
                    user_id=bot.user_id,
                    sell_token=sell_token,
                    buy_token=buy_token,
                    sell_amount=sell_amount,
                    chain_id=chain_id,
                    slippage_percentage=0.5,  # Default 0.5% slippage
                    db=session,
                    user_tier="free",  # Get from user profile
                )

                if swap_result and swap_result.get("success"):
                    return {
                        "id": swap_result.get("transaction_hash"),
                        "side": side,
                        "price": price,
                        "amount": amount,
                        "status": "open",  # Will be updated when confirmed
                        "symbol": bot.symbol,
                        "transaction_hash": swap_result.get("transaction_hash"),
                    }
                else:
                    logger.error(f"DEX swap failed for grid order: {swap_result}")
                    return None

        except Exception as e:
            logger.error(f"Error placing grid order: {str(e)}", exc_info=True)
            return None

    async def _parse_symbol_to_tokens(
        self, symbol: str, chain_id: int = 1
    ) -> Tuple[str, str]:
        """
        Parse trading symbol (e.g., "ETH/USDC") to token addresses using token registry.

        Returns:
            Tuple of (base_token_address, quote_token_address)
        """
        from ..blockchain.token_registry import get_token_registry

        token_registry = get_token_registry()
        base_address, quote_address = await token_registry.parse_symbol_to_tokens(
            symbol, chain_id
        )
        return base_address, quote_address

    async def _check_filled_orders(
        self, bot: GridBot, grid_state: Dict[str, Any], session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Check which orders have been filled."""
        filled = []

        if bot.trading_mode == "paper":
            # In paper trading, simulate order fills based on current price
            current_price = await self.coingecko.get_price(bot.symbol)

            if current_price:
                for order in grid_state.get("orders", []):
                    if order.get("status") == "open":
                        order_price = order.get("price")
                        order_side = order.get("side")

                        # Check if order would be filled
                        if (order_side == "buy" and current_price <= order_price) or (
                            order_side == "sell" and current_price >= order_price
                        ):
                            filled.append(order)
        else:
            # Real trading - check blockchain for filled orders
            # For DEX swaps, check transaction status
            transaction_service = get_transaction_service()
            chain_id = bot.chain_id or 1  # Default to Ethereum mainnet
            
            for order in grid_state.get("orders", []):
                if order.get("status") == "open":
                    tx_hash = order.get("transaction_hash")
                    if tx_hash:
                        # Check if transaction is confirmed and successful
                        tx_status = await transaction_service.get_transaction_status(
                            chain_id=chain_id,
                            tx_hash=tx_hash
                        )
                        
                        if tx_status:
                            if tx_status.get("status") == "confirmed" and tx_status.get("success"):
                                # Transaction confirmed and successful - order is filled
                                filled.append(order)
                                logger.info(
                                    f"Grid order {order.get('order_id')} confirmed via transaction {tx_hash}",
                                    extra={
                                        "bot_id": bot.id,
                                        "order_id": order.get("order_id"),
                                        "tx_hash": tx_hash,
                                        "chain_id": chain_id
                                    }
                                )
                            elif tx_status.get("status") == "failed" or (
                                tx_status.get("status") == "confirmed" and not tx_status.get("success")
                            ):
                                # Transaction failed - mark order as failed
                                order["status"] = "failed"
                                logger.warning(
                                    f"Grid order {order.get('order_id')} failed via transaction {tx_hash}",
                                    extra={
                                        "bot_id": bot.id,
                                        "order_id": order.get("order_id"),
                                        "tx_hash": tx_hash,
                                        "chain_id": chain_id
                                    }
                                )
                            # If status is "pending" or "not_found", keep order as open

        return filled

    async def _rebalance_grid(
        self,
        bot: GridBot,
        filled_orders: List[Dict[str, Any]],
        grid_state: Dict[str, Any],
        session: AsyncSession,
    ) -> None:
        """Rebalance grid after orders are filled."""
        # Remove filled orders from open orders
        filled_order_ids = {o.get("order_id") for o in filled_orders}
        grid_state["orders"] = [
            o
            for o in grid_state.get("orders", [])
            if o.get("order_id") not in filled_order_ids
        ]

        # Add to filled orders list
        grid_state["filled_orders"].extend(filled_orders)

        # Place new orders to maintain grid
        for filled_order in filled_orders:
            side = filled_order.get("side")
            price = filled_order.get("price")

            # Calculate opposite side order price
            grid_prices = self._calculate_grid_prices(
                bot.lower_price, bot.upper_price, bot.grid_count, bot.grid_spacing_type
            )

            # Find adjacent grid level
            if side == "buy":
                # Place sell order at next higher grid level
                next_price = min([p for p in grid_prices if p > price], default=None)
                if next_price:
                    new_order = await self._place_grid_order(
                        bot, "sell", next_price, bot.order_amount, session
                    )
                    if new_order:
                        grid_state["orders"].append(
                            {
                                "order_id": new_order.get("id"),
                                "side": "sell",
                                "price": next_price,
                                "amount": bot.order_amount,
                                "status": "open",
                            }
                        )
            else:
                # Place buy order at next lower grid level
                next_price = max([p for p in grid_prices if p < price], default=None)
                if next_price:
                    new_order = await self._place_grid_order(
                        bot, "buy", next_price, bot.order_amount, session
                    )
                    if new_order:
                        grid_state["orders"].append(
                            {
                                "order_id": new_order.get("id"),
                                "side": "buy",
                                "price": next_price,
                                "amount": bot.order_amount,
                                "status": "open",
                            }
                        )

        # Update grid state
        await self.repository.update_grid_state(
            session, bot.id, bot.user_id, grid_state
        )

    async def _update_performance(
        self, bot: GridBot, filled_orders: List[Dict[str, Any]], session: AsyncSession
    ) -> None:
        """Update grid bot performance metrics."""
        # Calculate profit from filled orders
        grid_state = (
            json.loads(bot.grid_state) if bot.grid_state else {"filled_orders": []}
        )

        # Simple profit calculation: sum of (sell_price - buy_price) for matched pairs
        # This is simplified - real implementation would match buy/sell pairs
        total_profit = bot.total_profit
        total_trades = bot.total_trades + len(filled_orders)

        # Update win rate (simplified)
        win_rate = bot.win_rate  # Would need to track wins/losses properly

        await self.repository.update_performance(
            session, bot.id, bot.user_id, total_profit, total_trades, win_rate
        )

    async def _cancel_all_orders(self, bot: GridBot, session: AsyncSession) -> None:
        """Cancel all open orders for the grid bot."""
        grid_state = json.loads(bot.grid_state) if bot.grid_state else {"orders": []}

        for order in grid_state.get("orders", []):
            if order.get("status") == "open":
                # For DEX swaps, orders cannot be cancelled once submitted to blockchain
                # Only pending transactions can be cancelled (before confirmation)
                # Mark as cancelled in state (actual blockchain transaction may still execute)
                if bot.trading_mode != "paper":
                    tx_hash = order.get("transaction_hash")
                    if tx_hash:
                        logger.warning(
                            f"Cannot cancel DEX swap transaction {tx_hash} - already on blockchain"
                        )
                        # Transaction may still execute - user should be aware

                order["status"] = "cancelled"

        # Update grid state
        await self.repository.update_grid_state(
            session, bot.id, bot.user_id, grid_state
        )

    async def get_grid_bot(self, bot_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Get grid bot details."""
        try:
            async with self._get_session() as session:
                bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not bot:
                    return None

                return bot.to_dict()

        except Exception as e:
            logger.error(f"Error getting grid bot {bot_id}: {str(e)}", exc_info=True)
            return None

    async def list_user_grid_bots(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List all grid bots for a user with total count."""
        try:
            async with self._get_session() as session:
                bots = await self.repository.get_user_grid_bots(
                    session, user_id, skip, limit
                )
                total = await self.repository.count_user_grid_bots(session, user_id)
                return [bot.to_dict() for bot in bots], total

        except Exception as e:
            logger.error(
                f"Error listing grid bots for user {user_id}: {str(e)}", exc_info=True
            )
            return [], 0
