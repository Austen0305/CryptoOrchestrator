"""
Leaderboard Routes
API endpoints for trader leaderboards.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies.auth import get_current_user, get_optional_user
from ..middleware.cache_manager import cached
from ..services.leaderboard_service import LeaderboardService
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
@cached(ttl=60, prefix="leaderboard")  # 60s TTL for leaderboard data
async def get_leaderboard(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[dict, Depends(get_optional_user)] | None = None,
    metric: str = Query(
        "total_pnl",
        description="Ranking metric: total_pnl, win_rate, profit_factor, sharpe_ratio",
    ),
    period: str = Query("all_time", description="Time period: 24h, 7d, 30d, all_time"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    mode: str = Query("paper", description="Trading mode: paper or real"),
):
    """Get trader leaderboard with pagination"""
    try:
        if metric not in ["total_pnl", "win_rate", "profit_factor", "sharpe_ratio"]:
            raise HTTPException(status_code=400, detail="Invalid metric")

        if period not in ["24h", "7d", "30d", "all_time"]:
            raise HTTPException(status_code=400, detail="Invalid period")

        if mode not in ["paper", "real"]:
            raise HTTPException(status_code=400, detail="Invalid mode")

        service = LeaderboardService(db)
        # Convert page/page_size to limit for service (fetch enough for current page)
        limit = page * page_size
        leaderboard = await service.get_leaderboard(
            metric=metric, period=period, limit=limit, mode=mode
        )

        # Apply pagination
        total = len(leaderboard)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_leaderboard = leaderboard[start_idx:end_idx]

        # Add user's rank if authenticated
        user_rank = None
        if current_user:
            user_id = _get_user_id(current_user)
            user_rank_data = await service.get_user_rank(user_id, metric, period, mode)
            if user_rank_data:
                user_rank = user_rank_data

        return {
            "leaderboard": leaderboard,
            "metric": metric,
            "period": period,
            "mode": mode,
            "user_rank": user_rank,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get leaderboard")


@router.get("/my-rank")
@cached(ttl=60, prefix="my_rank")  # 60s TTL for user rank
async def get_my_rank(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    metric: str = Query("total_pnl"),
    period: str = Query("all_time"),
    mode: str = Query("paper"),
):
    """Get current user's rank on the leaderboard"""
    try:
        user_id = _get_user_id(current_user)
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
