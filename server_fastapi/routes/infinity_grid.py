from __future__ import annotations

"""
Infinity Grid API Routes
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies.auth import get_current_user
from ..middleware.cache_manager import cached
from ..services.trading.infinity_grid_service import InfinityGridService
from ..utils.response_optimizer import ResponseOptimizer
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter()


class CreateInfinityGridRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    symbol: str = Field(..., description="Trading symbol (e.g., BTC/USD)")
    exchange: str = Field(..., description="Exchange name")
    grid_count: int = Field(..., ge=2, le=100)
    grid_spacing_percent: float = Field(
        ..., gt=0, description="Spacing between grids (%)"
    )
    order_amount: float = Field(..., gt=0)
    trading_mode: str = Field(default="paper", pattern="^(paper|real)$")
    upper_adjustment_percent: float = Field(default=5.0, gt=0)
    lower_adjustment_percent: float = Field(default=5.0, gt=0)
    config: dict[str, Any] | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "BTC Infinity Grid",
                "symbol": "BTC/USD",
                "exchange": "binance",
                "grid_count": 10,
                "grid_spacing_percent": 1.0,
                "order_amount": 100.0,
                "trading_mode": "paper",
            }
        }
    }


class InfinityGridResponse(BaseModel):
    id: str
    user_id: int
    name: str
    symbol: str
    exchange: str
    trading_mode: str
    grid_count: int
    grid_spacing_percent: float
    order_amount: float
    current_upper_price: float
    current_lower_price: float
    initial_price: float
    is_active: bool
    status: str
    total_profit: float
    total_trades: int
    grid_adjustments: int
    grid_state: dict[str, Any]
    config: dict[str, Any]
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


@router.post(
    "/infinity-grids",
    response_model=dict[str, str],
    status_code=status.HTTP_201_CREATED,
    tags=["Infinity Grid"],
)
async def create_infinity_grid(
    request: CreateInfinityGridRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Create a new infinity grid bot."""
    try:
        user_id = _get_user_id(current_user)
        service = InfinityGridService(session=db_session)
        bot_id = await service.create_infinity_grid(
            user_id=user_id,
            name=request.name,
            symbol=request.symbol,
            exchange=request.exchange,
            grid_count=request.grid_count,
            grid_spacing_percent=request.grid_spacing_percent,
            order_amount=request.order_amount,
            trading_mode=request.trading_mode,
            upper_adjustment_percent=request.upper_adjustment_percent,
            lower_adjustment_percent=request.lower_adjustment_percent,
            config=request.config,
        )

        if not bot_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create infinity grid",
            )

        return {"id": bot_id, "message": "Infinity grid created successfully"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating infinity grid: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create infinity grid",
        )


@router.get(
    "/infinity-grids", response_model=list[InfinityGridResponse], tags=["Infinity Grid"]
)
@cached(ttl=120, prefix="infinity_grids")  # 120s TTL for infinity grids list
async def list_infinity_grids(
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """List all infinity grids for the current user with pagination."""
    try:
        user_id = _get_user_id(current_user)
        service = InfinityGridService(session=db_session)
        # Convert page/page_size to skip/limit for service layer (backward compatibility)
        skip = (page - 1) * page_size
        limit = page_size
        bots, total = await service.list_user_infinity_grids(user_id, skip, limit)
        # Use ResponseOptimizer for paginated response with metadata
        return ResponseOptimizer.paginate_response(bots, page, page_size, total)
    except Exception as e:
        logger.error(f"Error listing infinity grids: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list infinity grids",
        )


@router.get(
    "/infinity-grids/{bot_id}",
    response_model=InfinityGridResponse,
    tags=["Infinity Grid"],
)
async def get_infinity_grid(
    bot_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get a specific infinity grid by ID."""
    try:
        user_id = _get_user_id(current_user)
        service = InfinityGridService(session=db_session)
        bot = await service.get_infinity_grid(bot_id, user_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Infinity grid not found"
            )
        return bot
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting infinity grid: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get infinity grid",
        )


@router.post(
    "/infinity-grids/{bot_id}/start",
    response_model=dict[str, str],
    tags=["Infinity Grid"],
)
async def start_infinity_grid(
    bot_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Start an infinity grid bot."""
    try:
        user_id = _get_user_id(current_user)
        service = InfinityGridService(session=db_session)
        success = await service.start_infinity_grid(bot_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to start infinity grid",
            )
        return {"message": "Infinity grid started successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting infinity grid: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start infinity grid",
        )


@router.post(
    "/infinity-grids/{bot_id}/stop",
    response_model=dict[str, str],
    tags=["Infinity Grid"],
)
async def stop_infinity_grid(
    bot_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Stop an infinity grid bot."""
    try:
        user_id = _get_user_id(current_user)
        service = InfinityGridService(session=db_session)
        success = await service.stop_infinity_grid(bot_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to stop infinity grid",
            )
        return {"message": "Infinity grid stopped successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping infinity grid: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop infinity grid",
        )


@router.delete(
    "/infinity-grids/{bot_id}", response_model=dict[str, str], tags=["Infinity Grid"]
)
async def delete_infinity_grid(
    bot_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Delete an infinity grid bot."""
    try:
        user_id = _get_user_id(current_user)
        service = InfinityGridService(session=db_session)
        await service.stop_infinity_grid(bot_id, user_id)

        from ...repositories.infinity_grid_repository import InfinityGridRepository

        repository = InfinityGridRepository()
        bot = await repository.get_by_user_and_id(db_session, bot_id, user_id)

        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Infinity grid not found"
            )

        bot.soft_delete()
        await db_session.commit()
        return {"message": "Infinity grid deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting infinity grid: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete infinity grid",
        )
