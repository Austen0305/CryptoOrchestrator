"""
Performance Routes - Trading performance summary
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from pydantic import BaseModel
import logging

from ..dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


class PerformanceSummary(BaseModel):
    """Performance summary model"""
    winRate: float
    avgProfit: float
    totalProfit: float
    bestTrade: float
    worstTrade: float


@router.get("/summary")
@cache_query_result(ttl=60, key_prefix="performance_summary", include_user=True, include_params=True)
async def get_performance_summary(
    mode: Optional[str] = Query("paper", description="Trading mode: paper or real"),
    current_user: dict = Depends(get_current_user)
) -> PerformanceSummary:
    """
    Get performance summary for the current user.
    
    Returns:
    - Win rate (percentage)
    - Average profit per trade
    - Total profit
    - Best trade (highest profit)
    - Worst trade (lowest profit/largest loss)
    """
    try:
        user_id = current_user.get('id')
        # Normalize mode
        normalized_mode = "real" if mode == "live" else mode
        
        # Import repositories
        from ..database import get_db_context
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import select, func
        from ..models.trade import Trade
        
        async with get_db_context() as db:
            # Get all trades for user in specified mode
            trades_result = await db.execute(
                select(Trade)
                .where(Trade.user_id == user_id)
                .where(Trade.mode == normalized_mode)
            )
            trades = trades_result.scalars().all()
            
            if not trades:
                # Return zero values if no trades
                return PerformanceSummary(
                    winRate=0.0,
                    avgProfit=0.0,
                    totalProfit=0.0,
                    bestTrade=0.0,
                    worstTrade=0.0
                )
            
            # Calculate metrics
            total_trades = len(trades)
            winning_trades = [t for t in trades if t.pnl and t.pnl > 0]
            win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0.0
            
            # Calculate profits
            profits = [t.pnl for t in trades if t.pnl is not None]
            total_profit = sum(profits) if profits else 0.0
            avg_profit = (total_profit / len(profits)) if profits else 0.0
            
            # Best and worst trades
            best_trade = max(profits) if profits else 0.0
            worst_trade = min(profits) if profits else 0.0
            
            return PerformanceSummary(
                winRate=win_rate,
                avgProfit=avg_profit,
                totalProfit=total_profit,
                bestTrade=best_trade,
                worstTrade=worst_trade
            )
        
    except Exception as e:
        logger.error(f"Error fetching performance summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch performance summary")
