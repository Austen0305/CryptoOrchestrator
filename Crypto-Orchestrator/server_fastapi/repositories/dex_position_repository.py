"""
DEX Position Repository
Data access layer for DEXPosition model operations.
"""

from typing import List, Optional
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models.dex_position import DEXPosition
from .base import SQLAlchemyRepository
import logging

logger = logging.getLogger(__name__)


class DEXPositionRepository(SQLAlchemyRepository[DEXPosition]):
    """Repository for DEXPosition model operations."""

    def __init__(self) -> None:
        super().__init__(DEXPosition)

    async def get_by_id(
        self, session: AsyncSession, id: int, load_options: Optional[List] = None
    ) -> Optional[DEXPosition]:
        """Get position by ID with eager loading."""
        if load_options is None:
            load_options = [
                joinedload(DEXPosition.user),
            ]
        # DEXPosition model doesn't have is_deleted, so override base method
        query = select(DEXPosition).where(DEXPosition.id == id)
        if load_options:
            for option in load_options:
                query = query.options(option)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        session: AsyncSession,
        user_id: int,
        chain_id: Optional[int] = None,
        is_open: Optional[bool] = None,
    ) -> List[DEXPosition]:
        """Get positions by user with eager loading."""
        conditions = [DEXPosition.user_id == user_id]

        if chain_id is not None:
            conditions.append(DEXPosition.chain_id == chain_id)
        if is_open is not None:
            conditions.append(DEXPosition.is_open.is_(is_open))

        query = select(DEXPosition).where(and_(*conditions))

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(DEXPosition.user),
        )

        query = query.order_by(DEXPosition.opened_at.desc())

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_open_positions(
        self, session: AsyncSession, user_id: Optional[int] = None
    ) -> List[DEXPosition]:
        """Get all open positions with eager loading."""
        conditions = [DEXPosition.is_open.is_(True)]

        if user_id is not None:
            conditions.append(DEXPosition.user_id == user_id)

        query = select(DEXPosition).where(and_(*conditions))

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(DEXPosition.user),
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def create_position(
        self, session: AsyncSession, position_data: dict
    ) -> DEXPosition:
        """Create a new position."""
        position = DEXPosition(**position_data)

        session.add(position)
        await session.commit()
        await session.refresh(position)

        return position

    async def update_position(
        self, session: AsyncSession, position_id: int, update_data: dict
    ) -> Optional[DEXPosition]:
        """Update position fields."""
        stmt = (
            update(DEXPosition)
            .where(DEXPosition.id == position_id)
            .values(**update_data)
            .returning(DEXPosition)
        )

        result = await session.execute(stmt)
        await session.commit()

        updated = result.scalar_one_or_none()
        if updated:
            await session.refresh(updated)
        return updated
