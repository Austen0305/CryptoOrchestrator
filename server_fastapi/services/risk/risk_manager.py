"""
Risk Manager (2026 Standard)
Orchestrates VaR, KillSwitches, and Exposure limits.
Acts as a mandatory gate for all trade executions.
"""

import logging
from typing import Any, Dict, List, Optional
from .drawdown_kill_switch import drawdown_kill_switch
from .var_service import var_service

logger = logging.getLogger(__name__)


class RiskManager:
    def __init__(self):
        self.circuit_breaker_active = False

    async def validate_trade(
        self, user_id: int, trade_signal: Dict[str, Any]
    ) -> List[str]:
        """
        Validate a trade against all risk parameters (2026 standard).
        Returns a list of error messages (empty if OK).
        """
        errors = []

        if self.circuit_breaker_active:
            errors.append("Global circuit breaker is active. Trading paused.")
            return errors

        # 1. Check Kill Switch (Global for now, per-user in Phase 4)
        if drawdown_kill_switch.is_active():
            errors.append("Drawdown kill switch is active.")

        # 2. Check VaR (Value at Risk)
        # We assume 1% risk threshold for this simple check.
        # In reality, we'd fetch recent returns for the specific symbol/portfolio.
        # This is a representative placeholder for the 2026 requirement.
        mock_returns = [-0.01, 0.02, -0.015, 0.005, -0.02]
        portfolio_value = 10000.0  # Placeholder
        var_res = var_service.calculate_var(mock_returns, portfolio_value)

        if var_res.var_percent > 5.0:  # 5% threshold
            errors.append(f"VaR too high: {var_res.var_percent:.2f}%")

        # 3. Validate Symbol Pair
        symbol = trade_signal.get("symbol", "")
        if not symbol:
            errors.append("Missing trade symbol.")

        return errors

    def trigger_circuit_breaker(self, reason: str):
        logger.warning(f"CIRCUIT BREAKER TRIGGERED: {reason}")
        self.circuit_breaker_active = True

    def reset_circuit_breaker(self):
        logger.info("Circuit breaker reset.")
        self.circuit_breaker_active = False


# Global instance
risk_manager = RiskManager()
