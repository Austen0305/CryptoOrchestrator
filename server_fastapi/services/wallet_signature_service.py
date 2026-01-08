"""
Wallet Signature Verification Service
Verifies EIP-712 signatures for trade authorization
Prevents replay attacks
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from eth_account import Account
    from eth_account.messages import encode_defunct, encode_structured_data
    from eth_utils import is_address, to_checksum_address

    ETH_ACCOUNT_AVAILABLE = True
except ImportError:
    ETH_ACCOUNT_AVAILABLE = False
    Account = None
    encode_defunct = None
    encode_structured_data = None
    to_checksum_address = None
    is_address = None

from ..models.wallet_nonce import WalletNonce

logger = logging.getLogger(__name__)


class WalletSignatureService:
    """Service for verifying wallet signatures for trade authorization"""

    def __init__(self):
        if not ETH_ACCOUNT_AVAILABLE:
            logger.warning(
                "eth-account not available. Install with: pip install eth-account"
            )

    def verify_eip712_signature(
        self,
        signature: str,
        message: dict[str, Any],
        domain: dict[str, Any],
        signer_address: str,
    ) -> bool:
        """
        Verify an EIP-712 structured data signature

        Args:
            signature: Hex signature string (0x...)
            message: EIP-712 message object
            domain: EIP-712 domain object
            signer_address: Expected signer address

        Returns:
            True if signature is valid, False otherwise
        """
        if not ETH_ACCOUNT_AVAILABLE:
            logger.error("eth-account not available for signature verification")
            return False

        try:
            # Normalize address to checksum format
            signer_address = to_checksum_address(signer_address)

            # Create EIP-712 structured data
            structured_data = {
                "types": {
                    "EIP712Domain": [
                        {"name": "name", "type": "string"},
                        {"name": "version", "type": "string"},
                        {"name": "chainId", "type": "uint256"},
                        {"name": "verifyingContract", "type": "address"},
                    ],
                    "TradeRequest": [
                        {"name": "sellToken", "type": "address"},
                        {"name": "buyToken", "type": "address"},
                        {"name": "sellAmount", "type": "uint256"},
                        {"name": "buyAmount", "type": "uint256"},
                        {"name": "chainId", "type": "uint256"},
                        {"name": "nonce", "type": "uint256"},
                        {"name": "expiry", "type": "uint256"},
                    ],
                },
                "primaryType": "TradeRequest",
                "domain": domain,
                "message": message,
            }

            # Encode and verify signature
            encoded = encode_structured_data(structured_data)
            recovered_address = Account.recover_message(encoded, signature=signature)

            # Normalize recovered address
            recovered_address = to_checksum_address(recovered_address)

            # Check if recovered address matches signer
            is_valid = recovered_address.lower() == signer_address.lower()

            if is_valid:
                logger.info(
                    f"EIP-712 signature verified for {signer_address}",
                    extra={"signer": signer_address, "recovered": recovered_address},
                )
            else:
                logger.warning(
                    f"EIP-712 signature verification failed: expected {signer_address}, got {recovered_address}",
                    extra={"expected": signer_address, "recovered": recovered_address},
                )

            return is_valid

        except Exception as e:
            logger.error(f"Error verifying EIP-712 signature: {e}", exc_info=True)
            return False

    def verify_simple_signature(
        self,
        signature: str,
        message: str,
        signer_address: str,
    ) -> bool:
        """
        Verify a simple message signature (not EIP-712)

        Args:
            signature: Hex signature string (0x...)
            message: Plain text message
            signer_address: Expected signer address

        Returns:
            True if signature is valid, False otherwise
        """
        if not ETH_ACCOUNT_AVAILABLE:
            logger.error("eth-account not available for signature verification")
            return False

        try:
            # Normalize address
            signer_address = to_checksum_address(signer_address)

            # Encode message
            encoded_message = encode_defunct(text=message)

            # Recover address from signature
            recovered_address = Account.recover_message(
                encoded_message, signature=signature
            )

            # Normalize recovered address
            recovered_address = to_checksum_address(recovered_address)

            # Check if recovered address matches signer
            is_valid = recovered_address.lower() == signer_address.lower()

            if is_valid:
                logger.info(
                    f"Simple signature verified for {signer_address}",
                    extra={"signer": signer_address, "recovered": recovered_address},
                )
            else:
                logger.warning(
                    f"Simple signature verification failed: expected {signer_address}, got {recovered_address}",
                    extra={"expected": signer_address, "recovered": recovered_address},
                )

            return is_valid

        except Exception as e:
            logger.error(f"Error verifying simple signature: {e}", exc_info=True)
            return False

    def create_trade_message(
        self,
        sell_token: str,
        buy_token: str,
        sell_amount: str,
        buy_amount: str,
        chain_id: int,
        nonce: int,
        expiry_seconds: int = 3600,  # 1 hour default
    ) -> dict[str, Any]:
        """
        Create an EIP-712 trade message for signing

        Args:
            sell_token: Token to sell address
            buy_token: Token to buy address
            sell_amount: Amount to sell (in wei/smallest unit)
            buy_amount: Amount to buy (in wei/smallest unit)
            chain_id: Blockchain ID
            nonce: Unique nonce to prevent replay attacks
            expiry_seconds: Message expiry in seconds from now

        Returns:
            EIP-712 message and domain objects
        """
        expiry = int(
            (datetime.utcnow() + timedelta(seconds=expiry_seconds)).timestamp()
        )

        message = {
            "sellToken": (
                to_checksum_address(sell_token)
                if ETH_ACCOUNT_AVAILABLE and is_address(sell_token)
                else sell_token
            ),
            "buyToken": (
                to_checksum_address(buy_token)
                if ETH_ACCOUNT_AVAILABLE and is_address(buy_token)
                else buy_token
            ),
            "sellAmount": str(sell_amount),
            "buyAmount": str(buy_amount),
            "chainId": chain_id,
            "nonce": nonce,
            "expiry": expiry,
        }

        domain = {
            "name": "CryptoOrchestrator",
            "version": "1",
            "chainId": chain_id,
            "verifyingContract": "0x0000000000000000000000000000000000000000",  # Placeholder
        }

        return {
            "message": message,
            "domain": domain,
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "TradeRequest": [
                    {"name": "sellToken", "type": "address"},
                    {"name": "buyToken", "type": "address"},
                    {"name": "sellAmount", "type": "uint256"},
                    {"name": "buyAmount", "type": "uint256"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "nonce", "type": "uint256"},
                    {"name": "expiry", "type": "uint256"},
                ],
            },
            "primaryType": "TradeRequest",
        }

    async def generate_nonce(
        self,
        user_id: int,
        wallet_address: str,
        chain_id: int = 1,
        message_type: str = "trade",
        db: AsyncSession | None = None,
    ) -> int:
        """
        Generate and store a unique nonce for a trade request

        Args:
            user_id: User ID
            wallet_address: Wallet address (checksummed)
            chain_id: Blockchain ID
            message_type: Type of message ('trade', 'withdrawal', etc.)
            db: Database session (optional, if None uses timestamp-based nonce)

        Returns:
            Unique nonce
        """
        if not db:
            # Fallback to timestamp-based nonce if no database
            timestamp = int(datetime.utcnow().timestamp() * 1000)
            nonce_string = f"{user_id}:{wallet_address}:{timestamp}"
            nonce_hash = hashlib.sha256(nonce_string.encode()).hexdigest()
            # Use first 8 bytes of hash as nonce (uint64)
            nonce = int(nonce_hash[:16], 16)
            return nonce

        try:
            # Get the highest nonce for this wallet/chain combination
            stmt = (
                select(WalletNonce.nonce)
                .where(WalletNonce.wallet_address == wallet_address)
                .where(WalletNonce.chain_id == chain_id)
                .order_by(WalletNonce.nonce.desc())
                .limit(1)
            )
            result = await db.execute(stmt)
            last_nonce = result.scalar()

            # Generate next nonce (increment from last or start at timestamp)
            if last_nonce:
                nonce = last_nonce + 1
            else:
                # Start with timestamp-based nonce
                timestamp = int(datetime.utcnow().timestamp())
                nonce = timestamp

            # Create nonce record
            expires_at = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
            nonce_record = WalletNonce(
                user_id=user_id,
                wallet_address=wallet_address,
                nonce=nonce,
                chain_id=chain_id,
                message_type=message_type,
                expires_at=expires_at,
                used=False,
            )
            db.add(nonce_record)
            await db.commit()
            await db.refresh(nonce_record)

            logger.debug(
                f"Generated nonce {nonce} for wallet {wallet_address}",
                extra={
                    "user_id": user_id,
                    "wallet_address": wallet_address,
                    "nonce": nonce,
                    "chain_id": chain_id,
                },
            )

            return nonce

        except Exception as e:
            logger.error(f"Error generating nonce: {e}", exc_info=True)
            await db.rollback()
            # Fallback to timestamp-based nonce
            timestamp = int(datetime.utcnow().timestamp() * 1000)
            nonce_string = f"{user_id}:{wallet_address}:{timestamp}"
            nonce_hash = hashlib.sha256(nonce_string.encode()).hexdigest()
            nonce = int(nonce_hash[:16], 16)
            return nonce

    async def verify_and_mark_nonce_used(
        self,
        wallet_address: str,
        nonce: int,
        chain_id: int = 1,
        message_hash: str | None = None,
        db: AsyncSession | None = None,
    ) -> bool:
        """
        Verify nonce is valid and mark it as used

        Args:
            wallet_address: Wallet address
            nonce: Nonce to verify
            chain_id: Blockchain ID
            message_hash: Optional message hash for tracking
            db: Database session

        Returns:
            True if nonce is valid and was marked as used, False otherwise
        """
        if not db:
            # Without database, can't verify nonce reuse
            return True

        try:
            # Find nonce record
            stmt = select(WalletNonce).where(
                WalletNonce.wallet_address == wallet_address,
                WalletNonce.nonce == nonce,
                WalletNonce.chain_id == chain_id,
            )
            result = await db.execute(stmt)
            nonce_record = result.scalar_one_or_none()

            if not nonce_record:
                logger.warning(
                    f"Nonce {nonce} not found for wallet {wallet_address}",
                    extra={
                        "wallet_address": wallet_address,
                        "nonce": nonce,
                        "chain_id": chain_id,
                    },
                )
                return False

            # Check if already used
            if nonce_record.used:
                logger.warning(
                    f"Nonce {nonce} already used for wallet {wallet_address}",
                    extra={"wallet_address": wallet_address, "nonce": nonce},
                )
                return False

            # Check if expired
            if nonce_record.is_expired():
                logger.warning(
                    f"Nonce {nonce} expired for wallet {wallet_address}",
                    extra={"wallet_address": wallet_address, "nonce": nonce},
                )
                return False

            # Mark as used
            nonce_record.used = True
            nonce_record.used_at = datetime.utcnow()
            if message_hash:
                nonce_record.message_hash = message_hash

            await db.commit()

            logger.info(
                f"Nonce {nonce} marked as used for wallet {wallet_address}",
                extra={"wallet_address": wallet_address, "nonce": nonce},
            )

            return True

        except Exception as e:
            logger.error(f"Error verifying nonce: {e}", exc_info=True)
            await db.rollback()
            return False

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
