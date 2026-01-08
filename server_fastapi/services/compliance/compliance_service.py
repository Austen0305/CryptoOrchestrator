"""
Compliance Service for Real Money Trading
Handles regulatory compliance, KYC checks, transaction monitoring, and reporting
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any

from ..kyc_service import kyc_service

logger = logging.getLogger(__name__)


class ComplianceCheckResult(str, Enum):
    """Compliance check result"""

    APPROVED = "approved"
    REQUIRES_KYC = "requires_kyc"
    REQUIRES_REVIEW = "requires_review"
    REJECTED = "rejected"
    BLOCKED = "blocked"


class ComplianceService:
    """Service for regulatory compliance and transaction monitoring"""

    # Regulatory thresholds (configurable)
    KYC_THRESHOLD_USD = 10000.0  # Require KYC for trades over $10,000
    LARGE_TRANSACTION_THRESHOLD_USD = 50000.0  # Flag for review
    DAILY_LIMIT_WITHOUT_KYC_USD = 50000.0  # Daily limit without KYC
    SUSPICIOUS_ACTIVITY_THRESHOLD = 100000.0  # Flag for suspicious activity monitoring

    def __init__(self):
        # Transaction history for monitoring (in production, use database)
        self.transaction_history: dict[int, list[dict]] = {}
        self.daily_volumes: dict[
            int, dict[str, float]
        ] = {}  # user_id -> {date: volume}

    async def check_trade_compliance(
        self, user_id: int, amount_usd: float, chain_id: int, symbol: str, side: str
    ) -> tuple[ComplianceCheckResult, list[str]]:
        """
        Check if a trade complies with regulatory requirements.

        Args:
            user_id: User ID
            amount_usd: Trade amount in USD
            chain_id: Blockchain chain ID (changed from exchange)
            symbol: Trading symbol
            side: Trade side (buy/sell)

        Returns:
            Tuple of (result, reasons)
        """
        reasons = []

        try:
            # 1. Check KYC requirement
            kyc_required = await self._check_kyc_requirement(user_id, amount_usd)
            if kyc_required:
                is_verified = await kyc_service.is_verified(user_id)
                if not is_verified:
                    reasons.append(
                        f"KYC verification required for trades over ${self.KYC_THRESHOLD_USD:,.0f}"
                    )
                    return ComplianceCheckResult.REQUIRES_KYC, reasons

            # 2. Check daily limits
            daily_limit_check = await self._check_daily_limits(user_id, amount_usd)
            if not daily_limit_check[0]:
                reasons.extend(daily_limit_check[1])
                return ComplianceCheckResult.BLOCKED, reasons

            # 3. Check for suspicious activity patterns
            suspicious_check = await self._check_suspicious_activity(
                user_id, amount_usd, chain_id, symbol
            )
            if suspicious_check[0]:
                reasons.extend(suspicious_check[1])
                return ComplianceCheckResult.REQUIRES_REVIEW, reasons

            # 4. Check large transaction reporting
            if amount_usd >= self.LARGE_TRANSACTION_THRESHOLD_USD:
                reasons.append(
                    f"Large transaction (${amount_usd:,.2f}) flagged for compliance review"
                )
                # Don't block, but flag for review
                return ComplianceCheckResult.REQUIRES_REVIEW, reasons

            # All checks passed
            return ComplianceCheckResult.APPROVED, []

        except Exception as e:
            logger.error(f"Error in compliance check: {e}", exc_info=True)
            # Fail safe: block trade if compliance check fails
            return ComplianceCheckResult.BLOCKED, [f"Compliance check error: {str(e)}"]

    async def _check_kyc_requirement(self, user_id: int, amount_usd: float) -> bool:
        """Check if KYC is required for this trade amount"""
        return amount_usd >= self.KYC_THRESHOLD_USD

    async def _check_daily_limits(
        self, user_id: int, amount_usd: float
    ) -> tuple[bool, list[str]]:
        """Check daily trading limits"""
        reasons = []
        today = datetime.now().date().isoformat()

        # Get or initialize daily volume
        if user_id not in self.daily_volumes:
            self.daily_volumes[user_id] = {}

        if today not in self.daily_volumes[user_id]:
            self.daily_volumes[user_id][today] = 0.0

        # Check if user is KYC verified
        is_verified = await kyc_service.is_verified(user_id)

        # Calculate new daily volume
        new_daily_volume = self.daily_volumes[user_id][today] + amount_usd

        # Check limits
        if not is_verified:
            if new_daily_volume > self.DAILY_LIMIT_WITHOUT_KYC_USD:
                reasons.append(
                    f"Daily limit exceeded: ${new_daily_volume:,.2f} / ${self.DAILY_LIMIT_WITHOUT_KYC_USD:,.2f}. "
                    "KYC verification required for higher limits."
                )
                return False, reasons

        # Update daily volume
        self.daily_volumes[user_id][today] = new_daily_volume

        return True, []

    async def _check_suspicious_activity(
        self, user_id: int, amount_usd: float, chain_id: int, symbol: str
    ) -> tuple[bool, list[str]]:
        """Check for suspicious activity patterns"""
        reasons = []
        is_suspicious = False

        # Get user transaction history
        user_history = self.transaction_history.get(user_id, [])

        # Check for rapid large transactions
        recent_transactions = [
            t
            for t in user_history
            if (
                datetime.now()
                - datetime.fromisoformat(t.get("timestamp", datetime.now().isoformat()))
            ).total_seconds()
            < 3600
        ]

        recent_volume = sum(t.get("amount_usd", 0) for t in recent_transactions)

        if recent_volume + amount_usd > self.SUSPICIOUS_ACTIVITY_THRESHOLD:
            is_suspicious = True
            reasons.append(
                f"Suspicious activity detected: ${recent_volume + amount_usd:,.2f} in transactions "
                f"within the last hour. Requires manual review."
            )

        # Check for unusual trading patterns (e.g., very large single transactions)
        if amount_usd > self.SUSPICIOUS_ACTIVITY_THRESHOLD:
            is_suspicious = True
            reasons.append(
                f"Unusually large transaction: ${amount_usd:,.2f}. "
                "Requires compliance review."
            )

        return is_suspicious, reasons

    async def check_withdrawal_fraud(
        self, user_id: int, amount: float, to_address: str, chain_id: int
    ) -> dict[str, Any]:
        """
        Check for fraudulent withdrawal patterns

        Args:
            user_id: User ID
            amount: Withdrawal amount
            to_address: Destination address
            chain_id: Blockchain chain ID

        Returns:
            Dict with 'allowed' boolean and 'reason' string
        """
        reasons = []
        is_fraudulent = False

        try:
            # Check for rapid withdrawals
            user_history = self.transaction_history.get(user_id, [])
            recent_withdrawals = [
                t
                for t in user_history
                if t.get("type") == "withdrawal"
                and (
                    datetime.utcnow()
                    - datetime.fromisoformat(t.get("timestamp", "1970-01-01"))
                ).total_seconds()
                < 3600
            ]

            if len(recent_withdrawals) > 5:  # More than 5 withdrawals in last hour
                is_fraudulent = True
                reasons.append("Too many withdrawals in short time period")

            # Check for unusual withdrawal amount
            if amount > self.SUSPICIOUS_ACTIVITY_THRESHOLD:
                is_fraudulent = True
                reasons.append(f"Unusually large withdrawal: ${amount:,.2f}")

            # Check for new address (first withdrawal to this address)
            address_history = [
                t
                for t in user_history
                if t.get("type") == "withdrawal" and t.get("to_address") == to_address
            ]

            if (
                not address_history and amount > 1000.0
            ):  # First withdrawal to new address > $1000
                is_fraudulent = True
                reasons.append("First withdrawal to new address exceeds threshold")

            return {
                "allowed": not is_fraudulent,
                "reason": "; ".join(reasons) if reasons else None,
            }

        except Exception as e:
            logger.error(f"Error in withdrawal fraud check: {e}", exc_info=True)
            # Fail safe: allow but flag for review
            return {"allowed": True, "reason": f"Fraud check error: {str(e)}"}

    async def record_transaction(
        self,
        user_id: int,
        transaction_id: str,
        amount_usd: float,
        chain_id: int,  # Changed from exchange
        symbol: str,
        side: str,
        order_id: str | None = None,
    ):
        """Record transaction for compliance monitoring"""
        try:
            if user_id not in self.transaction_history:
                self.transaction_history[user_id] = []

            transaction = {
                "chain_id": chain_id,  # Changed from exchange
                "transaction_id": transaction_id,
                "order_id": order_id,
                "user_id": user_id,
                "amount_usd": amount_usd,
                "symbol": symbol,
                "side": side,
                "type": "trade",  # Transaction type
                "timestamp": datetime.now().isoformat(),
            }

            self.transaction_history[user_id].append(transaction)

            # Keep only last 1000 transactions per user
            if len(self.transaction_history[user_id]) > 1000:
                self.transaction_history[user_id] = self.transaction_history[user_id][
                    -1000:
                ]

            logger.info(f"Transaction recorded for compliance: {transaction_id}")

        except Exception as e:
            logger.error(f"Error recording transaction: {e}", exc_info=True)

    async def record_withdrawal(
        self,
        user_id: int,
        withdrawal_id: str,
        amount: float,
        to_address: str,
        chain_id: int,
    ):
        """Record withdrawal for compliance monitoring"""
        try:
            if user_id not in self.transaction_history:
                self.transaction_history[user_id] = []

            withdrawal = {
                "chain_id": chain_id,
                "transaction_id": withdrawal_id,
                "user_id": user_id,
                "amount_usd": amount,
                "to_address": to_address,
                "type": "withdrawal",
                "timestamp": datetime.utcnow().isoformat(),
            }

            self.transaction_history[user_id].append(withdrawal)

            # Keep only last 1000 transactions per user
            if len(self.transaction_history[user_id]) > 1000:
                self.transaction_history[user_id] = self.transaction_history[user_id][
                    -1000:
                ]

            logger.info(f"Withdrawal recorded for compliance: {withdrawal_id}")

        except Exception as e:
            logger.error(f"Error recording withdrawal: {e}", exc_info=True)

    async def get_user_compliance_status(self, user_id: int) -> dict[str, Any]:
        """Get comprehensive compliance status for a user"""
        try:
            is_kyc_verified = await kyc_service.is_verified(user_id)
            kyc_status = await kyc_service.get_kyc_status(user_id)

            today = datetime.now().date().isoformat()
            daily_volume = self.daily_volumes.get(user_id, {}).get(today, 0.0)

            # Get recent transaction count
            user_history = self.transaction_history.get(user_id, [])
            recent_count = len(
                [
                    t
                    for t in user_history
                    if (
                        datetime.now()
                        - datetime.fromisoformat(
                            t.get("timestamp", datetime.now().isoformat())
                        )
                    ).total_seconds()
                    < 86400
                ]
            )

            return {
                "user_id": user_id,
                "kyc_verified": is_kyc_verified,
                "kyc_status": kyc_status.get("status") if kyc_status else "not_started",
                "daily_volume_usd": daily_volume,
                "daily_limit_usd": (
                    self.DAILY_LIMIT_WITHOUT_KYC_USD
                    if not is_kyc_verified
                    else float("inf")
                ),
                "recent_transactions_24h": recent_count,
                "can_trade": is_kyc_verified
                or daily_volume < self.DAILY_LIMIT_WITHOUT_KYC_USD,
            }

        except Exception as e:
            logger.error(f"Error getting compliance status: {e}", exc_info=True)
            return {"user_id": user_id, "error": str(e)}

    async def generate_compliance_report(
        self, start_date: datetime, end_date: datetime, user_id: int | None = None
    ) -> dict[str, Any]:
        """Generate compliance report for a date range"""
        try:
            # Filter transactions by date and user
            all_transactions = []
            for uid, transactions in self.transaction_history.items():
                if user_id and uid != user_id:
                    continue

                for txn in transactions:
                    txn_date = datetime.fromisoformat(
                        txn.get("timestamp", datetime.now().isoformat())
                    )
                    if start_date <= txn_date <= end_date:
                        all_transactions.append(txn)

            # Calculate statistics
            total_volume = sum(t.get("amount_usd", 0) for t in all_transactions)
            total_count = len(all_transactions)
            large_transactions = [
                t
                for t in all_transactions
                if t.get("amount_usd", 0) >= self.LARGE_TRANSACTION_THRESHOLD_USD
            ]

            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "user_id": user_id,
                "total_transactions": total_count,
                "total_volume_usd": total_volume,
                "large_transactions_count": len(large_transactions),
                "large_transactions": large_transactions[:100],  # Limit to 100
                "average_transaction_size": (
                    total_volume / total_count if total_count > 0 else 0
                ),
            }

        except Exception as e:
            logger.error(f"Error generating compliance report: {e}", exc_info=True)
            raise


# Global instance
compliance_service = ComplianceService()
