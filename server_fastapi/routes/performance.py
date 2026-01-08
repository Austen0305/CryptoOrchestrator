"""
Performance Optimization API Routes
Endpoints for performance monitoring and optimization
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies.auth import get_current_user
from ..dependencies.pnl import get_pnl_service
from ..middleware.cache_manager import cached
from ..services.analytics_engine import AnalyticsEngine
from ..services.performance.ml_inference_optimization import (
    OptimizationLevel,
    ml_inference_optimization_service,
)
from ..services.pnl_service import PnLService
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/performance", tags=["Performance"])


class PerformanceSummary(BaseModel):
    totalReturn: float
    sharpeRatio: float
    maxDrawdown: float
    winRate: float
    avgProfit: float | None = None
    totalProfit: float | None = None
    bestTrade: float | None = None
    worstTrade: float | None = None


class OptimizeModelRequest(BaseModel):
    model_id: str
    optimization_level: OptimizationLevel
    input_shape: tuple | None = None
    pruning_ratio: float | None = None


@router.get("/summary")
@cached(ttl=60, prefix="performance_summary")
async def get_performance_summary(
    mode: str | None = Query(None, description="Trading mode: paper or real"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db_session)] = None,
    pnl_service: Annotated[PnLService, Depends(get_pnl_service)] = None,
) -> PerformanceSummary:
    """
    Get user performance summary

    Returns key performance metrics including total return, Sharpe ratio,
    max drawdown, and win rate for the user's trading activity.
    """
    try:
        from ..utils.trading_utils import normalize_trading_mode

        user_id = _get_user_id(current_user)
        normalized_mode = normalize_trading_mode(mode) if mode else "paper"

        # Get analytics data
        analytics_engine = AnalyticsEngine()
        analytics_result = await analytics_engine.analyze(
            {"user_id": user_id, "type": "summary"},
            db_session=db,
        )

        # Calculate performance metrics
        summary_data = analytics_result.get("summary", {}) if analytics_result else {}

        # Get P&L data
        try:
            total_pnl = await pnl_service.calculate_total_pnl(
                str(user_id), normalized_mode
            )
            total_return = (
                total_pnl / 100000.0 if total_pnl else 0.0
            )  # Assume 100k initial
        except Exception as e:
            logger.warning(f"Failed to calculate total P&L: {e}")
            total_pnl = summary_data.get("total_pnl", 0.0)
            total_return = total_pnl / 100000.0 if total_pnl else 0.0

        # Get win rate
        successful_trades = summary_data.get("successfulTrades", 0) or summary_data.get(
            "successful_trades", 0
        )
        failed_trades = summary_data.get("failedTrades", 0) or summary_data.get(
            "failed_trades", 0
        )
        total_trades = successful_trades + failed_trades
        win_rate = (successful_trades / total_trades * 100) if total_trades > 0 else 0.0

        # Get Sharpe ratio (from analytics or calculate)
        sharpe_ratio = summary_data.get("sharpe_ratio", 0.0) or summary_data.get(
            "sharpeRatio", 0.0
        )

        # Get max drawdown
        max_drawdown = abs(
            summary_data.get("max_drawdown", 0.0)
            or summary_data.get("maxDrawdown", 0.0)
        )

        # Get average profit/loss
        avg_win = summary_data.get("averageWin", 0.0) or summary_data.get(
            "average_win", 0.0
        )
        avg_loss = summary_data.get("averageLoss", 0.0) or summary_data.get(
            "average_loss", 0.0
        )
        avg_profit = (
            (avg_win * (win_rate / 100)) + (avg_loss * ((100 - win_rate) / 100))
            if total_trades > 0
            else 0.0
        )

        # Get best/worst trades (simplified - would need trade history)
        best_trade = summary_data.get("bestTrade", avg_win) or summary_data.get(
            "best_trade", avg_win
        )
        worst_trade = summary_data.get("worstTrade", avg_loss) or summary_data.get(
            "worst_trade", avg_loss
        )

        return PerformanceSummary(
            totalReturn=round(total_return * 100, 2),  # Convert to percentage
            sharpeRatio=round(sharpe_ratio, 2),
            maxDrawdown=round(max_drawdown, 2),
            winRate=round(win_rate, 2),
            avgProfit=round(avg_profit, 2),
            totalProfit=round(total_pnl, 2),
            bestTrade=round(best_trade, 2),
            worstTrade=round(worst_trade, 2),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}", exc_info=True)
        # Return default values instead of error for better UX
        return PerformanceSummary(
            totalReturn=0.0,
            sharpeRatio=0.0,
            maxDrawdown=0.0,
            winRate=0.0,
            avgProfit=0.0,
            totalProfit=0.0,
            bestTrade=0.0,
            worstTrade=0.0,
        )


@router.get("/ml-optimization/stats")
async def get_ml_optimization_stats(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """Get ML inference optimization statistics"""
    try:
        return ml_inference_optimization_service.get_optimization_stats()
    except Exception as e:
        logger.error(f"Error getting ML optimization stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get optimization stats")


@router.post("/ml-optimization/optimize")
async def optimize_model(
    request: OptimizeModelRequest,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """
    Optimize a model for faster inference

    Note: This is a placeholder endpoint. In production, you would:
    1. Load the model from storage
    2. Apply optimization
    3. Save optimized model
    4. Return optimization results
    """
    try:
        # In production, load model here
        # model = load_model(request.model_id)

        # For now, return optimization configuration
        return {
            "status": "ok",
            "model_id": request.model_id,
            "optimization_level": request.optimization_level,
            "message": "Model optimization endpoint ready. Implement model loading in production.",
        }
    except Exception as e:
        logger.error(f"Error optimizing model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to optimize model")


@router.get("/ml-optimization/models/{model_id}")
async def get_model_optimization(
    model_id: str,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """Get optimization details for a model"""
    try:
        optimization = ml_inference_optimization_service.optimized_models.get(model_id)
        if not optimization:
            raise HTTPException(
                status_code=404, detail=f"Optimization not found for {model_id}"
            )

        return {
            "model_id": optimization.model_id,
            "optimization_level": optimization.optimization_level,
            "original_size_mb": optimization.original_size_mb,
            "optimized_size_mb": optimization.optimized_size_mb,
            "speedup_factor": optimization.speedup_factor,
            "accuracy_loss": optimization.accuracy_loss,
            "quantization_bits": optimization.quantization_bits,
            "pruning_ratio": optimization.pruning_ratio,
            "gpu_enabled": optimization.gpu_enabled,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model optimization: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get model optimization")
