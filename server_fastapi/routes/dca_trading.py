"""
DCA Trading API Routes
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies.auth import get_current_user
from ..middleware.cache_manager import cached
from ..services.trading.dca_trading_service import DCATradingService
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic request/response models
class CreateDCABotRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    symbol: str = Field(..., description="Trading symbol (e.g., BTC/USD)")
    exchange: str = Field(..., description="Exchange name")
    total_investment: float = Field(..., gt=0, description="Total amount to invest")
    order_amount: float = Field(..., gt=0, description="Amount per order")
    interval_minutes: int = Field(..., ge=1, description="Minutes between orders")
    trading_mode: str = Field(default="paper", pattern="^(paper|real)$")
    max_orders: int | None = Field(None, ge=1, description="Maximum number of orders")
    use_martingale: bool = Field(
        default=False, description="Enable martingale strategy"
    )
    martingale_multiplier: float = Field(
        default=1.5, ge=1.0, description="Martingale multiplier"
    )
    martingale_max_multiplier: float = Field(
        default=5.0, ge=1.0, description="Maximum multiplier"
    )
    take_profit_percent: float | None = Field(
        None, gt=0, description="Take profit at % gain"
    )
    stop_loss_percent: float | None = Field(
        None, gt=0, description="Stop loss at % loss"
    )
    config: dict[str, Any] | None = None

    @field_validator("martingale_max_multiplier")
    @classmethod
    def validate_max_multiplier(cls, v, info):
        if (
            info.data.get("martingale_multiplier")
            and v < info.data["martingale_multiplier"]
        ):
            raise ValueError("Max multiplier must be >= base multiplier")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "BTC DCA Bot",
                "symbol": "BTC/USD",
                "exchange": "binance",
                "total_investment": 1000.0,
                "order_amount": 100.0,
                "interval_minutes": 60,
                "trading_mode": "paper",
                "max_orders": 10,
                "use_martingale": False,
            }
        }
    }


class DCABotResponse(BaseModel):
    id: str
    user_id: int
    name: str
    symbol: str
    exchange: str
    trading_mode: str
    total_investment: float
    order_amount: float
    interval_minutes: int
    max_orders: int | None
    use_martingale: bool
    martingale_multiplier: float
    martingale_max_multiplier: float
    take_profit_percent: float | None
    stop_loss_percent: float | None
    is_active: bool
    status: str
    orders_executed: int
    total_invested: float
    average_price: float
    current_value: float
    total_profit: float
    profit_percent: float
    next_order_at: str | None
    config: dict[str, Any]
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


@router.post(
    "/dca-bots",
    response_model=dict[str, str],
    status_code=status.HTTP_201_CREATED,
    tags=["DCA Trading"],
)
async def create_dca_bot(
    request: CreateDCABotRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Create a new DCA (Dollar Cost Averaging) trading bot."""
    try:
        user_id = _get_user_id(current_user)
        service = DCATradingService(session=db_session)
        bot_id = await service.create_dca_bot(
            user_id=user_id,
            name=request.name,
            symbol=request.symbol,
            exchange=request.exchange,
            total_investment=request.total_investment,
            order_amount=request.order_amount,
            interval_minutes=request.interval_minutes,
            trading_mode=request.trading_mode,
            max_orders=request.max_orders,
            use_martingale=request.use_martingale,
            martingale_multiplier=request.martingale_multiplier,
            martingale_max_multiplier=request.martingale_max_multiplier,
            take_profit_percent=request.take_profit_percent,
            stop_loss_percent=request.stop_loss_percent,
            config=request.config,
        )

        if not bot_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create DCA bot",
            )

        return {"id": bot_id, "message": "DCA bot created successfully"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating DCA bot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create DCA bot",
        )


@router.get("/dca-bots", response_model=list[DCABotResponse], tags=["DCA Trading"])
@cached(ttl=120, prefix="dca_bots")  # 120s TTL for DCA bots list
async def list_dca_bots(
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """List all DCA bots for the current user with pagination."""
    try:
        user_id_str = _get_user_id(current_user)
        user_id = int(user_id_str)  # Convert to int for service
        service = DCATradingService(session=db_session)
        # Convert page/page_size to skip/limit for service layer (backward compatibility)
        skip = (page - 1) * page_size
        limit = page_size
        bots, total = await service.list_user_dca_bots(user_id, skip, limit)
        # Use ResponseOptimizer for paginated response with metadata
        from ..utils.response_optimizer import ResponseOptimizer

        return ResponseOptimizer.paginate_response(bots, page, page_size, total)

    except Exception as e:
        logger.error(f"Error listing DCA bots: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list DCA bots",
        )


@router.get("/dca-bots/{bot_id}", response_model=DCABotResponse, tags=["DCA Trading"])
async def get_dca_bot(
    bot_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get a specific DCA bot by ID."""
    try:
        user_id_str = _get_user_id(current_user)
        user_id = int(user_id_str)  # Convert to int for service
        service = DCATradingService(session=db_session)
        bot = await service.get_dca_bot(bot_id, user_id)

        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="DCA bot not found"
            )

        return bot

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting DCA bot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get DCA bot",
        )


@router.post(
    "/dca-bots/{bot_id}/start", response_model=dict[str, str], tags=["DCA Trading"]
)
async def start_dca_bot(
    bot_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Start a DCA trading bot."""
    try:
        user_id = _get_user_id(current_user)
        service = DCATradingService(session=db_session)
        success = await service.start_dca_bot(bot_id, user_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to start DCA bot",
            )

        return {"message": "DCA bot started successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting DCA bot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start DCA bot",
        )


@router.post(
    "/dca-bots/{bot_id}/stop", response_model=dict[str, str], tags=["DCA Trading"]
)
async def stop_dca_bot(
    bot_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Stop a DCA trading bot."""
    try:
        user_id_str = _get_user_id(current_user)
        user_id = int(user_id_str)  # Convert to int for service
        service = DCATradingService(session=db_session)
        success = await service.stop_dca_bot(bot_id, user_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to stop DCA bot"
            )

        return {"message": "DCA bot stopped successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping DCA bot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop DCA bot",
        )


@router.delete(
    "/dca-bots/{bot_id}", response_model=dict[str, str], tags=["DCA Trading"]
)
async def delete_dca_bot(
    bot_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Delete a DCA trading bot."""
    try:
        user_id_str = _get_user_id(current_user)
        user_id = int(user_id_str)  # Convert to int for service
        # First stop the bot if it's running
        service = DCATradingService(session=db_session)
        await service.stop_dca_bot(bot_id, user_id)

        # Then soft delete
        from ...repositories.dca_bot_repository import DCABotRepository

        repository = DCABotRepository()
        bot = await repository.get_by_user_and_id(db_session, bot_id, user_id)

        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="DCA bot not found"
            )

        bot.soft_delete()
        await db_session.commit()

        return {"message": "DCA bot deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting DCA bot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete DCA bot",
        )
