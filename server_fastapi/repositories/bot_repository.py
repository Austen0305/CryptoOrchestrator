"""
Bot repository for database operations.
"""

import contextlib
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.bot import Bot
from .base import SQLAlchemyRepository


class BotRepository(SQLAlchemyRepository[Bot]):
    """
    Repository for Bot model operations.
    """

    def __init__(self):
        super().__init__(Bot)

    async def get_by_user_and_id(
        self, session: AsyncSession, bot_id: str, user_id: int
    ) -> Bot | None:
        """
        Get a bot by ID and user ID with eager loading.
        """
        from sqlalchemy.orm import joinedload

        query = (
            select(Bot)
            .where(Bot.id == bot_id, Bot.user_id == user_id, ~Bot.is_deleted)
            .options(joinedload(Bot.user))  # Eager load user to prevent N+1 queries
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_bots(
        self, session: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[Bot]:
        """
        Get all bots for a user with pagination and eager loading.
        """
        query = (
            select(Bot)
            .where(Bot.user_id == user_id, ~Bot.is_deleted)
            .order_by(Bot.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        # Eager load user relationship to prevent N+1 queries
        from sqlalchemy.orm import joinedload

        query = query.options(joinedload(Bot.user))

        result = await session.execute(query)
        return list(result.scalars().all())

    async def update_bot_status(
        self,
        session: AsyncSession,
        bot_id: str,
        user_id: int,
        active: bool,
        status: str,
    ) -> Bot | None:
        """
        Update bot active status and status field.

        Note: Does not commit - service layer should handle commits (Service Layer Pattern).
        """
        from datetime import UTC, datetime

        update_data = {
            "active": active,
            "status": status,
        }

        if active:
            update_data["last_started_at"] = datetime.now(UTC)
        else:
            update_data["last_stopped_at"] = datetime.now(UTC)

        stmt = (
            update(Bot)
            .where(Bot.id == bot_id, Bot.user_id == user_id, ~Bot.is_deleted)
            .values(**update_data)
            .returning(Bot)
        )

        result = await session.execute(stmt)
        # Don't commit here - let service layer handle commits (Service Layer Pattern)
        # await session.commit()  # Removed - service should commit

        updated_bot = result.scalar_one_or_none()
        if updated_bot:
            await session.refresh(updated_bot)
        return updated_bot

    async def delete_bot(
        self, session: AsyncSession, bot_id: str, user_id: int
    ) -> bool:
        """
        Soft delete a bot.
        """
        from datetime import datetime

        stmt = (
            update(Bot)
            .where(Bot.id == bot_id, Bot.user_id == user_id, ~Bot.is_deleted)
            .values(is_deleted=True, deleted_at=datetime.now(UTC))
        )

        result = await session.execute(stmt)
        with contextlib.suppress(Exception):
            await session.flush()
        return result.rowcount > 0

    async def update_bot_config(
        self, session: AsyncSession, bot_id: str, user_id: int, updates: dict[str, Any]
    ) -> Bot | None:
        """
        Update bot configuration fields.
        """
        import json

        update_data = {}
        for key, value in updates.items():
            if key == "parameters" and isinstance(value, (dict, list)):
                # JSON-encode parameters/config
                update_data["parameters"] = json.dumps(value)
            else:
                update_data[key] = value

        stmt = (
            update(Bot)
            .where(Bot.id == bot_id, Bot.user_id == user_id, ~Bot.is_deleted)
            .values(**update_data)
            .returning(Bot)
        )

        result = await session.execute(stmt)
        with contextlib.suppress(Exception):
            await session.flush()

        updated_bot = result.scalar_one_or_none()
        if updated_bot:
            await session.refresh(updated_bot)
        return updated_bot

    async def update_performance_data(
        self,
        session: AsyncSession,
        bot_id: str,
        user_id: int,
        performance_data: dict[str, Any],
    ) -> bool:
        """
        Update bot performance data.
        """
        import json

        stmt = (
            update(Bot)
            .where(Bot.id == bot_id, Bot.user_id == user_id, ~Bot.is_deleted)
            .values(performance_data=json.dumps(performance_data))
        )

        result = await session.execute(stmt)
        with contextlib.suppress(Exception):
            await session.flush()
        return result.rowcount > 0

    async def create_bot(
        self,
        session: AsyncSession,
        bot_id: str,
        user_id: int,
        name: str,
        symbol: str,
        strategy: str,
        parameters: dict[str, Any],
    ) -> Bot:
        """
        Create a new bot.
        """
        import json

        bot_data = {
            "id": bot_id,
            "user_id": user_id,
            "name": name,
            "symbol": symbol,
            "strategy": strategy,
            "parameters": json.dumps(parameters),
            "active": False,
            "status": "stopped",
        }

        return await self.create(session, bot_data)
