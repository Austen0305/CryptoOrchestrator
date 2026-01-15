"""
Treasury Management Service
Comprehensive treasury management for institutional wallets
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TreasurySummary:
    """Treasury summary statistics"""

    total_balance_usd: Decimal
    total_wallets: int
    active_wallets: int
    pending_transactions: int
    total_transactions_24h: int
    total_volume_24h_usd: Decimal
    average_transaction_size_usd: Decimal
    largest_wallet_balance_usd: Decimal
    smallest_wallet_balance_usd: Decimal


@dataclass
class WalletBalance:
    """Wallet balance information"""

    wallet_id: int
    wallet_name: str
    balance_usd: Decimal
    balance_native: Decimal
    currency: str
    pending_balance_usd: Decimal
    available_balance_usd: Decimal
    last_activity: datetime | None
    signer_count: int
    required_signatures: int


@dataclass
class TreasuryActivity:
    """Treasury activity record"""

    timestamp: datetime
    wallet_id: int
    wallet_name: str
    activity_type: str  # "deposit", "withdrawal", "transfer", "signature"
    amount_usd: Decimal | None
    currency: str | None
    status: str
    description: str


class TreasuryService:
    """
    Treasury management service for institutional wallets

    Features:
    - Treasury overview and summary
    - Wallet balance aggregation
    - Activity tracking
    - Risk monitoring
    - Compliance reporting
    """

    def __init__(self, db_session):
        """
        Initialize treasury service

        Args:
            db_session: Database session factory
        """
        self.db_session = db_session

    def get_treasury_summary(self, user_id: int) -> TreasurySummary:
        """
        Get comprehensive treasury summary

        Args:
            user_id: User ID

        Returns:
            TreasurySummary with aggregated statistics
        """
        from ..models.institutional import (
            InstitutionalWallet,
            InstitutionalWalletTransaction,
            PendingTransaction,
        )

        with self.db_session() as session:
            # Get all wallets for user
            wallets = (
                session.query(InstitutionalWallet)
                .filter(InstitutionalWallet.owner_id == user_id)
                .all()
            )

            if not wallets:
                return TreasurySummary(
                    total_balance_usd=Decimal("0"),
                    total_wallets=0,
                    active_wallets=0,
                    pending_transactions=0,
                    total_transactions_24h=0,
                    total_volume_24h_usd=Decimal("0"),
                    average_transaction_size_usd=Decimal("0"),
                    largest_wallet_balance_usd=Decimal("0"),
                    smallest_wallet_balance_usd=Decimal("0"),
                )

            # Calculate balances (simplified - would need actual balance fetching)
            total_balance_usd = Decimal("0")
            wallet_balances = []

            for _wallet in wallets:
                # In production, fetch actual balances from blockchain/API
                balance_usd = Decimal("0")  # Placeholder
                wallet_balances.append(balance_usd)
                total_balance_usd += balance_usd

            # Get pending transactions
            pending_count = (
                session.query(PendingTransaction)
                .filter(PendingTransaction.wallet_id.in_([w.id for w in wallets]))
                .count()
            )

            # Get 24h transactions
            cutoff = datetime.now(UTC) - timedelta(hours=24)
            transactions_24h = (
                session.query(InstitutionalWalletTransaction)
                .filter(
                    InstitutionalWalletTransaction.wallet_id.in_(
                        [w.id for w in wallets]
                    ),
                    InstitutionalWalletTransaction.created_at >= cutoff,
                )
                .all()
            )

            total_volume_24h = sum(
                Decimal(str(tx.amount or 0)) for tx in transactions_24h
            )

            avg_tx_size = (
                total_volume_24h / len(transactions_24h)
                if transactions_24h
                else Decimal("0")
            )

            largest_balance = max(wallet_balances) if wallet_balances else Decimal("0")
            smallest_balance = min(wallet_balances) if wallet_balances else Decimal("0")

            return TreasurySummary(
                total_balance_usd=total_balance_usd,
                total_wallets=len(wallets),
                active_wallets=len([w for w in wallets if w.is_active]),
                pending_transactions=pending_count,
                total_transactions_24h=len(transactions_24h),
                total_volume_24h_usd=total_volume_24h,
                average_transaction_size_usd=avg_tx_size,
                largest_wallet_balance_usd=largest_balance,
                smallest_wallet_balance_usd=smallest_balance,
            )

    def get_wallet_balances(self, user_id: int) -> list[WalletBalance]:
        """
        Get balances for all wallets

        Args:
            user_id: User ID

        Returns:
            List of WalletBalance
        """
        from ..models.institutional import InstitutionalWallet, PendingTransaction

        with self.db_session() as session:
            wallets = (
                session.query(InstitutionalWallet)
                .filter(InstitutionalWallet.owner_id == user_id)
                .all()
            )

            balances = []
            for wallet in wallets:
                # Get pending transactions
                pending_txs = (
                    session.query(PendingTransaction)
                    .filter(
                        PendingTransaction.wallet_id == wallet.id,
                        PendingTransaction.status == "pending",
                    )
                    .all()
                )

                pending_balance = sum(
                    Decimal(str(tx.amount or 0)) for tx in pending_txs
                )

                # In production, fetch actual balances
                balance_usd = Decimal("0")  # Placeholder
                balance_native = Decimal("0")  # Placeholder

                # Get signer count
                signer_count = len(wallet.signers) if wallet.signers else 0

                balances.append(
                    WalletBalance(
                        wallet_id=wallet.id,
                        wallet_name=wallet.name or f"Wallet {wallet.id}",
                        balance_usd=balance_usd,
                        balance_native=balance_native,
                        currency=wallet.currency or "USD",
                        pending_balance_usd=pending_balance,
                        available_balance_usd=balance_usd - pending_balance,
                        last_activity=wallet.updated_at,
                        signer_count=signer_count,
                        required_signatures=wallet.required_signatures or 0,
                    )
                )

            return balances

    def get_treasury_activity(
        self,
        user_id: int,
        limit: int = 100,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[TreasuryActivity]:
        """
        Get treasury activity log

        Args:
            user_id: User ID
            limit: Maximum number of records
            start_date: Start date filter
            end_date: End date filter

        Returns:
            List of TreasuryActivity
        """
        from ..models.institutional import (
            InstitutionalWallet,
            InstitutionalWalletTransaction,
            WalletAccessLog,
        )

        with self.db_session() as session:
            wallets = (
                session.query(InstitutionalWallet)
                .filter(InstitutionalWallet.owner_id == user_id)
                .all()
            )

            if not wallets:
                return []

            wallet_ids = [w.id for w in wallets]
            activities = []

            # Get transactions
            tx_query = session.query(InstitutionalWalletTransaction).filter(
                InstitutionalWalletTransaction.wallet_id.in_(wallet_ids)
            )

            if start_date:
                tx_query = tx_query.filter(
                    InstitutionalWalletTransaction.created_at >= start_date
                )
            if end_date:
                tx_query = tx_query.filter(
                    InstitutionalWalletTransaction.created_at <= end_date
                )

            transactions = (
                tx_query.order_by(InstitutionalWalletTransaction.created_at.desc())
                .limit(limit)
                .all()
            )

            for tx in transactions:
                wallet = next((w for w in wallets if w.id == tx.wallet_id), None)
                activities.append(
                    TreasuryActivity(
                        timestamp=tx.created_at,
                        wallet_id=tx.wallet_id,
                        wallet_name=wallet.name if wallet else f"Wallet {tx.wallet_id}",
                        activity_type="transfer"
                        if tx.transaction_type == "transfer"
                        else tx.transaction_type or "unknown",
                        amount_usd=Decimal(str(tx.amount or 0)),
                        currency=tx.currency,
                        status=tx.status or "unknown",
                        description=f"{tx.transaction_type} transaction",
                    )
                )

            # Get access logs
            log_query = session.query(WalletAccessLog).filter(
                WalletAccessLog.wallet_id.in_(wallet_ids)
            )

            if start_date:
                log_query = log_query.filter(WalletAccessLog.timestamp >= start_date)
            if end_date:
                log_query = log_query.filter(WalletAccessLog.timestamp <= end_date)

            access_logs = (
                log_query.order_by(WalletAccessLog.timestamp.desc()).limit(limit).all()
            )

            for log in access_logs:
                wallet = next((w for w in wallets if w.id == log.wallet_id), None)
                activities.append(
                    TreasuryActivity(
                        timestamp=log.timestamp,
                        wallet_id=log.wallet_id,
                        wallet_name=wallet.name
                        if wallet
                        else f"Wallet {log.wallet_id}",
                        activity_type="signature",
                        amount_usd=None,
                        currency=None,
                        status="success" if log.action == "sign" else "info",
                        description=f"{log.action} - {log.details or ''}",
                    )
                )

            # Sort by timestamp and limit
            activities.sort(key=lambda a: a.timestamp, reverse=True)
            return activities[:limit]

    def get_risk_metrics(self, user_id: int) -> dict[str, Any]:
        """
        Get treasury risk metrics

        Args:
            user_id: User ID

        Returns:
            Risk metrics dictionary
        """
        summary = self.get_treasury_summary(user_id)
        balances = self.get_wallet_balances(user_id)

        # Calculate risk metrics
        total_pending = sum(b.pending_balance_usd for b in balances)
        pending_ratio = (
            (total_pending / summary.total_balance_usd * 100)
            if summary.total_balance_usd > 0
            else 0
        )

        # Concentration risk (largest wallet / total)
        concentration_ratio = (
            (summary.largest_wallet_balance_usd / summary.total_balance_usd * 100)
            if summary.total_balance_usd > 0
            else 0
        )

        # Average signatures per wallet
        avg_signatures = (
            sum(b.required_signatures for b in balances) / len(balances)
            if balances
            else 0
        )

        return {
            "total_balance_usd": float(summary.total_balance_usd),
            "pending_balance_usd": float(total_pending),
            "pending_ratio_percent": float(pending_ratio),
            "concentration_ratio_percent": float(concentration_ratio),
            "average_signatures_required": float(avg_signatures),
            "wallet_count": summary.total_wallets,
            "active_wallet_count": summary.active_wallets,
            "risk_level": (
                "high"
                if pending_ratio > 50 or concentration_ratio > 80
                else "medium"
                if pending_ratio > 25 or concentration_ratio > 60
                else "low"
            ),
        }
