"""
Withdrawal Routes
API endpoints for processing withdrawals
"""

import logging
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies.auth import get_current_user
from ..services.blockchain.withdrawal_service import get_withdrawal_service
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response models
class WithdrawalRequest(BaseModel):
    chain_id: int = Field(..., description="Blockchain chain ID")
    to_address: str = Field(..., description="Destination wallet address")
    amount: str = Field(
        ..., description="Withdrawal amount (as string to preserve precision)"
    )
    currency: str = Field(default="ETH", description="Currency (ETH or token address)")
    mfa_token: str | None = Field(
        None, description="2FA token (required for withdrawals)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "chain_id": 1,
                "to_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "amount": "0.1",
                "currency": "ETH",
                "mfa_token": "123456",
            }
        }
    }


class WithdrawalResponse(BaseModel):
    success: bool
    transaction_hash: str | None
    amount: str
    currency: str
    to_address: str
    status: str

    model_config = {"from_attributes": True}


class WithdrawalStatusResponse(BaseModel):
    status: str  # pending, confirmed, failed, not_found
    success: bool | None
    block_number: int | None
    gas_used: int | None

    model_config = {"from_attributes": True}


@router.post("/", response_model=WithdrawalResponse, tags=["Withdrawals"])
async def create_withdrawal(
    request: WithdrawalRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WithdrawalResponse:
    """
    Create a withdrawal request

    Requires 2FA token for security.
    """
    try:
        service = get_withdrawal_service()

        # Parse amount
        try:
            amount = Decimal(request.amount)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid amount format")

        # Process withdrawal
        user_id = _get_user_id(current_user)
        result = await service.process_withdrawal(
            user_id=user_id,
            chain_id=request.chain_id,
            to_address=request.to_address,
            amount=amount,
            currency=request.currency,
            mfa_token=request.mfa_token,
            db=db,
        )

        if not result:
            raise HTTPException(status_code=400, detail="Withdrawal failed")

        return WithdrawalResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating withdrawal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/status/{chain_id}/{tx_hash}",
    response_model=WithdrawalStatusResponse,
    tags=["Withdrawals"],
)
async def get_withdrawal_status(
    chain_id: int,
    tx_hash: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> WithdrawalStatusResponse:
    """
    Get withdrawal transaction status
    """
    try:
        service = get_withdrawal_service()
        status_data = await service.get_withdrawal_status(chain_id, tx_hash)

        if not status_data:
            raise HTTPException(status_code=404, detail="Transaction not found")

        return WithdrawalStatusResponse(**status_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting withdrawal status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
