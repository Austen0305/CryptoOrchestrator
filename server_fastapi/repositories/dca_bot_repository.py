"""
DCA Bot repository for database operations.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.dca_bot import DCABot
from .base import SQLAlchemyRepository
import json
import logging

logger = logging.getLogger(__name__)


class DCABotRepository(SQLAlchemyRepository[DCABot]):
    """
    Repository for DCABot model operations.
    """

    def __init__(self):
        super().__init__(DCABot)

    async def get_by_user_and_id(self, session: AsyncSession, bot_id: str, user_id: int) -> Optional[DCABot]:
        """Get a DCA bot by ID and user ID."""
        query = select(DCABot).where(
            DCABot.id == bot_id,
            DCABot.user_id == user_id,
            ~DCABot.is_deleted
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_dca_bots(self, session: AsyncSession, user_id: int,
                               skip: int = 0, limit: int = 100) -> List[DCABot]:
        """Get all DCA bots for a user with pagination."""
        query = select(DCABot).where(
            DCABot.user_id == user_id,
            ~DCABot.is_deleted
        ).order_by(DCABot.created_at.desc()).offset(skip).limit(limit)

        result = await session.execute(query)
        return list(result.scalars().all())

    async def update_bot_status(self, session: AsyncSession, bot_id: str, user_id: int,
                               active: bool, status: str) -> Optional[DCABot]:
        """Update DCA bot active status and status field."""
        from datetime import datetime
        update_data = {
            'active': active,
            'status': status,
        }

        if active:
            update_data['started_at'] = datetime.utcnow()
        else:
            update_data['stopped_at'] = datetime.utcnow()
            if status == "completed":
                update_data['completed_at'] = datetime.utcnow()

        stmt = update(DCABot).where(
            DCABot.id == bot_id,
            DCABot.user_id == user_id,
            ~DCABot.is_deleted
        ).values(**update_data).returning(DCABot)

        result = await session.execute(stmt)
        await session.commit()

        updated_bot = result.scalar_one_or_none()
        if updated_bot:
            await session.refresh(updated_bot)
        return updated_bot

    async def update_next_order_time(self, session: AsyncSession, bot_id: str, user_id: int,
                                     next_order_at: datetime) -> Optional[DCABot]:
        """Update next order execution time."""
        from datetime import datetime
        stmt = update(DCABot).where(
            DCABot.id == bot_id,
            DCABot.user_id == user_id,
            ~DCABot.is_deleted
        ).values(
            next_order_at=next_order_at,
            last_order_at=datetime.utcnow()
        ).returning(DCABot)

        result = await session.execute(stmt)
        await session.commit()

        updated_bot = result.scalar_one_or_none()
        if updated_bot:
            await session.refresh(updated_bot)
        return updated_bot

    async def update_performance(self, session: AsyncSession, bot_id: str, user_id: int,
                                orders_executed: int, total_invested: float, average_price: float,
                                current_value: float, total_profit: float, profit_percent: float) -> Optional[DCABot]:
        """Update DCA bot performance metrics."""
        stmt = update(DCABot).where(
            DCABot.id == bot_id,
            DCABot.user_id == user_id,
            ~DCABot.is_deleted
        ).values(
            orders_executed=orders_executed,
            total_invested=total_invested,
            average_price=average_price,
            current_value=current_value,
            total_profit=total_profit,
            profit_percent=profit_percent
        ).returning(DCABot)

        result = await session.execute(stmt)
        await session.commit()

        updated_bot = result.scalar_one_or_none()
        if updated_bot:
            await session.refresh(updated_bot)
        return updated_bot

    async def get_active_dca_bots(self, session: AsyncSession, user_id: Optional[int] = None) -> List[DCABot]:
        """Get all active DCA bots, optionally filtered by user."""
        query = select(DCABot).where(
            DCABot.active == True,
            ~DCABot.is_deleted
        )
        
        if user_id:
            query = query.where(DCABot.user_id == user_id)
        
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_bots_ready_for_order(self, session: AsyncSession) -> List[DCABot]:
        """Get DCA bots that are ready to execute their next order."""
        from datetime import datetime
        now = datetime.utcnow()
        
        query = select(DCABot).where(
            DCABot.active == True,
            DCABot.next_order_at <= now,
            ~DCABot.is_deleted
        )
        
        result = await session.execute(query)
        return list(result.scalars().all())

