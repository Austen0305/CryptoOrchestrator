"""
Cold Storage Service
Simulates cold storage for high-value crypto assets (security best practice)
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from enum import Enum

from ..models.wallet import (
    Wallet,
    WalletTransaction,
    TransactionType,
    TransactionStatus,
)

logger = logging.getLogger(__name__)


class ColdStorageStatus(str, Enum):
    """Cold storage status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ColdStorageService:
    """
    Service for managing cold storage transfers

    Cold storage is a security best practice where high-value assets
    are stored offline, disconnected from the internet, to prevent theft.
    """

    # Minimum amount to trigger cold storage recommendation (in USD)
    COLD_STORAGE_THRESHOLD = 10000.0  # $10,000

    # Supported currencies for cold storage
    SUPPORTED_CURRENCIES = ["BTC", "ETH", "USDT", "USDC", "SOL", "ADA"]

    # Processing time for cold storage transfers (hours)
    PROCESSING_TIME_HOURS = 24

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_cold_storage_eligibility(
        self, user_id: int, currency: str, amount: float
    ) -> Dict:
        """
        Check if transfer should go to cold storage

        Returns:
            Dict with recommendation and details
        """
        # Get current market price (simplified - would use real price feed)
        usd_value = await self._estimate_usd_value(currency, amount)

        should_use_cold = usd_value >= self.COLD_STORAGE_THRESHOLD
        is_supported = currency.upper() in self.SUPPORTED_CURRENCIES

        return {
            "eligible": should_use_cold and is_supported,
            "recommended": should_use_cold and is_supported,
            "usd_value": usd_value,
            "threshold": self.COLD_STORAGE_THRESHOLD,
            "currency_supported": is_supported,
            "reason": (
                "High-value transfer eligible for cold storage"
                if should_use_cold
                else f"Transfer value (${usd_value:.2f}) below cold storage threshold"
            ),
        }

    async def initiate_cold_storage_transfer(
        self,
        user_id: int,
        currency: str,
        amount: float,
        description: Optional[str] = None,
    ) -> Dict:
        """
        Initiate a transfer to cold storage

        This simulates the process of moving funds to cold storage:
        1. Create pending transaction
        2. Lock funds in hot wallet
        3. Schedule cold storage transfer
        4. Process after delay (simulating manual/offline process)
        """
        try:
            # Get wallet
            from ..services.wallet_service import WalletService

            wallet_service = WalletService(self.db)
            wallet = await wallet_service.get_or_create_wallet(
                user_id, currency, "trading"
            )

            # Check balance
            if wallet.available_balance < amount:
                raise ValueError(
                    f"Insufficient balance. Available: {wallet.available_balance}"
                )

            # Lock funds
            wallet.available_balance -= amount
            wallet.locked_balance += amount

            # Create cold storage transaction
            transaction = WalletTransaction(
                wallet_id=wallet.id,
                user_id=user_id,
                transaction_type=TransactionType.WITHDRAWAL.value,
                status=TransactionStatus.PENDING.value,
                amount=amount,
                currency=currency,
                fee=0.0,  # Cold storage transfers typically have no fee
                net_amount=amount,
                description=description
                or f"Cold storage transfer: {amount} {currency}",
                metadata={
                    "cold_storage": True,
                    "initiated_at": datetime.utcnow().isoformat(),
                    "estimated_completion": (
                        datetime.utcnow() + timedelta(hours=self.PROCESSING_TIME_HOURS)
                    ).isoformat(),
                    "status": ColdStorageStatus.PENDING.value,
                },
            )

            self.db.add(transaction)
            await self.db.commit()
            await self.db.refresh(transaction)

            logger.info(
                f"Cold storage transfer initiated: user {user_id}, "
                f"{amount} {currency} (transaction {transaction.id})"
            )

            return {
                "transaction_id": transaction.id,
                "status": ColdStorageStatus.PENDING.value,
                "amount": amount,
                "currency": currency,
                "estimated_completion": transaction.metadata["estimated_completion"],
                "processing_time_hours": self.PROCESSING_TIME_HOURS,
                "message": (
                    f"Cold storage transfer initiated. "
                    f"Funds will be moved to cold storage within {self.PROCESSING_TIME_HOURS} hours."
                ),
            }

        except Exception as e:
            logger.error(f"Error initiating cold storage transfer: {e}", exc_info=True)
            await self.db.rollback()
            raise

    async def complete_cold_storage_transfer(self, transaction_id: int) -> bool:
        """
        Complete a cold storage transfer

        This would be called by a background job or admin after
        the manual process of moving funds to cold storage is complete.
        """
        try:
            stmt = select(WalletTransaction).where(
                and_(
                    WalletTransaction.id == transaction_id,
                    WalletTransaction.metadata.has_key("cold_storage"),
                )
            )
            result = await self.db.execute(stmt)
            transaction = result.scalar_one_or_none()

            if not transaction:
                return False

            if transaction.status == TransactionStatus.COMPLETED.value:
                return True  # Already completed

            # Update wallet
            wallet_stmt = select(Wallet).where(Wallet.id == transaction.wallet_id)
            wallet_result = await self.db.execute(wallet_stmt)
            wallet = wallet_result.scalar_one_or_none()

            if wallet:
                # Remove from locked balance (funds now in cold storage)
                wallet.locked_balance -= transaction.amount
                wallet.total_withdrawn += transaction.amount

                # Update transaction
                transaction.status = TransactionStatus.COMPLETED.value
                transaction.processed_at = datetime.utcnow()

                if transaction.metadata:
                    transaction.metadata["status"] = ColdStorageStatus.COMPLETED.value
                    transaction.metadata["completed_at"] = datetime.utcnow().isoformat()

                await self.db.commit()

                logger.info(
                    f"Cold storage transfer completed: transaction {transaction_id}"
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Error completing cold storage transfer: {e}", exc_info=True)
            await self.db.rollback()
            return False

    async def get_cold_storage_balance(
        self, user_id: int, currency: Optional[str] = None
    ) -> Dict:
        """
        Get total balance in cold storage for user
        """
        try:
            conditions = [
                WalletTransaction.user_id == user_id,
                WalletTransaction.metadata.has_key("cold_storage"),
                WalletTransaction.status == TransactionStatus.COMPLETED.value,
            ]

            if currency:
                conditions.append(WalletTransaction.currency == currency)

            stmt = select(WalletTransaction).where(and_(*conditions))
            result = await self.db.execute(stmt)
            transactions = result.scalars().all()

            total_by_currency = {}
            for tx in transactions:
                currency_key = tx.currency
                if currency_key not in total_by_currency:
                    total_by_currency[currency_key] = 0.0
                total_by_currency[currency_key] += tx.amount

            return {
                "user_id": user_id,
                "cold_storage_balances": total_by_currency,
                "total_currencies": len(total_by_currency),
                "total_value_usd": await self._estimate_total_usd_value(
                    total_by_currency
                ),
            }

        except Exception as e:
            logger.error(f"Error getting cold storage balance: {e}", exc_info=True)
            return {
                "user_id": user_id,
                "cold_storage_balances": {},
                "total_currencies": 0,
                "total_value_usd": 0.0,
            }

    async def _estimate_usd_value(self, currency: str, amount: float) -> float:
        """Estimate USD value of crypto amount (simplified)"""
        # In production, would fetch real-time prices
        price_map = {
            "BTC": 45000.0,
            "ETH": 2500.0,
            "USDT": 1.0,
            "USDC": 1.0,
            "SOL": 100.0,
            "ADA": 0.5,
        }
        price = price_map.get(currency.upper(), 1.0)
        return amount * price

    async def _estimate_total_usd_value(self, balances: Dict[str, float]) -> float:
        """Estimate total USD value of multiple currencies"""
        total = 0.0
        for currency, amount in balances.items():
            total += await self._estimate_usd_value(currency, amount)
        return total
