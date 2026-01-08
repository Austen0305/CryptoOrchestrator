"""
AI Copilot Services Module
"""

from .copilot_service import (
    AICopilotService,
    BacktestSummaryRequest,
    StrategyGenerationRequest,
    StrategyOptimizationRequest,
    TradeExplanation,
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
