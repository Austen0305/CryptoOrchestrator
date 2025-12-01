"""
Crypto Transfer Service
Handles crypto transfers from external platforms and wallets
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..models.wallet import Wallet, WalletTransaction, TransactionType, TransactionStatus
from ..services.exchange_service import ExchangeService

logger = logging.getLogger(__name__)


class CryptoTransferService:
    """Service for transferring crypto from external platforms"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.exchange_service = ExchangeService()
    
    async def initiate_crypto_transfer(
        self,
        user_id: int,
        currency: str,
        amount: float,
        source_platform: str,  # 'binance', 'coinbase', 'kraken', 'external_wallet', etc.
        source_address: Optional[str] = None,  # For external wallets
        destination_address: Optional[str] = None,  # Our platform address
        network: Optional[str] = None,  # 'ERC20', 'TRC20', 'BEP20', etc.
        memo: Optional[str] = None
    ) -> Dict:
        """
        Initiate a crypto transfer from an external platform
        
        Returns:
            Dict with transfer details and instructions
        """
        try:
            # Get or create wallet
            from ..services.wallet_service import WalletService
            wallet_service = WalletService(self.db)
            wallet = await wallet_service.get_or_create_wallet(user_id, currency, "trading")
            
            # Generate deposit address if not provided
            if not destination_address:
                destination_address = await self._generate_deposit_address(currency, network)
            
            # Create pending transaction
            transaction = WalletTransaction(
                wallet_id=wallet.id,
                user_id=user_id,
                transaction_type=TransactionType.DEPOSIT.value,
                status=TransactionStatus.PENDING.value,
                amount=amount,
                currency=currency,
                fee=0.0,
                net_amount=amount,
                description=f"Crypto transfer from {source_platform}",
                reference_id=f"{source_platform}_{datetime.utcnow().timestamp()}",
                metadata={
                    "source_platform": source_platform,
                    "source_address": source_address,
                    "destination_address": destination_address,
                    "network": network,
                    "memo": memo
                }
            )
            self.db.add(transaction)
            await self.db.commit()
            await self.db.refresh(transaction)
            
            # Get transfer instructions based on source platform
            instructions = await self._get_transfer_instructions(
                source_platform,
                currency,
                destination_address,
                network,
                memo
            )
            
            logger.info(f"Crypto transfer initiated: user {user_id}, {amount} {currency} from {source_platform}")
            
            return {
                "transaction_id": transaction.id,
                "status": "pending",
                "amount": amount,
                "currency": currency,
                "destination_address": destination_address,
                "network": network,
                "instructions": instructions,
                "estimated_confirmation_time": self._get_estimated_confirmation_time(currency, network)
            }
            
        except Exception as e:
            logger.error(f"Error initiating crypto transfer: {e}", exc_info=True)
            await self.db.rollback()
            raise
    
    async def confirm_crypto_transfer(
        self,
        transaction_id: int,
        tx_hash: str,
        confirmations: int = 0
    ) -> bool:
        """
        Confirm a crypto transfer after blockchain confirmation
        
        Args:
            transaction_id: Transaction ID
            tx_hash: Blockchain transaction hash
            confirmations: Number of confirmations
            
        Returns:
            True if confirmed successfully
        """
        try:
            stmt = select(WalletTransaction).where(WalletTransaction.id == transaction_id)
            result = await self.db.execute(stmt)
            transaction = result.scalar_one_or_none()
            
            if not transaction:
                return False
            
            if transaction.status == TransactionStatus.COMPLETED.value:
                return True  # Already confirmed
            
            # Check if we have enough confirmations
            required_confirmations = self._get_required_confirmations(
                transaction.currency,
                transaction.metadata.get("network") if transaction.metadata else None
            )
            
            if confirmations < required_confirmations:
                # Update transaction with tx_hash but keep as pending
                if transaction.metadata:
                    transaction.metadata["tx_hash"] = tx_hash
                    transaction.metadata["confirmations"] = confirmations
                else:
                    transaction.metadata = {
                        "tx_hash": tx_hash,
                        "confirmations": confirmations
                    }
                await self.db.commit()
                return False  # Not enough confirmations yet
            
            # Verify transaction on blockchain
            verified = await self._verify_blockchain_transaction(
                tx_hash,
                transaction.currency,
                transaction.metadata.get("network") if transaction.metadata else None,
                transaction.destination_address if hasattr(transaction, 'destination_address') else None,
                transaction.amount
            )
            
            if not verified:
                logger.warning(f"Blockchain verification failed for transaction {transaction_id}")
                transaction.status = TransactionStatus.FAILED.value
                await self.db.commit()
                return False
            
            # Update wallet balance
            wallet_stmt = select(Wallet).where(Wallet.id == transaction.wallet_id)
            wallet_result = await self.db.execute(wallet_stmt)
            wallet = wallet_result.scalar_one_or_none()
            
            if wallet:
                wallet.balance += transaction.net_amount
                wallet.available_balance += transaction.net_amount
                wallet.total_deposited += transaction.net_amount
                
                transaction.status = TransactionStatus.COMPLETED.value
                transaction.processed_at = datetime.utcnow()
                if transaction.metadata:
                    transaction.metadata["tx_hash"] = tx_hash
                    transaction.metadata["confirmations"] = confirmations
                    transaction.metadata["verified_at"] = datetime.utcnow().isoformat()
                
                await self.db.commit()
                
                # Broadcast wallet update
                try:
                    from ..services.wallet_broadcast import broadcast_wallet_update
                    from ..services.wallet_service import WalletService
                    wallet_service = WalletService(self.db)
                    balance = await wallet_service.get_wallet_balance(wallet.user_id, wallet.currency)
                    await broadcast_wallet_update(wallet.user_id, balance)
                except Exception as e:
                    logger.warning(f"Failed to broadcast wallet update: {e}")
                
                logger.info(f"Crypto transfer confirmed: transaction {transaction_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error confirming crypto transfer: {e}", exc_info=True)
            await self.db.rollback()
            return False
    
    async def withdraw_crypto(
        self,
        user_id: int,
        currency: str,
        amount: float,
        destination_address: str,
        network: Optional[str] = None,
        memo: Optional[str] = None
    ) -> Dict:
        """
        Withdraw crypto to an external address
        
        Returns:
            Dict with withdrawal details
        """
        try:
            from ..services.wallet_service import WalletService
            wallet_service = WalletService(self.db)
            
            wallet = await wallet_service.get_or_create_wallet(user_id, currency, "trading")
            
            # Check balance
            if wallet.available_balance < amount:
                raise ValueError(f"Insufficient balance. Available: {wallet.available_balance}, Required: {amount}")
            
            # Calculate fee
            fee = await self._calculate_withdrawal_fee(currency, network)
            total_deduction = amount + fee
            
            if wallet.available_balance < total_deduction:
                raise ValueError(f"Insufficient balance for withdrawal and fees")
            
            # Validate destination address
            is_valid = await self._validate_crypto_address(destination_address, currency, network)
            if not is_valid:
                raise ValueError(f"Invalid destination address for {currency}")
            
            # Lock funds
            wallet.available_balance -= total_deduction
            wallet.locked_balance += total_deduction
            
            # Create withdrawal transaction
            transaction = WalletTransaction(
                wallet_id=wallet.id,
                user_id=user_id,
                transaction_type=TransactionType.WITHDRAWAL.value,
                status=TransactionStatus.PENDING.value,
                amount=amount,
                currency=currency,
                fee=fee,
                net_amount=amount,
                description=f"Withdrawal to {destination_address[:10]}...",
                reference_id=f"withdraw_{datetime.utcnow().timestamp()}",
                metadata={
                    "destination_address": destination_address,
                    "network": network,
                    "memo": memo
                }
            )
            self.db.add(transaction)
            await self.db.commit()
            await self.db.refresh(transaction)
            
            # Execute withdrawal (would integrate with exchange API or blockchain)
            # For now, mark as processing
            transaction.status = TransactionStatus.PROCESSING.value
            await self.db.commit()
            
            logger.info(f"Crypto withdrawal initiated: user {user_id}, {amount} {currency} to {destination_address[:10]}...")
            
            return {
                "transaction_id": transaction.id,
                "status": "processing",
                "amount": amount,
                "currency": currency,
                "fee": fee,
                "destination_address": destination_address,
                "network": network,
                "estimated_confirmation_time": self._get_estimated_confirmation_time(currency, network)
            }
            
        except Exception as e:
            logger.error(f"Error processing crypto withdrawal: {e}", exc_info=True)
            await self.db.rollback()
            raise
    
    async def _generate_deposit_address(
        self,
        currency: str,
        network: Optional[str] = None
    ) -> str:
        """Generate a deposit address for the currency"""
        # In production, this would generate addresses from your wallet infrastructure
        # For now, return a placeholder
        network_suffix = f"_{network}" if network else ""
        return f"{currency.lower()}_deposit_{datetime.utcnow().timestamp()}{network_suffix}"
    
    async def _get_transfer_instructions(
        self,
        source_platform: str,
        currency: str,
        destination_address: str,
        network: Optional[str],
        memo: Optional[str]
    ) -> Dict:
        """Get transfer instructions for a specific platform"""
        instructions = {
            "general": f"Send {currency} to the address below",
            "destination_address": destination_address,
            "network": network or "default",
            "memo": memo
        }
        
        platform_specific = {
            "binance": {
                "steps": [
                    "1. Log in to Binance",
                    "2. Go to Wallet > Withdraw",
                    f"3. Select {currency}",
                    f"4. Enter address: {destination_address}",
                    f"5. Select network: {network or 'default'}",
                    "6. Enter amount and confirm"
                ],
                "min_withdrawal": self._get_min_withdrawal(currency, "binance"),
                "fee": self._get_platform_fee(currency, "binance")
            },
            "coinbase": {
                "steps": [
                    "1. Log in to Coinbase",
                    "2. Go to Assets > Send",
                    f"3. Select {currency}",
                    f"4. Enter address: {destination_address}",
                    "5. Enter amount and confirm"
                ],
                "min_withdrawal": self._get_min_withdrawal(currency, "coinbase"),
                "fee": self._get_platform_fee(currency, "coinbase")
            },
            "kraken": {
                "steps": [
                    "1. Log in to Kraken",
                    "2. Go to Funding > Withdraw",
                    f"3. Select {currency}",
                    f"4. Enter address: {destination_address}",
                    "5. Enter amount and confirm"
                ],
                "min_withdrawal": self._get_min_withdrawal(currency, "kraken"),
                "fee": self._get_platform_fee(currency, "kraken")
            },
            "external_wallet": {
                "steps": [
                    f"1. Open your {currency} wallet",
                    "2. Select Send/Withdraw",
                    f"3. Enter address: {destination_address}",
                    f"4. Select network: {network or 'default'}",
                    "5. Enter amount and confirm"
                ],
                "note": "Make sure to select the correct network to avoid loss of funds"
            }
        }
        
        if source_platform.lower() in platform_specific:
            instructions.update(platform_specific[source_platform.lower()])
        
        return instructions
    
    async def _verify_blockchain_transaction(
        self,
        tx_hash: str,
        currency: str,
        network: Optional[str],
        destination_address: Optional[str],
        expected_amount: float
    ) -> bool:
        """Verify a blockchain transaction"""
        # In production, this would use blockchain APIs (e.g., Etherscan, BlockCypher)
        # For now, return True (would implement actual verification)
        logger.info(f"Verifying transaction {tx_hash} for {currency}")
        return True  # Placeholder
    
    def _get_required_confirmations(self, currency: str, network: Optional[str]) -> int:
        """Get required confirmations for a currency/network"""
        confirmation_map = {
            "BTC": 6,
            "ETH": 12,
            "USDT": 12 if network == "ERC20" else 1,
            "SOL": 32,
            "ADA": 10,
            "DOT": 12,
            "ATOM": 1
        }
        return confirmation_map.get(currency.upper(), 6)
    
    def _get_estimated_confirmation_time(self, currency: str, network: Optional[str]) -> str:
        """Get estimated confirmation time"""
        time_map = {
            "BTC": "10-60 minutes",
            "ETH": "1-5 minutes",
            "USDT": "1-5 minutes" if network == "ERC20" else "5-30 minutes",
            "SOL": "13 seconds",
            "ADA": "5-10 minutes",
            "DOT": "6 seconds",
            "ATOM": "6 seconds"
        }
        return time_map.get(currency.upper(), "5-30 minutes")
    
    async def _calculate_withdrawal_fee(self, currency: str, network: Optional[str]) -> float:
        """Calculate withdrawal fee"""
        # In production, this would fetch from exchange APIs
        fee_map = {
            "BTC": 0.0005,
            "ETH": 0.005,
            "USDT": 1.0 if network == "ERC20" else 0.1,
            "SOL": 0.000005,
            "ADA": 0.17,
            "DOT": 0.026,
            "ATOM": 0.001
        }
        return fee_map.get(currency.upper(), 0.01)
    
    async def _validate_crypto_address(self, address: str, currency: str, network: Optional[str]) -> bool:
        """Validate a crypto address format"""
        # In production, this would use proper address validation libraries
        # For now, basic validation
        if not address or len(address) < 10:
            return False
        
        # Basic format checks
        if currency.upper() == "BTC":
            return address.startswith(("1", "3", "bc1"))
        elif currency.upper() == "ETH":
            return address.startswith("0x") and len(address) == 42
        elif currency.upper() == "SOL":
            return len(address) >= 32 and len(address) <= 44
        
        return True  # Default to valid for other currencies
    
    def _get_min_withdrawal(self, currency: str, platform: str) -> float:
        """Get minimum withdrawal amount for a platform"""
        # In production, fetch from platform APIs
        return 0.001
    
    def _get_platform_fee(self, currency: str, platform: str) -> str:
        """Get platform withdrawal fee"""
        # In production, fetch from platform APIs
        return "Varies by network"

