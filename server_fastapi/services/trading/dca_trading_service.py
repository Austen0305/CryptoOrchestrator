"""
DCA (Dollar Cost Averaging) Trading Service
Implements DCA bot functionality - buys at regular intervals to average out purchase price.
"""

import json
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db_context
from ...models.dca_bot import DCABot
from ...repositories.dca_bot_repository import DCABotRepository
from ...services.advanced_risk_manager import AdvancedRiskManager
from ...services.market_data_service import get_market_data_service
from ...services.trading.dex_trading_service import DEXTradingService

logger = logging.getLogger(__name__)


class DCATradingService:
    """
    Service for DCA (Dollar Cost Averaging) bot operations.
    Buys at regular intervals with optional martingale strategy.
    """

    def __init__(self, session: AsyncSession | None = None):
        self.repository = DCABotRepository()
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

    async def create_dca_bot(
        self,
        user_id: int,
        name: str,
        symbol: str,
        exchange: str,
        total_investment: float,
        order_amount: float,
        interval_minutes: int,
        trading_mode: str = "paper",
        max_orders: int | None = None,
        use_martingale: bool = False,
        martingale_multiplier: float = 1.5,
        martingale_max_multiplier: float = 5.0,
        take_profit_percent: float | None = None,
        stop_loss_percent: float | None = None,
        config: dict[str, Any] | None = None,
    ) -> str | None:
        """
        Create a new DCA trading bot.

        Args:
            user_id: User ID
            name: Bot name
            symbol: Trading symbol (e.g., "BTC/USD")
            exchange: Exchange name
            total_investment: Total amount to invest
            order_amount: Amount per order
            interval_minutes: Minutes between orders
            trading_mode: "paper" or "real"
            max_orders: Maximum number of orders (None = unlimited)
            use_martingale: Enable martingale strategy
            martingale_multiplier: Increase order size by this multiplier on losses
            martingale_max_multiplier: Maximum multiplier
            take_profit_percent: Take profit at this % gain
            stop_loss_percent: Stop loss at this % loss
            config: Additional configuration

        Returns:
            Bot ID if successful, None otherwise
        """
        try:
            # Validate inputs
            if total_investment <= 0:
                raise ValueError("Total investment must be positive")
            if order_amount <= 0:
                raise ValueError("Order amount must be positive")
            if interval_minutes < 1:
                raise ValueError("Interval must be at least 1 minute")
            if max_orders and max_orders < 1:
                raise ValueError("Max orders must be at least 1")
            if martingale_multiplier < 1.0:
                raise ValueError("Martingale multiplier must be >= 1.0")
            if martingale_max_multiplier < martingale_multiplier:
                raise ValueError("Max multiplier must be >= base multiplier")

            bot_id = f"dca-{user_id}-{uuid.uuid4().hex[:12]}"

            async with self._get_session() as session:
                # Calculate next order time
                next_order_at = datetime.now(UTC) + timedelta(minutes=interval_minutes)

                # Extract chain_id from exchange (temporary - exchange field stores chain_id as string)
                # Default to Ethereum (1) if exchange is not a numeric chain_id
                chain_id = int(exchange) if exchange.isdigit() else 1

                # Create DCA bot
                dca_bot = DCABot(
                    id=bot_id,
                    user_id=user_id,
                    name=name,
                    symbol=symbol,
                    exchange=exchange,
                    trading_mode=trading_mode,
                    total_investment=total_investment,
                    order_amount=order_amount,
                    interval_minutes=interval_minutes,
                    max_orders=max_orders,
                    use_martingale=use_martingale,
                    martingale_multiplier=martingale_multiplier,
                    martingale_max_multiplier=martingale_max_multiplier,
                    take_profit_percent=take_profit_percent,
                    stop_loss_percent=stop_loss_percent,
                    active=False,
                    status="stopped",
                    next_order_at=next_order_at,
                    config=json.dumps((config or {}) | {"chain_id": chain_id}),
                )

                session.add(dca_bot)
                await session.commit()
                await session.refresh(dca_bot)

                logger.info(f"Created DCA bot {bot_id} for user {user_id}")
                return bot_id

        except Exception as e:
            logger.error(
                f"Error creating DCA bot for user {user_id}: {str(e)}", exc_info=True
            )
            raise

    async def start_dca_bot(self, bot_id: str, user_id: int) -> bool:
        """Start a DCA trading bot."""
        try:
            async with self._get_session() as session:
                bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not bot:
                    logger.warning(f"DCA bot {bot_id} not found for user {user_id}")
                    return False

                if bot.active:
                    logger.info(f"DCA bot {bot_id} is already active")
                    return True

                # Validate start conditions
                validation = await self._validate_start_conditions(bot, session)
                if not validation["can_start"]:
                    logger.warning(
                        f"Cannot start DCA bot {bot_id}: {validation['reason']}"
                    )
                    return False

                # Calculate next order time
                next_order_at = datetime.now(UTC) + timedelta(
                    minutes=bot.interval_minutes
                )

                # Update bot status
                updated_bot = await self.repository.update_bot_status(
                    session, bot_id, user_id, True, "running"
                )

                if updated_bot:
                    await self.repository.update_next_order_time(
                        session, bot_id, user_id, next_order_at
                    )
                    logger.info(f"Started DCA bot {bot_id} for user {user_id}")
                    return True
                else:
                    logger.error(f"Failed to start DCA bot {bot_id}")
                    return False

        except Exception as e:
            logger.error(f"Error starting DCA bot {bot_id}: {str(e)}", exc_info=True)
            return False

    async def stop_dca_bot(self, bot_id: str, user_id: int) -> bool:
        """Stop a DCA trading bot."""
        try:
            async with self._get_session() as session:
                bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not bot:
                    logger.warning(f"DCA bot {bot_id} not found for user {user_id}")
                    return False

                if not bot.active:
                    logger.info(f"DCA bot {bot_id} is already stopped")
                    return True

                # Update bot status
                updated_bot = await self.repository.update_bot_status(
                    session, bot_id, user_id, False, "stopped"
                )

                if updated_bot:
                    logger.info(f"Stopped DCA bot {bot_id} for user {user_id}")
                    return True
                else:
                    logger.error(f"Failed to stop DCA bot {bot_id}")
                    return False

        except Exception as e:
            logger.error(f"Error stopping DCA bot {bot_id}: {str(e)}", exc_info=True)
            return False

    async def execute_dca_order(self, bot_id: str, user_id: int) -> dict[str, Any]:
        """
        Execute the next DCA order for a bot.
        Called by scheduler when next_order_at is reached.
        """
        try:
            async with self._get_session() as session:
                bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not bot or not bot.active:
                    return {"action": "skipped", "reason": "bot_inactive"}

                # Check if it's time to execute order
                if bot.next_order_at and bot.next_order_at > datetime.now(UTC):
                    return {"action": "skipped", "reason": "not_time_yet"}

                # Check max orders limit
                if bot.max_orders and bot.orders_executed >= bot.max_orders:
                    await self.repository.update_bot_status(
                        session, bot_id, user_id, False, "completed"
                    )
                    return {"action": "completed", "reason": "max_orders_reached"}

                # Check take profit / stop loss
                tp_sl_check = await self._check_take_profit_stop_loss(bot, session)
                if tp_sl_check["should_stop"]:
                    await self.repository.update_bot_status(
                        session, bot_id, user_id, False, tp_sl_check["status"]
                    )
                    return {"action": "stopped", "reason": tp_sl_check["reason"]}

                # Calculate order amount (with martingale if enabled)
                order_amount = await self._calculate_order_amount(bot)

                # Check if sufficient balance
                if bot.total_invested + order_amount > bot.total_investment:
                    # Adjust to remaining investment
                    order_amount = bot.total_investment - bot.total_invested
                    if order_amount <= 0:
                        await self.repository.update_bot_status(
                            session, bot_id, user_id, False, "completed"
                        )
                        return {"action": "completed", "reason": "investment_exhausted"}

                # Execute order
                order_result = await self._place_dca_order(bot, order_amount, session)

                if order_result["success"]:
                    # Update bot state
                    new_orders_executed = bot.orders_executed + 1
                    new_total_invested = bot.total_invested + order_amount
                    new_average_price = await self._calculate_average_price(
                        bot, order_result["price"], order_amount
                    )

                    # Calculate current value and profit
                    current_price = order_result[
                        "price"
                    ]  # Use execution price as current
                    current_value = (
                        new_total_invested / new_average_price
                    ) * current_price
                    total_profit = current_value - new_total_invested
                    profit_percent = (
                        (total_profit / new_total_invested * 100)
                        if new_total_invested > 0
                        else 0.0
                    )

                    # Update performance
                    await self.repository.update_performance(
                        session,
                        bot_id,
                        user_id,
                        new_orders_executed,
                        new_total_invested,
                        new_average_price,
                        current_value,
                        total_profit,
                        profit_percent,
                    )

                    # Calculate next order time
                    next_order_at = datetime.now(UTC) + timedelta(
                        minutes=bot.interval_minutes
                    )
                    await self.repository.update_next_order_time(
                        session, bot_id, user_id, next_order_at
                    )

                    return {
                        "action": "executed",
                        "order_amount": order_amount,
                        "price": order_result["price"],
                        "orders_executed": new_orders_executed,
                        "total_invested": new_total_invested,
                    }
                else:
                    return {"action": "failed", "error": order_result.get("error")}

        except Exception as e:
            logger.error(
                f"Error executing DCA order for bot {bot_id}: {str(e)}", exc_info=True
            )
            return {"action": "error", "error": str(e)}

    async def process_all_due_orders(self) -> dict[str, Any]:
        """Process all DCA bots that are due for their next order."""
        try:
            async with self._get_session() as session:
                bots = await self.repository.get_bots_ready_for_order(session)

                results = {"processed": 0, "skipped": 0, "errors": 0}

                for bot in bots:
                    try:
                        result = await self.execute_dca_order(bot.id, bot.user_id)
                        if result.get("action") == "executed":
                            results["processed"] += 1
                        else:
                            results["skipped"] += 1
                    except Exception as e:
                        logger.error(
                            f"Error processing DCA bot {bot.id}: {e}", exc_info=True
                        )
                        results["errors"] += 1

                return results

        except Exception as e:
            logger.error(f"Error processing due DCA orders: {str(e)}", exc_info=True)
            return {"processed": 0, "skipped": 0, "errors": 1}

    async def _validate_start_conditions(
        self, bot: DCABot, session: AsyncSession
    ) -> dict[str, Any]:
        """Validate that DCA bot can start."""
        # Check if exchange is configured
        # Check if user has sufficient balance
        # Check risk limits
        return {"can_start": True, "reason": None}

    async def _calculate_order_amount(self, bot: DCABot) -> float:
        """Calculate order amount, applying martingale if enabled."""
        base_amount = bot.order_amount

        if not bot.use_martingale:
            return base_amount

        # Martingale: increase order size after losses
        # Simplified: increase if current profit is negative
        if bot.total_profit < 0:
            # Calculate multiplier based on consecutive losses
            # This is simplified - real implementation would track consecutive losses
            multiplier = min(bot.martingale_multiplier, bot.martingale_max_multiplier)
            return base_amount * multiplier

        return base_amount

    async def _place_dca_order(
        self, bot: DCABot, amount: float, session: AsyncSession
    ) -> dict[str, Any]:
        """Place a DCA buy order."""
        try:
            # Get current market price from MarketDataService
            current_price = await self.market_data.get_price(bot.symbol)

            if not current_price:
                return {"success": False, "error": "Could not get market price"}

            if bot.trading_mode == "paper":
                # Paper trading - simulate order
                return {
                    "success": True,
                    "order_id": f"paper-{uuid.uuid4().hex[:12]}",
                    "price": current_price,
                    "amount": amount,
                }
            else:
                # Real trading - execute DEX swap (buy base token with quote token)
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

                # DCA buys base token with quote token
                sell_token = quote_address  # Sell quote token (USDC)
                buy_token = base_address  # Buy base token (ETH)
                sell_amount = str(amount)  # Amount of quote token to sell

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
                    # Get actual execution price from swap result
                    executed_price = swap_result.get("price", current_price)
                    return {
                        "success": True,
                        "order_id": swap_result.get("transaction_hash"),
                        "price": executed_price,
                        "amount": amount,
                        "transaction_hash": swap_result.get("transaction_hash"),
                    }
                else:
                    return {"success": False, "error": "DEX swap failed"}
        except Exception as e:
            logger.error(f"Error placing DCA order: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

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

    async def _calculate_average_price(
        self, bot: DCABot, new_price: float, new_amount: float
    ) -> float:
        """Calculate new average price after adding a new order."""
        if bot.orders_executed == 0:
            return new_price

        # Weighted average: (old_total_value + new_value) / (old_total_quantity + new_quantity)
        old_total_value = bot.total_invested
        old_quantity = (
            old_total_value / bot.average_price if bot.average_price > 0 else 0
        )
        new_quantity = new_amount / new_price

        total_value = old_total_value + new_amount
        total_quantity = old_quantity + new_quantity

        return total_value / total_quantity if total_quantity > 0 else new_price

    async def _check_take_profit_stop_loss(
        self, bot: DCABot, session: AsyncSession
    ) -> dict[str, Any]:
        """Check if take profit or stop loss conditions are met."""
        if bot.orders_executed == 0:
            return {"should_stop": False, "status": None, "reason": None}

        # Get current market price from MarketDataService
        current_price = await self.market_data.get_price(bot.symbol)

        if not current_price or bot.average_price == 0:
            return {"should_stop": False, "status": None, "reason": None}

        # Calculate profit percentage
        profit_percent = ((current_price - bot.average_price) / bot.average_price) * 100

        # Check take profit
        if bot.take_profit_percent and profit_percent >= bot.take_profit_percent:
            return {
                "should_stop": True,
                "status": "completed",
                "reason": f"Take profit reached: {profit_percent:.2f}%",
            }

        # Check stop loss
        if bot.stop_loss_percent and profit_percent <= -bot.stop_loss_percent:
            return {
                "should_stop": True,
                "status": "stopped",
                "reason": f"Stop loss triggered: {profit_percent:.2f}%",
            }

        return {"should_stop": False, "status": None, "reason": None}

    async def get_dca_bot(self, bot_id: str, user_id: int) -> dict[str, Any] | None:
        """Get DCA bot details."""
        try:
            async with self._get_session() as session:
                bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not bot:
                    return None

                return bot.to_dict()

        except Exception as e:
            logger.error(f"Error getting DCA bot {bot_id}: {str(e)}", exc_info=True)
            return None

    async def list_user_dca_bots(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> tuple[list[dict[str, Any]], int]:
        """List all DCA bots for a user with total count."""
        try:
            async with self._get_session() as session:
                bots = await self.repository.get_user_dca_bots(
                    session, user_id, skip, limit
                )
                total = await self.repository.count_user_dca_bots(session, user_id)
                return [bot.to_dict() for bot in bots], total

        except Exception as e:
            logger.error(
                f"Error listing DCA bots for user {user_id}: {str(e)}", exc_info=True
            )
            return [], 0
