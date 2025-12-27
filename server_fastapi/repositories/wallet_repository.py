"""
Wallet Repository
Data access layer for wallet operations
"""

import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime

from ..models.user_wallet import UserWallet

logger = logging.getLogger(__name__)


class WalletRepository:
    """Repository for wallet database operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_wallet(
        self, user_id: int, chain_id: int, wallet_type: str = "custodial"
    ) -> Optional[UserWallet]:
        """
        Get user's wallet for a specific chain

        Args:
            user_id: User ID
            chain_id: Blockchain ID
            wallet_type: Wallet type ('custodial' or 'external')

        Returns:
            UserWallet instance or None if not found
        """
        try:
            stmt = select(UserWallet).where(
                and_(
                    UserWallet.user_id == user_id,
                    UserWallet.chain_id == chain_id,
                    UserWallet.wallet_type == wallet_type,
                    UserWallet.is_active.is_(True),
                )
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user wallet: {e}", exc_info=True)
            return None

    async def get_user_wallets(
        self, user_id: int, wallet_type: Optional[str] = None
    ) -> List[UserWallet]:
        """
        Get all wallets for a user

        Args:
            user_id: User ID
            wallet_type: Optional wallet type filter

        Returns:
            List of UserWallet instances
        """
        try:
            conditions = [UserWallet.user_id == user_id, UserWallet.is_active.is_(True)]
            if wallet_type:
                conditions.append(UserWallet.wallet_type == wallet_type)

            stmt = select(UserWallet).where(and_(*conditions))
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting user wallets: {e}", exc_info=True)
            return []

    async def create_wallet(
        self,
        user_id: int,
        wallet_address: str,
        chain_id: int,
        wallet_type: str = "custodial",
        label: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[UserWallet]:
        """
        Create a new wallet for a user

        Args:
            user_id: User ID
            wallet_address: Ethereum address (checksummed)
            chain_id: Blockchain ID
            wallet_type: Wallet type ('custodial' or 'external')
            label: Optional user-friendly label
            metadata: Optional metadata dictionary

        Returns:
            Created UserWallet instance or None if error
        """
        try:
            # Check if wallet already exists
            existing = await self.get_user_wallet(user_id, chain_id, wallet_type)
            if existing:
                logger.warning(
                    f"Wallet already exists for user {user_id} on chain {chain_id}",
                    extra={
                        "user_id": user_id,
                        "chain_id": chain_id,
                        "wallet_type": wallet_type,
                    },
                )
                return existing

            wallet = UserWallet(
                user_id=user_id,
                wallet_address=wallet_address,
                chain_id=chain_id,
                wallet_type=wallet_type,
                label=label,
                metadata=metadata,
                is_active=True,
                is_verified=(
                    wallet_type == "custodial"
                ),  # Custodial wallets are auto-verified
                balance=None,
                last_balance_update=None,
            )
            self.db.add(wallet)
            await self.db.commit()
            await self.db.refresh(wallet)

            logger.info(
                f"Created wallet for user {user_id}",
                extra={
                    "user_id": user_id,
                    "wallet_address": wallet_address,
                    "chain_id": chain_id,
                    "wallet_type": wallet_type,
                },
            )

            return wallet
        except Exception as e:
            logger.error(f"Error creating wallet: {e}", exc_info=True)
            await self.db.rollback()
            return None

    async def update_wallet_balance(
        self,
        wallet_id: int,
        balance: dict,
    ) -> Optional[UserWallet]:
        """
        Update wallet balance cache

        Args:
            wallet_id: Wallet ID
            balance: Balance dictionary {token_address: balance_string}

        Returns:
            Updated UserWallet instance or None if error
        """
        try:
            stmt = select(UserWallet).where(UserWallet.id == wallet_id)
            result = await self.db.execute(stmt)
            wallet = result.scalar_one_or_none()

            if not wallet:
                logger.warning(f"Wallet {wallet_id} not found")
                return None

            wallet.balance = balance
            wallet.last_balance_update = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(wallet)

            return wallet
        except Exception as e:
            logger.error(f"Error updating wallet balance: {e}", exc_info=True)
            await self.db.rollback()
            return None

    async def deactivate_wallet(self, wallet_id: int) -> bool:
        """
        Deactivate a wallet

        Args:
            wallet_id: Wallet ID

        Returns:
            True if successful, False otherwise
        """
        try:
            stmt = select(UserWallet).where(UserWallet.id == wallet_id)
            result = await self.db.execute(stmt)
            wallet = result.scalar_one_or_none()

            if not wallet:
                logger.warning(f"Wallet {wallet_id} not found")
                return False

            wallet.is_active = False
            await self.db.commit()

            logger.info(f"Deactivated wallet {wallet_id}")
            return True
        except Exception as e:
            logger.error(f"Error deactivating wallet: {e}", exc_info=True)
            await self.db.rollback()
            return False
