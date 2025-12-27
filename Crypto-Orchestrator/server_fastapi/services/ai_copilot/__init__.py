"""
AI Copilot Services Module
"""

from .copilot_service import (
    AICopilotService,
    TradeExplanation,
    StrategyGenerationRequest,
    StrategyOptimizationRequest,
    BacktestSummaryRequest,
    copilot_service,
)

__all__ = [
    "AICopilotService",
    "TradeExplanation",
    "StrategyGenerationRequest",
    "StrategyOptimizationRequest",
    "BacktestSummaryRequest",
    "copilot_service",
]
