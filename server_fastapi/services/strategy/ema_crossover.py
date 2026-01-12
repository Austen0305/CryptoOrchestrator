from .base_strategy import BaseStrategy, StrategySignal, StrategyConfig
from typing import Any, Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EMACrossoverStrategy(BaseStrategy):
    """
    Standard EMA Crossover Strategy (2026 Deterministic Standard).
    Generates 'buy' when Short EMA crosses above Long EMA.
    Generates 'sell' when Short EMA crosses below Long EMA.
    """

    async def generate_signal(self, market_data: Dict[str, Any]) -> StrategySignal:
        """
        Expects market_data to contain 'ema_short', 'ema_long', and 'current_price'.
        """
        short_ema = market_data.get("ema_short")
        long_ema = market_data.get("ema_long")
        price = market_data.get("current_price")

        if short_ema is None or long_ema is None or price is None:
            logger.warning("Missing EMA data or price for signal generation.")
            return StrategySignal(action="hold", confidence=0.0)

        action = "hold"
        confidence = 0.0

        if short_ema > long_ema:
            action = "buy"
            confidence = 0.8  # Simplified confidence
        elif short_ema < long_ema:
            action = "sell"
            confidence = 0.8

        self.last_run = datetime.utcnow()

        # Calculate dynamic stop-loss/take-profit if needed
        stop_loss = price * 0.98 if action == "buy" else price * 1.02
        take_profit = price * 1.05 if action == "buy" else price * 0.95

        return StrategySignal(
            action=action,
            confidence=confidence,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            metadata={"short_ema": short_ema, "long_ema": long_ema},
        )

    async def on_trade_executed(self, trade_result: Dict[str, Any]) -> None:
        self.performance_history.append(trade_result)
        logger.info(
            f"EMACrossoverStrategy trade recorded: {trade_result.get('tx_hash')}"
        )
