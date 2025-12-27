"""
Bot runner service for FastAPI backend using async SQLAlchemy
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from ...database import get_db_context
from ...repositories.bot_repository import BotRepository

logger = logging.getLogger(__name__)


class BotConfiguration(BaseModel):
    id: str
    strategy: str
    parameters: Dict[str, Any]
    active: bool


class BotRunner:
    """Async bot runner service with SQLAlchemy database persistence"""

    def __init__(self):
        self.repository = BotRepository()

    async def start_bot(self, bot_id: str, user_id: int) -> bool:
        """Start a trading bot"""
        try:
            logger.info(f"Starting bot {bot_id} for user {user_id}")

            async with get_db_context() as session:
                # Check if bot exists and belongs to user
                bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not bot:
                    logger.warning(f"Bot {bot_id} not found for user {user_id}")
                    return False

                if bot.active:  # already active
                    logger.warning(f"Bot {bot_id} is already active")
                    return False

                # Update bot status
                updated_bot = await self.repository.update_bot_status(
                    session, bot_id, user_id, True, "running"
                )
                if updated_bot:
                    logger.info(f"Bot {bot_id} started successfully")
                    return True
                else:
                    logger.error(f"Failed to update bot {bot_id} status")
                    return False

        except Exception as e:
            logger.error(f"Error starting bot {bot_id}: {str(e)}")
            return False

    async def stop_bot(self, bot_id: str, user_id: int) -> bool:
        """Stop a trading bot"""
        try:
            logger.info(f"Stopping bot {bot_id} for user {user_id}")

            async with get_db_context() as session:
                # Check if bot exists and belongs to user
                bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not bot:
                    logger.warning(f"Bot {bot_id} not found for user {user_id}")
                    return False

                if not bot.active:  # not active
                    logger.warning(f"Bot {bot_id} is not active")
                    return False

                # Update bot status
                updated_bot = await self.repository.update_bot_status(
                    session, bot_id, user_id, False, "stopped"
                )
                if updated_bot:
                    logger.info(f"Bot {bot_id} stopped successfully")
                    return True
                else:
                    logger.error(f"Failed to update bot {bot_id} status")
                    return False

        except Exception as e:
            logger.error(f"Error stopping bot {bot_id}: {str(e)}")
            return False

    async def get_bot_status(
        self, bot_id: str, user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get bot status"""
        try:
            async with get_db_context() as session:
                bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not bot:
                    return None

                return bot.to_dict()

        except Exception as e:
            logger.error(f"Error getting bot status for {bot_id}: {str(e)}")
            return None

    async def list_bots(self, user_id: int) -> List[BotConfiguration]:
        """List all bots for a user"""
        try:
            async with get_db_context() as session:
                bots = await self.repository.get_user_bots(session, user_id)

                result = []
                for bot in bots:
                    result.append(
                        BotConfiguration(
                            id=bot.id,
                            strategy=bot.strategy,
                            parameters=bot.to_dict().get("parameters", {}),
                            active=bot.active,
                        )
                    )

                return result

        except Exception as e:
            logger.error(f"Error listing bots for user {user_id}: {str(e)}")
            return []

    async def create_bot(
        self,
        user_id: int,
        name: str,
        symbol: str,
        strategy: str,
        parameters: Dict[str, Any],
    ) -> Optional[str]:
        """Create a new bot"""
        try:
            bot_id = f"bot-{user_id}-{hash(f'{user_id}-{name}-{datetime.now().isoformat()}') % 1000000}"

            async with get_db_context() as session:
                bot = await self.repository.create_bot(
                    session, bot_id, user_id, name, symbol, strategy, parameters
                )
                if bot:
                    logger.info(f"Created bot {bot_id} for user {user_id}")
                    return bot_id
                else:
                    logger.error(f"Failed to create bot for user {user_id}")
                    return None

        except Exception as e:
            logger.error(f"Error creating bot for user {user_id}: {str(e)}")
            return None

    async def update_bot_performance(
        self, bot_id: str, user_id: int, performance_data: Dict[str, Any]
    ) -> bool:
        """Update bot performance data"""
        try:
            async with get_db_context() as session:
                return await self.repository.update_performance_data(
                    session, bot_id, user_id, performance_data
                )

        except Exception as e:
            logger.error(f"Error updating performance for bot {bot_id}: {str(e)}")
            return False
