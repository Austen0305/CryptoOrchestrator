"""
Trailing Bot Trading Service
Implements trailing buy/sell bot functionality - follows price movements with dynamic stop-loss/take-profit.
"""

import logging
import uuid
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.trailing_bot import TrailingBot
from ...repositories.trailing_bot_repository import TrailingBotRepository
from ...services.exchange_service import ExchangeService
from ...services.advanced_risk_manager import AdvancedRiskManager
from ...database import get_db_context
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class TrailingBotService:
    """
    Service for Trailing Bot operations.
    Trailing buy (buy on dips) or trailing sell (sell on peaks).
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        self.repository = TrailingBotRepository()
        self._session = session
        self.risk_manager = AdvancedRiskManager.get_instance()

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
        initial_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_price: Optional[float] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
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
                    exchange_service = ExchangeService(exchange)
                    initial_price = await exchange_service.get_market_price(symbol)
                    if not initial_price:
                        raise ValueError(f"Could not get market price for {symbol}")

                # Create trailing bot
                trailing_bot = TrailingBot(
                    id=bot_id,
                    user_id=user_id,
                    name=name,
                    symbol=symbol,
                    exchange=exchange,
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
                    config=json.dumps(config or {})
                )

                session.add(trailing_bot)
                await session.commit()
                await session.refresh(trailing_bot)

                logger.info(f"Created trailing bot {bot_id} for user {user_id}")
                return bot_id

        except Exception as e:
            logger.error(f"Error creating trailing bot for user {user_id}: {str(e)}", exc_info=True)
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
            logger.error(f"Error starting trailing bot {bot_id}: {str(e)}", exc_info=True)
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
            logger.error(f"Error stopping trailing bot {bot_id}: {str(e)}", exc_info=True)
            return False

    async def process_trailing_bot_cycle(self, bot_id: str, user_id: int) -> Dict[str, Any]:
        """Process one trailing bot cycle: check price and execute order if conditions met."""
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

                # Update price tracking
                highest_price = max(bot.highest_price, current_price)
                lowest_price = min(bot.lowest_price, current_price)

                await self.repository.update_trailing_price(
                    session, bot.id, bot.user_id, current_price, highest_price, lowest_price
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
                        result = await self._execute_trailing_order(bot, "buy", current_price, session)
                        if result["success"]:
                            # Update trailing price to current price
                            await self.repository.update_trailing_price(
                                session, bot.id, bot.user_id, current_price, highest_price, lowest_price
                            )
                            return {"action": "executed", "side": "buy", "price": current_price}

                elif bot.bot_type == "trailing_sell":
                    # Trailing sell: sell when price rises by trailing_percent
                    trigger_price = bot.current_price * (1 + bot.trailing_percent / 100)
                    if current_price >= trigger_price:
                        # Check min price limit
                        if bot.min_price and current_price < bot.min_price:
                            return {"action": "skipped", "reason": "below_min_price"}

                        # Execute sell order
                        result = await self._execute_trailing_order(bot, "sell", current_price, session)
                        if result["success"]:
                            # Update trailing price to current price
                            await self.repository.update_trailing_price(
                                session, bot.id, bot.user_id, current_price, highest_price, lowest_price
                            )
                            return {"action": "executed", "side": "sell", "price": current_price}

                return {"action": "monitoring", "current_price": current_price}

        except Exception as e:
            logger.error(f"Error processing trailing bot cycle: {str(e)}", exc_info=True)
            return {"action": "error", "error": str(e)}

    async def _execute_trailing_order(
        self,
        bot: TrailingBot,
        side: str,
        price: float,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Execute a trailing order."""
        try:
            if bot.trading_mode == "paper":
                # Paper trading - simulate order
                return {
                    "success": True,
                    "order_id": f"paper-{uuid.uuid4().hex[:12]}",
                    "price": price,
                    "amount": bot.order_amount
                }
            else:
                # Real trading - place actual order
                exchange_service = ExchangeService(bot.exchange)
                order = await exchange_service.place_order(
                    pair=bot.symbol,
                    side=side,
                    type_="market",
                    amount=bot.order_amount
                )
                
                if order:
                    return {
                        "success": True,
                        "order_id": order.get("id"),
                        "price": price,
                        "amount": bot.order_amount
                    }
                else:
                    return {"success": False, "error": "Order placement failed"}

        except Exception as e:
            logger.error(f"Error executing trailing order: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def get_trailing_bot(self, bot_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Get trailing bot details."""
        try:
            async with self._get_session() as session:
                bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not bot:
                    return None
                return bot.to_dict()
        except Exception as e:
            logger.error(f"Error getting trailing bot {bot_id}: {str(e)}", exc_info=True)
            return None

    async def list_user_trailing_bots(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List all trailing bots for a user."""
        try:
            async with self._get_session() as session:
                bots = await self.repository.get_user_trailing_bots(session, user_id, skip, limit)
                return [bot.to_dict() for bot in bots]
        except Exception as e:
            logger.error(f"Error listing trailing bots: {str(e)}", exc_info=True)
            return []

