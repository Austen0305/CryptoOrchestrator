from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Annotated
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from ..services.payments.trading_fee_service import TradingFeeService
from ..dependencies.auth import get_current_user
from ..dependencies.user import get_current_user_db
from ..database import get_db_session
from ..utils.route_helpers import _get_user_id
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


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
async def get_fees(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    volumeUSD: Optional[float] = None,
):
    """Get current fee information for DEX trading"""
    try:
        # Use real volume if provided, otherwise use mock volume for tier calculation
        volume = volumeUSD or 100000.0

        # Get fees from trading fee service (DEX trading fees)
        fee_service = TradingFeeService()
        fee_structure = fee_service.get_fee_structure()

        # Get user tier from subscription (default to free tier)
        user_id = _get_user_id(current_user)
        user_tier = "free"  # Default

        try:
            from ..dependencies.user import get_current_user_db

            user = await get_current_user_db(current_user, db)
            if user.subscription and user.subscription.status == "active":
                user_tier = user.subscription.plan  # Get tier from subscription plan
        except Exception as e:
            logger.warning(
                f"Failed to get user subscription tier: {e}", extra={"user_id": user_id}
            )
            # Default to free tier if subscription lookup fails

        tier_fees = fee_structure["tiers"].get(
            user_tier, fee_structure["tiers"]["free"]
        )

        fee_info = {
            "makerFee": tier_fees["fee_bps"] / 100,  # Convert bps to percentage
            "takerFee": tier_fees["fee_bps"]
            / 100,  # DEX doesn't distinguish maker/taker, use same fee
            "volumeUSD": volume,
            "nextTierVolume": (
                500000.0 if volume < 500000 else None
            ),  # Simplified tier logic
        }

        return fee_info
    except Exception as e:
        logger.error(f"Failed to get fees: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve fee information"
        )


@router.post("/calculate", response_model=FeeResponse)
async def calculate_fees(
    request: FeeCalculationRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Calculate trading fees for a specific DEX trade"""
    try:
        from decimal import Decimal

        user_id = _get_user_id(current_user)

        # Get current trading volume for fee tier calculation
        # In production, get from user trading history
        volume_usd = 100000.0  # Default, will be calculated from database if available

        # Get user tier and monthly volume from database
        fee_service = TradingFeeService()
        monthly_volume = await fee_service.get_user_monthly_volume(str(user_id), db)
        if monthly_volume:
            volume_usd = float(monthly_volume)

        # Get user tier from subscription (default to free)
        user_tier = "free"  # Default
        try:
            user = await get_current_user_db(current_user, db)
            if user.subscription and user.subscription.status == "active":
                user_tier = user.subscription.plan  # Get tier from subscription plan
        except Exception as e:
            logger.warning(
                f"Failed to get user subscription tier: {e}", extra={"user_id": user_id}
            )
            # Default to free tier if subscription lookup fails

        # Calculate fee using trading fee service (DEX trading)
        trade_amount = Decimal(str(request.amount * request.price))
        fee_amount_decimal = fee_service.calculate_fee(
            trade_amount=trade_amount,
            user_tier=user_tier,
            is_custodial=True,  # Default to custodial
            monthly_volume=Decimal(str(volume_usd)),
        )
        fee_amount = float(fee_amount_decimal)

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
            "netAmount": net_amount,
        }
    except Exception as e:
        logger.error(f"Failed to calculate fees: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate fees")
