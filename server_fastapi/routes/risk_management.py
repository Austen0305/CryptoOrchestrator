"""
Enhanced Risk Management Routes - Complete risk management API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional, List
import logging
from pydantic import BaseModel, Field
from datetime import datetime

from ..services.risk_service import get_risk_service, RiskService, RiskLimits, RiskAlert, RiskMetrics
from ..services.risk.drawdown_kill_switch import (
    drawdown_kill_switch,
    DrawdownKillSwitchConfig,
    DrawdownState,
    DrawdownEvent
)
from ..services.risk.var_service import var_service, VaRConfig, VaRResult
from ..services.risk.monte_carlo_service import monte_carlo_service, MonteCarloConfig, MonteCarloResult
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/risk", tags=["Risk Management"])


def risk_service_dep() -> RiskService:
    return get_risk_service()


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
                "minDiversification": 0.5
            }
        }
    }


@router.get("/metrics", response_model=RiskMetrics)
async def get_metrics(svc: RiskService = Depends(risk_service_dep)):
    return await svc.get_metrics()


@router.get("/alerts", response_model=list[RiskAlert])
async def get_alerts(svc: RiskService = Depends(risk_service_dep)):
    return await svc.get_alerts()


@router.get("/limits", response_model=RiskLimits)
async def get_limits(svc: RiskService = Depends(risk_service_dep)):
    return await svc.get_limits()


@router.post("/limits", response_model=RiskLimits)
async def update_limits(payload: UpdateLimitsRequest, svc: RiskService = Depends(risk_service_dep)):
    # Manual validation to enforce reasonable ranges beyond model bounds if needed
    updates: Dict[str, Any] = {}
    for field, value in payload.model_dump(exclude_none=True).items():
        if field == "maxPositionSize" and not (0 <= value <= 100):
            raise HTTPException(status_code=400, detail="maxPositionSize out of range (0-100)")
        if field == "maxDailyLoss" and not (0 <= value <= 100):
            raise HTTPException(status_code=400, detail="maxDailyLoss out of range (0-100)")
        if field == "maxPortfolioRisk" and not (0 <= value <= 100):
            raise HTTPException(status_code=400, detail="maxPortfolioRisk out of range (0-100)")
        if field == "maxLeverage" and not (1 <= value <= 10):
            raise HTTPException(status_code=400, detail="maxLeverage out of range (1-10)")
        if field == "maxCorrelation" and not (0 <= value <= 1):
            raise HTTPException(status_code=400, detail="maxCorrelation out of range (0-1)")
        if field == "minDiversification" and not (0 <= value <= 1):
            raise HTTPException(status_code=400, detail="minDiversification out of range (0-1)")
        updates[field] = value
    updated = await svc.update_limits(updates)
    return updated


@router.post("/alerts/{alert_id}/acknowledge", response_model=RiskAlert)
async def acknowledge_alert(
    alert_id: str,
    svc: RiskService = Depends(risk_service_dep),
    current_user: dict = Depends(get_current_user)
):
    """Acknowledge a risk alert"""
    try:
        return await svc.acknowledge_alert(alert_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Alert not found")
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")


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
    current_user: dict = Depends(get_current_user)
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
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Manually activate drawdown kill switch"""
    try:
        success = await drawdown_kill_switch.manually_activate(reason or "Manual activation")
        return {
            "success": success,
            "active": drawdown_kill_switch.is_active(),
            "message": "Kill switch activated" if success else "Failed to activate"
        }
    except Exception as e:
        logger.error(f"Error activating kill switch: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to activate: {str(e)}")


@router.post("/kill-switch/deactivate", response_model=Dict)
async def deactivate_kill_switch(
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Manually deactivate drawdown kill switch"""
    try:
        success = await drawdown_kill_switch.manually_deactivate(reason or "Manual deactivation")
        return {
            "success": success,
            "active": drawdown_kill_switch.is_active(),
            "message": "Kill switch deactivated" if success else "Failed to deactivate or not active"
        }
    except Exception as e:
        logger.error(f"Error deactivating kill switch: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to deactivate: {str(e)}")


@router.get("/kill-switch/events", response_model=Dict)
async def get_kill_switch_events(
    limit: int = Query(50, ge=1, le=500),
    current_user: dict = Depends(get_current_user)
):
    """Get recent drawdown kill switch events"""
    try:
        events = drawdown_kill_switch.get_events(limit)
        return {
            "events": [event.dict() for event in events],
            "count": len(events)
        }
    except Exception as e:
        logger.error(f"Error getting kill switch events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get events: {str(e)}")


@router.post("/kill-switch/config", response_model=Dict)
async def update_kill_switch_config(
    config: KillSwitchConfigRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update drawdown kill switch configuration"""
    try:
        kill_switch_config = DrawdownKillSwitchConfig(**config.dict())
        drawdown_kill_switch.config = kill_switch_config
        return {
            "success": True,
            "config": kill_switch_config.dict(),
            "message": "Configuration updated"
        }
    except Exception as e:
        logger.error(f"Error updating kill switch config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")


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
    current_user: dict = Depends(get_current_user)
):
    """Calculate Value at Risk (VaR)"""
    try:
        config = VaRConfig(
            confidence_level=request.confidence_level,
            time_horizon_days=request.time_horizon_days,
            method=request.method
        )
        result = var_service.calculate_var(request.returns, request.portfolio_value, config)
        return result.dict()
    except Exception as e:
        logger.error(f"Error calculating VaR: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate VaR: {str(e)}")


@router.post("/var/multi-horizon", response_model=Dict)
async def calculate_multi_horizon_var(
    returns: List[float],
    portfolio_value: float,
    confidence_level: float = Query(0.95, ge=0.5, le=0.99),
    horizons: Optional[List[int]] = None,
    current_user: dict = Depends(get_current_user)
):
    """Calculate VaR for multiple time horizons"""
    try:
        if horizons is None:
            horizons = [1, 7, 30]
        
        results = var_service.calculate_multi_horizon_var(
            returns,
            portfolio_value,
            confidence_level,
            horizons
        )
        return {
            "results": results,
            "confidence_level": confidence_level,
            "portfolio_value": portfolio_value
        }
    except Exception as e:
        logger.error(f"Error calculating multi-horizon VaR: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate multi-horizon VaR: {str(e)}")


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
    current_user: dict = Depends(get_current_user)
):
    """Run Monte Carlo simulation"""
    try:
        config = MonteCarloConfig(
            num_simulations=request.num_simulations,
            time_horizon_days=request.time_horizon_days,
            confidence_level=request.confidence_level,
            random_seed=request.random_seed
        )
        result = monte_carlo_service.run_simulation(
            request.historical_returns,
            request.initial_value,
            config
        )
        return result.dict()
    except Exception as e:
        logger.error(f"Error running Monte Carlo simulation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run simulation: {str(e)}")


@router.post("/monte-carlo/risk-of-ruin", response_model=Dict)
async def calculate_risk_of_ruin(
    historical_returns: List[float],
    initial_value: float,
    target_value: float = 0.0,
    num_simulations: int = Query(10000, ge=1000, le=100000),
    time_horizon_days: int = Query(365, ge=1, le=3650),
    current_user: dict = Depends(get_current_user)
):
    """Calculate risk of ruin"""
    try:
        result = monte_carlo_service.calculate_risk_of_ruin(
            historical_returns,
            initial_value,
            target_value,
            num_simulations,
            time_horizon_days
        )
        return result
    except Exception as e:
        logger.error(f"Error calculating risk of ruin: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate risk of ruin: {str(e)}")
