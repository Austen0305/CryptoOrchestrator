"""
Wallet Trading Integration Service
Integrates wallet system with trading operations
"""

import logging
from typing import Dict, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..models.wallet import (
    Wallet,
    WalletTransaction,
    TransactionType,
    TransactionStatus,
)
from ..models.trade import Trade

logger = logging.getLogger(__name__)


class WalletTradingIntegration:
    """Service for integrating wallet with trading operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def reserve_funds_for_trade(
        self, user_id: int, amount: float, currency: str = "USD"
    ) -> bool:
        """
        Reserve funds in wallet for a pending trade.
        Moves funds from available_balance to locked_balance.

        Returns:
            True if funds were successfully reserved, False if insufficient balance
        """
        try:
            from ..services.wallet_service import WalletService

            service = WalletService(self.db)

            wallet = await service.get_or_create_wallet(user_id, currency, "trading")

            if wallet.available_balance < amount:
                logger.warning(
                    f"Insufficient balance for trade: user {user_id}, required {amount}, available {wallet.available_balance}"
                )
                return False

            # Lock the funds
            wallet.available_balance -= amount
            wallet.locked_balance += amount

            await self.db.commit()
            logger.info(f"Reserved {amount} {currency} for trade: user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error reserving funds for trade: {e}", exc_info=True)
            await self.db.rollback()
            return False

    async def release_funds_from_trade(
        self, user_id: int, amount: float, currency: str = "USD"
    ) -> bool:
        """
        Release funds that were reserved for a trade (if trade was cancelled).
        Moves funds from locked_balance back to available_balance.
        """
        try:
            from ..services.wallet_service import WalletService

            service = WalletService(self.db)

            wallet = await service.get_or_create_wallet(user_id, currency, "trading")

            if wallet.locked_balance < amount:
                logger.warning(
                    f"Insufficient locked balance: user {user_id}, required {amount}, locked {wallet.locked_balance}"
                )
                return False

            # Release the funds
            wallet.locked_balance -= amount
            wallet.available_balance += amount

            await self.db.commit()
            logger.info(f"Released {amount} {currency} from trade: user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error releasing funds from trade: {e}", exc_info=True)
            await self.db.rollback()
            return False

    async def process_trade_execution(
        self,
        user_id: int,
        trade: Trade,
        trade_amount: float,
        fee: float,
        currency: str = "USD",
    ) -> bool:
        """
        Process wallet updates after a trade is executed.
        Deducts funds from locked balance and records transaction.
        """
        try:
            from ..services.wallet_service import WalletService

            service = WalletService(self.db)

            wallet = await service.get_or_create_wallet(user_id, currency, "trading")

            total_cost = trade_amount + fee

            # Check if we have enough locked balance
            if wallet.locked_balance < total_cost:
                logger.error(
                    f"Insufficient locked balance for trade execution: user {user_id}"
                )
                return False

            # Deduct from locked balance
            wallet.locked_balance -= total_cost
            wallet.balance -= total_cost
            wallet.total_traded += trade_amount

            # Create transaction record
            transaction = WalletTransaction(
                wallet_id=wallet.id,
                user_id=user_id,
                transaction_type=TransactionType.TRADE.value,
                status=TransactionStatus.COMPLETED.value,
                amount=trade_amount,
                currency=currency,
                fee=fee,
                net_amount=trade_amount,
                trade_id=trade.id,
                description=f"Trade execution: {trade.pair} {trade.side}",
                processed_at=datetime.utcnow(),
            )
            self.db.add(transaction)

            await self.db.commit()
            logger.info(
                f"Processed trade execution in wallet: user {user_id}, trade {trade.id}"
            )
            return True

        except Exception as e:
            logger.error(f"Error processing trade execution: {e}", exc_info=True)
            await self.db.rollback()
            return False

    async def process_trade_profit(
        self, user_id: int, trade: Trade, profit: float, currency: str = "USD"
    ) -> bool:
        """
        Add profit from a completed trade to wallet.
        """
        try:
            from ..services.wallet_service import WalletService
            from datetime import datetime

            service = WalletService(self.db)

            wallet = await service.get_or_create_wallet(user_id, currency, "trading")

            # Add profit to wallet
            wallet.balance += profit
            wallet.available_balance += profit

            # Create transaction record
            transaction = WalletTransaction(
                wallet_id=wallet.id,
                user_id=user_id,
                transaction_type=TransactionType.REWARD.value,
                status=TransactionStatus.COMPLETED.value,
                amount=profit,
                currency=currency,
                fee=0.0,
                net_amount=profit,
                trade_id=trade.id,
                description=f"Trade profit: {trade.pair}",
                processed_at=datetime.utcnow(),
            )
            self.db.add(transaction)

            await self.db.commit()
            logger.info(
                f"Added trade profit to wallet: user {user_id}, profit {profit} {currency}"
            )
            return True

        except Exception as e:
            logger.error(f"Error processing trade profit: {e}", exc_info=True)
            await self.db.rollback()
            return False
