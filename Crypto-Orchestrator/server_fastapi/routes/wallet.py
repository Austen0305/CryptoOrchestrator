"""
Wallet Routes
API endpoints for wallet management, deposits, and withdrawals.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Annotated
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.wallet_service import WalletService
from ..dependencies.auth import get_current_user
from ..database import get_db_session
from ..services.wallet_broadcast import broadcast_wallet_update
from ..utils.route_helpers import _get_user_id
from ..middleware.cache_manager import cached
from ..utils.query_optimizer import QueryOptimizer
from ..utils.response_optimizer import ResponseOptimizer

logger = logging.getLogger(__name__)

router = APIRouter()


class DepositRequest(BaseModel):
    amount: float
    currency: str = "USD"
    payment_method_id: Optional[str] = None
    payment_method_type: str = "card"  # 'card', 'ach', 'bank_transfer'
    description: Optional[str] = None


class WithdrawRequest(BaseModel):
    amount: float
    currency: str = "USD"
    destination: Optional[str] = None
    description: Optional[str] = None


@router.get("/balance")
@cached(ttl=30, prefix="wallet_balance")  # 30s TTL for wallet balance (real-time data)
async def get_wallet_balance(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    currency: str = Query("USD", description="Currency code"),
):
    """Get wallet balance for current user"""
    try:
        user_id = _get_user_id(current_user)
        service = WalletService(db)
        balance = await service.get_wallet_balance(user_id, currency)
        return balance
    except Exception as e:
        logger.error(f"Error getting wallet balance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get wallet balance")


@router.post("/deposit")
async def deposit_funds(
    request: DepositRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Deposit funds into wallet.

    Note: A 5% deposit fee applies (5 cents per dollar).
    For example: $100 deposit = $5 fee, $95 credited to wallet.
    """
    try:
        if request.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")

        # Calculate fee for user information
        deposit_fee = request.amount * 0.05  # 5% fee
        net_amount = request.amount - deposit_fee

        user_id = _get_user_id(current_user)
        service = WalletService(db)

        result = await service.deposit(
            user_id=user_id,
            amount=request.amount,
            currency=request.currency,
            payment_method_id=request.payment_method_id,
            payment_method_type=request.payment_method_type,
            description=request.description,
        )

        # Add fee information to response
        result["fee"] = deposit_fee
        result["fee_percentage"] = 5.0
        result["net_amount"] = net_amount
        result["message"] = (
            f"Deposit of ${request.amount:.2f} processed. Fee: ${deposit_fee:.2f} (5%). Amount credited: ${net_amount:.2f}"
        )

        # Broadcast wallet update
        try:
            balance = await service.get_wallet_balance(user_id, request.currency)
            await broadcast_wallet_update(user_id, balance)
        except Exception as e:
            logger.warning(f"Failed to broadcast wallet update: {e}")

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing deposit: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process deposit")


@router.post("/withdraw")
async def withdraw_funds(
    request: WithdrawRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Withdraw funds from wallet"""
    try:
        if request.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")

        user_id = _get_user_id(current_user)
        service = WalletService(db)

        result = await service.withdraw(
            user_id=user_id,
            amount=request.amount,
            currency=request.currency,
            destination=request.destination,
            description=request.description,
        )

        # Broadcast wallet update
        try:
            balance = await service.get_wallet_balance(user_id, request.currency)
            await broadcast_wallet_update(user_id, balance)
        except Exception as e:
            logger.warning(f"Failed to broadcast wallet update: {e}")

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing withdrawal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process withdrawal")


@router.get("/transactions")
@cached(ttl=60, prefix="wallet_transactions")  # 60s TTL for wallet transactions list
async def get_transactions(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    currency: Optional[str] = Query(None, description="Filter by currency"),
    transaction_type: Optional[str] = Query(None, description="Filter by type"),
):
    """Get wallet transactions with pagination"""
    try:
        user_id = _get_user_id(current_user)
        service = WalletService(db)

        # Convert page/page_size to limit for service (fetch enough for current page)
        limit = page * page_size
        transactions = await service.get_transactions(
            user_id=user_id,
            currency=currency,
            transaction_type=transaction_type,
            limit=limit,
        )

        # Apply pagination
        total = len(transactions)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_transactions = transactions[start_idx:end_idx]

        return {"transactions": paginated_transactions}
    except Exception as e:
        logger.error(f"Error getting transactions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get transactions")


@router.post("/deposit/confirm")
async def confirm_deposit(
    transaction_id: int,
    payment_intent_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Confirm a deposit transaction (called after payment verification)"""
    try:
        user_id = _get_user_id(current_user)
        service = WalletService(db)

        success = await service.confirm_deposit(transaction_id, payment_intent_id)

        if success:
            return {"message": "Deposit confirmed successfully"}
        else:
            raise HTTPException(
                status_code=404, detail="Transaction not found or already processed"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming deposit: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to confirm deposit")
