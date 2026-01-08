"""
Crypto Transfer Service
Handles crypto transfers from external platforms and wallets
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

# Exchange service removed - platform uses DEX-only trading
# All transfers now go through blockchain/DEX, not centralized exchanges
EXCHANGE_SERVICE_AVAILABLE = False
ExchangeService = None


class CryptoTransferService:
    """Service for transferring crypto from external platforms"""

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
        # Exchange service removed - platform uses DEX-only trading

    async def initiate_crypto_transfer(
        self,
        user_id: int,
        currency: str,
        amount: float,
        source_platform: str,  # 'binance', 'coinbase', 'kraken', 'external_wallet', etc.
        source_address: str | None = None,  # For external wallets
        destination_address: str | None = None,  # Our platform address
        network: str | None = None,  # 'ERC20', 'TRC20', 'BEP20', etc.
        memo: str | None = None,
    ) -> dict:
        """
        Initiate a crypto transfer from an external platform

        Returns:
            Dict with transfer details and instructions
        """
        try:
            # ✅ Data access delegated to repository
            wallet = await self.wallet_repository.get_or_create_wallet(
                self.db, user_id, currency, "trading"
            )

            # Generate deposit address if not provided
            if not destination_address:
                destination_address = await self._generate_deposit_address(
                    currency, network
                )

            # ✅ Business logic: Create pending transaction
            # ✅ Data access delegated to repository
            transaction = await self.transaction_repository.create_transaction(
                self.db,
                {
                    "wallet_id": wallet.id,
                    "user_id": user_id,
                    "transaction_type": TransactionType.DEPOSIT.value,
                    "status": TransactionStatus.PENDING.value,
                    "amount": amount,
                    "currency": currency,
                    "fee": 0.0,
                    "net_amount": amount,
                    "description": f"Crypto transfer from {source_platform}",
                    "reference_id": f"{source_platform}_{datetime.utcnow().timestamp()}",
                    "transaction_metadata": {
                        "source_platform": source_platform,
                        "source_address": source_address,
                        "destination_address": destination_address,
                        "network": network,
                        "memo": memo,
                    },
                },
            )

            # Get transfer instructions based on source platform
            instructions = await self._get_transfer_instructions(
                source_platform, currency, destination_address, network, memo
            )

            logger.info(
                f"Crypto transfer initiated: user {user_id}, {amount} {currency} from {source_platform}",
                extra={
                    "user_id": user_id,
                    "currency": currency,
                    "amount": amount,
                    "source_platform": source_platform,
                },
            )

            return {
                "transaction_id": transaction.id,
                "status": "pending",
                "amount": amount,
                "currency": currency,
                "destination_address": destination_address,
                "network": network,
                "instructions": instructions,
                "estimated_confirmation_time": self._get_estimated_confirmation_time(
                    currency, network
                ),
            }

        except Exception as e:
            logger.error(f"Error initiating crypto transfer: {e}", exc_info=True)
            await self.db.rollback()
            raise

    async def confirm_crypto_transfer(
        self, transaction_id: int, tx_hash: str, confirmations: int = 0
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
            # ✅ Data access delegated to repository
            transaction = await self.transaction_repository.get_by_id(
                self.db, transaction_id
            )

            if not transaction:
                return False

            if transaction.status == TransactionStatus.COMPLETED.value:
                return True  # Already confirmed

            # ✅ Business logic: Check if we have enough confirmations
            transaction_metadata = transaction.transaction_metadata or {}
            required_confirmations = self._get_required_confirmations(
                transaction.currency,
                transaction_metadata.get("network"),
            )

            if confirmations < required_confirmations:
                # ✅ Data access delegated to repository
                transaction_metadata["tx_hash"] = tx_hash
                transaction_metadata["confirmations"] = confirmations
                await self.transaction_repository.update(
                    self.db,
                    transaction_id,
                    {"transaction_metadata": transaction_metadata},
                )
                return False  # Not enough confirmations yet

            # ✅ Business logic: Verify transaction on blockchain
            verified = await self._verify_blockchain_transaction(
                tx_hash,
                transaction.currency,
                transaction_metadata.get("network"),
                transaction_metadata.get("destination_address"),
                transaction.amount,
            )

            if not verified:
                logger.warning(
                    f"Blockchain verification failed for transaction {transaction_id}",
                    extra={"transaction_id": transaction_id, "tx_hash": tx_hash},
                )
                # ✅ Data access delegated to repository
                await self.transaction_repository.update_status(
                    self.db, transaction_id, TransactionStatus.FAILED.value
                )
                return False

            # ✅ Data access delegated to repository
            wallet = await self.wallet_repository.get_by_id(
                self.db, transaction.wallet_id
            )

            if wallet:
                # ✅ Business logic: Update wallet balance
                # ✅ Data access delegated to repository
                await self.wallet_repository.update_balance(
                    self.db,
                    wallet.id,
                    balance=wallet.balance + transaction.net_amount,
                    available_balance=wallet.available_balance + transaction.net_amount,
                    total_deposited=wallet.total_deposited + transaction.net_amount,
                )

                # ✅ Data access delegated to repository
                transaction_metadata["tx_hash"] = tx_hash
                transaction_metadata["confirmations"] = confirmations
                transaction_metadata["verified_at"] = datetime.utcnow().isoformat()
                await self.transaction_repository.update_status(
                    self.db,
                    transaction_id,
                    TransactionStatus.COMPLETED.value,
                    processed_at=datetime.utcnow(),
                )
                await self.transaction_repository.update(
                    self.db,
                    transaction_id,
                    {"transaction_metadata": transaction_metadata},
                )

                # Broadcast wallet update
                try:
                    from ..services.wallet_broadcast import broadcast_wallet_update

                    # ✅ Use wallet balance directly (internal Wallet model)
                    balance = {
                        "currency": wallet.currency,
                        "balance": wallet.balance,
                        "available_balance": wallet.available_balance,
                        "locked_balance": wallet.locked_balance,
                    }
                    await broadcast_wallet_update(wallet.user_id, balance)
                except Exception as e:
                    logger.warning(
                        f"Failed to broadcast wallet update: {e}",
                        extra={"user_id": wallet.user_id},
                    )

                logger.info(
                    f"Crypto transfer confirmed: transaction {transaction_id}",
                    extra={"transaction_id": transaction_id, "tx_hash": tx_hash},
                )
                return True

            return False

        except Exception as e:
            logger.error(
                f"Error confirming crypto transfer: {e}",
                exc_info=True,
                extra={"transaction_id": transaction_id, "tx_hash": tx_hash},
            )
            await self.db.rollback()
            return False

    async def withdraw_crypto(
        self,
        user_id: int,
        currency: str,
        amount: float,
        destination_address: str,
        network: str | None = None,
        memo: str | None = None,
    ) -> dict:
        """
        Withdraw crypto to an external address

        Returns:
            Dict with withdrawal details
        """
        try:
            # ✅ Data access delegated to repository
            wallet = await self.wallet_repository.get_or_create_wallet(
                self.db, user_id, currency, "trading"
            )

            # Check balance
            if wallet.available_balance < amount:
                raise ValueError(
                    f"Insufficient balance. Available: {wallet.available_balance}, Required: {amount}"
                )

            # Calculate fee
            fee = await self._calculate_withdrawal_fee(currency, network)
            total_deduction = amount + fee

            if wallet.available_balance < total_deduction:
                raise ValueError("Insufficient balance for withdrawal and fees")

            # Validate destination address
            is_valid = await self._validate_crypto_address(
                destination_address, currency, network
            )
            if not is_valid:
                raise ValueError(f"Invalid destination address for {currency}")

            # ✅ Business logic: Lock funds
            # ✅ Data access delegated to repository
            await self.wallet_repository.update_balance(
                self.db,
                wallet.id,
                available_balance=wallet.available_balance - total_deduction,
                locked_balance=wallet.locked_balance + total_deduction,
            )

            # ✅ Business logic: Create withdrawal transaction
            # ✅ Data access delegated to repository
            transaction = await self.transaction_repository.create_transaction(
                self.db,
                {
                    "wallet_id": wallet.id,
                    "user_id": user_id,
                    "transaction_type": TransactionType.WITHDRAWAL.value,
                    "status": TransactionStatus.PENDING.value,
                    "amount": amount,
                    "currency": currency,
                    "fee": fee,
                    "net_amount": amount,
                    "description": f"Withdrawal to {destination_address[:10]}...",
                    "reference_id": f"withdraw_{datetime.utcnow().timestamp()}",
                    "transaction_metadata": {
                        "destination_address": destination_address,
                        "network": network,
                        "memo": memo,
                    },
                },
            )

            # ✅ Business logic: Execute withdrawal (would integrate with exchange API or blockchain)
            # For now, mark as processing
            # ✅ Data access delegated to repository
            await self.transaction_repository.update_status(
                self.db, transaction.id, TransactionStatus.PROCESSING.value
            )

            logger.info(
                f"Crypto withdrawal initiated: user {user_id}, {amount} {currency} to {destination_address[:10]}...",
                extra={
                    "user_id": user_id,
                    "currency": currency,
                    "amount": amount,
                    "destination_address": destination_address[:10],
                },
            )

            return {
                "transaction_id": transaction.id,
                "status": "processing",
                "amount": amount,
                "currency": currency,
                "fee": fee,
                "destination_address": destination_address,
                "network": network,
                "estimated_confirmation_time": self._get_estimated_confirmation_time(
                    currency, network
                ),
            }

        except Exception as e:
            logger.error(f"Error processing crypto withdrawal: {e}", exc_info=True)
            await self.db.rollback()
            raise

    async def _generate_deposit_address(
        self, currency: str, network: str | None = None
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
        network: str | None,
        memo: str | None,
    ) -> dict:
        """Get transfer instructions for a specific platform"""
        instructions = {
            "general": f"Send {currency} to the address below",
            "destination_address": destination_address,
            "network": network or "default",
            "memo": memo,
        }

        platform_specific = {
            "binance": {
                "steps": [
                    "1. Log in to Binance",
                    "2. Go to Wallet > Withdraw",
                    f"3. Select {currency}",
                    f"4. Enter address: {destination_address}",
                    f"5. Select network: {network or 'default'}",
                    "6. Enter amount and confirm",
                ],
                "min_withdrawal": self._get_min_withdrawal(currency, "binance"),
                "fee": self._get_platform_fee(currency, "binance"),
            },
            "coinbase": {
                "steps": [
                    "1. Log in to Coinbase",
                    "2. Go to Assets > Send",
                    f"3. Select {currency}",
                    f"4. Enter address: {destination_address}",
                    "5. Enter amount and confirm",
                ],
                "min_withdrawal": self._get_min_withdrawal(currency, "coinbase"),
                "fee": self._get_platform_fee(currency, "coinbase"),
            },
            "kraken": {
                "steps": [
                    "1. Log in to Kraken",
                    "2. Go to Funding > Withdraw",
                    f"3. Select {currency}",
                    f"4. Enter address: {destination_address}",
                    "5. Enter amount and confirm",
                ],
                "min_withdrawal": self._get_min_withdrawal(currency, "kraken"),
                "fee": self._get_platform_fee(currency, "kraken"),
            },
            "external_wallet": {
                "steps": [
                    f"1. Open your {currency} wallet",
                    "2. Select Send/Withdraw",
                    f"3. Enter address: {destination_address}",
                    f"4. Select network: {network or 'default'}",
                    "5. Enter amount and confirm",
                ],
                "note": "Make sure to select the correct network to avoid loss of funds",
            },
        }

        if source_platform.lower() in platform_specific:
            instructions.update(platform_specific[source_platform.lower()])

        return instructions

    async def _verify_blockchain_transaction(
        self,
        tx_hash: str,
        currency: str,
        network: str | None,
        destination_address: str | None,
        expected_amount: float,
    ) -> bool:
        """Verify a blockchain transaction"""
        # In production, this would use blockchain APIs (e.g., Etherscan, BlockCypher)
        # For now, return True (would implement actual verification)
        logger.info(f"Verifying transaction {tx_hash} for {currency}")
        return True  # Placeholder

    def _get_required_confirmations(self, currency: str, network: str | None) -> int:
        """Get required confirmations for a currency/network"""
        confirmation_map = {
            "BTC": 6,
            "ETH": 12,
            "USDT": 12 if network == "ERC20" else 1,
            "SOL": 32,
            "ADA": 10,
            "DOT": 12,
            "ATOM": 1,
        }
        return confirmation_map.get(currency.upper(), 6)

    def _get_estimated_confirmation_time(
        self, currency: str, network: str | None
    ) -> str:
        """Get estimated confirmation time"""
        time_map = {
            "BTC": "10-60 minutes",
            "ETH": "1-5 minutes",
            "USDT": "1-5 minutes" if network == "ERC20" else "5-30 minutes",
            "SOL": "13 seconds",
            "ADA": "5-10 minutes",
            "DOT": "6 seconds",
            "ATOM": "6 seconds",
        }
        return time_map.get(currency.upper(), "5-30 minutes")

    async def _calculate_withdrawal_fee(
        self, currency: str, network: str | None
    ) -> float:
        """Calculate withdrawal fee"""
        # In production, this would fetch from exchange APIs
        fee_map = {
            "BTC": 0.0005,
            "ETH": 0.005,
            "USDT": 1.0 if network == "ERC20" else 0.1,
            "SOL": 0.000005,
            "ADA": 0.17,
            "DOT": 0.026,
            "ATOM": 0.001,
        }
        return fee_map.get(currency.upper(), 0.01)

    async def _validate_crypto_address(
        self, address: str, currency: str, network: str | None
    ) -> bool:
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
