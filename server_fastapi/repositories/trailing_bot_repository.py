"""
Trailing Bot repository for database operations.
"""

import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models.trailing_bot import TrailingBot
from .base import SQLAlchemyRepository

logger = logging.getLogger(__name__)


class TrailingBotRepository(SQLAlchemyRepository[TrailingBot]):
    """Repository for TrailingBot model operations."""

    def __init__(self):
        super().__init__(TrailingBot)

    async def get_by_user_and_id(
        self, session: AsyncSession, bot_id: str, user_id: int
    ) -> TrailingBot | None:
        """Get a trailing bot by ID and user ID with eager loading."""
        query = (
            select(TrailingBot)
            .where(
                TrailingBot.id == bot_id,
                TrailingBot.user_id == user_id,
                ~TrailingBot.is_deleted,
            )
            .options(joinedload(TrailingBot.user))
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_trailing_bots(
        self, session: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[TrailingBot]:
        """Get all trailing bots for a user with pagination and eager loading."""
        query = (
            select(TrailingBot)
            .where(TrailingBot.user_id == user_id, ~TrailingBot.is_deleted)
            .order_by(TrailingBot.created_at.desc())
            .offset(skip)
            .limit(limit)
            .options(joinedload(TrailingBot.user))
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def count_user_trailing_bots(
        self, session: AsyncSession, user_id: int
    ) -> int:
        """Get total count of trailing bots for a user."""
        from sqlalchemy import func

        query = select(func.count(TrailingBot.id)).where(
            TrailingBot.user_id == user_id, ~TrailingBot.is_deleted
        )
        result = await session.execute(query)
        return result.scalar() or 0

    async def update_bot_status(
        self,
        session: AsyncSession,
        bot_id: str,
        user_id: int,
        active: bool,
        status: str,
    ) -> TrailingBot | None:
        """Update trailing bot active status and status field."""
        from datetime import UTC, datetime

        update_data = {
            "active": active,
            "status": status,
        }

        if active:
            update_data["started_at"] = datetime.now(UTC)
        else:
            update_data["stopped_at"] = datetime.now(UTC)

        stmt = (
            update(TrailingBot)
            .where(
                TrailingBot.id == bot_id,
                TrailingBot.user_id == user_id,
                ~TrailingBot.is_deleted,
            )
            .values(**update_data)
            .returning(TrailingBot)
        )

        result = await session.execute(stmt)
        await session.commit()

        updated_bot = result.scalar_one_or_none()
        if updated_bot:
            await session.refresh(updated_bot)
        return updated_bot

    async def update_trailing_price(
        self,
        session: AsyncSession,
        bot_id: str,
        user_id: int,
        current_price: float,
        highest_price: float,
        lowest_price: float,
    ) -> TrailingBot | None:
        """Update trailing bot price tracking."""
        from datetime import datetime

        stmt = (
            update(TrailingBot)
            .where(
                TrailingBot.id == bot_id,
                TrailingBot.user_id == user_id,
                ~TrailingBot.is_deleted,
            )
            .values(
                current_price=current_price,
                highest_price=highest_price,
                lowest_price=lowest_price,
                last_price_update_at=datetime.now(UTC),
            )
            .returning(TrailingBot)
        )

        result = await session.execute(stmt)
        await session.commit()

        updated_bot = result.scalar_one_or_none()
        if updated_bot:
            await session.refresh(updated_bot)
        return updated_bot

    async def get_active_trailing_bots(
        self, session: AsyncSession, user_id: int | None = None
    ) -> list[TrailingBot]:
        """Get all active trailing bots with eager loading, optionally filtered by user."""
        query = (
            select(TrailingBot)
            .where(TrailingBot.active, ~TrailingBot.is_deleted)
            .options(joinedload(TrailingBot.user))
        )

        if user_id:
            query = query.where(TrailingBot.user_id == user_id)

        result = await session.execute(query)
        return list(result.scalars().all())
