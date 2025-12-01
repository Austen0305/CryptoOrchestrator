"""
Staking Service
Handles staking rewards for supported cryptocurrencies.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from ..models.wallet import Wallet, WalletTransaction, TransactionType, TransactionStatus
from ..models.user import User

logger = logging.getLogger(__name__)


class StakingService:
    """Service for staking rewards"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # Supported staking assets and their APY
    STAKING_ASSETS = {
        "ETH": {"apy": 4.5, "min_amount": 0.1, "lock_period_days": 0},  # Flexible
        "BTC": {"apy": 2.0, "min_amount": 0.001, "lock_period_days": 0},
        "SOL": {"apy": 6.0, "min_amount": 1.0, "lock_period_days": 0},
        "ADA": {"apy": 5.5, "min_amount": 10.0, "lock_period_days": 0},
        "DOT": {"apy": 12.0, "min_amount": 1.0, "lock_period_days": 0},
        "ATOM": {"apy": 18.0, "min_amount": 1.0, "lock_period_days": 0},
    }
    
    async def get_staking_options(self) -> List[Dict]:
        """Get available staking options"""
        return [
            {
                "asset": asset,
                "apy": info["apy"],
                "min_amount": info["min_amount"],
                "lock_period_days": info["lock_period_days"],
                "description": f"Stake {asset} and earn {info['apy']}% APY"
            }
            for asset, info in self.STAKING_ASSETS.items()
        ]
    
    async def stake_assets(
        self,
        user_id: int,
        asset: str,
        amount: float
    ) -> Dict:
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
                raise ValueError(f"Minimum staking amount is {staking_info['min_amount']} {asset}")
            
            # Get or create staking wallet
            wallet = await self._get_or_create_staking_wallet(user_id, asset)
            
            # Check available balance
            trading_wallet_stmt = select(Wallet).where(
                and_(
                    Wallet.user_id == user_id,
                    Wallet.currency == asset,
                    Wallet.wallet_type == "trading"
                )
            )
            trading_wallet_result = await self.db.execute(trading_wallet_stmt)
            trading_wallet = trading_wallet_result.scalar_one_or_none()
            
            if not trading_wallet or trading_wallet.available_balance < amount:
                raise ValueError(f"Insufficient balance. Available: {trading_wallet.available_balance if trading_wallet else 0} {asset}")
            
            # Transfer from trading to staking wallet
            trading_wallet.available_balance -= amount
            wallet.balance += amount
            wallet.available_balance += amount
            
            # Create transaction
            transaction = WalletTransaction(
                wallet_id=wallet.id,
                user_id=user_id,
                transaction_type=TransactionType.TRANSFER.value,
                status=TransactionStatus.COMPLETED.value,
                amount=amount,
                currency=asset,
                fee=0.0,
                net_amount=amount,
                description=f"Staked {amount} {asset}",
                processed_at=datetime.utcnow()
            )
            self.db.add(transaction)
            
            await self.db.commit()
            await self.db.refresh(wallet)
            await self.db.refresh(transaction)
            
            logger.info(f"User {user_id} staked {amount} {asset}")
            
            return {
                "staking_id": transaction.id,
                "asset": asset,
                "amount": amount,
                "apy": staking_info["apy"],
                "estimated_rewards_per_year": amount * (staking_info["apy"] / 100),
                "wallet_id": wallet.id
            }
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error staking assets: {e}", exc_info=True)
            await self.db.rollback()
            raise
    
    async def unstake_assets(
        self,
        user_id: int,
        asset: str,
        amount: float
    ) -> Dict:
        """Unstake assets"""
        try:
            # Get staking wallet
            wallet_stmt = select(Wallet).where(
                and_(
                    Wallet.user_id == user_id,
                    Wallet.currency == asset,
                    Wallet.wallet_type == "staking"
                )
            )
            wallet_result = await self.db.execute(wallet_stmt)
            wallet = wallet_result.scalar_one_or_none()
            
            if not wallet or wallet.available_balance < amount:
                raise ValueError(f"Insufficient staked balance. Available: {wallet.available_balance if wallet else 0} {asset}")
            
            # Get trading wallet
            trading_wallet = await self._get_or_create_staking_wallet(user_id, asset, "trading")
            
            # Transfer back
            wallet.available_balance -= amount
            wallet.balance -= amount
            trading_wallet.available_balance += amount
            trading_wallet.balance += amount
            
            # Create transaction
            transaction = WalletTransaction(
                wallet_id=wallet.id,
                user_id=user_id,
                transaction_type=TransactionType.TRANSFER.value,
                status=TransactionStatus.COMPLETED.value,
                amount=amount,
                currency=asset,
                fee=0.0,
                net_amount=amount,
                description=f"Unstaked {amount} {asset}",
                processed_at=datetime.utcnow()
            )
            self.db.add(transaction)
            
            await self.db.commit()
            
            logger.info(f"User {user_id} unstaked {amount} {asset}")
            
            return {
                "transaction_id": transaction.id,
                "asset": asset,
                "amount": amount,
                "status": "completed"
            }
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error unstaking assets: {e}", exc_info=True)
            await self.db.rollback()
            raise
    
    async def calculate_staking_rewards(
        self,
        user_id: int,
        asset: str
    ) -> Dict:
        """Calculate staking rewards for a user"""
        try:
            wallet_stmt = select(Wallet).where(
                and_(
                    Wallet.user_id == user_id,
                    Wallet.currency == asset,
                    Wallet.wallet_type == "staking"
                )
            )
            wallet_result = await self.db.execute(wallet_stmt)
            wallet = wallet_result.scalar_one_or_none()
            
            if not wallet or wallet.balance == 0:
                return {
                    "asset": asset,
                    "staked_amount": 0.0,
                    "apy": 0.0,
                    "daily_rewards": 0.0,
                    "monthly_rewards": 0.0,
                    "yearly_rewards": 0.0
                }
            
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
                "yearly_rewards": round(yearly_rewards, 6)
            }
            
        except Exception as e:
            logger.error(f"Error calculating staking rewards: {e}", exc_info=True)
            return {
                "asset": asset,
                "staked_amount": 0.0,
                "apy": 0.0,
                "daily_rewards": 0.0,
                "monthly_rewards": 0.0,
                "yearly_rewards": 0.0
            }
    
    async def distribute_staking_rewards(self):
        """Distribute daily staking rewards (called by scheduled task)"""
        try:
            # Get all staking wallets
            wallets_stmt = select(Wallet).where(Wallet.wallet_type == "staking")
            wallets_result = await self.db.execute(wallets_stmt)
            wallets = wallets_result.scalars().all()
            
            distributed = 0
            for wallet in wallets:
                if wallet.balance > 0:
                    staking_info = self.STAKING_ASSETS.get(wallet.currency, {"apy": 0.0})
                    if staking_info["apy"] > 0:
                        # Calculate daily reward
                        daily_reward = wallet.balance * (staking_info["apy"] / 100) / 365
                        
                        # Add to wallet
                        wallet.balance += daily_reward
                        wallet.available_balance += daily_reward
                        
                        # Create transaction
                        transaction = WalletTransaction(
                            wallet_id=wallet.id,
                            user_id=wallet.user_id,
                            transaction_type=TransactionType.STAKING_REWARD.value,
                            status=TransactionStatus.COMPLETED.value,
                            amount=daily_reward,
                            currency=wallet.currency,
                            fee=0.0,
                            net_amount=daily_reward,
                            description=f"Daily staking reward for {wallet.currency}",
                            processed_at=datetime.utcnow()
                        )
                        self.db.add(transaction)
                        distributed += 1
            
            await self.db.commit()
            logger.info(f"Distributed staking rewards to {distributed} wallets")
            
        except Exception as e:
            logger.error(f"Error distributing staking rewards: {e}", exc_info=True)
            await self.db.rollback()
    
    async def _get_or_create_staking_wallet(
        self,
        user_id: int,
        currency: str,
        wallet_type: str = "staking"
    ) -> Wallet:
        """Get or create a staking wallet"""
        stmt = select(Wallet).where(
            and_(
                Wallet.user_id == user_id,
                Wallet.currency == currency,
                Wallet.wallet_type == wallet_type
            )
        )
        result = await self.db.execute(stmt)
        wallet = result.scalar_one_or_none()
        
        if not wallet:
            wallet = Wallet(
                user_id=user_id,
                currency=currency,
                wallet_type=wallet_type,
                balance=0.0,
                available_balance=0.0,
                locked_balance=0.0
            )
            self.db.add(wallet)
            await self.db.commit()
            await self.db.refresh(wallet)
        
        return wallet

