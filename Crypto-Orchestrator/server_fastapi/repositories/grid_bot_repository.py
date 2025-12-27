"""
Grid Bot repository for database operations.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from ..models.grid_bot import GridBot
from .base import SQLAlchemyRepository
import json
import logging

logger = logging.getLogger(__name__)


class GridBotRepository(SQLAlchemyRepository[GridBot]):
    """
    Repository for GridBot model operations.
    """

    def __init__(self):
        super().__init__(GridBot)

    async def get_by_user_and_id(
        self, session: AsyncSession, bot_id: str, user_id: int
    ) -> Optional[GridBot]:
        """Get a grid bot by ID and user ID with eager loading."""
        query = (
            select(GridBot)
            .where(
                GridBot.id == bot_id, GridBot.user_id == user_id, ~GridBot.is_deleted
            )
            .options(joinedload(GridBot.user))
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_grid_bots(
        self, session: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[GridBot]:
        """Get all grid bots for a user with pagination and eager loading."""
        query = (
            select(GridBot)
            .where(GridBot.user_id == user_id, ~GridBot.is_deleted)
            .order_by(GridBot.created_at.desc())
            .offset(skip)
            .limit(limit)
            .options(joinedload(GridBot.user))
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def count_user_grid_bots(self, session: AsyncSession, user_id: int) -> int:
        """Get total count of grid bots for a user."""
        from sqlalchemy import func

        query = select(func.count(GridBot.id)).where(
            GridBot.user_id == user_id, ~GridBot.is_deleted
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
    ) -> Optional[GridBot]:
        """Update grid bot active status and status field."""
        from datetime import datetime

        update_data = {
            "active": active,
            "status": status,
        }

        if active:
            update_data["started_at"] = datetime.utcnow()
        else:
            update_data["stopped_at"] = datetime.utcnow()

        stmt = (
            update(GridBot)
            .where(
                GridBot.id == bot_id, GridBot.user_id == user_id, ~GridBot.is_deleted
            )
            .values(**update_data)
            .returning(GridBot)
        )

        result = await session.execute(stmt)
        await session.commit()

        updated_bot = result.scalar_one_or_none()
        if updated_bot:
            await session.refresh(updated_bot)
        return updated_bot

    async def update_grid_state(
        self,
        session: AsyncSession,
        bot_id: str,
        user_id: int,
        grid_state: Dict[str, Any],
    ) -> Optional[GridBot]:
        """Update grid bot state (orders, filled orders, etc.)."""
        stmt = (
            update(GridBot)
            .where(
                GridBot.id == bot_id, GridBot.user_id == user_id, ~GridBot.is_deleted
            )
            .values(grid_state=json.dumps(grid_state))
            .returning(GridBot)
        )

        result = await session.execute(stmt)
        await session.commit()

        updated_bot = result.scalar_one_or_none()
        if updated_bot:
            await session.refresh(updated_bot)
        return updated_bot

    async def update_performance(
        self,
        session: AsyncSession,
        bot_id: str,
        user_id: int,
        total_profit: float,
        total_trades: int,
        win_rate: float,
    ) -> Optional[GridBot]:
        """Update grid bot performance metrics."""
        from datetime import datetime

        stmt = (
            update(GridBot)
            .where(
                GridBot.id == bot_id, GridBot.user_id == user_id, ~GridBot.is_deleted
            )
            .values(
                total_profit=total_profit,
                total_trades=total_trades,
                win_rate=win_rate,
                last_trade_at=datetime.utcnow(),
            )
            .returning(GridBot)
        )

        result = await session.execute(stmt)
        await session.commit()

        updated_bot = result.scalar_one_or_none()
        if updated_bot:
            await session.refresh(updated_bot)
        return updated_bot

    async def get_active_grid_bots(
        self, session: AsyncSession, user_id: Optional[int] = None
    ) -> List[GridBot]:
        """Get all active grid bots with eager loading, optionally filtered by user."""
        query = (
            select(GridBot)
            .where(GridBot.active == True, ~GridBot.is_deleted)
            .options(joinedload(GridBot.user))
        )

        if user_id:
            query = query.where(GridBot.user_id == user_id)

        result = await session.execute(query)
        return list(result.scalars().all())
