"""
Wallet Balance Repository
Data access layer for Wallet model operations (internal trading/staking wallets).
Note: This is different from WalletRepository which handles UserWallet (blockchain wallets).
"""

import logging

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models.wallet import Wallet
from .base import SQLAlchemyRepository

logger = logging.getLogger(__name__)


class WalletBalanceRepository(SQLAlchemyRepository[Wallet]):
    """Repository for Wallet model operations (internal trading/staking wallets)."""

    def __init__(self) -> None:
        super().__init__(Wallet)

    async def get_by_id(
        self, session: AsyncSession, id: int, load_options: list | None = None
    ) -> Wallet | None:
        """Get wallet by ID with eager loading."""
        if load_options is None:
            load_options = [
                joinedload(Wallet.user),
                joinedload(Wallet.transactions),
            ]
        # Wallet model doesn't have is_deleted, so override base method
        query = select(Wallet).where(Wallet.id == id)
        if load_options:
            for option in load_options:
                query = query.options(option)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user_and_currency_and_type(
        self, session: AsyncSession, user_id: int, currency: str, wallet_type: str
    ) -> Wallet | None:
        """Get wallet by user, currency, and type with eager loading."""
        query = select(Wallet).where(
            and_(
                Wallet.user_id == user_id,
                Wallet.currency == currency,
                Wallet.wallet_type == wallet_type,
                Wallet.is_active.is_(True),
            )
        )

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(Wallet.user),
        )

        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        session: AsyncSession,
        user_id: int,
        wallet_type: str | None = None,
        currency: str | None = None,
    ) -> list[Wallet]:
        """Get all wallets for a user with eager loading."""
        conditions = [
            Wallet.user_id == user_id,
            Wallet.is_active.is_(True),
        ]

        if wallet_type:
            conditions.append(Wallet.wallet_type == wallet_type)
        if currency:
            conditions.append(Wallet.currency == currency)

        query = select(Wallet).where(and_(*conditions))

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(Wallet.user),
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_type(
        self, session: AsyncSession, wallet_type: str, currency: str | None = None
    ) -> list[Wallet]:
        """Get all wallets by type with eager loading."""
        conditions = [
            Wallet.wallet_type == wallet_type,
            Wallet.is_active.is_(True),
        ]

        if currency:
            conditions.append(Wallet.currency == currency)

        query = select(Wallet).where(and_(*conditions))

        # Eager load relationships to prevent N+1 queries
        query = query.options(
            joinedload(Wallet.user),
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def create_wallet(
        self,
        session: AsyncSession,
        user_id: int,
        currency: str,
        wallet_type: str,
        balance: float = 0.0,
        available_balance: float = 0.0,
        locked_balance: float = 0.0,
    ) -> Wallet:
        """Create a new wallet."""
        wallet = Wallet(
            user_id=user_id,
            currency=currency,
            wallet_type=wallet_type,
            balance=balance,
            available_balance=available_balance,
            locked_balance=locked_balance,
            is_active=True,
        )

        session.add(wallet)
        await session.commit()
        await session.refresh(wallet)

        return wallet

    async def update_balance(
        self,
        session: AsyncSession,
        wallet_id: int,
        balance: float | None = None,
        available_balance: float | None = None,
        locked_balance: float | None = None,
        total_deposited: float | None = None,
        total_withdrawn: float | None = None,
        total_traded: float | None = None,
    ) -> Wallet | None:
        """Update wallet balance and statistics."""
        update_data = {}
        if balance is not None:
            update_data["balance"] = balance
        if available_balance is not None:
            update_data["available_balance"] = available_balance
        if locked_balance is not None:
            update_data["locked_balance"] = locked_balance
        if total_deposited is not None:
            update_data["total_deposited"] = total_deposited
        if total_withdrawn is not None:
            update_data["total_withdrawn"] = total_withdrawn
        if total_traded is not None:
            update_data["total_traded"] = total_traded

        if not update_data:
            return None

        stmt = (
            update(Wallet)
            .where(Wallet.id == wallet_id)
            .values(**update_data)
            .returning(Wallet)
        )

        result = await session.execute(stmt)
        await session.commit()

        updated = result.scalar_one_or_none()
        if updated:
            await session.refresh(updated)
        return updated

    async def get_or_create_wallet(
        self, session: AsyncSession, user_id: int, currency: str, wallet_type: str
    ) -> Wallet:
        """Get existing wallet or create new one."""
        wallet = await self.get_by_user_and_currency_and_type(
            session, user_id, currency, wallet_type
        )

        if wallet:
            return wallet

        return await self.create_wallet(session, user_id, currency, wallet_type)
