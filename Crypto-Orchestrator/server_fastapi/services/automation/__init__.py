"""
Automation Services Module
"""

from .auto_hedging import (
    AutoHedgingService,
    HedgingStrategy,
    HedgingConfig,
    auto_hedging_service,
)
from .strategy_switching import (
    StrategySwitchingService,
    StrategySwitchConfig,
    strategy_switching_service,
)
from .smart_alerts import (
    SmartAlertsService,
    AlertRule,
    AlertPriority,
    smart_alerts_service,
)
from .portfolio_optimizer import (
    PortfolioOptimizationAdvisor,
    OptimizationGoal,
    OptimizationRecommendation,
    portfolio_optimizer,
)

__all__ = [
    "AutoHedgingService",
    "HedgingStrategy",
    "HedgingConfig",
    "auto_hedging_service",
    "StrategySwitchingService",
    "StrategySwitchConfig",
    "strategy_switching_service",
    "SmartAlertsService",
    "AlertRule",
    "AlertPriority",
    "smart_alerts_service",
    "PortfolioOptimizationAdvisor",
    "OptimizationGoal",
    "OptimizationRecommendation",
    "portfolio_optimizer",
]
