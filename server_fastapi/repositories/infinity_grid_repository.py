"""
Infinity Grid repository for database operations.
"""

from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from ..models.infinity_grid import InfinityGrid
from .base import SQLAlchemyRepository
import json
import logging

logger = logging.getLogger(__name__)


class InfinityGridRepository(SQLAlchemyRepository[InfinityGrid]):
    """Repository for InfinityGrid model operations."""

    def __init__(self):
        super().__init__(InfinityGrid)

    async def get_by_user_and_id(
        self, session: AsyncSession, bot_id: str, user_id: int
    ) -> Optional[InfinityGrid]:
        """Get an infinity grid by ID and user ID with eager loading."""
        query = (
            select(InfinityGrid)
            .where(
                InfinityGrid.id == bot_id,
                InfinityGrid.user_id == user_id,
                ~InfinityGrid.is_deleted,
            )
            .options(joinedload(InfinityGrid.user))
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_infinity_grids(
        self, session: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[InfinityGrid]:
        """Get all infinity grids for a user with pagination and eager loading."""
        query = (
            select(InfinityGrid)
            .where(InfinityGrid.user_id == user_id, ~InfinityGrid.is_deleted)
            .order_by(InfinityGrid.created_at.desc())
            .offset(skip)
            .limit(limit)
            .options(joinedload(InfinityGrid.user))
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def count_user_infinity_grids(self, session: AsyncSession, user_id: int) -> int:
        """Get total count of infinity grids for a user."""
        from sqlalchemy import func

        query = select(func.count(InfinityGrid.id)).where(
            InfinityGrid.user_id == user_id, ~InfinityGrid.is_deleted
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
    ) -> Optional[InfinityGrid]:
        """Update infinity grid active status and status field."""
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
            update(InfinityGrid)
            .where(
                InfinityGrid.id == bot_id,
                InfinityGrid.user_id == user_id,
                ~InfinityGrid.is_deleted,
            )
            .values(**update_data)
            .returning(InfinityGrid)
        )

        result = await session.execute(stmt)
        await session.commit()

        updated_bot = result.scalar_one_or_none()
        if updated_bot:
            await session.refresh(updated_bot)
        return updated_bot

    async def update_grid_bounds(
        self,
        session: AsyncSession,
        bot_id: str,
        user_id: int,
        upper_price: float,
        lower_price: float,
    ) -> Optional[InfinityGrid]:
        """Update infinity grid bounds."""
        from datetime import datetime

        stmt = (
            update(InfinityGrid)
            .where(
                InfinityGrid.id == bot_id,
                InfinityGrid.user_id == user_id,
                ~InfinityGrid.is_deleted,
            )
            .values(
                current_upper_price=upper_price,
                current_lower_price=lower_price,
                grid_adjustments=InfinityGrid.grid_adjustments + 1,
                last_adjustment_at=datetime.utcnow(),
            )
            .returning(InfinityGrid)
        )

        result = await session.execute(stmt)
        await session.commit()

        updated_bot = result.scalar_one_or_none()
        if updated_bot:
            await session.refresh(updated_bot)
        return updated_bot

    async def get_active_infinity_grids(
        self, session: AsyncSession, user_id: Optional[int] = None
    ) -> List[InfinityGrid]:
        """Get all active infinity grids with eager loading, optionally filtered by user."""
        query = (
            select(InfinityGrid)
            .where(InfinityGrid.active == True, ~InfinityGrid.is_deleted)
            .options(joinedload(InfinityGrid.user))
        )

        if user_id:
            query = query.where(InfinityGrid.user_id == user_id)

        result = await session.execute(query)
        return list(result.scalars().all())
