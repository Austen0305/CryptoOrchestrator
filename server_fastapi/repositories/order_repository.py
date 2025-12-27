"""
Order Repository
Data access layer for Order model operations (advanced orders: stop-loss, take-profit, trailing stops).
"""

from typing import List, Optional
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models.order import Order
from .base import SQLAlchemyRepository
import logging

logger = logging.getLogger(__name__)


class OrderRepository(SQLAlchemyRepository[Order]):
    """Repository for Order model operations (advanced orders)."""

    def __init__(self) -> None:
        super().__init__(Order)

    async def get_by_id(
        self, session: AsyncSession, id: int, load_options: Optional[List] = None
    ) -> Optional[Order]:
        """Get order by ID with eager loading."""
        if load_options is None:
            load_options = [
                joinedload(Order.user),
                joinedload(Order.trades),
            ]
        # Order model doesn't have is_deleted, so override base method
        query = select(Order).where(Order.id == id)
        if load_options:
            for option in load_options:
                query = query.options(option)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        session: AsyncSession,
        user_id: int,
        order_type: Optional[str] = None,
        status: Optional[str] = None,
        symbol: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """Get orders by user with eager loading."""
        conditions = [Order.user_id == user_id]

        if order_type:
            conditions.append(Order.order_type == order_type)
        if status:
            conditions.append(Order.status == status)
        if symbol:
            conditions.append(Order.symbol == symbol)

        query = select(Order).where(and_(*conditions))

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(Order.user),
            joinedload(Order.trades),
        )

        query = query.offset(skip).limit(limit).order_by(Order.created_at.desc())

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_symbol_and_status(
        self,
        session: AsyncSession,
        symbol: str,
        statuses: List[str],
        order_types: Optional[List[str]] = None,
        chain_id: Optional[int] = None,
    ) -> List[Order]:
        """Get orders by symbol and status with eager loading."""
        conditions = [
            Order.symbol == symbol,
            Order.status.in_(statuses),
        ]

        if order_types:
            conditions.append(Order.order_type.in_(order_types))
        if chain_id:
            conditions.append(Order.chain_id == chain_id)

        query = select(Order).where(and_(*conditions))

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(Order.user),
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_bot_id(self, session: AsyncSession, bot_id: str) -> List[Order]:
        """Get orders by bot_id (used for OCO order linking)."""
        query = select(Order).where(Order.bot_id == bot_id)

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(Order.user),
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def create_order(self, session: AsyncSession, order_data: dict) -> Order:
        """Create a new order."""
        order = Order(**order_data)

        session.add(order)
        await session.commit()
        await session.refresh(order)

        return order

    async def update_order(
        self, session: AsyncSession, order_id: int, update_data: dict
    ) -> Optional[Order]:
        """Update order fields."""
        stmt = (
            update(Order)
            .where(Order.id == order_id)
            .values(**update_data)
            .returning(Order)
        )

        result = await session.execute(stmt)
        await session.commit()

        updated = result.scalar_one_or_none()
        if updated:
            await session.refresh(updated)
        return updated

    async def update_status(
        self,
        session: AsyncSession,
        order_id: int,
        status: str,
        filled_amount: Optional[float] = None,
        average_fill_price: Optional[float] = None,
        transaction_hash: Optional[str] = None,
    ) -> Optional[Order]:
        """Update order status and execution details."""
        update_data: dict = {"status": status}

        if filled_amount is not None:
            update_data["filled_amount"] = filled_amount
        if average_fill_price is not None:
            update_data["average_fill_price"] = average_fill_price
        if transaction_hash is not None:
            update_data["transaction_hash"] = transaction_hash

        return await self.update_order(session, order_id, update_data)
