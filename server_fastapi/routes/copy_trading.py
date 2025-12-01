"""
Copy Trading Routes
API endpoints for copy trading functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.copy_trading_service import CopyTradingService
from ..dependencies.auth import get_current_user
from ..database import get_db_session

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
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Follow a trader to copy their trades"""
    try:
        follower_id = current_user.get("id")
        service = CopyTradingService(db)
        
        result = await service.follow_trader(
            follower_id=follower_id,
            trader_id=request.trader_id,
            allocation_percentage=request.allocation_percentage,
            max_position_size=request.max_position_size
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
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Unfollow a trader"""
    try:
        follower_id = current_user.get("id")
        service = CopyTradingService(db)
        
        success = await service.unfollow_trader(follower_id, trader_id)
        
        if success:
            return {"message": "Successfully unfollowed trader"}
        else:
            raise HTTPException(status_code=404, detail="Follow relationship not found")
    except Exception as e:
        logger.error(f"Error unfollowing trader: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to unfollow trader")


@router.get("/followed")
async def get_followed_traders(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get list of traders being followed"""
    try:
        follower_id = current_user.get("id")
        service = CopyTradingService(db)
        
        traders = await service.get_followed_traders(follower_id)
        return {"traders": traders}
    except Exception as e:
        logger.error(f"Error getting followed traders: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get followed traders")


@router.post("/copy")
async def copy_trade(
    request: CopyTradeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Copy a specific trade from a trader"""
    try:
        follower_id = current_user.get("id")
        service = CopyTradingService(db)
        
        result = await service.copy_trade(
            follower_id=follower_id,
            trader_id=request.trader_id,
            original_trade_id=request.original_trade_id,
            allocation_percentage=request.allocation_percentage
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error copying trade: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to copy trade")


@router.get("/stats")
async def get_copy_trading_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get copy trading statistics"""
    try:
        follower_id = current_user.get("id")
        service = CopyTradingService(db)
        
        stats = await service.get_copy_trading_stats(follower_id)
        return stats
    except Exception as e:
        logger.error(f"Error getting copy trading stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get copy trading stats")

