"""
Trading Fee Service
Calculates and tracks trading fees for DEX trades
Implements tier-based fee structure
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class TradingFeeService:
    """Service for calculating and tracking trading fees"""

    # Fee tiers (in basis points)
    FREE_TIER_FEE_BPS = 30  # 0.3%
    BASIC_TIER_FEE_BPS = 25  # 0.25%
    PRO_TIER_FEE_BPS = 20  # 0.2%
    ENTERPRISE_TIER_FEE_BPS = 15  # 0.15%

    # Volume discount thresholds (monthly volume in USD)
    VOLUME_DISCOUNT_THRESHOLDS = {
        100000: 5,  # $100k/month = 5 bps discount
        500000: 10,  # $500k/month = 10 bps discount
        1000000: 15,  # $1M/month = 15 bps discount
        5000000: 20,  # $5M/month = 20 bps discount
    }

    def __init__(self):
        pass

    def calculate_fee(
        self,
        trade_amount: Decimal,
        user_tier: str = "free",
        is_custodial: bool = True,
        monthly_volume: Decimal | None = None,
    ) -> Decimal:
        """
        Calculate trading fee for a trade

        Args:
            trade_amount: Trade amount (in token units)
            user_tier: User subscription tier ("free", "basic", "pro", "enterprise")
            is_custodial: Whether trade is custodial (True) or non-custodial (False)
            monthly_volume: User's monthly trading volume in USD (for volume discounts)

        Returns:
            Fee amount in token units
        """
        # Base fee based on tier
        if user_tier == "free":
            base_fee_bps = self.FREE_TIER_FEE_BPS
        elif user_tier == "basic":
            base_fee_bps = self.BASIC_TIER_FEE_BPS
        elif user_tier == "pro":
            base_fee_bps = self.PRO_TIER_FEE_BPS
        elif user_tier == "enterprise":
            base_fee_bps = self.ENTERPRISE_TIER_FEE_BPS
        else:
            # Default to free tier
            base_fee_bps = self.FREE_TIER_FEE_BPS

        # Adjust for custodial vs non-custodial
        if not is_custodial:
            # Non-custodial gets 5 bps discount
            base_fee_bps = max(10, base_fee_bps - 5)

        # Apply volume discount if applicable
        if monthly_volume:
            discount_bps = self._get_volume_discount(monthly_volume)
            base_fee_bps = max(5, base_fee_bps - discount_bps)  # Minimum 0.05%

        # Calculate fee
        fee_bps = Decimal(base_fee_bps)
        fee_amount = trade_amount * fee_bps / Decimal(10000)

        logger.debug(
            f"Fee calculated: {fee_amount} ({base_fee_bps} bps) for {trade_amount}",
            extra={
                "trade_amount": str(trade_amount),
                "fee_amount": str(fee_amount),
                "fee_bps": base_fee_bps,
                "user_tier": user_tier,
                "is_custodial": is_custodial,
                "monthly_volume": str(monthly_volume) if monthly_volume else None,
            },
        )

        return fee_amount

    def _get_volume_discount(self, monthly_volume: Decimal) -> int:
        """
        Get volume discount in basis points

        Args:
            monthly_volume: Monthly trading volume in USD

        Returns:
            Discount in basis points
        """
        # Sort thresholds in descending order
        sorted_thresholds = sorted(
            self.VOLUME_DISCOUNT_THRESHOLDS.items(), reverse=True
        )

        for threshold, discount_bps in sorted_thresholds:
            if monthly_volume >= Decimal(threshold):
                return discount_bps

        return 0

    async def get_user_monthly_volume(
        self, user_id: str, db: AsyncSession, month: datetime | None = None
    ) -> Decimal:
        """
        Get user's monthly trading volume in USD

        Args:
            user_id: User ID
            db: Database session
            month: Month to calculate volume for (default: current month)

        Returns:
            Monthly volume in USD
        """
        if not month:
            month = datetime.utcnow().replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )

        # Calculate end of month
        if month.month == 12:
            next_month = month.replace(year=month.year + 1, month=1)
        else:
            next_month = month.replace(month=month.month + 1)

        try:
            # Query both CEX trades and DEX trades for monthly volume
            from ...models.dex_trade import DEXTrade
            from ...models.trade import Trade

            # Get CEX trade volume
            cex_stmt = (
                select(func.sum(Trade.cost))
                .where(Trade.user_id == int(user_id))
                .where(Trade.executed_at >= month)
                .where(Trade.executed_at < next_month)
                .where(Trade.status == "completed")
                .where(Trade.mode == "real")
            )
            cex_result = await db.execute(cex_stmt)
            cex_volume = cex_result.scalar() or Decimal(0)

            # Get DEX trade volume (using sell_amount_decimal as approximation)
            # Note: For accurate USD volume, would need token price conversion
            dex_stmt = (
                select(func.sum(DEXTrade.sell_amount_decimal))
                .where(DEXTrade.user_id == int(user_id))
                .where(DEXTrade.executed_at >= month)
                .where(DEXTrade.executed_at < next_month)
                .where(DEXTrade.status == "completed")
            )
            dex_result = await db.execute(dex_stmt)
            dex_volume = dex_result.scalar() or Decimal(0)

            # Combine volumes (approximation - in production, convert to USD)
            volume = cex_volume + dex_volume

            logger.debug(
                f"Monthly volume for user {user_id}: {volume} USD",
                extra={
                    "user_id": user_id,
                    "month": month.isoformat(),
                    "volume": str(volume),
                },
            )

            return volume

        except Exception as e:
            logger.error(f"Error getting monthly volume: {e}", exc_info=True)
            return Decimal(0)

    def get_fee_structure(self) -> dict[str, Any]:
        """
        Get current fee structure for display

        Returns:
            Fee structure information
        """
        return {
            "tiers": {
                "free": {
                    "fee_bps": self.FREE_TIER_FEE_BPS,
                    "fee_percent": self.FREE_TIER_FEE_BPS / 100,
                },
                "basic": {
                    "fee_bps": self.BASIC_TIER_FEE_BPS,
                    "fee_percent": self.BASIC_TIER_FEE_BPS / 100,
                },
                "pro": {
                    "fee_bps": self.PRO_TIER_FEE_BPS,
                    "fee_percent": self.PRO_TIER_FEE_BPS / 100,
                },
                "enterprise": {
                    "fee_bps": self.ENTERPRISE_TIER_FEE_BPS,
                    "fee_percent": self.ENTERPRISE_TIER_FEE_BPS / 100,
                },
            },
            "custodial": {
                "fee_bps": 20,  # 0.2% default
                "fee_percent": 0.2,
            },
            "non_custodial": {
                "fee_bps": 15,  # 0.15% default
                "fee_percent": 0.15,
            },
            "volume_discounts": {
                f"${threshold:,}": f"{discount_bps / 100}% discount"
                for threshold, discount_bps in self.VOLUME_DISCOUNT_THRESHOLDS.items()
            },
        }
