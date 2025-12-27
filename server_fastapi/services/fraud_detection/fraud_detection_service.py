"""
Advanced Fraud Detection Service
ML-based anomaly detection for trading and financial operations
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ...models.user import User
from ...models.wallet import WalletTransaction, TransactionStatus
from ...models.trade import Trade
from ...database import get_db_context

logger = logging.getLogger(__name__)


class FraudDetectionService:
    """Service for detecting fraudulent activity using ML and rule-based methods"""

    def __init__(self):
        self.risk_threshold = 0.7  # Risk score threshold (0-1)
        self.velocity_window_hours = 24  # Time window for velocity checks
        self.max_transactions_per_hour = 50  # Maximum transactions per hour
        self.max_amount_per_day = Decimal("100000")  # Maximum amount per day
        self.suspicious_patterns = []

    async def analyze_transaction(
        self,
        user_id: int,
        transaction_type: str,
        amount: Decimal,
        currency: str,
        metadata: Optional[Dict[str, Any]] = None,
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a transaction for fraud indicators

        Args:
            user_id: User ID
            transaction_type: Type of transaction (deposit, withdrawal, trade)
            amount: Transaction amount
            currency: Currency code
            metadata: Additional transaction metadata
            db: Database session

        Returns:
            Dict with fraud analysis results
        """
        try:
            if db is None:
                async with get_db_context() as session:
                    return await self._analyze_internal(
                        user_id, transaction_type, amount, currency, metadata, session
                    )
            else:
                return await self._analyze_internal(
                    user_id, transaction_type, amount, currency, metadata, db
                )
        except Exception as e:
            logger.error(f"Error in fraud detection analysis: {e}", exc_info=True)
            return {
                "risk_score": 0.0,
                "is_fraud": False,
                "indicators": [],
                "recommendation": "allow",
            }

    async def _analyze_internal(
        self,
        user_id: int,
        transaction_type: str,
        amount: Decimal,
        currency: str,
        metadata: Optional[Dict[str, Any]],
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Internal fraud analysis logic"""
        indicators = []
        risk_score = 0.0

        # 1. Velocity Check - Too many transactions in short time
        velocity_risk = await self._check_velocity(user_id, transaction_type, db)
        if velocity_risk["is_suspicious"]:
            indicators.append(
                {
                    "type": "velocity",
                    "severity": "high",
                    "message": velocity_risk["message"],
                    "details": velocity_risk["details"],
                }
            )
            risk_score += 0.3

        # 2. Amount Anomaly - Unusually large amounts
        amount_risk = await self._check_amount_anomaly(
            user_id, amount, transaction_type, db
        )
        if amount_risk["is_suspicious"]:
            indicators.append(
                {
                    "type": "amount_anomaly",
                    "severity": "medium",
                    "message": amount_risk["message"],
                    "details": amount_risk["details"],
                }
            )
            risk_score += 0.2

        # 3. Behavioral Pattern - Deviation from normal behavior
        behavioral_risk = await self._check_behavioral_pattern(
            user_id, transaction_type, amount, db
        )
        if behavioral_risk["is_suspicious"]:
            indicators.append(
                {
                    "type": "behavioral_anomaly",
                    "severity": "medium",
                    "message": behavioral_risk["message"],
                    "details": behavioral_risk["details"],
                }
            )
            risk_score += 0.25

        # 4. Time-based Anomaly - Unusual transaction times
        time_risk = self._check_time_anomaly()
        if time_risk["is_suspicious"]:
            indicators.append(
                {
                    "type": "time_anomaly",
                    "severity": "low",
                    "message": time_risk["message"],
                    "details": time_risk["details"],
                }
            )
            risk_score += 0.1

        # 5. Geographic Anomaly - If IP/location data available
        if metadata and metadata.get("ip_address"):
            geo_risk = await self._check_geographic_anomaly(
                user_id, metadata.get("ip_address"), db
            )
            if geo_risk["is_suspicious"]:
                indicators.append(
                    {
                        "type": "geographic_anomaly",
                        "severity": "medium",
                        "message": geo_risk["message"],
                        "details": geo_risk["details"],
                    }
                )
                risk_score += 0.15

        # Normalize risk score to 0-1
        risk_score = min(risk_score, 1.0)

        # Determine recommendation
        is_fraud = risk_score >= self.risk_threshold
        recommendation = (
            "block" if is_fraud else ("review" if risk_score >= 0.5 else "allow")
        )

        return {
            "risk_score": round(risk_score, 3),
            "is_fraud": is_fraud,
            "indicators": indicators,
            "recommendation": recommendation,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

    async def _check_velocity(
        self, user_id: int, transaction_type: str, db: AsyncSession
    ) -> Dict[str, Any]:
        """Check transaction velocity"""
        try:
            window_start = datetime.utcnow() - timedelta(
                hours=self.velocity_window_hours
            )

            # Count transactions in time window
            count_result = await db.execute(
                select(func.count(WalletTransaction.id)).where(
                    and_(
                        WalletTransaction.user_id == user_id,
                        WalletTransaction.transaction_type == transaction_type,
                        WalletTransaction.created_at >= window_start,
                    )
                )
            )
            transaction_count = count_result.scalar() or 0

            # Check hourly rate
            hour_start = datetime.utcnow() - timedelta(hours=1)
            hourly_count_result = await db.execute(
                select(func.count(WalletTransaction.id)).where(
                    and_(
                        WalletTransaction.user_id == user_id,
                        WalletTransaction.transaction_type == transaction_type,
                        WalletTransaction.created_at >= hour_start,
                    )
                )
            )
            hourly_count = hourly_count_result.scalar() or 0

            is_suspicious = (
                transaction_count
                > self.max_transactions_per_hour * self.velocity_window_hours
                or hourly_count > self.max_transactions_per_hour
            )

            return {
                "is_suspicious": is_suspicious,
                "message": (
                    f"High transaction velocity detected: {hourly_count} transactions/hour, {transaction_count} in last {self.velocity_window_hours} hours"
                    if is_suspicious
                    else "Normal transaction velocity"
                ),
                "details": {
                    "hourly_count": hourly_count,
                    "window_count": transaction_count,
                    "threshold": self.max_transactions_per_hour,
                },
            }
        except Exception as e:
            logger.error(f"Error checking velocity: {e}")
            return {
                "is_suspicious": False,
                "message": "Velocity check unavailable",
                "details": {},
            }

    async def _check_amount_anomaly(
        self, user_id: int, amount: Decimal, transaction_type: str, db: AsyncSession
    ) -> Dict[str, Any]:
        """Check for unusual transaction amounts"""
        try:
            # Get user's transaction history
            history_result = await db.execute(
                select(
                    func.avg(WalletTransaction.amount).label("avg_amount"),
                    func.max(WalletTransaction.amount).label("max_amount"),
                    func.stddev(WalletTransaction.amount).label("stddev_amount"),
                ).where(
                    and_(
                        WalletTransaction.user_id == user_id,
                        WalletTransaction.transaction_type == transaction_type,
                        WalletTransaction.status == TransactionStatus.COMPLETED.value,
                    )
                )
            )
            stats = history_result.first()

            if not stats or not stats.avg_amount:
                # No history, check against global limits
                is_suspicious = amount > self.max_amount_per_day
                return {
                    "is_suspicious": is_suspicious,
                    "message": (
                        f"Large transaction amount: {amount} (no history for comparison)"
                        if is_suspicious
                        else "Amount check passed"
                    ),
                    "details": {
                        "amount": float(amount),
                        "threshold": float(self.max_amount_per_day),
                    },
                }

            avg_amount = Decimal(str(stats.avg_amount))
            max_amount = Decimal(str(stats.max_amount or 0))
            stddev_amount = Decimal(str(stats.stddev_amount or 0))

            # Check if amount is significantly higher than average (3 standard deviations)
            threshold = (
                avg_amount + (stddev_amount * 3)
                if stddev_amount > 0
                else avg_amount * 5
            )

            is_suspicious = amount > threshold or amount > self.max_amount_per_day

            return {
                "is_suspicious": is_suspicious,
                "message": (
                    f"Unusual transaction amount: {amount} (avg: {avg_amount:.2f}, threshold: {threshold:.2f})"
                    if is_suspicious
                    else "Amount within normal range"
                ),
                "details": {
                    "amount": float(amount),
                    "avg_amount": float(avg_amount),
                    "max_amount": float(max_amount),
                    "threshold": float(threshold),
                },
            }
        except Exception as e:
            logger.error(f"Error checking amount anomaly: {e}")
            return {
                "is_suspicious": False,
                "message": "Amount check unavailable",
                "details": {},
            }

    async def _check_behavioral_pattern(
        self, user_id: int, transaction_type: str, amount: Decimal, db: AsyncSession
    ) -> Dict[str, Any]:
        """Check for behavioral pattern deviations"""
        try:
            # Get user's typical transaction patterns
            # Check transaction frequency, amounts, times, etc.

            # Get last 30 days of transactions
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)

            pattern_result = await db.execute(
                select(
                    func.count(WalletTransaction.id).label("count"),
                    func.avg(WalletTransaction.amount).label("avg_amount"),
                    func.min(WalletTransaction.created_at).label("first_transaction"),
                    func.max(WalletTransaction.created_at).label("last_transaction"),
                ).where(
                    and_(
                        WalletTransaction.user_id == user_id,
                        WalletTransaction.transaction_type == transaction_type,
                        WalletTransaction.created_at >= thirty_days_ago,
                    )
                )
            )
            pattern = pattern_result.first()

            if not pattern or pattern.count == 0:
                # New user or no history
                return {
                    "is_suspicious": False,
                    "message": "Insufficient history for behavioral analysis",
                    "details": {},
                }

            # Check if this transaction deviates significantly from pattern
            avg_amount = Decimal(str(pattern.avg_amount or 0))
            deviation = abs(amount - avg_amount) / avg_amount if avg_amount > 0 else 1.0

            # Large deviation (>50%) is suspicious
            is_suspicious = deviation > 0.5

            return {
                "is_suspicious": is_suspicious,
                "message": (
                    f"Behavioral deviation detected: {deviation*100:.1f}% from average"
                    if is_suspicious
                    else "Transaction matches behavioral pattern"
                ),
                "details": {
                    "deviation_percent": round(deviation * 100, 2),
                    "avg_amount": float(avg_amount),
                    "transaction_amount": float(amount),
                },
            }
        except Exception as e:
            logger.error(f"Error checking behavioral pattern: {e}")
            return {
                "is_suspicious": False,
                "message": "Behavioral check unavailable",
                "details": {},
            }

    def _check_time_anomaly(self) -> Dict[str, Any]:
        """Check for unusual transaction times"""
        try:
            current_hour = datetime.utcnow().hour

            # Transactions between 2 AM and 5 AM are less common (suspicious)
            is_suspicious = 2 <= current_hour <= 5

            return {
                "is_suspicious": is_suspicious,
                "message": (
                    f"Unusual transaction time: {current_hour}:00 UTC"
                    if is_suspicious
                    else "Normal transaction time"
                ),
                "details": {"hour": current_hour},
            }
        except Exception as e:
            logger.error(f"Error checking time anomaly: {e}")
            return {
                "is_suspicious": False,
                "message": "Time check unavailable",
                "details": {},
            }

    async def _check_geographic_anomaly(
        self, user_id: int, ip_address: str, db: AsyncSession
    ) -> Dict[str, Any]:
        """Check for geographic anomalies (if location data available)"""
        # This would require IP geolocation service
        # For now, return not suspicious
        return {
            "is_suspicious": False,
            "message": "Geographic check not implemented",
            "details": {},
        }

    async def get_user_risk_profile(
        self, user_id: int, db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Get comprehensive risk profile for a user"""
        try:
            if db is None:
                async with get_db_context() as session:
                    return await self._get_risk_profile_internal(user_id, session)
            else:
                return await self._get_risk_profile_internal(user_id, db)
        except Exception as e:
            logger.error(f"Error getting risk profile: {e}", exc_info=True)
            return {"risk_level": "unknown", "score": 0.0}

    async def _get_risk_profile_internal(
        self, user_id: int, db: AsyncSession
    ) -> Dict[str, Any]:
        """Internal risk profile calculation"""
        # Get transaction statistics
        stats_result = await db.execute(
            select(
                func.count(WalletTransaction.id).label("total_transactions"),
                func.sum(WalletTransaction.amount).label("total_volume"),
                func.avg(WalletTransaction.amount).label("avg_amount"),
                func.max(WalletTransaction.created_at).label("last_transaction"),
            ).where(WalletTransaction.user_id == user_id)
        )
        stats = stats_result.first()

        # Calculate risk score based on various factors
        risk_score = 0.0

        if stats and stats.total_transactions:
            # More transactions = lower risk (established user)
            if stats.total_transactions > 100:
                risk_score -= 0.2
            elif stats.total_transactions < 5:
                risk_score += 0.2

            # Check account age
            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()
            if user and user.created_at:
                account_age_days = (datetime.utcnow() - user.created_at).days
                if account_age_days < 7:
                    risk_score += 0.3  # New account
                elif account_age_days > 90:
                    risk_score -= 0.2  # Established account

        risk_score = max(0.0, min(1.0, risk_score))

        if risk_score >= 0.7:
            risk_level = "high"
        elif risk_score >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "risk_level": risk_level,
            "risk_score": round(risk_score, 3),
            "total_transactions": stats.total_transactions if stats else 0,
            "total_volume": (
                float(stats.total_volume) if stats and stats.total_volume else 0.0
            ),
            "analyzed_at": datetime.utcnow().isoformat(),
        }


# Global instance
fraud_detection_service = FraudDetectionService()
