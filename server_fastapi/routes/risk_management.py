"""
Enhanced Risk Management Routes - Complete risk management API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional, List, Annotated
import logging
from pydantic import BaseModel, Field
from datetime import datetime

from ..services.risk_service import RiskService, RiskLimits, RiskAlert, RiskMetrics
from ..services.risk.drawdown_kill_switch import (
    drawdown_kill_switch,
    DrawdownKillSwitchConfig,
    DrawdownState,
    DrawdownEvent,
)
from ..services.risk.var_service import var_service, VaRConfig, VaRResult
from ..services.risk.monte_carlo_service import (
    monte_carlo_service,
    MonteCarloConfig,
    MonteCarloResult,
)
from ..dependencies.auth import get_current_user
from ..dependencies.risk import get_risk_service
from ..utils.route_helpers import _get_user_id
from ..middleware.cache_manager import cached
from ..utils.query_optimizer import QueryOptimizer
from ..utils.response_optimizer import ResponseOptimizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/risk", tags=["Risk Management"])


class UpdateLimitsRequest(BaseModel):
    maxPositionSize: float | None = None
    maxDailyLoss: float | None = None
    maxPortfolioRisk: float | None = None
    maxLeverage: int | None = None
    maxCorrelation: float | None = None
    minDiversification: float | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "maxPositionSize": 15,
                "maxDailyLoss": 5,
                "maxPortfolioRisk": 55,
                "maxLeverage": 4,
                "maxCorrelation": 0.75,
                "minDiversification": 0.5,
            }
        }
    }


@router.get("/metrics", response_model=RiskMetrics)
async def get_metrics(svc: Annotated[RiskService, Depends(get_risk_service)]):
    return await svc.get_metrics()


@router.get("/alerts", response_model=list[RiskAlert])
@cached(ttl=60, prefix="risk_alerts")  # 60s TTL for risk alerts
async def get_alerts(
    current_user: Annotated[dict, Depends(get_current_user)],
    svc: Annotated[RiskService, Depends(get_risk_service)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """Get user's risk alerts with pagination"""
    user_id = _get_user_id(current_user)
    # Service uses limit parameter - convert page_size to limit for backward compatibility
    alerts = await svc.get_user_alerts_db(
        user_id, limit=page_size * page, unresolved_only=False
    )
    # Apply pagination manually (service returns all up to limit)
    total = len(alerts)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    return alerts[start_idx:end_idx]


@router.get("/limits", response_model=RiskLimits)
@cached(ttl=300, prefix="risk_limits")  # 5min TTL for risk limits (static config)
async def get_limits(
    current_user: Annotated[dict, Depends(get_current_user)],
    svc: Annotated[RiskService, Depends(get_risk_service)],
):
    user_id = _get_user_id(current_user)
    return await svc.get_user_limits(user_id)


@router.post("/limits", response_model=RiskLimits)
async def update_limits(
    payload: UpdateLimitsRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    svc: Annotated[RiskService, Depends(get_risk_service)],
):
    user_id = _get_user_id(current_user)
    # Manual validation to enforce reasonable ranges beyond model bounds if needed
    updates: Dict[str, Any] = {}
    for field, value in payload.model_dump(exclude_none=True).items():
        if field == "maxPositionSize" and not (0 <= value <= 100):
            raise HTTPException(
                status_code=400, detail="maxPositionSize out of range (0-100)"
            )
        if field == "maxDailyLoss" and not (0 <= value <= 100):
            raise HTTPException(
                status_code=400, detail="maxDailyLoss out of range (0-100)"
            )
        if field == "maxPortfolioRisk" and not (0 <= value <= 100):
            raise HTTPException(
                status_code=400, detail="maxPortfolioRisk out of range (0-100)"
            )
        if field == "maxLeverage" and not (1 <= value <= 10):
            raise HTTPException(
                status_code=400, detail="maxLeverage out of range (1-10)"
            )
        if field == "maxCorrelation" and not (0 <= value <= 1):
            raise HTTPException(
                status_code=400, detail="maxCorrelation out of range (0-1)"
            )
        if field == "minDiversification" and not (0 <= value <= 1):
            raise HTTPException(
                status_code=400, detail="minDiversification out of range (0-1)"
            )
        updates[field] = value
    if not updates:
        return await svc.get_user_limits(user_id)
    updated = await svc.update_user_limits(user_id, updates)
    return updated


