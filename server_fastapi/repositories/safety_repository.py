"""
Safety Repository
Data access layer for persistent user safety statistics
"""

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user_safety_stats import UserSafetyStats

logger = logging.getLogger(__name__)


class SafetyRepository:
    """Repository for user safety statistics"""

    async def get_safety_stats(
        self, session: AsyncSession, user_id: int
    ) -> UserSafetyStats | None:
        """Retrieve safety stats for a user"""
        stmt = select(UserSafetyStats).where(UserSafetyStats.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_safety_stats(
        self, session: AsyncSession, user_id: int
    ) -> UserSafetyStats:
        """Initialize safety stats for a user"""
        stats = UserSafetyStats(
            user_id=user_id,
            daily_loss=0.0,
            daily_volume=0.0,
            total_trades_today=0,
            last_reset_at=datetime.now(UTC),
            emergency_stop_active=0,
        )
        session.add(stats)
        await session.commit()
        await session.refresh(stats)
        return stats

    async def update_trade_stats(
        self,
        session: AsyncSession,
        user_id: int,
        realized_loss: float,
        trade_volume: float,
    ) -> UserSafetyStats:
        """Update daily stats after a trade"""
        stats = await self.get_safety_stats(session, user_id)
        if not stats:
            stats = await self.create_safety_stats(session, user_id)

        # Check for daily reset (2026 standard)
        now = datetime.now(UTC)
        if stats.last_reset_at.date() < now.date():
            stats.daily_loss = realized_loss
            stats.daily_volume = trade_volume
            stats.total_trades_today = 1
            stats.last_reset_at = now
        else:
            stats.daily_loss += realized_loss
            stats.daily_volume += trade_volume
            stats.total_trades_today += 1

        await session.commit()
        await session.refresh(stats)
        return stats

    async def set_emergency_stop(
        self, session: AsyncSession, user_id: int, active: bool
    ) -> None:
        """Set emergency stop flag"""
        stats = await self.get_safety_stats(session, user_id)
        if stats:
            stats.emergency_stop_active = 1 if active else 0
            await session.commit()
