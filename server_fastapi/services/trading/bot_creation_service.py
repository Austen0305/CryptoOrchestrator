"""
Bot creation and management service
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db_context
from ...repositories.bot_repository import BotRepository
from ..portfolio_reconciliation import reconcile_user_portfolio
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class BotConfiguration(BaseModel):
    id: str
    strategy: str
    parameters: Dict[str, Any]
    active: bool


class BotCreationService:
    """Service for bot creation, updates, and basic management operations"""

    def __init__(self, session: Optional[AsyncSession] = None):
        self.repository = BotRepository()
        self._session = session

    @asynccontextmanager
    async def _get_session(self):
        if self._session is not None:
            yield self._session
        else:
            async with get_db_context() as session:
                yield session

    async def create_bot(self, user_id: int, name: str, symbol: str, strategy: str, parameters: Dict[str, Any]) -> Optional[str]:
        """Create a new bot"""
        try:
            bot_id = f"bot-{user_id}-{hash(f'{user_id}-{name}-{datetime.now().isoformat()}') % 1000000}"

            async with self._get_session() as session:
                bot = await self.repository.create_bot(session, bot_id, user_id, name, symbol, strategy, parameters)
                if bot:
                    logger.info(f"Created bot {bot_id} for user {user_id}")
                    await self._trigger_reconciliation(user_id, session)
                    return bot_id
                else:
                    logger.error(f"Failed to create bot for user {user_id}")
                    return None

        except Exception as e:
            logger.error(f"Error creating bot for user {user_id}: {str(e)}")
            raise

    async def update_bot(self, bot_id: str, user_id: int, updates: Dict[str, Any]) -> bool:
        """Update an existing bot"""
        try:
            async with self._get_session() as session:
                # First check if bot exists and belongs to user
                existing_bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not existing_bot:
                    logger.warning(f"Bot {bot_id} not found for user {user_id}")
                    return False

                # Map API fields to DB fields
                db_updates = {}
                for key, value in updates.items():
                    if key == 'config':
                        # Map 'config' -> 'parameters' (will be JSON-encoded by update_bot_config)
                        db_updates['parameters'] = value
                    elif key == 'is_active':
                        # Map 'is_active' -> 'active'
                        db_updates['active'] = value
                    else:
                        db_updates[key] = value

                # Use bot_repository's update_bot_config which handles string IDs
                updated_bot = await self.repository.update_bot_config(session, bot_id, user_id, db_updates)
                if updated_bot:
                    logger.info(f"Updated bot {bot_id} for user {user_id}")
                    return True
                else:
                    logger.error(f"Failed to update bot {bot_id}")
                    return False

        except Exception as e:
            logger.error(f"Error updating bot {bot_id}: {str(e)}")
            raise

    async def delete_bot(self, bot_id: str, user_id: int) -> bool:
        """Delete a bot"""
        try:
            async with self._get_session() as session:
                # First check if bot exists and belongs to user
                existing_bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not existing_bot:
                    logger.warning(f"Bot {bot_id} not found for user {user_id}")
                    return False

                success = await self.repository.delete_bot(session, bot_id, user_id)
                if success:
                    logger.info(f"Deleted bot {bot_id} for user {user_id}")
                    await self._trigger_reconciliation(user_id, session)
                    return True
                else:
                    logger.error(f"Failed to delete bot {bot_id}")
                    return False

        except Exception as e:
            logger.error(f"Error deleting bot {bot_id}: {str(e)}")
            raise

    @cache_query_result(ttl=60, key_prefix="bot_config", include_user=True, include_params=True) if CACHE_AVAILABLE else lambda f: f
    async def get_bot_config(self, bot_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Get bot configuration (cached for 1 minute)"""
        try:
            async with self._get_session() as session:
                bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not bot:
                    return None
                return bot.to_dict()

        except Exception as e:
            logger.error(f"Error getting bot config for {bot_id}: {str(e)}")
            raise

    @cache_query_result(ttl=120, key_prefix="bot_list", include_user=True) if CACHE_AVAILABLE else lambda f: f
    async def list_user_bots(self, user_id: int) -> List[BotConfiguration]:
        """List all bots for a user (cached for 2 minutes)"""
        try:
            async with self._get_session() as session:
                bots = await self.repository.get_user_bots(session, user_id)

                result = []
                for bot in bots:
                    result.append(BotConfiguration(
                        id=bot.id,
                        strategy=bot.strategy,
                        parameters=bot.to_dict().get('parameters', {}),
                        active=bot.active
                    ))

                return result

        except Exception as e:
            logger.error(f"Error listing bots for user {user_id}: {str(e)}")
            raise

    async def validate_bot_config(self, strategy: str, config: Dict[str, Any]) -> bool:
        """Validate bot configuration for given strategy"""
        try:
            # Basic validation - strategy exists
            valid_strategies = ['ml_enhanced', 'ensemble', 'neural_network', 'simple_ma', 'rsi']
            if strategy not in valid_strategies:
                logger.warning(f"Invalid strategy: {strategy}")
                return False

            # Strategy-specific validation (only for ML strategies requiring ml_config)
            if strategy in ['ml_enhanced', 'ensemble', 'neural_network']:
                ml_config = config.get('ml_config', {})
                if ml_config:  # Only validate if provided
                    confidence_threshold = ml_config.get('confidence_threshold', 0.5)
                    if not (0.0 <= confidence_threshold <= 1.0):
                        logger.warning(f"Invalid confidence threshold: {confidence_threshold}")
                        return False

            # Risk parameters validation (only if provided)
            if 'risk_per_trade' in config:
                risk_per_trade = config['risk_per_trade']
                if not (0.001 <= risk_per_trade <= 0.1):
                    logger.warning(f"Invalid risk per trade: {risk_per_trade}")
                    return False

            if 'stop_loss' in config:
                stop_loss = config['stop_loss']
                if not (0.005 <= stop_loss <= 0.5):
                    logger.warning(f"Invalid stop loss: {stop_loss}")
                    return False

            if 'take_profit' in config:
                take_profit = config['take_profit']
                if not (0.01 <= take_profit <= 1.0):
                    logger.warning(f"Invalid take profit: {take_profit}")
                    return False

            return True

    async def _trigger_reconciliation(self, user_id: int, session: AsyncSession) -> None:
        try:
            await reconcile_user_portfolio(str(user_id), session)
        except Exception as exc:
            logger.warning(
                f"Portfolio reconciliation after bot change failed for user {user_id}: {exc}",
                exc_info=True,
            )

        except Exception as e:
            logger.error(f"Error validating bot config: {str(e)}")
            return False
