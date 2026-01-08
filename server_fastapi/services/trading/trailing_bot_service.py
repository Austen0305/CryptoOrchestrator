"""
Trailing Bot Trading Service
Implements trailing buy/sell bot functionality - follows price movements with dynamic stop-loss/take-profit.
"""

import json
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db_context
from ...models.trailing_bot import TrailingBot
from ...repositories.trailing_bot_repository import TrailingBotRepository
from ...services.advanced_risk_manager import AdvancedRiskManager
from ...services.coingecko_service import CoinGeckoService
from ...services.trading.dex_trading_service import DEXTradingService

logger = logging.getLogger(__name__)


class TrailingBotService:
    """
    Service for Trailing Bot operations.
    Trailing buy (buy on dips) or trailing sell (sell on peaks).
    """

    def __init__(self, session: AsyncSession | None = None):
        self.repository = TrailingBotRepository()
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

    async def create_trailing_bot(
        self,
        user_id: int,
        name: str,
        symbol: str,
        exchange: str,
        bot_type: str,
        trailing_percent: float,
        order_amount: float,
        trading_mode: str = "paper",
        initial_price: float | None = None,
        max_price: float | None = None,
        min_price: float | None = None,
        config: dict[str, Any] | None = None,
    ) -> str | None:
        """Create a new trailing bot."""
        try:
            # Validate inputs
            if bot_type not in ["trailing_buy", "trailing_sell"]:
                raise ValueError("Bot type must be 'trailing_buy' or 'trailing_sell'")
            if trailing_percent <= 0:
                raise ValueError("Trailing percent must be positive")
            if order_amount <= 0:
                raise ValueError("Order amount must be positive")

            bot_id = f"trailing-{user_id}-{uuid.uuid4().hex[:12]}"

            async with self._get_session() as session:
                # Get current market price if not provided
                if not initial_price:
                    initial_price = await self.coingecko.get_price(symbol)
                    if not initial_price:
                        raise ValueError(f"Could not get market price for {symbol}")

                # Extract chain_id from config or use default
                chain_id = 1  # Default to Ethereum
                if config and isinstance(config, dict):
                    chain_id = config.get("chain_id", 1)
                elif isinstance(exchange, str) and exchange.isdigit():
                    chain_id = int(exchange)

                # Create trailing bot (using exchange field for chain_id temporarily)
                trailing_bot = TrailingBot(
                    id=bot_id,
                    user_id=user_id,
                    name=name,
                    symbol=symbol,
                    exchange=str(
                        chain_id
                    ),  # Store chain_id as string in exchange field (temporary)
                    trading_mode=trading_mode,
                    bot_type=bot_type,
                    initial_price=initial_price,
                    current_price=initial_price,
                    trailing_percent=trailing_percent,
                    order_amount=order_amount,
                    max_price=max_price,
                    min_price=min_price,
                    active=False,
                    status="stopped",
                    highest_price=initial_price,
                    lowest_price=initial_price,
                    config=json.dumps((config or {}) | {"chain_id": chain_id}),
                )

                session.add(trailing_bot)
                await session.commit()
                await session.refresh(trailing_bot)

                logger.info(f"Created trailing bot {bot_id} for user {user_id}")
                return bot_id

        except Exception as e:
            logger.error(
                f"Error creating trailing bot for user {user_id}: {str(e)}",
                exc_info=True,
            )
            raise

    async def start_trailing_bot(self, bot_id: str, user_id: int) -> bool:
        """Start a trailing bot."""
        try:
            async with self._get_session() as session:
                bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not bot:
                    return False

                if bot.active:
                    return True

                # Update bot status
                updated_bot = await self.repository.update_bot_status(
                    session, bot_id, user_id, True, "running"
                )

                return updated_bot is not None

        except Exception as e:
            logger.error(
                f"Error starting trailing bot {bot_id}: {str(e)}", exc_info=True
            )
            return False

    async def stop_trailing_bot(self, bot_id: str, user_id: int) -> bool:
        """Stop a trailing bot."""
        try:
            async with self._get_session() as session:
                bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not bot:
                    return False

                # Update bot status
                updated_bot = await self.repository.update_bot_status(
                    session, bot_id, user_id, False, "stopped"
                )

                return updated_bot is not None

        except Exception as e:
            logger.error(
                f"Error stopping trailing bot {bot_id}: {str(e)}", exc_info=True
            )
            return False

    async def process_trailing_bot_cycle(
        self, bot_id: str, user_id: int
    ) -> dict[str, Any]:
        """Process one trailing bot cycle: check price and execute order if conditions met."""
        try:
            async with self._get_session() as session:
                bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not bot or not bot.active:
                    return {"action": "skipped", "reason": "bot_inactive"}

                # Get current market price from CoinGecko
                current_price = await self.coingecko.get_price(bot.symbol)

                if not current_price:
                    return {"action": "skipped", "reason": "no_price_data"}

                # Update price tracking
                highest_price = max(bot.highest_price, current_price)
                lowest_price = min(bot.lowest_price, current_price)

                await self.repository.update_trailing_price(
                    session,
                    bot.id,
                    bot.user_id,
                    current_price,
                    highest_price,
                    lowest_price,
                )

                # Check if order should be triggered
                if bot.bot_type == "trailing_buy":
                    # Trailing buy: buy when price drops by trailing_percent
                    trigger_price = bot.current_price * (1 - bot.trailing_percent / 100)
                    if current_price <= trigger_price:
                        # Check max price limit
                        if bot.max_price and current_price > bot.max_price:
                            return {"action": "skipped", "reason": "above_max_price"}

                        # Execute buy order
                        result = await self._execute_trailing_order(
                            bot, "buy", current_price, session
                        )
                        if result["success"]:
                            # Update trailing price to current price
                            await self.repository.update_trailing_price(
                                session,
                                bot.id,
                                bot.user_id,
                                current_price,
                                highest_price,
                                lowest_price,
                            )
                            return {
                                "action": "executed",
                                "side": "buy",
                                "price": current_price,
                            }

                elif bot.bot_type == "trailing_sell":
                    # Trailing sell: sell when price rises by trailing_percent
                    trigger_price = bot.current_price * (1 + bot.trailing_percent / 100)
                    if current_price >= trigger_price:
                        # Check min price limit
                        if bot.min_price and current_price < bot.min_price:
                            return {"action": "skipped", "reason": "below_min_price"}

                        # Execute sell order
                        result = await self._execute_trailing_order(
                            bot, "sell", current_price, session
                        )
                        if result["success"]:
                            # Update trailing price to current price
                            await self.repository.update_trailing_price(
                                session,
                                bot.id,
                                bot.user_id,
                                current_price,
                                highest_price,
                                lowest_price,
                            )
                            return {
                                "action": "executed",
                                "side": "sell",
                                "price": current_price,
                            }

                return {"action": "monitoring", "current_price": current_price}

        except Exception as e:
            logger.error(
                f"Error processing trailing bot cycle: {str(e)}", exc_info=True
            )
            return {"action": "error", "error": str(e)}

    async def _execute_trailing_order(
        self, bot: TrailingBot, side: str, price: float, session: AsyncSession
    ) -> dict[str, Any]:
        """Execute a trailing order."""
        try:
            if bot.trading_mode == "paper":
                # Paper trading - simulate order
                return {
                    "success": True,
                    "order_id": f"paper-{uuid.uuid4().hex[:12]}",
                    "price": price,
                    "amount": bot.order_amount,
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

                # Calculate amounts based on side
                if side == "buy":
                    # Buying: sell quote token to get base token
                    sell_token = quote_address
                    buy_token = base_address
                    sell_amount = str(bot.order_amount * price)  # Amount of quote token
                else:
                    # Selling: sell base token to get quote token
                    sell_token = base_address
                    buy_token = quote_address
                    sell_amount = str(bot.order_amount)  # Amount of base token

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
                        "success": True,
                        "order_id": swap_result.get("transaction_hash"),
                        "price": price,
                        "amount": bot.order_amount,
                        "transaction_hash": swap_result.get("transaction_hash"),
                    }
                else:
                    return {"success": False, "error": "DEX swap failed"}

        except Exception as e:
            logger.error(f"Error executing trailing order: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _parse_symbol_to_tokens(
        self, symbol: str, chain_id: int = 1
    ) -> tuple[str, str]:
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

    async def get_trailing_bot(
        self, bot_id: str, user_id: int
    ) -> dict[str, Any] | None:
        """Get trailing bot details."""
        try:
            async with self._get_session() as session:
                bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not bot:
                    return None
                return bot.to_dict()
        except Exception as e:
            logger.error(
                f"Error getting trailing bot {bot_id}: {str(e)}", exc_info=True
            )
            return None

    async def list_user_trailing_bots(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> tuple[list[dict[str, Any]], int]:
        """List all trailing bots for a user with total count."""
        try:
            async with self._get_session() as session:
                bots = await self.repository.get_user_trailing_bots(
                    session, user_id, skip, limit
                )
                total = await self.repository.count_user_trailing_bots(session, user_id)
                return [bot.to_dict() for bot in bots], total
        except Exception as e:
            logger.error(f"Error listing trailing bots: {str(e)}", exc_info=True)
            return [], 0
