"""
Futures Trading API Routes
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Annotated
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies.auth import get_current_user
from ..database import get_db_session
from ..services.trading.futures_trading_service import FuturesTradingService
from ..utils.route_helpers import _get_user_id
from ..middleware.cache_manager import cached
from ..utils.response_optimizer import ResponseOptimizer

logger = logging.getLogger(__name__)

router = APIRouter()


class CreateFuturesPositionRequest(BaseModel):
    symbol: str = Field(..., description="Trading symbol (e.g., BTC/USD)")
    exchange: str = Field(..., description="Exchange name")
    side: str = Field(..., pattern="^(long|short)$")
    quantity: float = Field(..., gt=0)
    leverage: int = Field(..., ge=1, le=125, description="Leverage multiplier (1-125x)")
    trading_mode: str = Field(default="paper", pattern="^(paper|real)$")
    entry_price: Optional[float] = Field(
        None, gt=0, description="Entry price (None = market)"
    )
    stop_loss_price: Optional[float] = Field(None, gt=0)
    take_profit_price: Optional[float] = Field(None, gt=0)
    trailing_stop_percent: Optional[float] = Field(None, gt=0, le=100)
    name: Optional[str] = Field(None, max_length=100)
    config: Optional[Dict[str, Any]] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "BTC/USD",
                "exchange": "binance",
                "side": "long",
                "quantity": 0.1,
                "leverage": 10,
                "trading_mode": "paper",
                "stop_loss_price": 45000.0,
                "take_profit_price": 55000.0,
            }
        }
    }


class FuturesPositionResponse(BaseModel):
    id: str
    user_id: int
    name: Optional[str]
    symbol: str
    exchange: str
    trading_mode: str
    side: str
    leverage: int
    quantity: float
    entry_price: float
    current_price: float
    margin_used: float
    margin_available: float
    liquidation_price: float
    maintenance_margin: float
    stop_loss_price: Optional[float]
    take_profit_price: Optional[float]
    trailing_stop_percent: Optional[float]
    is_open: bool
    status: str
    unrealized_pnl: float
    realized_pnl: float
    total_pnl: float
    pnl_percent: float
    liquidation_risk: float
    margin_ratio: float
    opened_at: str
    closed_at: Optional[str]
    config: Dict[str, Any]

    model_config = {"from_attributes": True}


@router.post(
    "/futures/positions",
    response_model=Dict[str, str],
    status_code=status.HTTP_201_CREATED,
    tags=["Futures Trading"],
)
async def create_futures_position(
    request: CreateFuturesPositionRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Create a new futures position with leverage."""
    try:
        user_id = _get_user_id(current_user)
        service = FuturesTradingService(session=db_session)
        position_id = await service.create_futures_position(
            user_id=user_id,
            symbol=request.symbol,
            exchange=request.exchange,
            side=request.side,
            quantity=request.quantity,
            leverage=request.leverage,
            trading_mode=request.trading_mode,
            entry_price=request.entry_price,
            stop_loss_price=request.stop_loss_price,
            take_profit_price=request.take_profit_price,
            trailing_stop_percent=request.trailing_stop_percent,
            name=request.name,
            config=request.config,
        )

        if not position_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create futures position",
            )

        return {"id": position_id, "message": "Futures position created successfully"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating futures position: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create futures position",
        )


@router.get(
    "/futures/positions",
    response_model=List[FuturesPositionResponse],
    tags=["Futures Trading"],
)
@cached(ttl=60, prefix="futures_positions")  # 60s TTL for futures positions list
async def list_futures_positions(
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    open_only: bool = Query(False, description="Only return open positions"),
):
    """List all futures positions for the current user with pagination."""
    try:
        user_id = _get_user_id(current_user)
        service = FuturesTradingService(session=db_session)
        # Convert page/page_size to skip/limit for service layer (backward compatibility)
        skip = (page - 1) * page_size
        limit = page_size
        positions, total = await service.list_user_futures_positions(
            user_id, skip, limit, open_only
        )
        # Use ResponseOptimizer for paginated response with metadata
        # Note: When open_only=True, total will be the length of open positions
        return ResponseOptimizer.paginate_response(positions, page, page_size, total)
    except Exception as e:
        logger.error(f"Error listing futures positions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list futures positions",
        )


@router.get(
    "/futures/positions/{position_id}",
    response_model=FuturesPositionResponse,
    tags=["Futures Trading"],
)
async def get_futures_position(
    position_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get a specific futures position by ID."""
    try:
        user_id = _get_user_id(current_user)
        service = FuturesTradingService(session=db_session)
        position = await service.get_futures_position(position_id, user_id)
        if not position:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Futures position not found",
            )
        return position
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting futures position: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get futures position",
        )


@router.post(
    "/futures/positions/{position_id}/close",
    response_model=Dict[str, Any],
    tags=["Futures Trading"],
)
async def close_futures_position(
    position_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    close_price: Optional[float] = Query(None, gt=0),
):
    """Close a futures position."""
    try:
        user_id = _get_user_id(current_user)
        service = FuturesTradingService(session=db_session)
        result = await service.close_futures_position(position_id, user_id, close_price)

        if result.get("action") == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to close position"),
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing futures position: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to close futures position",
        )


@router.post(
    "/futures/positions/{position_id}/update-pnl",
    response_model=Dict[str, Any],
    tags=["Futures Trading"],
)
async def update_position_pnl(
    position_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Update P&L for a futures position."""
    try:
        user_id = _get_user_id(current_user)
        service = FuturesTradingService(session=db_session)
        result = await service.update_position_pnl(position_id, user_id)
        return result
    except Exception as e:
        logger.error(f"Error updating position P&L: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update position P&L",
        )
