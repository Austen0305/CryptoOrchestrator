"""
Follow repository for database operations.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from ..models.follow import Follow
from .base import SQLAlchemyRepository
import logging

logger = logging.getLogger(__name__)


class FollowRepository(SQLAlchemyRepository[Follow]):
    """Repository for Follow model operations."""

    def __init__(self):
        super().__init__(Follow)

    async def get_by_follower_and_trader(
        self, session: AsyncSession, follower_id: int, trader_id: int
    ) -> Optional[Follow]:
        """Get follow relationship by follower and trader IDs."""
        query = select(Follow).where(
            Follow.follower_id == follower_id,
            Follow.trader_id == trader_id,
            ~Follow.is_deleted,
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_active_auto_copy_follows(
        self, session: AsyncSession, follower_id: Optional[int] = None
    ) -> List[Follow]:
        """Get all active follow relationships with auto-copy enabled."""
        query = select(Follow).where(
            Follow.is_active == True,
            Follow.auto_copy_enabled == True,
            ~Follow.is_deleted,
        )

        if follower_id:
            query = query.where(Follow.follower_id == follower_id)

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_follower_follows(
        self, session: AsyncSession, follower_id: int
    ) -> List[Follow]:
        """Get all follow relationships for a follower with eager loading."""
        query = select(Follow).where(
            Follow.follower_id == follower_id, ~Follow.is_deleted
        )

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(Follow.follower),
            joinedload(Follow.trader),
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_active_follows_by_follower(
        self, session: AsyncSession, follower_id: int
    ) -> List[Follow]:
        """Get active follow relationships for a follower with eager loading."""
        query = select(Follow).where(
            and_(
                Follow.follower_id == follower_id,
                Follow.is_active == True,
                ~Follow.is_deleted,
            )
        )

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(Follow.follower),
            joinedload(Follow.trader),
        )

        result = await session.execute(query)
        return list(result.scalars().all())
