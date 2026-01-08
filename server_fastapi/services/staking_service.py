"""
Staking Service
Handles staking rewards for supported cryptocurrencies.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..repositories.transaction_repository import TransactionRepository
    from ..repositories.wallet_balance_repository import WalletBalanceRepository
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.wallet import TransactionStatus, TransactionType
from ..repositories.transaction_repository import TransactionRepository
from ..repositories.wallet_balance_repository import WalletBalanceRepository

logger = logging.getLogger(__name__)


class StakingService:
    """Service for staking rewards"""

    def __init__(
        self,
        db: AsyncSession,
        wallet_repository: WalletBalanceRepository | None = None,
        transaction_repository: TransactionRepository | None = None,
    ):
        # ✅ Repository injected via dependency injection (Service Layer Pattern)
        self.wallet_repository = wallet_repository or WalletBalanceRepository()
        self.transaction_repository = transaction_repository or TransactionRepository()
        self.db = db  # Keep db for transaction handling

    # Supported staking assets and their APY
    STAKING_ASSETS = {
        "ETH": {"apy": 4.5, "min_amount": 0.1, "lock_period_days": 0},  # Flexible
        "BTC": {"apy": 2.0, "min_amount": 0.001, "lock_period_days": 0},
        "SOL": {"apy": 6.0, "min_amount": 1.0, "lock_period_days": 0},
        "ADA": {"apy": 5.5, "min_amount": 10.0, "lock_period_days": 0},
        "DOT": {"apy": 12.0, "min_amount": 1.0, "lock_period_days": 0},
        "ATOM": {"apy": 18.0, "min_amount": 1.0, "lock_period_days": 0},
    }

    async def get_staking_options(self) -> list[dict]:
        """Get available staking options"""
        return [
            {
                "asset": asset,
                "apy": info["apy"],
                "min_amount": info["min_amount"],
                "lock_period_days": info["lock_period_days"],
                "description": f"Stake {asset} and earn {info['apy']}% APY",
            }
            for asset, info in self.STAKING_ASSETS.items()
        ]

    async def stake_assets(self, user_id: int, asset: str, amount: float) -> dict:
        """
        Stake assets to earn rewards.

        Args:
            user_id: User ID
            asset: Asset to stake (ETH, BTC, etc.)
            amount: Amount to stake

        Returns:
            Dict with staking details
        """
        try:
            if asset not in self.STAKING_ASSETS:
                raise ValueError(f"Staking not supported for {asset}")

            staking_info = self.STAKING_ASSETS[asset]

            if amount < staking_info["min_amount"]:
                raise ValueError(
                    f"Minimum staking amount is {staking_info['min_amount']} {asset}"
                )

            # ✅ Data access delegated to repository
            wallet = await self.wallet_repository.get_or_create_wallet(
                self.db, user_id, asset, "staking"
            )

            # ✅ Data access delegated to repository
            trading_wallet = (
                await self.wallet_repository.get_by_user_and_currency_and_type(
                    self.db, user_id, asset, "trading"
                )
            )

            if not trading_wallet or trading_wallet.available_balance < amount:
                raise ValueError(
                    f"Insufficient balance. Available: {trading_wallet.available_balance if trading_wallet else 0} {asset}"
                )

            # ✅ Business logic: Transfer from trading to staking wallet
            # ✅ Data access delegated to repository
            await self.wallet_repository.update_balance(
                self.db,
                trading_wallet.id,
                available_balance=trading_wallet.available_balance - amount,
            )

            await self.wallet_repository.update_balance(
                self.db,
                wallet.id,
                balance=wallet.balance + amount,
                available_balance=wallet.available_balance + amount,
            )

            # ✅ Business logic: Create transaction
            # ✅ Data access delegated to repository
            transaction = await self.transaction_repository.create_transaction(
                self.db,
                {
                    "wallet_id": wallet.id,
                    "user_id": user_id,
                    "transaction_type": TransactionType.TRANSFER.value,
                    "status": TransactionStatus.COMPLETED.value,
                    "amount": amount,
                    "currency": asset,
                    "fee": 0.0,
                    "net_amount": amount,
                    "description": f"Staked {amount} {asset}",
                    "processed_at": datetime.utcnow(),
                },
            )

            logger.info(
                f"User {user_id} staked {amount} {asset}",
                extra={"user_id": user_id, "asset": asset, "amount": amount},
            )

            return {
                "staking_id": transaction.id,
                "asset": asset,
                "amount": amount,
                "apy": staking_info["apy"],
                "estimated_rewards_per_year": amount * (staking_info["apy"] / 100),
                "wallet_id": wallet.id,
            }

        except ValueError:
            raise
        except Exception as e:
            logger.error(
                f"Error staking assets: {e}",
                exc_info=True,
                extra={"user_id": user_id, "asset": asset, "amount": amount},
            )
            await self.db.rollback()
            raise

    async def unstake_assets(self, user_id: int, asset: str, amount: float) -> dict:
        """Unstake assets"""
        try:
            # ✅ Data access delegated to repository
            wallet = await self.wallet_repository.get_by_user_and_currency_and_type(
                self.db, user_id, asset, "staking"
            )

            if not wallet or wallet.available_balance < amount:
                raise ValueError(
                    f"Insufficient staked balance. Available: {wallet.available_balance if wallet else 0} {asset}"
                )

            # ✅ Data access delegated to repository
            trading_wallet = await self.wallet_repository.get_or_create_wallet(
                self.db, user_id, asset, "trading"
            )

            # ✅ Business logic: Transfer back
            # ✅ Data access delegated to repository
            await self.wallet_repository.update_balance(
                self.db,
                wallet.id,
                balance=wallet.balance - amount,
                available_balance=wallet.available_balance - amount,
            )

            await self.wallet_repository.update_balance(
                self.db,
                trading_wallet.id,
                balance=trading_wallet.balance + amount,
                available_balance=trading_wallet.available_balance + amount,
            )

            # ✅ Business logic: Create transaction
            # ✅ Data access delegated to repository
            transaction = await self.transaction_repository.create_transaction(
                self.db,
                {
                    "wallet_id": wallet.id,
                    "user_id": user_id,
                    "transaction_type": TransactionType.TRANSFER.value,
                    "status": TransactionStatus.COMPLETED.value,
                    "amount": amount,
                    "currency": asset,
                    "fee": 0.0,
                    "net_amount": amount,
                    "description": f"Unstaked {amount} {asset}",
                    "processed_at": datetime.utcnow(),
                },
            )

            logger.info(
                f"User {user_id} unstaked {amount} {asset}",
                extra={"user_id": user_id, "asset": asset, "amount": amount},
            )

            return {
                "transaction_id": transaction.id,
                "asset": asset,
                "amount": amount,
                "status": "completed",
            }

        except ValueError:
            raise
        except Exception as e:
            logger.error(
                f"Error unstaking assets: {e}",
                exc_info=True,
                extra={"user_id": user_id, "asset": asset, "amount": amount},
            )
            await self.db.rollback()
            raise

    async def calculate_staking_rewards(self, user_id: int, asset: str) -> dict:
        """Calculate staking rewards for a user"""
        try:
            # ✅ Data access delegated to repository
            wallet = await self.wallet_repository.get_by_user_and_currency_and_type(
                self.db, user_id, asset, "staking"
            )

            if not wallet or wallet.balance == 0:
                return {
                    "asset": asset,
                    "staked_amount": 0.0,
                    "apy": 0.0,
                    "daily_rewards": 0.0,
                    "monthly_rewards": 0.0,
                    "yearly_rewards": 0.0,
                }

            # ✅ Business logic: Calculate rewards
            staking_info = self.STAKING_ASSETS.get(asset, {"apy": 0.0})
            apy = staking_info["apy"]

            yearly_rewards = wallet.balance * (apy / 100)
            monthly_rewards = yearly_rewards / 12
            daily_rewards = yearly_rewards / 365

            return {
                "asset": asset,
                "staked_amount": wallet.balance,
                "apy": apy,
                "daily_rewards": round(daily_rewards, 6),
                "monthly_rewards": round(monthly_rewards, 6),
                "yearly_rewards": round(yearly_rewards, 6),
            }

        except Exception as e:
            logger.error(
                f"Error calculating staking rewards: {e}",
                exc_info=True,
                extra={"user_id": user_id, "asset": asset},
            )
            return {
                "asset": asset,
                "staked_amount": 0.0,
                "apy": 0.0,
                "daily_rewards": 0.0,
                "monthly_rewards": 0.0,
                "yearly_rewards": 0.0,
            }

    async def distribute_staking_rewards(self):
        """Distribute daily staking rewards (called by scheduled task)"""
        try:
            # ✅ Data access delegated to repository
            wallets = await self.wallet_repository.get_by_type(self.db, "staking")

            distributed = 0
            for wallet in wallets:
                if wallet.balance > 0:
                    staking_info = self.STAKING_ASSETS.get(
                        wallet.currency, {"apy": 0.0}
                    )
                    if staking_info["apy"] > 0:
                        # ✅ Business logic: Calculate daily reward
                        daily_reward = (
                            wallet.balance * (staking_info["apy"] / 100) / 365
                        )

                        # ✅ Data access delegated to repository
                        await self.wallet_repository.update_balance(
                            self.db,
                            wallet.id,
                            balance=wallet.balance + daily_reward,
                            available_balance=wallet.available_balance + daily_reward,
                        )

                        # ✅ Business logic: Create transaction
                        # ✅ Data access delegated to repository
                        await self.transaction_repository.create_transaction(
                            self.db,
                            {
                                "wallet_id": wallet.id,
                                "user_id": wallet.user_id,
                                "transaction_type": TransactionType.STAKING_REWARD.value,
                                "status": TransactionStatus.COMPLETED.value,
                                "amount": daily_reward,
                                "currency": wallet.currency,
                                "fee": 0.0,
                                "net_amount": daily_reward,
                                "description": f"Daily staking reward for {wallet.currency}",
                                "processed_at": datetime.utcnow(),
                            },
                        )
                        distributed += 1

            logger.info(
                f"Distributed staking rewards to {distributed} wallets",
                extra={"distributed_count": distributed},
            )

        except Exception as e:
            logger.error(f"Error distributing staking rewards: {e}", exc_info=True)
            await self.db.rollback()

    async def _get_or_create_staking_wallet(
        self, user_id: int, currency: str, wallet_type: str = "staking"
    ):
        """Get or create a staking wallet (delegates to repository)"""
        # ✅ Data access delegated to repository
        return await self.wallet_repository.get_or_create_wallet(
            self.db, user_id, currency, wallet_type
        )
