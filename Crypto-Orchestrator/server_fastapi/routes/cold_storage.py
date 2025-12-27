"""
Cold Storage Routes
API endpoints for cold storage management
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Annotated
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.cold_storage_service import ColdStorageService
from ..dependencies.auth import get_current_user
from ..database import get_db_session
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cold-storage", tags=["Cold Storage"])


class InitiateColdStorageRequest(BaseModel):
    """Request to initiate cold storage transfer"""

    currency: str
    amount: float
    description: Optional[str] = None


@router.post("/check-eligibility")
async def check_cold_storage_eligibility(
    currency: str,
    amount: float,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Dict:
    """Check if transfer is eligible for cold storage"""
    try:
        user_id = _get_user_id(current_user)

        service = ColdStorageService(db)
        result = await service.check_cold_storage_eligibility(
            user_id=user_id, currency=currency, amount=amount
        )

        return result

    except Exception as e:
        logger.error(f"Error checking cold storage eligibility: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to check eligibility")


@router.post("/initiate")
async def initiate_cold_storage_transfer(
    request: InitiateColdStorageRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Dict:
    """Initiate a transfer to cold storage"""
    try:
        user_id = _get_user_id(current_user)

        service = ColdStorageService(db)

        result = await service.initiate_cold_storage_transfer(
            user_id=user_id,
            currency=request.currency,
            amount=request.amount,
            description=request.description,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error initiating cold storage transfer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to initiate transfer")


@router.get("/balance")
async def get_cold_storage_balance(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    currency: Optional[str] = None,
) -> Dict:
    """Get cold storage balance for current user"""
    try:
        user_id = _get_user_id(current_user)

        service = ColdStorageService(db)

        result = await service.get_cold_storage_balance(
            user_id=user_id, currency=currency
        )

        return result

    except Exception as e:
        logger.error(f"Error getting cold storage balance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get balance")
