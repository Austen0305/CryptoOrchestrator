"""
Futures Position repository for database operations.
"""

import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models.futures_position import FuturesPosition
from .base import SQLAlchemyRepository

logger = logging.getLogger(__name__)


class FuturesPositionRepository(SQLAlchemyRepository[FuturesPosition]):
    """Repository for FuturesPosition model operations."""

    def __init__(self):
        super().__init__(FuturesPosition)

    async def get_by_user_and_id(
        self, session: AsyncSession, position_id: str, user_id: int
    ) -> FuturesPosition | None:
        """Get a futures position by ID and user ID with eager loading."""
        query = (
            select(FuturesPosition)
            .where(
                FuturesPosition.id == position_id,
                FuturesPosition.user_id == user_id,
                ~FuturesPosition.is_deleted,
            )
            .options(joinedload(FuturesPosition.user))
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_futures_positions(
        self, session: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[FuturesPosition]:
        """Get all futures positions for a user with pagination and eager loading."""
        query = (
            select(FuturesPosition)
            .where(FuturesPosition.user_id == user_id, ~FuturesPosition.is_deleted)
            .order_by(FuturesPosition.created_at.desc())
            .offset(skip)
            .limit(limit)
            .options(joinedload(FuturesPosition.user))
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_open_positions(
        self, session: AsyncSession, user_id: int | None = None
    ) -> list[FuturesPosition]:
        """Get all open futures positions with eager loading, optionally filtered by user."""
        query = (
            select(FuturesPosition)
            .where(FuturesPosition.is_open, ~FuturesPosition.is_deleted)
            .options(joinedload(FuturesPosition.user))
        )

        if user_id:
            query = query.where(FuturesPosition.user_id == user_id)

        result = await session.execute(query)
        return list(result.scalars().all())

    async def count_user_futures_positions(
        self, session: AsyncSession, user_id: int
    ) -> int:
        """Get total count of futures positions for a user."""
        from sqlalchemy import func

        query = select(func.count(FuturesPosition.id)).where(
            FuturesPosition.user_id == user_id, ~FuturesPosition.is_deleted
        )
        result = await session.execute(query)
        return result.scalar() or 0

    async def update_position_pnl(
        self,
        session: AsyncSession,
        position_id: str,
        user_id: int,
        current_price: float,
        unrealized_pnl: float,
        realized_pnl: float,
        total_pnl: float,
        pnl_percent: float,
        liquidation_risk: float,
        margin_ratio: float,
    ) -> FuturesPosition | None:
        """Update futures position P&L and risk metrics."""
        from datetime import UTC, datetime

        stmt = (
            update(FuturesPosition)
            .where(
                FuturesPosition.id == position_id,
                FuturesPosition.user_id == user_id,
                ~FuturesPosition.is_deleted,
            )
            .values(
                current_price=current_price,
                unrealized_pnl=unrealized_pnl,
                realized_pnl=realized_pnl,
                total_pnl=total_pnl,
                pnl_percent=pnl_percent,
                liquidation_risk=liquidation_risk,
                margin_ratio=margin_ratio,
                last_updated_at=datetime.now(UTC),
            )
            .returning(FuturesPosition)
        )

        result = await session.execute(stmt)
        await session.commit()

        updated_position = result.scalar_one_or_none()
        if updated_position:
            await session.refresh(updated_position)
        return updated_position

    async def close_position(
        self,
        session: AsyncSession,
        position_id: str,
        user_id: int,
        realized_pnl: float,
        total_pnl: float,
    ) -> FuturesPosition | None:
        """Close a futures position."""
        from datetime import datetime

        stmt = (
            update(FuturesPosition)
            .where(
                FuturesPosition.id == position_id,
                FuturesPosition.user_id == user_id,
                ~FuturesPosition.is_deleted,
            )
            .values(
                is_open=False,
                status="closed",
                realized_pnl=realized_pnl,
                total_pnl=total_pnl,
                closed_at=datetime.now(UTC),
                last_updated_at=datetime.now(UTC),
            )
            .returning(FuturesPosition)
        )

        result = await session.execute(stmt)
        await session.commit()

        updated_position = result.scalar_one_or_none()
        if updated_position:
            await session.refresh(updated_position)
        return updated_position
