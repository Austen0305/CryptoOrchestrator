"""
Crypto-Only Subscription Service
Monitors blockchain payments and automatically activates subscriptions
100% free - no payment processor fees
"""

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.subscription import Subscription
from ..blockchain.token_registry import get_token_registry
from ..blockchain.transaction_service import TransactionService

logger = logging.getLogger(__name__)


class CryptoSubscriptionService:
    """Service for managing crypto-based subscriptions"""

    # Subscription prices in USD (converted to crypto at payment time)
    SUBSCRIPTION_PRICES_USD = {
        "free": 0,
        "basic": 49.00,  # $49/month
        "pro": 99.00,  # $99/month
        "enterprise": 299.00,  # $299/month
    }

    # Supported payment tokens (addresses for each chain)
    SUPPORTED_TOKENS = {
        1: {  # Ethereum
            "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
            "ETH": "0x0000000000000000000000000000000000000000",  # Native ETH
        },
        8453: {  # Base
            "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            "ETH": "0x0000000000000000000000000000000000000000",
        },
        42161: {  # Arbitrum
            "USDC": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
            "ETH": "0x0000000000000000000000000000000000000000",
        },
        137: {  # Polygon
            "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
            "MATIC": "0x0000000000000000000000000000000000000000",
        },
    }

    def __init__(self):
        self.transaction_service = TransactionService()
        self.token_registry = get_token_registry()

    async def get_subscription_payment_address(
        self, user_id: int, chain_id: int = 1
    ) -> dict[str, Any] | None:
        """
        Get a unique payment address for user's subscription payments

        Args:
            user_id: User ID
            chain_id: Blockchain ID

        Returns:
            Payment address info or None
        """
        # In a real implementation, you would:
        # 1. Generate a unique payment address per user (could be a smart contract or EOA)
        # 2. Store the mapping in database
        # 3. Monitor this address for incoming payments

        # For now, return a placeholder - in production, this would be a real address
        # You could use a smart contract that routes payments to your main wallet
        # and emits events with user_id metadata

        return {
            "address": "0x0000000000000000000000000000000000000000",  # Placeholder
            "chain_id": chain_id,
            "message": f"Send payment to this address for user {user_id}",
            "supported_tokens": self.SUPPORTED_TOKENS.get(chain_id, {}),
        }

    async def calculate_payment_amount(
        self,
        tier: str,
        token_symbol: str,
        chain_id: int = 1,
    ) -> dict[str, Any] | None:
        """
        Calculate payment amount in crypto for a subscription tier

        Args:
            tier: Subscription tier (basic, pro, enterprise)
            token_symbol: Token symbol (USDC, USDT, ETH, etc.)
            chain_id: Blockchain ID

        Returns:
            Payment amount info or None
        """
        if tier not in self.SUBSCRIPTION_PRICES_USD:
            return None

        usd_price = self.SUBSCRIPTION_PRICES_USD[tier]
        if usd_price == 0:
            return {"amount": "0", "currency": token_symbol, "usd_equivalent": 0}

        # Get token price in USD
        # In production, use a price oracle (Market Data Service, etc.)
        token_price_usd = await self._get_token_price_usd(token_symbol)

        if not token_price_usd:
            return None

        # Calculate amount needed
        token_amount = Decimal(usd_price) / Decimal(token_price_usd)

        # Get token decimals
        token_address = self.SUPPORTED_TOKENS.get(chain_id, {}).get(token_symbol)
        if not token_address:
            return None

        decimals = await self.token_registry.get_token_decimals(token_address, chain_id)
        if decimals is None:
            decimals = 18  # Default

        # Convert to token units
        amount_wei = int(token_amount * Decimal(10**decimals))

        return {
            "amount": str(amount_wei),
            "amount_human": str(token_amount),
            "currency": token_symbol,
            "usd_equivalent": usd_price,
            "chain_id": chain_id,
            "token_address": token_address,
        }

    async def verify_payment(
        self,
        user_id: int,
        transaction_hash: str,
        chain_id: int = 1,
    ) -> dict[str, Any] | None:
        """
        Verify a payment transaction and activate subscription

        Args:
            user_id: User ID
            transaction_hash: Transaction hash
            chain_id: Blockchain ID

        Returns:
            Verification result or None
        """
        try:
            # Get transaction receipt
            receipt = await self.transaction_service.get_transaction_receipt(
                chain_id, transaction_hash
            )

            if not receipt:
                return None

            # Check if transaction is confirmed
            if receipt.get("status") != 1:  # 1 = success
                return None

            # Extract payment details from transaction
            # In production, you would:
            # 1. Parse transaction logs for payment events
            # 2. Verify amount matches subscription price
            # 3. Verify token is supported
            # 4. Check payment address matches user

            # For now, return a placeholder verification
            return {
                "verified": True,
                "transaction_hash": transaction_hash,
                "chain_id": chain_id,
                "block_number": receipt.get("blockNumber"),
                "timestamp": datetime.now(UTC),
            }

        except Exception as e:
            logger.error(f"Error verifying payment: {e}", exc_info=True)
            return None

    async def activate_subscription_from_payment(
        self,
        db: AsyncSession,
        user_id: int,
        tier: str,
        transaction_hash: str,
        chain_id: int = 1,
    ) -> Subscription | None:
        """
        Activate subscription after payment verification

        Args:
            db: Database session
            user_id: User ID
            tier: Subscription tier
            transaction_hash: Payment transaction hash
            chain_id: Blockchain ID

        Returns:
            Updated subscription or None
        """
        try:
            # Verify payment first
            verification = await self.verify_payment(
                user_id, transaction_hash, chain_id
            )
            if not verification or not verification.get("verified"):
                logger.warning(f"Payment verification failed for user {user_id}")
                return None

            # Get or create subscription
            result = await db.execute(
                select(Subscription).where(Subscription.user_id == user_id)
            )
            subscription = result.scalar_one_or_none()

            if not subscription:
                subscription = Subscription(
                    user_id=user_id,
                    plan=tier,
                    status="active",
                    current_period_start=datetime.now(UTC),
                    current_period_end=datetime.now(UTC) + timedelta(days=30),
                )
                db.add(subscription)
            else:
                subscription.plan = tier
                subscription.status = "active"
                subscription.current_period_start = datetime.now(UTC)
                subscription.current_period_end = datetime.now(UTC) + timedelta(days=30)

            # Store payment info (you might want a separate payments table)
            subscription.metadata = subscription.metadata or {}
            subscription.metadata["last_payment"] = {
                "transaction_hash": transaction_hash,
                "chain_id": chain_id,
                "timestamp": datetime.now(UTC).isoformat(),
            }

            await db.commit()
            await db.refresh(subscription)

            logger.info(
                f"Activated {tier} subscription for user {user_id} via crypto payment"
            )

            return subscription

        except Exception as e:
            logger.error(f"Error activating subscription: {e}", exc_info=True)
            await db.rollback()
            return None

    async def check_subscription_status(
        self, db: AsyncSession, user_id: int
    ) -> dict[str, Any]:
        """
        Check subscription status and payment requirements

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Subscription status info
        """
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            return {
                "has_subscription": False,
                "tier": "free",
                "status": "inactive",
                "needs_payment": False,
            }

        now = datetime.now(UTC)
        is_active = (
            subscription.status == "active"
            and subscription.current_period_end
            and subscription.current_period_end > now
        )

        needs_payment = (
            subscription.status != "active"
            or not subscription.current_period_end
            or subscription.current_period_end <= now
        )

        return {
            "has_subscription": True,
            "tier": subscription.plan,
            "status": subscription.status if is_active else "expired",
            "current_period_end": (
                subscription.current_period_end.isoformat()
                if subscription.current_period_end
                else None
            ),
            "needs_payment": needs_payment,
            "days_remaining": (
                (subscription.current_period_end - now).days
                if subscription.current_period_end and is_active
                else 0
            ),
        }

    async def _get_token_price_usd(self, token_symbol: str) -> float | None:
        """
        Get token price in USD (simplified - use price oracle in production)

        Args:
            token_symbol: Token symbol

        Returns:
            Price in USD or None
        """
        # In production, use Market Data Service or another price oracle
        # For now, return placeholder prices
        prices = {
            "USDC": 1.0,
            "USDT": 1.0,
            "DAI": 1.0,
            "ETH": 2500.0,  # Placeholder
            "MATIC": 0.8,  # Placeholder
        }

        return prices.get(token_symbol.upper())