@router.post("/alerts/{alert_id}/acknowledge", response_model=RiskAlert)
async def acknowledge_alert(
    alert_id: str,
    svc: Annotated[RiskService, Depends(get_risk_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Acknowledge a risk alert - uses database as primary storage"""
    try:
        user_id = _get_user_id(current_user)
        if svc.db:
            try:
                numeric_id = int(alert_id)
            except ValueError as parse_error:
                raise HTTPException(
                    status_code=400, detail="Invalid alert ID"
                ) from parse_error
            acknowledged = await svc.acknowledge_alert_db(numeric_id)
            if not acknowledged:
                raise HTTPException(status_code=404, detail="Alert not found")
            alerts = await svc.get_user_alerts(user_id)
            updated_alert = next((a for a in alerts if a.id == alert_id), None)
            if not updated_alert:
                raise HTTPException(status_code=404, detail="Alert not found")
            return updated_alert
        # Fallback to in-memory only if DB unavailable
        return await svc.acknowledge_alert(alert_id, user_id)
    except HTTPException:
        raise
    except KeyError:
        raise HTTPException(status_code=404, detail="Alert not found")
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to acknowledge alert")
        raise HTTPException(
            status_code=500, detail=f"Failed to acknowledge alert: {str(e)}"
        )


# ===== Drawdown Kill Switch Routes =====


class KillSwitchConfigRequest(BaseModel):
    """Kill switch configuration request"""

    enabled: bool = True
    max_drawdown_percent: float = Field(15.0, ge=0, le=100)
    warning_threshold_percent: float = Field(10.0, ge=0, le=100)
    critical_threshold_percent: float = Field(12.0, ge=0, le=100)
    recovery_threshold_percent: float = Field(5.0, ge=0, le=100)
    check_interval_seconds: int = Field(60, ge=10, le=3600)
    auto_recovery: bool = True
    shutdown_all_bots: bool = True


@router.get("/kill-switch/state", response_model=Dict)
async def get_kill_switch_state(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get current drawdown kill switch state"""
    try:
        state = drawdown_kill_switch.get_state()
        if state:
            return state.dict()
        return {"active": False, "message": "Kill switch not initialized"}
    except Exception as e:
        logger.error(f"Error getting kill switch state: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get state: {str(e)}")


@router.post("/kill-switch/activate", response_model=Dict)
async def activate_kill_switch(
    current_user: Annotated[dict, Depends(get_current_user)],
    reason: Optional[str] = None,
):
    """Manually activate drawdown kill switch"""
    try:
        success = await drawdown_kill_switch.manually_activate(
            reason or "Manual activation"
        )
        return {
            "success": success,
            "active": drawdown_kill_switch.is_active(),
            "message": "Kill switch activated" if success else "Failed to activate",
        }
    except Exception as e:
        logger.error(f"Error activating kill switch: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to activate: {str(e)}")


@router.post("/kill-switch/deactivate", response_model=Dict)
async def deactivate_kill_switch(
    current_user: Annotated[dict, Depends(get_current_user)],
    reason: Optional[str] = None,
):
    """Manually deactivate drawdown kill switch"""
    try:
        success = await drawdown_kill_switch.manually_deactivate(
            reason or "Manual deactivation"
        )
        return {
            "success": success,
            "active": drawdown_kill_switch.is_active(),
            "message": (
                "Kill switch deactivated"
                if success
                else "Failed to deactivate or not active"
            ),
        }
    except Exception as e:
        logger.error(f"Error deactivating kill switch: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to deactivate: {str(e)}")


@router.get("/kill-switch/events", response_model=Dict)
async def get_kill_switch_events(
    current_user: Annotated[dict, Depends(get_current_user)],
    limit: int = Query(50, ge=1, le=500),
):
    """Get recent drawdown kill switch events"""
    try:
        events = drawdown_kill_switch.get_events(limit)
        return {"events": [event.dict() for event in events], "count": len(events)}
    except Exception as e:
        logger.error(f"Error getting kill switch events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get events: {str(e)}")


@router.post("/kill-switch/config", response_model=Dict)
async def update_kill_switch_config(
    config: KillSwitchConfigRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Update drawdown kill switch configuration"""
    try:
        kill_switch_config = DrawdownKillSwitchConfig(**config.dict())
        drawdown_kill_switch.config = kill_switch_config
        return {
            "success": True,
            "config": kill_switch_config.dict(),
            "message": "Configuration updated",
        }
    except Exception as e:
        logger.error(f"Error updating kill switch config: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update config: {str(e)}"
        )


# ===== VaR Routes =====


class VaRRequest(BaseModel):
    """VaR calculation request"""

    returns: List[float]
    portfolio_value: float
    confidence_level: float = Field(0.95, ge=0.5, le=0.99)
    time_horizon_days: int = Field(1, ge=1, le=365)
    method: str = Field("historical", pattern="^(historical|parametric|monte_carlo)$")


@router.post("/var/calculate", response_model=Dict)
async def calculate_var(
    request: VaRRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Calculate Value at Risk (VaR)"""
    try:
        config = VaRConfig(
            confidence_level=request.confidence_level,
            time_horizon_days=request.time_horizon_days,
            method=request.method,
        )
        result = var_service.calculate_var(
            request.returns, request.portfolio_value, config
        )
        return result.dict()
    except Exception as e:
        logger.error(f"Error calculating VaR: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to calculate VaR: {str(e)}"
        )


@router.post("/var/multi-horizon", response_model=Dict)
async def calculate_multi_horizon_var(
    current_user: Annotated[dict, Depends(get_current_user)],
    returns: List[float],
    portfolio_value: float,
    confidence_level: float = Query(0.95, ge=0.5, le=0.99),
    horizons: Optional[List[int]] = None,
):
    """Calculate VaR for multiple time horizons"""
    try:
        if horizons is None:
            horizons = [1, 7, 30]

        results = var_service.calculate_multi_horizon_var(
            returns, portfolio_value, confidence_level, horizons
        )
        return {
            "results": results,
            "confidence_level": confidence_level,
            "portfolio_value": portfolio_value,
        }
    except Exception as e:
        logger.error(f"Error calculating multi-horizon VaR: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to calculate multi-horizon VaR: {str(e)}"
        )


# ===== Monte Carlo Routes =====


class MonteCarloRequest(BaseModel):
    """Monte Carlo simulation request"""

    historical_returns: List[float]
    initial_value: float
    num_simulations: int = Field(10000, ge=100, le=100000)
    time_horizon_days: int = Field(30, ge=1, le=365)
    confidence_level: float = Field(0.95, ge=0.5, le=0.99)
    random_seed: Optional[int] = None


@router.post("/monte-carlo/simulate", response_model=Dict)
async def run_monte_carlo_simulation(
    request: MonteCarloRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Run Monte Carlo simulation"""
    try:
        config = MonteCarloConfig(
            num_simulations=request.num_simulations,
            time_horizon_days=request.time_horizon_days,
            confidence_level=request.confidence_level,
            random_seed=request.random_seed,
        )
        result = monte_carlo_service.run_simulation(
            request.historical_returns, request.initial_value, config
        )
        return result.dict()
    except Exception as e:
        logger.error(f"Error running Monte Carlo simulation: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to run simulation: {str(e)}"
        )


@router.post("/monte-carlo/risk-of-ruin", response_model=Dict)
async def calculate_risk_of_ruin(
    current_user: Annotated[dict, Depends(get_current_user)],
    historical_returns: List[float],
    initial_value: float,
    target_value: float = 0.0,
    num_simulations: int = Query(10000, ge=1000, le=100000),
    time_horizon_days: int = Query(365, ge=1, le=3650),
):
    """Calculate risk of ruin"""
    try:
        result = monte_carlo_service.calculate_risk_of_ruin(
            historical_returns,
            initial_value,
            target_value,
            num_simulations,
            time_horizon_days,
        )
        return result
    except Exception as e:
        logger.error(f"Error calculating risk of ruin: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to calculate risk of ruin: {str(e)}"
        )
