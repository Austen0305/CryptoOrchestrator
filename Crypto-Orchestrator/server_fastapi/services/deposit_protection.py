"""
Deposit Protection Service
Additional protection layers to ensure no money is lost during deposits
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from ..models.wallet import WalletTransaction, TransactionStatus

logger = logging.getLogger(__name__)


class DepositProtectionService:
    """Additional protection for deposit operations"""

    async def check_deposit_consistency(
        self, user_id: int, db: AsyncSession
    ) -> Dict[str, any]:
        """
        Check deposit consistency - verify all deposits are properly recorded

        Returns:
            Dict with consistency check results
        """
        try:
            # Get all deposits for user
            deposits_result = await db.execute(
                select(WalletTransaction)
                .where(
                    and_(
                        WalletTransaction.user_id == user_id,
                        WalletTransaction.transaction_type == "deposit",
                    )
                )
                .order_by(WalletTransaction.created_at.desc())
            )
            deposits = deposits_result.scalars().all()

            # Calculate totals
            total_deposited = sum(
                d.net_amount
                for d in deposits
                if d.status == TransactionStatus.COMPLETED.value
            )
            pending_deposits = [
                d for d in deposits if d.status == TransactionStatus.PENDING.value
            ]
            processing_deposits = [
                d for d in deposits if d.status == TransactionStatus.PROCESSING.value
            ]
            failed_deposits = [
                d for d in deposits if d.status == TransactionStatus.FAILED.value
            ]

            # Check for orphaned deposits (payment_intent_id but no completion)
            orphaned = [
                d
                for d in deposits
                if d.payment_intent_id
                and d.status
                in [TransactionStatus.PENDING.value, TransactionStatus.PROCESSING.value]
                and (datetime.utcnow() - d.created_at) > timedelta(hours=24)
            ]

            return {
                "total_deposits": len(deposits),
                "completed_deposits": len(
                    [
                        d
                        for d in deposits
                        if d.status == TransactionStatus.COMPLETED.value
                    ]
                ),
                "pending_deposits": len(pending_deposits),
                "processing_deposits": len(processing_deposits),
                "failed_deposits": len(failed_deposits),
                "total_deposited": float(total_deposited),
                "orphaned_deposits": len(orphaned),
                "orphaned_details": [
                    {
                        "transaction_id": d.id,
                        "payment_intent_id": d.payment_intent_id,
                        "amount": d.amount,
                        "created_at": d.created_at.isoformat(),
                        "status": d.status,
                    }
                    for d in orphaned
                ],
                "is_consistent": len(orphaned) == 0,
            }
        except Exception as e:
            logger.error(f"Error checking deposit consistency: {e}", exc_info=True)
            return {"error": str(e), "is_consistent": False}

    async def reconcile_deposit(
        self, payment_intent_id: str, db: AsyncSession
    ) -> Dict[str, any]:
        """
        Reconcile a deposit - verify payment was received and transaction is recorded

        Returns:
            Dict with reconciliation results
        """
        try:
            from sqlalchemy import select
            from ..models.wallet import WalletTransaction

            # Find transaction
            txn_result = await db.execute(
                select(WalletTransaction).where(
                    WalletTransaction.payment_intent_id == payment_intent_id
                )
            )
            transaction = txn_result.scalar_one_or_none()

            if not transaction:
                return {
                    "found": False,
                    "message": f"No transaction found for payment_intent {payment_intent_id}",
                }

            # Verify payment with Stripe
            try:
                from ..services.deposit_safety import deposit_safety_service

                is_verified, error_msg, payment_details = (
                    await deposit_safety_service.verify_payment_received(
                        payment_intent_id,
                        Decimal(str(transaction.amount)),
                        transaction.currency,
                    )
                )

                return {
                    "found": True,
                    "transaction_id": transaction.id,
                    "status": transaction.status,
                    "amount": transaction.amount,
                    "currency": transaction.currency,
                    "payment_verified": is_verified,
                    "payment_error": error_msg,
                    "payment_details": payment_details,
                    "is_reconciled": is_verified
                    and transaction.status == TransactionStatus.COMPLETED.value,
                }
            except ImportError:
                return {
                    "found": True,
                    "transaction_id": transaction.id,
                    "status": transaction.status,
                    "amount": transaction.amount,
                    "currency": transaction.currency,
                    "payment_verified": None,
                    "message": "Payment verification service not available",
                }
        except Exception as e:
            logger.error(f"Error reconciling deposit: {e}", exc_info=True)
            return {"error": str(e), "found": False}


# Global instance
deposit_protection_service = DepositProtectionService()
