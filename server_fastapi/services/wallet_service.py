"""
Wallet Management Service
Generates and manages user blockchain wallets
Handles custodial wallet creation, deposit address generation, balance fetching, and withdrawals
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

try:
    from eth_account import Account
    from eth_utils import is_address, to_checksum_address

    ETH_ACCOUNT_AVAILABLE = True
except ImportError:
    ETH_ACCOUNT_AVAILABLE = False
    Account = None
    to_checksum_address = None
    is_address = None

from ..config.settings import get_settings
from ..repositories.wallet_repository import WalletRepository
from ..repositories.transaction_repository import TransactionRepository
from .security.vault_interface import AbstractVault
from ..core.domain_registry import domain_registry

# Optional blockchain imports (may not be available if web3 is not installed)
try:
    from ..blockchain.balance_service import get_balance_service
    from ..blockchain.transaction_service import get_transaction_service

    BLOCKCHAIN_AVAILABLE = True
except ImportError:
    BLOCKCHAIN_AVAILABLE = False
    get_balance_service = None
    get_transaction_service = None

logger = logging.getLogger(__name__)

if not BLOCKCHAIN_AVAILABLE:
    logger.warning(
        "Blockchain services not available - wallet features will be limited"
    )

logger = logging.getLogger(__name__)


class WalletService:
    """Service for managing user blockchain wallets"""

    def __init__(self, db: AsyncSession | None = None):
        if not ETH_ACCOUNT_AVAILABLE:
            logger.warning(
                "eth-account not available. Install with: pip install eth-account"
            )
        self.db = db
        self._vault = None

    @property
    def vault(self) -> AbstractVault:
        if self._vault is None:
            self._vault = domain_registry.resolve(AbstractVault)
        return self._vault

    def generate_wallet_address(self) -> dict[str, Any] | None:
        """
        Generate a new Ethereum wallet address and private key

        Returns:
            Dictionary with 'address' and 'private_key' (hex strings)
            Returns None if eth-account is not available
        """
        if not ETH_ACCOUNT_AVAILABLE:
            logger.error("eth-account not available for wallet generation")
            return None

        try:
            # Generate new account
            account = Account.create()
            address = to_checksum_address(account.address)
            private_key = account.key.hex()

            logger.info(f"Generated new wallet address: {address[:10]}...")

            return {
                "address": address,
                "private_key": private_key,
            }
        except Exception as e:
            logger.error(f"Error generating wallet address: {e}", exc_info=True)
            return None

    async def create_custodial_wallet(
        self,
        user_id: int,
        chain_id: int,
        label: str | None = None,
        db: AsyncSession | None = None,
    ) -> dict[str, Any] | None:
        """
        Create a custodial wallet for a user (platform-managed)

        Args:
            user_id: User ID
            chain_id: Blockchain ID
            label: Optional user-friendly label
            db: Database session

        Returns:
            Wallet information (address only, private key should be stored securely elsewhere)
            Returns None if error
        """
        if not db:
            logger.error("Database session required for wallet creation")
            return None

        try:
            repository = WalletRepository(db)

            # Check if wallet already exists
            existing = await repository.get_user_wallet(user_id, chain_id, "custodial")
            if existing:
                logger.info(
                    f"Custodial wallet already exists for user {user_id} on chain {chain_id}",
                    extra={"user_id": user_id, "chain_id": chain_id},
                )
                return {
                    "wallet_id": existing.id,
                    "address": existing.wallet_address,
                    "chain_id": existing.chain_id,
                    "wallet_type": existing.wallet_type,
                    "label": existing.label,
                    "is_verified": existing.is_verified,
                    "is_active": existing.is_active,
                }

            # Generate new wallet
            wallet_data = self.generate_wallet_address()
            if not wallet_data:
                raise ValueError("Failed to generate wallet address")

            # Store wallet in database
            # We store the address. The private key is handled by the Vault implementation.
            # In Phase 3, we expect LocalEnvVault or HashiCorpVault to be configured.
            wallet = await repository.create_wallet(
                user_id=user_id,
                wallet_address=wallet_data["address"],
                chain_id=chain_id,
                wallet_type="custodial",
                label=label or f"Custodial Wallet (Chain {chain_id})",
                metadata={
                    "generated_at": datetime.utcnow().isoformat(),
                    "vault_managed": True,
                },
            )

            # NOTE: In a real production flow, we'd now push wallet_data["private_key"]
            # to the secure Vault (e.g. HashiCorp) before returning.
            # For Phase 3, we're establishing the architectural boundary.

            if not wallet:
                raise ValueError("Failed to create wallet in database")

            logger.info(
                f"Created custodial wallet for user {user_id}",
                extra={
                    "user_id": user_id,
                    "wallet_id": wallet.id,
                    "address": wallet.wallet_address,
                    "chain_id": chain_id,
                },
            )

            # Audit log wallet creation
            try:
                from ..services.audit.audit_logger import audit_logger

                audit_logger.log_wallet_operation(
                    user_id=user_id,
                    operation="create",
                    wallet_id=wallet.id,
                    wallet_type="custodial",
                    chain_id=chain_id,
                    success=True,
                )
            except Exception as e:
                logger.warning(f"Failed to audit log wallet creation: {e}")

            return {
                "wallet_id": wallet.id,
                "address": wallet.wallet_address,
                "chain_id": wallet.chain_id,
                "wallet_type": wallet.wallet_type,
                "label": wallet.label,
                "is_verified": wallet.is_verified,
                "is_active": wallet.is_active,
            }

        except Exception as e:
            logger.error(f"Error creating custodial wallet: {e}", exc_info=True)
            return None

    async def register_external_wallet(
        self,
        user_id: int,
        wallet_address: str,
        chain_id: int,
        label: str | None = None,
        db: AsyncSession | None = None,
    ) -> dict[str, Any] | None:
        """
        Register an external wallet address (user's own wallet)

        Args:
            user_id: User ID
            wallet_address: User's wallet address
            chain_id: Blockchain ID
            label: Optional user-friendly label
            db: Database session

        Returns:
            Wallet information or None if error
        """
        if not db:
            logger.error("Database session required for wallet registration")
            return None

        if not ETH_ACCOUNT_AVAILABLE or not is_address(wallet_address):
            logger.error(f"Invalid wallet address: {wallet_address}")
            return None

        try:
            repository = WalletRepository(db)

            # Normalize address to checksum format
            wallet_address = to_checksum_address(wallet_address)

            # Check if wallet already exists
            existing = await repository.get_user_wallet(user_id, chain_id, "external")
            if existing and existing.wallet_address.lower() == wallet_address.lower():
                logger.info(
                    f"External wallet already registered for user {user_id}",
                    extra={"user_id": user_id, "wallet_address": wallet_address},
                )
                return {
                    "wallet_id": existing.id,
                    "address": existing.wallet_address,
                    "chain_id": existing.chain_id,
                    "wallet_type": existing.wallet_type,
                    "label": existing.label,
                    "is_verified": existing.is_verified,
                    "is_active": existing.is_active,
                }

            # Create wallet record (not verified until user proves ownership)
            wallet = await repository.create_wallet(
                user_id=user_id,
                wallet_address=wallet_address,
                chain_id=chain_id,
                wallet_type="external",
                label=label or f"External Wallet (Chain {chain_id})",
                metadata={},
            )

            if not wallet:
                raise ValueError("Failed to create wallet in database")

            logger.info(
                f"Registered external wallet for user {user_id}",
                extra={
                    "user_id": user_id,
                    "wallet_id": wallet.id,
                    "address": wallet.wallet_address,
                    "chain_id": chain_id,
                },
            )

            # Audit log wallet registration
            try:
                from ..services.audit.audit_logger import audit_logger

                audit_logger.log_wallet_operation(
                    user_id=user_id,
                    operation="register_external",
                    wallet_id=wallet.id,
                    wallet_type="external",
                    chain_id=chain_id,
                    success=True,
                )
            except Exception as e:
                logger.warning(f"Failed to audit log wallet registration: {e}")

            return {
                "wallet_id": wallet.id,
                "address": wallet.wallet_address,
                "chain_id": wallet.chain_id,
                "wallet_type": wallet.wallet_type,
                "label": wallet.label,
                "is_verified": wallet.is_verified,
                "is_active": wallet.is_active,
            }

        except Exception as e:
            logger.error(f"Error registering external wallet: {e}", exc_info=True)
            return None

    async def get_user_wallets(
        self, user_id: int, db: AsyncSession | None = None
    ) -> list[dict[str, Any]]:
        """
        Get all wallets for a user

        Args:
            user_id: User ID
            db: Database session

        Returns:
            List of wallet information dictionaries
        """
        if not db:
            logger.error("Database session required")
            return []

        try:
            repository = WalletRepository(db)
            wallets = await repository.get_user_wallets(user_id)

            return [
                {
                    "wallet_id": wallet.id,
                    "address": wallet.wallet_address,
                    "chain_id": wallet.chain_id,
                    "wallet_type": wallet.wallet_type,
                    "label": wallet.label,
                    "is_verified": wallet.is_verified,
                    "is_active": wallet.is_active,
                    "balance": wallet.balance,
                    "last_balance_update": (
                        wallet.last_balance_update.isoformat()
                        if wallet.last_balance_update
                        else None
                    ),
                }
                for wallet in wallets
            ]
        except Exception as e:
            logger.error(f"Error getting user wallets: {e}", exc_info=True)
            return []

    async def get_deposit_address(
        self, user_id: int, chain_id: int, db: AsyncSession | None = None
    ) -> str | None:
        """
        Get or create deposit address for a user (custodial wallet)

        Args:
            user_id: User ID
            chain_id: Blockchain ID
            db: Database session

        Returns:
            Deposit address (checksummed) or None if error
        """
        if not db:
            logger.error("Database session required")
            return None

        try:
            # Get or create custodial wallet
            wallet_info = await self.create_custodial_wallet(
                user_id=user_id, chain_id=chain_id, db=db
            )

            if not wallet_info:
                return None

            return wallet_info["address"]
        except Exception as e:
            logger.error(f"Error getting deposit address: {e}", exc_info=True)
            return None

    def is_address_valid(self, address: str) -> bool:
        """
        Check if an Ethereum address is valid

        Args:
            address: Address string to validate

        Returns:
            True if valid, False otherwise
        """
        if not ETH_ACCOUNT_AVAILABLE:
            return False

        try:
            return is_address(address)
        except Exception:
            return False

    async def get_wallet_balance(
        self,
        wallet_id: int,
        chain_id: int,
        address: str,
        token_address: str | None = None,
        db: AsyncSession | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any] | None:
        """
        Get wallet balance (ETH or ERC-20 token) with caching

        Args:
            wallet_id: Wallet ID
            chain_id: Blockchain ID
            address: Wallet address
            token_address: Optional token contract address (None for ETH)
            db: Database session
            use_cache: Whether to use cached balance

        Returns:
            Balance dictionary with 'balance', 'token', 'chain_id', 'last_updated' or None if error
        """
        try:
            if not BLOCKCHAIN_AVAILABLE:
                logger.warning(
                    "Blockchain services not available - falling back to cached balance"
                )
                if db:
                    repository = WalletRepository(db)
                    from sqlalchemy import select
                    from ..models.user_wallet import UserWallet

                    stmt = select(UserWallet).where(UserWallet.id == wallet_id)
                    result = await db.execute(stmt)
                    wallet = result.scalar_one_or_none()
                    if wallet and wallet.balance:
                        balance_key = token_address or "ETH"
                        balance = wallet.balance.get(balance_key, "0.0")
                        return {
                            "balance": str(balance),
                            "token": "TOKEN" if token_address else "ETH",
                            "token_address": token_address,
                            "chain_id": chain_id,
                            "last_updated": (
                                wallet.last_balance_update.isoformat()
                                if wallet.last_balance_update
                                else datetime.utcnow().isoformat()
                            ),
                        }
                return None
            balance_service = get_balance_service()

            # Get balance from blockchain
            if token_address:
                balance = await balance_service.get_token_balance(
                    chain_id=chain_id,
                    address=address,
                    token_address=token_address,
                    use_cache=use_cache,
                )
                token_symbol = "TOKEN"  # Could be fetched from token contract
            else:
                balance = await balance_service.get_eth_balance(
                    chain_id=chain_id,
                    address=address,
                    use_cache=use_cache,
                )
                token_symbol = "ETH"

            if balance is None:
                logger.warning(f"Could not fetch balance for wallet {wallet_id}")
                return None

            # Update wallet balance cache in database
            if db:
                repository = WalletRepository(db)
                # Get current wallet to check existing balance
                from sqlalchemy import select

                from ..models.user_wallet import UserWallet

                stmt = select(UserWallet).where(UserWallet.id == wallet_id)
                result = await db.execute(stmt)
                wallet = result.scalar_one_or_none()

                if wallet:
                    balance_dict = wallet.balance or {}
                    balance_key = token_address or "ETH"
                    balance_dict[balance_key] = str(balance)
                    await repository.update_wallet_balance(wallet_id, balance_dict)

            return {
                "balance": str(balance),
                "token": token_symbol,
                "token_address": token_address,
                "chain_id": chain_id,
                "last_updated": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error getting wallet balance: {e}", exc_info=True)
            return None

    async def refresh_wallet_balances(
        self,
        user_id: int,
        db: AsyncSession | None = None,
    ) -> dict[int, bool]:
        """
        Refresh balances for all user wallets

        Args:
            user_id: User ID
            db: Database session

        Returns:
            Dictionary mapping wallet_id to success status
        """
        if not db:
            logger.error("Database session required")
            return {}

        try:
            repository = WalletRepository(db)
            wallets = await repository.get_user_wallets(user_id)

            results = {}
            if not BLOCKCHAIN_AVAILABLE:
                logger.warning(
                    "Blockchain services not available - cannot fetch balance"
                )
                return {}
            balance_service = get_balance_service()

            for wallet in wallets:
                try:
                    # Get ETH balance
                    eth_balance = await balance_service.get_eth_balance(
                        chain_id=wallet.chain_id,
                        address=wallet.wallet_address,
                        use_cache=False,  # Force refresh
                    )

                    balance_dict = wallet.balance or {}
                    if eth_balance is not None:
                        balance_dict["ETH"] = str(eth_balance)

                    # Update in database
                    await repository.update_wallet_balance(wallet.id, balance_dict)
                    results[wallet.id] = True

                    # Audit log balance refresh
                    try:
                        from ..services.audit.audit_logger import audit_logger

                        audit_logger.log_wallet_operation(
                            user_id=user_id,
                            operation="balance_refresh",
                            wallet_id=wallet.id,
                            wallet_type=wallet.wallet_type,
                            chain_id=wallet.chain_id,
                            success=True,
                        )
                    except Exception:
                        pass  # Don't fail if audit logging fails
                except Exception as e:
                    logger.error(
                        f"Error refreshing balance for wallet {wallet.id}: {e}"
                    )
                    results[wallet.id] = False

            return results
        except Exception as e:
            logger.error(f"Error refreshing wallet balances: {e}", exc_info=True)
            return {}

    async def process_withdrawal(
        self,
        wallet_id: int,
        user_id: int,
        to_address: str,
        amount: Decimal,
        token_address: str | None = None,
        chain_id: int = 1,
        db: AsyncSession | None = None,
    ) -> dict[str, Any] | None:
        """
        Process a withdrawal from a custodial wallet

        Args:
            wallet_id: Wallet ID
            user_id: User ID
            to_address: Destination address
            amount: Amount to withdraw (in token units, not wei)
            token_address: Optional token contract address (None for ETH)
            chain_id: Blockchain ID
            db: Database session

        Returns:
            Transaction hash and status or None if error
        """
        if not db:
            logger.error("Database session required")
            return None

        try:
            # Validate addresses
            if not self.is_address_valid(to_address):
                raise ValueError("Invalid destination address")

            repository = WalletRepository(db)
            wallet = await repository.get_user_wallet(user_id, chain_id, "custodial")

            if not wallet or wallet.id != wallet_id:
                raise ValueError("Wallet not found or not owned by user")

            # Check balance
            balance_info = await self.get_wallet_balance(
                wallet_id=wallet_id,
                chain_id=chain_id,
                address=wallet.wallet_address,
                token_address=token_address,
                db=db,
                use_cache=False,
            )

            if not balance_info:
                raise ValueError("Could not fetch wallet balance")

            current_balance = Decimal(balance_info["balance"])
            if current_balance < amount:
                raise ValueError(f"Insufficient balance: {current_balance} < {amount}")

            # Get transaction service
            if not BLOCKCHAIN_AVAILABLE:
                logger.warning(
                    "Blockchain services not available - cannot execute transaction"
                )
                return None
            transaction_service = get_transaction_service()

            # Prepare transaction
            # Note: In production, private key should be retrieved from secure key management
            # For now, this is a placeholder - actual implementation requires secure key storage
            settings = get_settings()

            # This is a simplified version - in production, you'd:
            # 1. Retrieve private key from secure key management (AWS KMS, HashiCorp Vault)
            # 2. Sign transaction
            # 3. Send transaction
            # 4. Store transaction record in database

            logger.warning(
                "Withdrawal processing requires secure key management - not fully implemented",
                extra={
                    "wallet_id": wallet_id,
                    "user_id": user_id,
                    "to_address": to_address,
                    "amount": str(amount),
                    "token_address": token_address,
                },
            )

            # Audit log withdrawal
            try:
                from ..services.audit.audit_logger import audit_logger

                audit_logger.log_wallet_operation(
                    user_id=user_id,
                    operation="withdraw",
                    wallet_id=wallet_id,
                    wallet_type="custodial",
                    chain_id=chain_id,
                    amount=float(amount),
                    token_address=token_address,
                    success=True,
                )
            except Exception as e:
                logger.warning(f"Failed to audit log withdrawal: {e}")

            # Track transaction for monitoring
            try:
                from ..services.monitoring.transaction_monitor import (
                    transaction_monitor,
                )

                await transaction_monitor.track_transaction(
                    transaction_hash="pending",  # Will be updated when transaction is sent
                    chain_id=chain_id,
                    transaction_type="withdrawal",
                    user_id=user_id,
                    amount=amount,
                    token_address=token_address,
                    from_address=wallet.wallet_address,
                    to_address=to_address,
                    status="pending",
                )
            except Exception as e:
                logger.warning(f"Failed to track transaction for monitoring: {e}")

            # Return placeholder response
            return {
                "status": "pending",
                "message": "Withdrawal processing requires secure key management setup",
                "wallet_id": wallet_id,
                "to_address": to_address,
                "amount": str(amount),
                "token_address": token_address,
            }

        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Error processing withdrawal: {e}", exc_info=True)
            return None

    async def get_transactions(
        self,
        user_id: int,
        currency: str | None = None,
        transaction_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """
        Get paginated wallet transactions for a user.
        """
        target_db = db or self.db
        if not target_db:
            logger.error("Database session not available for get_transactions")
            return {
                "transactions": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
            }

        skip = (page - 1) * page_size
        limit = page_size

        repo = TransactionRepository()

        transactions = await repo.get_by_user(
            session=target_db,
            user_id=user_id,
            transaction_type=transaction_type,
            currency=currency,
            skip=skip,
            limit=limit,
        )

        total = await repo.get_count_by_user(
            session=target_db,
            user_id=user_id,
            transaction_type=transaction_type,
            currency=currency,
        )

        return {
            "transactions": transactions,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
