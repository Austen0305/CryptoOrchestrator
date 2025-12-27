"""
Fraud Detection Routes
API endpoints for fraud detection and risk analysis
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, Annotated
from decimal import Decimal
import logging

from ..dependencies.auth import get_current_user
from ..services.fraud_detection.fraud_detection_service import fraud_detection_service
from ..database import get_db_context
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fraud-detection", tags=["Fraud Detection"])


class TransactionAnalysisRequest(BaseModel):
    """Request to analyze a transaction for fraud"""

    transaction_type: str  # 'deposit', 'withdrawal', 'trade'
    amount: float
    currency: str = "USD"
    metadata: Optional[Dict[str, Any]] = None


@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_transaction(
    request: TransactionAnalysisRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Dict[str, Any]:
    """
    Analyze a transaction for fraud indicators

    Note: This endpoint can be called before processing a transaction
    to check for fraud risks.
    """
    try:
        user_id = _get_user_id(current_user)

        async with get_db_context() as db:
            result = await fraud_detection_service.analyze_transaction(
                user_id=int(user_id),
                transaction_type=request.transaction_type,
                amount=Decimal(str(request.amount)),
                currency=request.currency,
                metadata=request.metadata,
                db=db,
            )
            return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing transaction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to analyze transaction")


@router.get("/risk-profile", response_model=Dict[str, Any])
async def get_risk_profile(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Get user's risk profile"""
    try:
        user_id = _get_user_id(current_user)

        async with get_db_context() as db:
            profile = await fraud_detection_service.get_user_risk_profile(
                user_id=int(user_id), db=db
            )
            return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting risk profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get risk profile")
