import logging
from math import sqrt
from typing import Dict, Any, Callable

logger = logging.getLogger(__name__)

class RiskScenarioService:
    """Service for portfolio risk scenario analysis (shock VaR, multi-horizon scaling).

    This is a lightweight, stateless calculator. Future iteration can pull real
    return distributions from a repository layer or historical price service.
    """

    async def compute_scenario(self,
                               portfolio_value: float,
                               current_var: float,
                               shock_percent: float,
                               horizon_days: int = 1,
                               correlation_factor: float = 1.0,
                               notify: Callable[[Dict[str, Any]], Any] | None = None) -> Dict[str, Any]:
        """Compute a shocked Value-at-Risk scenario.

        Args:
            portfolio_value: Current total portfolio value (absolute).
            current_var: Baseline 95% VaR (absolute currency units).
            shock_percent: Hypothetical instantaneous price move (e.g. -0.12 for -12%).
            horizon_days: Number of days to project (scaled by sqrt(time)).
            correlation_factor: Multiplier capturing portfolio correlation concentration (>1 amplifies shock).
        Returns:
            dict with shocked values and metadata.
        """
        try:
            horizon_scale = sqrt(max(1, horizon_days))
            shocked_move_abs = abs(portfolio_value * shock_percent)
            shocked_var = current_var + shocked_move_abs * correlation_factor
            projected_var = shocked_var * horizon_scale
            stress_loss = abs(portfolio_value * min(0, shock_percent) * correlation_factor)
            result = {
                "portfolio_value": portfolio_value,
                "baseline_var": current_var,
                "shock_percent": shock_percent,
                "correlation_factor": correlation_factor,
                "horizon_days": horizon_days,
                "shocked_var": shocked_var,
                "projected_var": projected_var,
                "stress_loss": stress_loss,
                "horizon_scale": horizon_scale,
                "explanation": (
                    "Shock VaR = baseline_var + |portfolio_value * shock_percent| * correlation_factor; "
                    "Projected VaR scales by sqrt(horizon_days)."
                )
            }
            # Optional real-time notification hook
            if notify:
                try:
                    await notify({
                        "type": "risk_scenario",
                        "category": "risk",
                        "level": "info",
                        "message": "Scenario computed",
                        "data": result
                    })
                except Exception as cb_e:
                    logger.warning(f"Risk scenario notify callback failed: {cb_e}")
            return result
        except Exception as e:
            logger.error("Scenario computation failed: %s", e)
            raise

risk_scenario_service = RiskScenarioService()
