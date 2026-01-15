"""
Transaction Repository
Data access layer for WalletTransaction model operations.
"""

import logging
from datetime import UTC, datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models.wallet import WalletTransaction
from .base import SQLAlchemyRepository

logger = logging.getLogger(__name__)


class TransactionRepository(SQLAlchemyRepository[WalletTransaction]):
    """Repository for WalletTransaction model operations."""

    def __init__(self):
        super().__init__(WalletTransaction)

    async def get_by_id(
        self, session: AsyncSession, id: int, load_options: list | None = None
    ) -> WalletTransaction | None:
        """Get transaction by ID with eager loading."""
        if load_options is None:
            load_options = [
                joinedload(WalletTransaction.wallet),
            ]
        # WalletTransaction model doesn't have is_deleted, so override base method
        query = select(WalletTransaction).where(WalletTransaction.id == id)
        if load_options:
            for option in load_options:
                query = query.options(option)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        session: AsyncSession,
        user_id: int,
        transaction_type: str | None = None,
        currency: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[WalletTransaction]:
        """Get all transactions for a user with eager loading."""
        conditions = [WalletTransaction.user_id == user_id]

        if transaction_type:
            conditions.append(WalletTransaction.transaction_type == transaction_type)

        if currency:
            conditions.append(WalletTransaction.currency == currency)

        query = (
            select(WalletTransaction)
            .where(and_(*conditions))
            .order_by(WalletTransaction.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(WalletTransaction.wallet),
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_count_by_user(
        self,
        session: AsyncSession,
        user_id: int,
        transaction_type: str | None = None,
        currency: str | None = None,
    ) -> int:
        """Get total count of transactions for a user."""
        from sqlalchemy import func

        conditions = [WalletTransaction.user_id == user_id]

        if transaction_type:
            conditions.append(WalletTransaction.transaction_type == transaction_type)

        if currency:
            conditions.append(WalletTransaction.currency == currency)

        query = (
            select(func.count()).select_from(WalletTransaction).where(and_(*conditions))
        )
        result = await session.execute(query)
        return result.scalar_one() or 0

    async def get_by_wallet(
        self,
        session: AsyncSession,
        wallet_id: int,
        transaction_type: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[WalletTransaction]:
        """Get all transactions for a wallet with eager loading."""
        conditions = [WalletTransaction.wallet_id == wallet_id]

        if transaction_type:
            conditions.append(WalletTransaction.transaction_type == transaction_type)

        query = (
            select(WalletTransaction)
            .where(and_(*conditions))
            .order_by(WalletTransaction.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(WalletTransaction.wallet),
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_status(
        self, session: AsyncSession, status: str, skip: int = 0, limit: int = 100
    ) -> list[WalletTransaction]:
        """Get transactions by status with eager loading."""
        query = (
            select(WalletTransaction)
            .where(WalletTransaction.status == status)
            .order_by(WalletTransaction.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(WalletTransaction.wallet),
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_reference_id(
        self, session: AsyncSession, reference_id: str
    ) -> WalletTransaction | None:
        """Get transaction by reference ID with eager loading."""
        query = select(WalletTransaction).where(
            WalletTransaction.reference_id == reference_id
        )

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(WalletTransaction.wallet),
        )

        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def create_transaction(
        self, session: AsyncSession, transaction_data: dict
    ) -> WalletTransaction:
        """Create a new transaction record."""
        transaction = WalletTransaction(**transaction_data)

        session.add(transaction)
        await session.commit()
        await session.refresh(transaction)

        return transaction

    async def update_status(
        self,
        session: AsyncSession,
        transaction_id: int,
        status: str,
        processed_at: datetime | None = None,
    ) -> WalletTransaction | None:
        """Update transaction status."""
        from sqlalchemy import update

        update_data = {"status": status}
        if processed_at:
            update_data["processed_at"] = processed_at
        elif status in ["completed", "failed"]:
            update_data["processed_at"] = datetime.now(UTC)

        stmt = (
            update(WalletTransaction)
            .where(WalletTransaction.id == transaction_id)
            .values(**update_data)
            .returning(WalletTransaction)
        )

        result = await session.execute(stmt)
        await session.commit()

        updated = result.scalar_one_or_none()
        if updated:
            await session.refresh(updated)
        return updated
