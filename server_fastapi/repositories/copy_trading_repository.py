"""
Copy Trading Repository
Data access layer for CopiedTrade model operations.
"""

from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from ..models.follow import CopiedTrade
from .base import SQLAlchemyRepository
import logging

logger = logging.getLogger(__name__)


class CopyTradingRepository(SQLAlchemyRepository[CopiedTrade]):
    """Repository for CopiedTrade model operations."""

    def __init__(self):
        super().__init__(CopiedTrade)

    async def get_by_id(
        self, session: AsyncSession, id: int, load_options: Optional[List] = None
    ) -> Optional[CopiedTrade]:
        """Get copied trade by ID with eager loading."""
        if load_options is None:
            load_options = [
                joinedload(CopiedTrade.follower),
                joinedload(CopiedTrade.trader),
                joinedload(CopiedTrade.original_trade),
                joinedload(CopiedTrade.copied_trade),
            ]
        return await super().get_by_id(session, id, load_options)

    async def get_by_follower(
        self, session: AsyncSession, follower_id: int, skip: int = 0, limit: int = 100
    ) -> List[CopiedTrade]:
        """Get all copied trades for a follower with eager loading."""
        query = (
            select(CopiedTrade)
            .where(CopiedTrade.follower_id == follower_id, ~CopiedTrade.is_deleted)
            .order_by(CopiedTrade.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(CopiedTrade.follower),
            joinedload(CopiedTrade.trader),
            joinedload(CopiedTrade.original_trade),
            joinedload(CopiedTrade.copied_trade),
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_trader(
        self, session: AsyncSession, trader_id: int, skip: int = 0, limit: int = 100
    ) -> List[CopiedTrade]:
        """Get all copied trades for a trader with eager loading."""
        query = (
            select(CopiedTrade)
            .where(CopiedTrade.trader_id == trader_id, ~CopiedTrade.is_deleted)
            .order_by(CopiedTrade.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(CopiedTrade.follower),
            joinedload(CopiedTrade.trader),
            joinedload(CopiedTrade.original_trade),
            joinedload(CopiedTrade.copied_trade),
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_follower_and_trader(
        self, session: AsyncSession, follower_id: int, trader_id: int
    ) -> List[CopiedTrade]:
        """Get copied trades for a specific follower-trader relationship."""
        query = (
            select(CopiedTrade)
            .where(
                and_(
                    CopiedTrade.follower_id == follower_id,
                    CopiedTrade.trader_id == trader_id,
                    ~CopiedTrade.is_deleted,
                )
            )
            .order_by(CopiedTrade.created_at.desc())
        )

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(CopiedTrade.follower),
            joinedload(CopiedTrade.trader),
            joinedload(CopiedTrade.original_trade),
            joinedload(CopiedTrade.copied_trade),
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_status(
        self,
        session: AsyncSession,
        status: str,
        follower_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CopiedTrade]:
        """Get copied trades by status with eager loading."""
        conditions = [CopiedTrade.status == status, ~CopiedTrade.is_deleted]

        if follower_id:
            conditions.append(CopiedTrade.follower_id == follower_id)

        query = (
            select(CopiedTrade)
            .where(and_(*conditions))
            .order_by(CopiedTrade.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(CopiedTrade.follower),
            joinedload(CopiedTrade.trader),
            joinedload(CopiedTrade.original_trade),
            joinedload(CopiedTrade.copied_trade),
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def update_status(
        self,
        session: AsyncSession,
        copied_trade_id: int,
        status: str,
        error_message: Optional[str] = None,
    ) -> Optional[CopiedTrade]:
        """Update copied trade status."""
        from sqlalchemy import update

        stmt = (
            update(CopiedTrade)
            .where(CopiedTrade.id == copied_trade_id, ~CopiedTrade.is_deleted)
            .values(status=status, error_message=error_message)
            .returning(CopiedTrade)
        )

        result = await session.execute(stmt)
        await session.commit()

        updated = result.scalar_one_or_none()
        if updated:
            await session.refresh(updated)
        return updated

    async def create_copied_trade(
        self,
        session: AsyncSession,
        follower_id: int,
        trader_id: int,
        original_trade_id: int,
        allocation_percentage: float,
        original_amount: float,
        copied_amount: float,
        original_price: float,
        copied_price: float,
        status: str = "pending",
    ) -> CopiedTrade:
        """Create a new copied trade record."""
        copied_trade = CopiedTrade(
            follower_id=follower_id,
            trader_id=trader_id,
            original_trade_id=original_trade_id,
            allocation_percentage=allocation_percentage,
            original_amount=original_amount,
            copied_amount=copied_amount,
            original_price=original_price,
            copied_price=copied_price,
            status=status,
        )

        session.add(copied_trade)
        await session.commit()
        await session.refresh(copied_trade)

        return copied_trade
