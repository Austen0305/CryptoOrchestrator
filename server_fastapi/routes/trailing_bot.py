"""
Trailing Bot API Routes
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies.auth import get_current_user
from ..middleware.cache_manager import cached
from ..services.trading.trailing_bot_service import TrailingBotService
from ..utils.response_optimizer import ResponseOptimizer
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter()


class CreateTrailingBotRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    symbol: str = Field(..., description="Trading symbol (e.g., BTC/USD)")
    exchange: str = Field(..., description="Exchange name")
    bot_type: str = Field(..., pattern="^(trailing_buy|trailing_sell)$")
    trailing_percent: float = Field(..., gt=0, description="Trailing distance (%)")
    order_amount: float = Field(..., gt=0)
    trading_mode: str = Field(default="paper", pattern="^(paper|real)$")
    initial_price: float | None = Field(None, gt=0)
    max_price: float | None = Field(
        None, gt=0, description="Max price for trailing buy"
    )
    min_price: float | None = Field(
        None, gt=0, description="Min price for trailing sell"
    )
    config: dict[str, Any] | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "BTC Trailing Buy",
                "symbol": "BTC/USD",
                "exchange": "binance",
                "bot_type": "trailing_buy",
                "trailing_percent": 2.0,
                "order_amount": 100.0,
                "trading_mode": "paper",
            }
        }
    }


class TrailingBotResponse(BaseModel):
    id: str
    user_id: int
    name: str
    symbol: str
    exchange: str
    trading_mode: str
    bot_type: str
    initial_price: float
    current_price: float
    trailing_percent: float
    order_amount: float
    max_price: float | None
    min_price: float | None
    is_active: bool
    status: str
    orders_executed: int
    total_profit: float
    highest_price: float
    lowest_price: float
    config: dict[str, Any]
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


@router.post(
    "/trailing-bots",
    response_model=dict[str, str],
    status_code=status.HTTP_201_CREATED,
    tags=["Trailing Bot"],
)
async def create_trailing_bot(
    request: CreateTrailingBotRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Create a new trailing bot."""
    try:
        user_id = _get_user_id(current_user)
        service = TrailingBotService(session=db_session)
        bot_id = await service.create_trailing_bot(
            user_id=user_id,
            name=request.name,
            symbol=request.symbol,
            exchange=request.exchange,
            bot_type=request.bot_type,
            trailing_percent=request.trailing_percent,
            order_amount=request.order_amount,
            trading_mode=request.trading_mode,
            initial_price=request.initial_price,
            max_price=request.max_price,
            min_price=request.min_price,
            config=request.config,
        )

        if not bot_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create trailing bot",
            )

        return {"id": bot_id, "message": "Trailing bot created successfully"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating trailing bot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create trailing bot",
        )


@router.get(
    "/trailing-bots", response_model=list[TrailingBotResponse], tags=["Trailing Bot"]
)
@cached(ttl=120, prefix="trailing_bots")  # 120s TTL for trailing bots list
async def list_trailing_bots(
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """List all trailing bots for the current user with pagination."""
    try:
        user_id = _get_user_id(current_user)
        service = TrailingBotService(session=db_session)
        # Convert page/page_size to skip/limit for service layer (backward compatibility)
        skip = (page - 1) * page_size
        limit = page_size
        bots, total = await service.list_user_trailing_bots(user_id, skip, limit)
        # Use ResponseOptimizer for paginated response with metadata
        return ResponseOptimizer.paginate_response(bots, page, page_size, total)
    except Exception as e:
        logger.error(f"Error listing trailing bots: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list trailing bots",
        )


@router.get(
    "/trailing-bots/{bot_id}", response_model=TrailingBotResponse, tags=["Trailing Bot"]
)
async def get_trailing_bot(
    bot_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get a specific trailing bot by ID."""
    try:
        user_id = _get_user_id(current_user)
        service = TrailingBotService(session=db_session)
        bot = await service.get_trailing_bot(bot_id, user_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Trailing bot not found"
            )
        return bot
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trailing bot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get trailing bot",
        )


@router.post(
    "/trailing-bots/{bot_id}/start",
    response_model=dict[str, str],
    tags=["Trailing Bot"],
)
async def start_trailing_bot(
    bot_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Start a trailing bot."""
    try:
        user_id = _get_user_id(current_user)
        service = TrailingBotService(session=db_session)
        success = await service.start_trailing_bot(bot_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to start trailing bot",
            )
        return {"message": "Trailing bot started successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting trailing bot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start trailing bot",
        )


@router.post(
    "/trailing-bots/{bot_id}/stop", response_model=dict[str, str], tags=["Trailing Bot"]
)
async def stop_trailing_bot(
    bot_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Stop a trailing bot."""
    try:
        user_id = _get_user_id(current_user)
        service = TrailingBotService(session=db_session)
        success = await service.stop_trailing_bot(bot_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to stop trailing bot",
            )
        return {"message": "Trailing bot stopped successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping trailing bot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop trailing bot",
        )


@router.delete(
    "/trailing-bots/{bot_id}", response_model=dict[str, str], tags=["Trailing Bot"]
)
async def delete_trailing_bot(
    bot_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Delete a trailing bot."""
    try:
        user_id = _get_user_id(current_user)
        service = TrailingBotService(session=db_session)
        await service.stop_trailing_bot(bot_id, user_id)

        from ...repositories.trailing_bot_repository import TrailingBotRepository

        repository = TrailingBotRepository()
        bot = await repository.get_by_user_and_id(db_session, bot_id, user_id)

        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Trailing bot not found"
            )

        bot.soft_delete()
        await db_session.commit()
        return {"message": "Trailing bot deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting trailing bot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete trailing bot",
        )
