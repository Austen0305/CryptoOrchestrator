"""
Automation Services Module
"""

from .auto_hedging import (
    AutoHedgingService,
    HedgingConfig,
    HedgingStrategy,
    auto_hedging_service,
)
from .portfolio_optimizer import (
    OptimizationGoal,
    OptimizationRecommendation,
    PortfolioOptimizationAdvisor,
    portfolio_optimizer,
)
from .smart_alerts import (
    AlertPriority,
    AlertRule,
    SmartAlertsService,
    smart_alerts_service,
)
from .strategy_switching import (
    StrategySwitchConfig,
    StrategySwitchingService,
    strategy_switching_service,
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
