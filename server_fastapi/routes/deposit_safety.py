"""
Deposit Safety Routes
Endpoints for deposit safety checks and reconciliation
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..database import get_db_context
from ..dependencies.auth import get_current_user
from ..services.deposit_protection import deposit_protection_service
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/deposit-safety", tags=["Deposit Safety"])


class ReconcileDepositRequest(BaseModel):
    """Request to reconcile a deposit"""

    payment_intent_id: str


@router.get("/consistency-check")
async def check_deposit_consistency(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """Check deposit consistency for current user"""
    try:
        user_id = _get_user_id(current_user)

        async with get_db_context() as db:
            result = await deposit_protection_service.check_deposit_consistency(
                user_id=int(user_id), db=db
            )
            return result
    except Exception as e:
        logger.error(f"Error checking deposit consistency: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to check deposit consistency"
        )


@router.post("/reconcile")
async def reconcile_deposit(
    request: ReconcileDepositRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """Reconcile a specific deposit"""
    try:
        user_id = _get_user_id(current_user)

        async with get_db_context() as db:
            result = await deposit_protection_service.reconcile_deposit(
                payment_intent_id=request.payment_intent_id, db=db
            )

            if not result.get("found"):
                raise HTTPException(status_code=404, detail="Deposit not found")

            # Verify user owns this deposit
            from sqlalchemy import select

            from ..models.wallet import WalletTransaction

            txn_result = await db.execute(
                select(WalletTransaction).where(
                    WalletTransaction.payment_intent_id == request.payment_intent_id
                )
            )
            transaction = txn_result.scalar_one_or_none()

            if transaction and transaction.user_id != int(user_id):
                raise HTTPException(status_code=403, detail="Access denied")

            return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reconciling deposit: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to reconcile deposit")
