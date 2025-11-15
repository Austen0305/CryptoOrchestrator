from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import logging
import jwt
import os
from ..services.exchange_service import default_exchange

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Environment variables
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Pydantic models
class FeeCalculationRequest(BaseModel):
    amount: float
    price: float
    side: str  # 'buy' or 'sell'
    isMaker: Optional[bool] = None
    volumeUSD: Optional[float] = None

class FeeResponse(BaseModel):
    feeAmount: float
    feePercentage: float
    totalAmount: float
    netAmount: float

class FeeInfo(BaseModel):
    makerFee: float
    takerFee: float
    volumeUSD: float
    nextTierVolume: Optional[float] = None

@router.get("/", response_model=FeeInfo)
async def get_fees(volumeUSD: Optional[float] = None, current_user: dict = Depends(get_current_user)):
    """Get current fee information from exchange"""
    try:
        # Use real volume if provided, otherwise use mock volume for tier calculation
        volume = volumeUSD or 100000.0

        # Get fees from exchange service
        fees = default_exchange.get_fees(volume)

        fee_info = {
            "makerFee": fees.maker,
            "takerFee": fees.taker,
            "volumeUSD": volume,
            "nextTierVolume": 500000.0 if volume < 500000 else None  # Simplified tier logic
        }

        return fee_info
    except Exception as e:
        logger.error(f"Failed to get fees: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve fee information")

@router.post("/calculate", response_model=FeeResponse)
async def calculate_fees(request: FeeCalculationRequest, current_user: dict = Depends(get_current_user)):
    """Calculate trading fees for a specific trade using exchange service"""
    try:
        # Get current trading volume for fee tier calculation (mock for now)
        volume_usd = 100000.0  # In production, get from user trading history

        # Calculate fee using exchange service
        fee_amount = default_exchange.calculate_fee(
            amount=request.amount,
            price=request.price,
            is_maker=request.isMaker if request.isMaker is not None else False,
            volume_usd=volume_usd
        )

        total_amount = request.amount * request.price
        fee_percentage = fee_amount / total_amount

        # Calculate net amount based on side
        if request.side == "buy":
            net_amount = total_amount + fee_amount
        else:  # sell
            net_amount = total_amount - fee_amount

        return {
            "feeAmount": fee_amount,
            "feePercentage": fee_percentage,
            "totalAmount": total_amount,
            "netAmount": net_amount
        }
    except Exception as e:
        logger.error(f"Failed to calculate fees: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate fees")
