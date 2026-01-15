"""
Trade Repository
Data access layer for Trade model operations.
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models.trade import Trade
from .base import SQLAlchemyRepository

logger = logging.getLogger(__name__)


class TradeRepository(SQLAlchemyRepository[Trade]):
    """Repository for Trade model operations."""

    def __init__(self) -> None:
        super().__init__(Trade)

    async def get_by_id(
        self, session: AsyncSession, id: int, load_options: list | None = None
    ) -> Trade | None:
        """Get trade by ID with eager loading."""
        if load_options is None:
            load_options = [
                joinedload(Trade.user),
                joinedload(Trade.bot),
                joinedload(Trade.grid_bot),
                joinedload(Trade.dca_bot),
                joinedload(Trade.infinity_grid),
                joinedload(Trade.trailing_bot),
                joinedload(Trade.futures_position),
            ]
        # Trade model doesn't have is_deleted, so override base method
        query = select(Trade).where(Trade.id == id)
        if load_options:
            for option in load_options:
                query = query.options(option)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        session: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        mode: str | None = None,
    ) -> list[Trade]:
        """Get all trades for a user with eager loading."""
        conditions = [Trade.user_id == user_id]

        if mode:
            conditions.append(Trade.mode == mode)

        query = (
            select(Trade)
            .where(and_(*conditions))
            .order_by(Trade.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(Trade.user),
            joinedload(Trade.bot),
            joinedload(Trade.grid_bot),
            joinedload(Trade.dca_bot),
            joinedload(Trade.infinity_grid),
            joinedload(Trade.trailing_bot),
            joinedload(Trade.futures_position),
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_bot(
        self, session: AsyncSession, bot_id: str, skip: int = 0, limit: int = 100
    ) -> list[Trade]:
        """Get all trades for a bot with eager loading."""
        query = (
            select(Trade)
            .where(Trade.bot_id == bot_id)
            .order_by(Trade.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(Trade.user),
            joinedload(Trade.bot),
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_grid_bot(
        self, session: AsyncSession, grid_bot_id: str, skip: int = 0, limit: int = 100
    ) -> list[Trade]:
        """Get all trades for a grid bot with eager loading."""
        query = (
            select(Trade)
            .where(Trade.grid_bot_id == grid_bot_id)
            .order_by(Trade.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(Trade.user),
            joinedload(Trade.grid_bot),
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_dca_bot(
        self, session: AsyncSession, dca_bot_id: str, skip: int = 0, limit: int = 100
    ) -> list[Trade]:
        """Get all trades for a DCA bot with eager loading."""
        query = (
            select(Trade)
            .where(Trade.dca_bot_id == dca_bot_id)
            .order_by(Trade.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(Trade.user),
            joinedload(Trade.dca_bot),
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_infinity_grid(
        self,
        session: AsyncSession,
        infinity_grid_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Trade]:
        """Get all trades for an infinity grid with eager loading."""
        query = (
            select(Trade)
            .where(Trade.infinity_grid_id == infinity_grid_id)
            .order_by(Trade.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(Trade.user),
            joinedload(Trade.infinity_grid),
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_trailing_bot(
        self,
        session: AsyncSession,
        trailing_bot_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Trade]:
        """Get all trades for a trailing bot with eager loading."""
        query = (
            select(Trade)
            .where(Trade.trailing_bot_id == trailing_bot_id)
            .order_by(Trade.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(Trade.user),
            joinedload(Trade.trailing_bot),
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_futures_position(
        self,
        session: AsyncSession,
        futures_position_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Trade]:
        """Get all trades for a futures position with eager loading."""
        query = (
            select(Trade)
            .where(Trade.futures_position_id == futures_position_id)
            .order_by(Trade.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(Trade.user),
            joinedload(Trade.futures_position),
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_symbol(
        self,
        session: AsyncSession,
        symbol: str,
        user_id: int | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Trade]:
        """Get trades by symbol with eager loading."""
        conditions = [Trade.symbol == symbol]

        if user_id:
            conditions.append(Trade.user_id == user_id)

        query = (
            select(Trade)
            .where(and_(*conditions))
            .order_by(Trade.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(Trade.user),
            joinedload(Trade.bot),
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def create_trade(self, session: AsyncSession, trade_data: dict) -> Trade:
        """Create a new trade record."""
        trade = Trade(**trade_data)

        session.add(trade)
        await session.commit()
        await session.refresh(trade)

        return trade

    async def update_trade(
        self, session: AsyncSession, trade_id: int, updates: dict
    ) -> Trade | None:
        """Update a trade record."""
        from sqlalchemy import update

        stmt = (
            update(Trade).where(Trade.id == trade_id).values(**updates).returning(Trade)
        )

        result = await session.execute(stmt)
        await session.commit()

        updated = result.scalar_one_or_none()
        if updated:
            await session.refresh(updated)
        return updated

    async def get_completed_trades_for_pnl(
        self,
        session: AsyncSession,
        user_id: int,
        mode: str,
        pairs: list[str] | str | None = None,
        period_hours: int | None = None,
    ) -> list[Trade]:
        """
        Get completed trades for P&L calculations.

        Args:
            session: Database session
            user_id: User ID
            mode: Trading mode ("paper" or "real")
            pair: Optional trading pair symbol (e.g., "BTC/USD")
            period_hours: Optional time period in hours (e.g., 24 for 24h P&L)

        Returns:
            List of completed trades ordered by timestamp
        """
        conditions = [
            Trade.user_id == user_id,
            Trade.mode == mode,
            Trade.status == "completed",
        ]

        if pairs:
            if isinstance(pairs, list):
                conditions.append(Trade.pair.in_(pairs))
            else:
                conditions.append(Trade.pair == pairs)

        if period_hours:
            cutoff_time = datetime.now(UTC) - timedelta(hours=period_hours)
            conditions.append(Trade.timestamp >= cutoff_time)

        query = select(Trade).where(and_(*conditions)).order_by(Trade.timestamp)

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(Trade.user),
        )

        result = await session.execute(query)
        return list(result.scalars().all())
