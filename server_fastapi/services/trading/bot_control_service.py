"""
Bot control service for start/stop/status operations
"""

import logging
from typing import Dict, Optional, Any
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db_context
from ...repositories.bot_repository import BotRepository
from .bot_creation_service import BotCreationService
from ..portfolio_reconciliation import reconcile_user_portfolio

logger = logging.getLogger(__name__)


class BotControlService:
    """Service for bot control operations (start, stop, status)"""

    def __init__(self, session: Optional[AsyncSession] = None):
        self.repository = BotRepository()
        self.creation_service = BotCreationService(session=session)
        self._session = session

    @asynccontextmanager
    async def _get_session(self):
        if self._session is not None:
            yield self._session
        else:
            async with get_db_context() as session:
                yield session

    async def start_bot(self, bot_id: str, user_id: int) -> bool:
        """Start a trading bot"""
        try:
            logger.info(f"Starting bot {bot_id} for user {user_id}")

            async with self._get_session() as session:
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
                    # Commit transaction (Service Layer Pattern - service handles commits)
                    await session.commit()
                    await session.refresh(updated_bot)

                    logger.info(f"Bot {bot_id} started successfully")
                    await self._trigger_reconciliation(user_id, session)

                    # Invalidate cache for this bot - use bot_id in pattern (custom key format: bot_id:user_id)
                    try:
                        from ..middleware.cache_manager import invalidate_pattern

                        # Invalidate cache keys for this specific bot (custom key format includes bot_id)
                        await invalidate_pattern(f"bots:get_bot:{bot_id}:*")
                        # Also invalidate any other bot-related cache
                        await invalidate_pattern(f"bots:*{bot_id}*")
                    except Exception as e:
                        logger.warning(
                            f"Failed to invalidate cache for bot {bot_id}: {e}"
                        )

                    return True
                else:
                    logger.error(f"Failed to update bot {bot_id} status")
                    return False

        except Exception as e:
            logger.error(f"Error starting bot {bot_id}: {str(e)}")
            raise

    async def stop_bot(self, bot_id: str, user_id: int) -> bool:
        """Stop a trading bot"""
        try:
            logger.info(f"Stopping bot {bot_id} for user {user_id}")

            async with self._get_session() as session:
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
                    # Commit transaction (Service Layer Pattern - service handles commits)
                    await session.commit()
                    await session.refresh(updated_bot)

                    logger.info(f"Bot {bot_id} stopped successfully")
                    await self._trigger_reconciliation(user_id, session)

                    # Invalidate cache for this bot - use bot_id in pattern (custom key format: bot_id:user_id)
                    try:
                        from ..middleware.cache_manager import invalidate_pattern

                        # Invalidate cache keys for this specific bot (custom key format includes bot_id)
                        await invalidate_pattern(f"bots:get_bot:{bot_id}:*")
                        # Also invalidate any other bot-related cache
                        await invalidate_pattern(f"bots:*{bot_id}*")
                    except Exception as e:
                        logger.warning(
                            f"Failed to invalidate cache for bot {bot_id}: {e}"
                        )

                    return True
                else:
                    logger.error(f"Failed to update bot {bot_id} status")
                    return False

        except Exception as e:
            logger.error(f"Error stopping bot {bot_id}: {str(e)}")
            raise

    async def get_bot_status(
        self, bot_id: str, user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get bot status"""
        try:
            async with self._get_session() as session:
                bot = await self.repository.get_by_user_and_id(session, bot_id, user_id)
                if not bot:
                    return None

                return bot.to_dict()

        except Exception as e:
            logger.error(f"Error getting bot status for {bot_id}: {str(e)}")
            raise

    async def is_bot_active(self, bot_id: str, user_id: int) -> bool:
        """Check if bot is currently active"""
        try:
            status = await self.get_bot_status(bot_id, user_id)
            # to_dict() returns 'is_active' field after mapping
            return status is not None and status.get("is_active", False)

        except Exception as e:
            logger.error(f"Error checking if bot {bot_id} is active: {str(e)}")
            return False

    async def get_bot_state(self, bot_id: str, user_id: int) -> str:
        """Get bot state (running, stopped, error, etc.)"""
        try:
            status = await self.get_bot_status(bot_id, user_id)
            if not status:
                return "not_found"

            return status.get("status", "unknown")

        except Exception as e:
            logger.error(f"Error getting bot state for {bot_id}: {str(e)}")
            return "error"

    async def update_bot_status(
        self, bot_id: str, user_id: int, active: bool, status: str
    ) -> bool:
        """Update bot status directly"""
        try:
            async with self._get_session() as session:
                updated_bot = await self.repository.update_bot_status(
                    session, bot_id, user_id, active, status
                )
                if updated_bot:
                    logger.info(
                        f"Updated bot {bot_id} status to {status} (active: {active})"
                    )
                    await self._trigger_reconciliation(user_id, session)
                    return True
                else:
                    logger.error(f"Failed to update bot {bot_id} status")
                    return False

        except Exception as e:
            logger.error(f"Error updating bot status for {bot_id}: {str(e)}")
            raise

    async def bulk_stop_user_bots(self, user_id: int) -> int:
        """Stop all active bots for a user, return count of stopped bots"""
        try:
            logger.info(f"Stopping all bots for user {user_id}")

            stopped_count = 0
            user_bots = await self.creation_service.list_user_bots(user_id)

            for bot_config in user_bots:
                if bot_config.active:
                    success = await self.stop_bot(bot_config.id, user_id)
                    if success:
                        stopped_count += 1

            logger.info(f"Stopped {stopped_count} bots for user {user_id}")
            return stopped_count

        except Exception as e:
            logger.error(f"Error bulk stopping bots for user {user_id}: {str(e)}")
            raise

    async def _trigger_reconciliation(
        self, user_id: int, session: AsyncSession
    ) -> None:
        try:
            await reconcile_user_portfolio(str(user_id), session)
        except Exception as exc:
            logger.warning(
                f"Portfolio reconciliation after bot status change failed for user {user_id}: {exc}",
                exc_info=True,
            )
