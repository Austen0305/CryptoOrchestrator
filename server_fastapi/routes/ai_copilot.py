"""
AI Copilot Routes - Trade explanations, strategy generation, optimization, backtest summaries
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional, List
import logging
from pydantic import BaseModel, Field
from datetime import datetime

from ..services.ai_copilot.copilot_service import (
    copilot_service,
    TradeExplanation,
    StrategyGenerationRequest,
    GeneratedStrategy,
    StrategyOptimizationRequest,
    OptimizationResult,
    BacktestSummaryRequest,
    BacktestSummary
)
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai-copilot", tags=["AI Copilot"])


# ===== Trade Explanation Routes =====

class TradeExplanationRequest(BaseModel):
    """Trade explanation request"""
    trade_id: str
    trade_data: Dict[str, Any]
    market_data: Optional[Dict[str, Any]] = None


@router.post("/trade/explain", response_model=Dict)
async def explain_trade(
    request: TradeExplanationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate natural language explanation of a trade"""
    try:
        explanation = await copilot_service.explain_trade(
            request.trade_id,
            request.trade_data,
            request.market_data
        )
        return explanation.dict()
    except Exception as e:
        logger.error(f"Error explaining trade: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to explain trade: {str(e)}")


# ===== Strategy Generation Routes =====

@router.post("/strategy/generate", response_model=Dict)
async def generate_strategy(
    request: StrategyGenerationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate trading strategy from natural language description"""
    try:
        strategy = await copilot_service.generate_strategy_from_text(request)
        return strategy.dict()
    except Exception as e:
        logger.error(f"Error generating strategy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate strategy: {str(e)}")


# ===== Strategy Optimization Routes =====

@router.post("/strategy/optimize", response_model=Dict)
async def optimize_strategy(
    request: StrategyOptimizationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate strategy optimization recommendations"""
    try:
        result = await copilot_service.optimize_strategy(request)
        return result.dict()
    except Exception as e:
        logger.error(f"Error optimizing strategy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to optimize strategy: {str(e)}")


# ===== Backtest Summary Routes =====

class BacktestSummaryRequestWrapper(BaseModel):
    """Backtest summary request wrapper"""
    backtest_id: str
    backtest_data: Dict[str, Any]
    include_charts: bool = True
    include_detailed_metrics: bool = True
    focus_areas: Optional[List[str]] = None


@router.post("/backtest/summarize", response_model=Dict)
async def summarize_backtest(
    request: BacktestSummaryRequestWrapper,
    current_user: dict = Depends(get_current_user)
):
    """Generate AI summary of backtesting results"""
    try:
        summary_request = BacktestSummaryRequest(
            backtest_id=request.backtest_id,
            include_charts=request.include_charts,
            include_detailed_metrics=request.include_detailed_metrics,
            focus_areas=request.focus_areas
        )
        
        summary = await copilot_service.summarize_backtest(
            summary_request,
            request.backtest_data
        )
        return summary.dict()
    except Exception as e:
        logger.error(f"Error summarizing backtest: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to summarize backtest: {str(e)}")

