"""
Leaderboard Routes
API endpoints for trader leaderboards.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.leaderboard_service import LeaderboardService
from ..dependencies.auth import get_current_user, get_optional_user
from ..database import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_leaderboard(
    metric: str = Query("total_pnl", description="Ranking metric: total_pnl, win_rate, profit_factor, sharpe_ratio"),
    period: str = Query("all_time", description="Time period: 24h, 7d, 30d, all_time"),
    limit: int = Query(100, ge=1, le=1000, description="Number of top traders"),
    mode: str = Query("paper", description="Trading mode: paper or real"),
    current_user: Optional[dict] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get trader leaderboard"""
    try:
        if metric not in ["total_pnl", "win_rate", "profit_factor", "sharpe_ratio"]:
            raise HTTPException(status_code=400, detail="Invalid metric")
        
        if period not in ["24h", "7d", "30d", "all_time"]:
            raise HTTPException(status_code=400, detail="Invalid period")
        
        if mode not in ["paper", "real"]:
            raise HTTPException(status_code=400, detail="Invalid mode")
        
        service = LeaderboardService(db)
        leaderboard = await service.get_leaderboard(
            metric=metric,
            period=period,
            limit=limit,
            mode=mode
        )
        
        # Add user's rank if authenticated
        user_rank = None
        if current_user:
            user_id = current_user.get("id")
            user_rank_data = await service.get_user_rank(user_id, metric, period, mode)
            if user_rank_data:
                user_rank = user_rank_data
        
        return {
            "leaderboard": leaderboard,
            "metric": metric,
            "period": period,
            "mode": mode,
            "user_rank": user_rank
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get leaderboard")


@router.get("/my-rank")
async def get_my_rank(
    metric: str = Query("total_pnl"),
    period: str = Query("all_time"),
    mode: str = Query("paper"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get current user's rank on the leaderboard"""
    try:
        user_id = current_user.get("id")
        service = LeaderboardService(db)
        
        rank = await service.get_user_rank(user_id, metric, period, mode)
        
        if rank:
            return rank
        else:
            raise HTTPException(status_code=404, detail="User not found on leaderboard")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user rank: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get user rank")

