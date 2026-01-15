from abc import ABC, abstractmethod
from typing import Any

import pydantic


class StrategyConfig(pydantic.BaseModel):
    symbol: str
    timeframe: str
    params: dict[str, Any]
    risk_limit_pct: float = 1.0


class StrategySignal(pydantic.BaseModel):
    action: str  # buy, sell, hold
    confidence: float
    price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    metadata: dict[str, Any] = {}


class BaseStrategy(ABC):
    """
    Base Strategy interface for 2026 CryptoOrchestrator standard.
    All strategies must be deterministic and support dry-runs.
    """

    def __init__(self, config: StrategyConfig):
        self.config = config
        self.last_run = None
        self.performance_history = []

    @abstractmethod
    async def generate_signal(self, market_data: dict[str, Any]) -> StrategySignal:
        """
        Analyze market data and return a signal.
        Must be a pure function where possible to ensure determinism.
        """
        pass

    @abstractmethod
    async def on_trade_executed(self, trade_result: dict[str, Any]) -> None:
        """Called when a trade is successfully executed."""
        pass

    def get_performance_metrics(self) -> dict[str, Any]:
        """Return performance metrics for this strategy instance."""
        # Simple placeholder for now
        return {
            "total_trades": len(self.performance_history),
            "last_signal": self.last_run.isoformat() if self.last_run else None,
        }
