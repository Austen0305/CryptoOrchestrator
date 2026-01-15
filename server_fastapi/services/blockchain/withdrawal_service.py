"""
Withdrawal Service
Secure withdrawal processing with security checks, limits, and validation
"""

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.settings import get_settings
from .balance_service import get_balance_service
from .key_management import get_key_management_service
from .transaction_service import get_transaction_service
from .web3_service import get_web3_service

logger = logging.getLogger(__name__)


class WithdrawalService:
    """Service for processing secure withdrawals"""

    def __init__(self):
        self.settings = get_settings()
        self.web3_service = get_web3_service()
        self.transaction_service = get_transaction_service()
        self.balance_service = get_balance_service()
        self.key_management = get_key_management_service()

        # Withdrawal limits (configurable)
        self.daily_withdrawal_limit_usd = 10000.0  # $10k daily limit
        self.weekly_withdrawal_limit_usd = 50000.0  # $50k weekly limit
        self.min_withdrawal_amount = 0.001  # Minimum withdrawal amount in ETH

    async def validate_withdrawal(
        self,
        user_id: int,
        chain_id: int,
        to_address: str,
        amount: Decimal,
        currency: str = "ETH",
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """
        Validate withdrawal request

        Args:
            user_id: User ID
            chain_id: Blockchain chain ID
            to_address: Destination address
            amount: Withdrawal amount
            currency: Currency (ETH or token address)
            db: Database session

        Returns:
            Validation result dictionary with 'valid' boolean and 'errors' list
        """
        errors = []
        warnings = []

        try:
            # Validate address format
            normalized_address = self.web3_service.normalize_address(to_address)
            if not normalized_address:
                errors.append("Invalid destination address format")
                return {"valid": False, "errors": errors, "warnings": warnings}

            # Validate amount
            if amount <= 0:
                errors.append("Withdrawal amount must be greater than 0")
            elif amount < Decimal(self.min_withdrawal_amount):
                errors.append(
                    f"Withdrawal amount below minimum: {self.min_withdrawal_amount}"
                )

            # Check if address is whitelisted (optional security feature)
            if db and self.settings.enable_withdrawal_whitelist:
                from ...models.withdrawal_address_whitelist import (
                    WithdrawalAddressWhitelist,
                )

                stmt = select(WithdrawalAddressWhitelist).where(
                    and_(
                        WithdrawalAddressWhitelist.user_id == user_id,
                        WithdrawalAddressWhitelist.address == normalized_address,
                        WithdrawalAddressWhitelist.chain_id == chain_id,
                        WithdrawalAddressWhitelist.is_whitelisted,
                    )
                )
                result = await db.execute(stmt)
                whitelist_entry = result.scalar_one_or_none()

                if not whitelist_entry:
                    errors.append(
                        "Withdrawal address not whitelisted. Add address and wait 24 hours before withdrawing."
                    )
                elif whitelist_entry.is_in_cooldown():
                    hours_remaining = (
                        whitelist_entry.cooldown_until - datetime.now(UTC)
                    ).total_seconds() / 3600
                    errors.append(
                        f"Withdrawal address is in cooldown period. {hours_remaining:.1f} hours remaining."
                    )

            # Get user's wallet
            if db:
                from ...repositories.wallet_repository import WalletRepository

                repository = WalletRepository(db)
                wallet = await repository.get_user_wallet(
                    user_id, chain_id, "custodial"
                )

                if not wallet:
                    errors.append("Custodial wallet not found")
                else:
                    # Check balance
                    if currency == "ETH" or currency.lower() == "eth":
                        balance = await self.balance_service.get_eth_balance(
                            chain_id, wallet.wallet_address, use_cache=False
                        )
                    else:
                        balance = await self.balance_service.get_token_balance(
                            chain_id, wallet.wallet_address, currency, use_cache=False
                        )

                    if balance is None:
                        errors.append("Could not check balance")
                    elif balance < amount:
                        errors.append(
                            f"Insufficient balance. Available: {balance}, Requested: {amount}"
                        )

                    # Check daily/weekly withdrawal limits
                    if db:
                        from sqlalchemy import func

                        from ...models.wallet_transaction import WalletTransaction

                        # Get withdrawals in last 24 hours
                        daily_cutoff = datetime.now(UTC) - timedelta(hours=24)
                        daily_stmt = select(func.sum(WalletTransaction.amount)).where(
                            and_(
                                WalletTransaction.user_id == user_id,
                                WalletTransaction.transaction_type == "withdrawal",
                                WalletTransaction.status == "completed",
                                WalletTransaction.created_at >= daily_cutoff,
                            )
                        )
                        daily_result = await db.execute(daily_stmt)
                        daily_total = float(daily_result.scalar() or 0)

                        # Get withdrawals in last 7 days
                        weekly_cutoff = datetime.now(UTC) - timedelta(days=7)
                        weekly_stmt = select(func.sum(WalletTransaction.amount)).where(
                            and_(
                                WalletTransaction.user_id == user_id,
                                WalletTransaction.transaction_type == "withdrawal",
                                WalletTransaction.status == "completed",
                                WalletTransaction.created_at >= weekly_cutoff,
                            )
                        )
                        weekly_result = await db.execute(weekly_stmt)
                        weekly_total = float(weekly_result.scalar() or 0)

                        # Convert amount to USD for limit checking (simplified - use current price)
                        # In production, use actual token price from Market Data Service or similar
                        amount_usd = (
                            float(amount) * 2000.0
                        )  # Placeholder: assume $2000 per ETH

                        if daily_total + amount_usd > self.daily_withdrawal_limit_usd:
                            errors.append(
                                f"Daily withdrawal limit exceeded. "
                                f"Limit: ${self.daily_withdrawal_limit_usd}, "
                                f"Used: ${daily_total:.2f}, "
                                f"Requested: ${amount_usd:.2f}"
                            )

                        if weekly_total + amount_usd > self.weekly_withdrawal_limit_usd:
                            errors.append(
                                f"Weekly withdrawal limit exceeded. "
                                f"Limit: ${self.weekly_withdrawal_limit_usd}, "
                                f"Used: ${weekly_total:.2f}, "
                                f"Requested: ${amount_usd:.2f}"
                            )

            # Check for suspicious patterns (fraud detection)
            if db:
                try:
                    from ...services.compliance.compliance_service import (
                        compliance_service,
                    )

                    # Check for suspicious withdrawal patterns
                    fraud_check = await compliance_service.check_withdrawal_fraud(
                        user_id=user_id,
                        amount=float(amount),
                        to_address=normalized_address,
                        chain_id=chain_id,
                    )

                    if not fraud_check.get("allowed", True):
                        errors.append(
                            f"Withdrawal flagged for review: {fraud_check.get('reason', 'Suspicious pattern detected')}"
                        )
                except ImportError:
                    logger.warning(
                        "Compliance service not available for fraud detection"
                    )
                except Exception as e:
                    logger.warning(f"Fraud detection check failed: {e}", exc_info=True)

            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
            }

        except Exception as e:
            logger.error(f"Error validating withdrawal: {e}", exc_info=True)
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": warnings,
            }

    async def process_withdrawal(
        self,
        user_id: int,
        chain_id: int,
        to_address: str,
        amount: Decimal,
        currency: str = "ETH",
        mfa_token: str | None = None,
        db: AsyncSession | None = None,
    ) -> dict[str, Any] | None:
        """
        Process withdrawal request

        Args:
            user_id: User ID
            chain_id: Blockchain chain ID
            to_address: Destination address
            amount: Withdrawal amount
            currency: Currency (ETH or token address)
            mfa_token: 2FA token (required for withdrawals)
            db: Database session

        Returns:
            Withdrawal result with transaction hash or None if error
        """
        try:
            if not db:
                raise ValueError("Database session required")

            # Validate withdrawal
            validation = await self.validate_withdrawal(
                user_id=user_id,
                chain_id=chain_id,
                to_address=to_address,
                amount=amount,
                currency=currency,
                db=db,
            )

            if not validation["valid"]:
                raise ValueError(
                    f"Withdrawal validation failed: {', '.join(validation['errors'])}"
                )

            # MANDATORY 2FA verification for withdrawals
            import speakeasy
            from sqlalchemy import select

            from ...database import get_db_context
            from ...models.base import User

            async with get_db_context() as session:
                result = await session.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()

                if not user:
                    raise ValueError("User not found")

                # MANDATORY: 2FA must be enabled for withdrawals
                if not user.mfa_enabled:
                    raise ValueError(
                        "2FA is required for withdrawals. Please enable 2FA in your account settings."
                    )

                # MANDATORY: 2FA token must be provided
                if not mfa_token:
                    raise ValueError(
                        "2FA token is required for withdrawals. Please provide your 2FA token."
                    )

                # Verify 2FA token
                if user.mfa_method == "totp" and user.mfa_secret:
                    verified = speakeasy.totp.verify(
                        {
                            "secret": user.mfa_secret,
                            "encoding": "base32",
                            "token": mfa_token,
                            "window": 2,
                        }
                    )
                    if not verified:
                        raise ValueError(
                            "Invalid 2FA token. Please check your authenticator app."
                        )
                elif user.mfa_method in ("email", "sms"):
                    # Verify one-time code
                    if not user.mfa_code or user.mfa_code != mfa_token:
                        raise ValueError(
                            "Invalid 2FA code. Please check your email/SMS."
                        )
                    # Check expiration
                    if (
                        user.mfa_code_expires_at
                        and datetime.now(UTC) > user.mfa_code_expires_at
                    ):
                        raise ValueError(
                            "2FA code has expired. Please request a new code."
                        )
                else:
                    raise ValueError(
                        "Unsupported 2FA method. Please use TOTP, email, or SMS."
                    )

            # Get user's wallet
            from ...repositories.wallet_repository import WalletRepository

            repository = WalletRepository(db)
            wallet = await repository.get_user_wallet(user_id, chain_id, "custodial")

            if not wallet:
                raise ValueError("Custodial wallet not found")

            # Get private key from secure storage
            private_key = await self.key_management.get_private_key(
                wallet.wallet_address, chain_id
            )
            if not private_key:
                raise ValueError(
                    "Private key not available. Key management not configured."
                )

            # Build transaction
            normalized_to = self.web3_service.normalize_address(to_address)
            if not normalized_to:
                raise ValueError("Invalid destination address")

            # Convert amount to wei (for ETH) or token units
            if currency == "ETH" or currency.lower() == "eth":
                value_wei = int(amount * Decimal(10**18))
                data = "0x"  # Empty data for ETH transfer
            else:
                # ERC-20 transfer - encode transfer function call
                # ERC-20 transfer function signature: transfer(address to, uint256 amount)
                try:
                    from eth_abi import encode
                    from eth_utils import to_checksum_address
                except ImportError:
                    logger.error(
                        "eth-abi and eth-utils required for ERC-20 transfers. Install with: pip install eth-abi eth-utils"
                    )
                    raise ValueError(
                        "ERC-20 transfers require eth-abi and eth-utils packages"
                    )

                # Get token decimals (default to 18, but should query contract)
                token_decimals = (
                    18  # Default, should query contract for actual decimals
                )
                try:
                    # Try to get decimals from token contract
                    w3 = await self.web3_service.get_connection(chain_id)
                    if w3:
                        # ERC-20 decimals() function call
                        decimals_abi = [
                            {
                                "constant": True,
                                "inputs": [],
                                "name": "decimals",
                                "outputs": [{"name": "", "type": "uint8"}],
                                "type": "function",
                            }
                        ]
                        token_contract = w3.eth.contract(
                            address=to_checksum_address(currency), abi=decimals_abi
                        )
                        token_decimals = (
                            await token_contract.functions.decimals().call()
                        )
                except Exception as e:
                    logger.warning(
                        f"Could not get token decimals for {currency}, using default 18: {e}"
                    )

                # Convert amount to token units
                amount_token_units = int(amount * Decimal(10**token_decimals))

                # Encode transfer(address to, uint256 amount)
                # Function selector: transfer(address,uint256) = 0xa9059cbb
                function_selector = "0xa9059cbb"
                encoded_params = encode(
                    ["address", "uint256"],
                    [to_checksum_address(normalized_to), amount_token_units],
                )
                data = function_selector + encoded_params.hex()
                value_wei = 0  # No ETH value for ERC-20 transfers

            # Get transaction count and gas price
            nonce = await self.transaction_service.get_transaction_count(
                chain_id, wallet.wallet_address
            )
            gas_price = await self.transaction_service.get_gas_price(chain_id)

            if nonce is None or gas_price is None:
                raise ValueError("Could not get transaction parameters")

            # Build transaction
            transaction = {
                "from": wallet.wallet_address,
                "to": normalized_to,
                "value": value_wei,
                "data": data,
                "gasPrice": gas_price,
                "nonce": nonce,
                "chainId": chain_id,
            }

            # Estimate gas
            gas = await self.transaction_service.estimate_gas(chain_id, transaction)
            if gas is None:
                raise ValueError("Could not estimate gas")
            transaction["gas"] = int(gas * 1.2)  # 20% buffer

            # Sign and send transaction
            tx_hash = await self.transaction_service.sign_and_send_transaction(
                chain_id=chain_id,
                private_key=private_key,
                transaction=transaction,
            )

            if not tx_hash:
                raise ValueError("Failed to send withdrawal transaction")

            logger.info(
                f"Withdrawal transaction sent: {tx_hash}",
                extra={
                    "user_id": user_id,
                    "chain_id": chain_id,
                    "to_address": normalized_to,
                    "amount": str(amount),
                    "currency": currency,
                    "tx_hash": tx_hash,
                },
            )

            # Record withdrawal for compliance monitoring
            try:
                from ...services.compliance.compliance_service import compliance_service

                await compliance_service.record_withdrawal(
                    user_id=user_id,
                    withdrawal_id=tx_hash,
                    amount=float(amount),
                    to_address=normalized_to,
                    chain_id=chain_id,
                )
            except Exception as e:
                logger.warning(
                    f"Failed to record withdrawal for compliance: {e}", exc_info=True
                )

            return {
                "success": True,
                "transaction_hash": tx_hash,
                "amount": str(amount),
                "currency": currency,
                "to_address": normalized_to,
                "status": "pending",
            }

        except ValueError as e:
            logger.warning(
                f"Withdrawal validation error: {e}", extra={"user_id": user_id}
            )
            return None
        except Exception as e:
            logger.error(
                f"Error processing withdrawal: {e}",
                exc_info=True,
                extra={"user_id": user_id},
            )
            return None

    async def get_withdrawal_status(
        self, chain_id: int, tx_hash: str
    ) -> dict[str, Any] | None:
        """
        Get withdrawal transaction status

        Args:
            chain_id: Blockchain chain ID
            tx_hash: Transaction hash

        Returns:
            Transaction status dictionary
        """
        try:
            status = await self.transaction_service.get_transaction_status(
                chain_id, tx_hash
            )
            return status
        except Exception as e:
            logger.error(f"Error getting withdrawal status: {e}", exc_info=True)
            return None


# Singleton instance
_withdrawal_service: WithdrawalService | None = None


def get_withdrawal_service() -> WithdrawalService:
    """Get singleton WithdrawalService instance"""
    global _withdrawal_service
    if _withdrawal_service is None:
        _withdrawal_service = WithdrawalService()
    return _withdrawal_service
