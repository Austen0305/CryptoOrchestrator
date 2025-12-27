"""
Copy Trading Routes
API endpoints for copy trading functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Annotated
import logging

from ..services.copy_trading_service import CopyTradingService
from ..dependencies.copy_trading import get_copy_trading_service
from ..dependencies.auth import get_current_user
from ..utils.route_helpers import _get_user_id
from ..middleware.cache_manager import cached
from ..utils.query_optimizer import QueryOptimizer
from ..utils.response_optimizer import ResponseOptimizer

logger = logging.getLogger(__name__)

router = APIRouter()


class FollowTraderRequest(BaseModel):
    trader_id: int
    allocation_percentage: float = 100.0
    max_position_size: Optional[float] = None


class CopyTradeRequest(BaseModel):
    trader_id: int
    original_trade_id: str
    allocation_percentage: float = 100.0


@router.post("/follow")
async def follow_trader(
    request: FollowTraderRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[CopyTradingService, Depends(get_copy_trading_service)],
):
    """Follow a trader to copy their trades"""
    try:
        follower_id = _get_user_id(current_user)

        result = await service.follow_trader(
            follower_id=follower_id,
            trader_id=request.trader_id,
            allocation_percentage=request.allocation_percentage,
            max_position_size=request.max_position_size,
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error following trader: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to follow trader")


@router.delete("/follow/{trader_id}")
async def unfollow_trader(
    trader_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[CopyTradingService, Depends(get_copy_trading_service)],
):
    """Unfollow a trader"""
    try:
        follower_id = _get_user_id(current_user)

        success = await service.unfollow_trader(follower_id, trader_id)

        if success:
            return {"message": "Successfully unfollowed trader"}
        else:
            raise HTTPException(status_code=404, detail="Follow relationship not found")
    except Exception as e:
        logger.error(f"Error unfollowing trader: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to unfollow trader")


@router.get("/followed")
@cached(ttl=120, prefix="followed_traders")  # 120s TTL for followed traders list
async def get_followed_traders(
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[CopyTradingService, Depends(get_copy_trading_service)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """Get list of traders being followed with pagination"""
    try:
        follower_id = _get_user_id(current_user)

        traders = await service.get_followed_traders(follower_id)

        # Apply pagination (service returns all, paginate in route)
        total = len(traders)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_traders = traders[start_idx:end_idx]

        return {"traders": paginated_traders}
    except Exception as e:
        logger.error(f"Error getting followed traders: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get followed traders")


@router.post("/copy")
async def copy_trade(
    request: CopyTradeRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[CopyTradingService, Depends(get_copy_trading_service)],
):
    """Copy a specific trade from a trader"""
    try:
        follower_id = _get_user_id(current_user)

        result = await service.copy_trade(
            follower_id=follower_id,
            trader_id=request.trader_id,
            original_trade_id=request.original_trade_id,
            allocation_percentage=request.allocation_percentage,
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error copying trade: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to copy trade")


@router.get("/stats")
@cached(ttl=120, prefix="copy_trading_stats")  # 120s TTL for copy trading stats
async def get_copy_trading_stats(
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[CopyTradingService, Depends(get_copy_trading_service)],
):
    """Get copy trading statistics"""
    try:
        follower_id = _get_user_id(current_user)

        stats = await service.get_copy_trading_stats(follower_id)
        return stats
    except Exception as e:
        logger.error(f"Error getting copy trading stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get copy trading stats")
