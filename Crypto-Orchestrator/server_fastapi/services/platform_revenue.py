"""
Platform Revenue Service
Tracks platform revenue from deposit fees and other sources
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ..models.wallet import WalletTransaction, TransactionStatus

logger = logging.getLogger(__name__)


class PlatformRevenueService:
    """Service for tracking platform revenue"""

    def __init__(self):
        self.deposit_fee_rate = Decimal("0.05")  # 5% deposit fee

    async def get_total_revenue(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Get total platform revenue from deposit fees

        Returns:
            Dict with revenue statistics
        """
        if db is None:
            from ..database import get_db_context

            async with get_db_context() as session:
                return await self._get_total_revenue_internal(
                    start_date, end_date, session
                )
        else:
            return await self._get_total_revenue_internal(start_date, end_date, db)

    async def _get_total_revenue_internal(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Internal revenue calculation"""
        try:
            # Build query conditions
            conditions = [
                WalletTransaction.transaction_type == "deposit",
                WalletTransaction.status == TransactionStatus.COMPLETED.value,
                WalletTransaction.fee > 0,
            ]

            if start_date:
                conditions.append(WalletTransaction.created_at >= start_date)
            if end_date:
                conditions.append(WalletTransaction.created_at <= end_date)

            # Get total fees collected
            fees_result = await db.execute(
                select(func.sum(WalletTransaction.fee)).where(and_(*conditions))
            )
            total_fees = fees_result.scalar() or Decimal("0")

            # Get total deposits (before fees)
            deposits_result = await db.execute(
                select(func.sum(WalletTransaction.amount)).where(and_(*conditions))
            )
            total_deposits = deposits_result.scalar() or Decimal("0")

            # Get transaction count
            count_result = await db.execute(
                select(func.count(WalletTransaction.id)).where(and_(*conditions))
            )
            transaction_count = count_result.scalar() or 0

            # Calculate average fee
            avg_fee = (
                total_fees / transaction_count
                if transaction_count > 0
                else Decimal("0")
            )

            return {
                "total_revenue": float(total_fees),
                "total_deposits": float(total_deposits),
                "transaction_count": transaction_count,
                "average_fee": float(avg_fee),
                "fee_rate": float(self.deposit_fee_rate),
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            }
        except Exception as e:
            logger.error(f"Error calculating total revenue: {e}", exc_info=True)
            return {
                "total_revenue": 0.0,
                "total_deposits": 0.0,
                "transaction_count": 0,
                "average_fee": 0.0,
                "fee_rate": float(self.deposit_fee_rate),
                "error": str(e),
            }

    async def get_daily_revenue(
        self, days: int = 30, db: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """
        Get daily revenue breakdown

        Args:
            days: Number of days to retrieve

        Returns:
            List of daily revenue records
        """
        if db is None:
            from ..database import get_db_context

            async with get_db_context() as session:
                return await self._get_daily_revenue_internal(days, session)
        else:
            return await self._get_daily_revenue_internal(days, db)

    async def _get_daily_revenue_internal(
        self, days: int, db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Internal daily revenue calculation"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            # Get daily revenue grouped by date
            daily_result = await db.execute(
                select(
                    func.date(WalletTransaction.created_at).label("date"),
                    func.sum(WalletTransaction.fee).label("daily_fees"),
                    func.sum(WalletTransaction.amount).label("daily_deposits"),
                    func.count(WalletTransaction.id).label("transaction_count"),
                )
                .where(
                    and_(
                        WalletTransaction.transaction_type == "deposit",
                        WalletTransaction.status == TransactionStatus.COMPLETED.value,
                        WalletTransaction.fee > 0,
                        WalletTransaction.created_at >= start_date,
                    )
                )
                .group_by(func.date(WalletTransaction.created_at))
                .order_by(func.date(WalletTransaction.created_at).desc())
            )

            daily_records = daily_result.all()

            return [
                {
                    "date": (
                        record.date.isoformat()
                        if hasattr(record.date, "isoformat")
                        else str(record.date)
                    ),
                    "revenue": float(record.daily_fees or 0),
                    "total_deposits": float(record.daily_deposits or 0),
                    "transaction_count": record.transaction_count or 0,
                }
                for record in daily_records
            ]
        except Exception as e:
            logger.error(f"Error calculating daily revenue: {e}", exc_info=True)
            return []


# Global instance
platform_revenue_service = PlatformRevenueService()
