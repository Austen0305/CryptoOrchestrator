"""
Automation Routes - Auto-hedging, strategy switching, smart alerts, portfolio optimization
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..dependencies.auth import get_current_user
from ..middleware.cache_manager import cached
from ..services.automation.auto_hedging import (
    HedgingConfig,
    HedgingStrategy,
    auto_hedging_service,
)
from ..services.automation.portfolio_optimizer import (
    OptimizationGoal,
    portfolio_optimizer,
)
from ..services.automation.smart_alerts import (
    AlertPriority,
    AlertRule,
    AlertType,
    smart_alerts_service,
)
from ..services.automation.strategy_switching import (
    StrategySwitchConfig,
    strategy_switching_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/automation", tags=["Automation"])


# ===== Auto-Hedging Routes =====


class HedgingConfigRequest(BaseModel):
    """Hedging configuration request"""

    strategy: HedgingStrategy
    enabled: bool = True
    threshold_percent: float = Field(5.0, ge=0, le=100)
    hedge_ratio: float = Field(1.0, ge=0, le=1)
    rebalance_interval_seconds: int = Field(3600, ge=60, le=86400)
    max_hedge_size: float = Field(0.5, ge=0, le=1)


@router.post("/hedging/start", response_model=dict)
async def start_hedging(
    portfolio_id: str,
    config: HedgingConfigRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Start automatic hedging for a portfolio"""
    try:
        hedging_config = HedgingConfig(**config.dict())
        success = await auto_hedging_service.start_hedging(portfolio_id, hedging_config)
        return {
            "success": success,
            "portfolio_id": portfolio_id,
            "config": hedging_config.dict(),
            "message": "Hedging started" if success else "Failed to start hedging",
        }
    except Exception as e:
        logger.error(f"Error starting hedging: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start hedging: {str(e)}"
        )


@router.post("/hedging/stop", response_model=dict)
async def stop_hedging(
    portfolio_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Stop automatic hedging for a portfolio"""
    try:
        success = await auto_hedging_service.stop_hedging(portfolio_id)
        return {
            "success": success,
            "portfolio_id": portfolio_id,
            "message": "Hedging stopped" if success else "Failed to stop hedging",
        }
    except Exception as e:
        logger.error(f"Error stopping hedging: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop hedging: {str(e)}")


@router.get("/hedging/positions", response_model=dict)
async def get_hedge_positions(
    current_user: Annotated[dict, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    portfolio_id: str | None = None,
):
    """Get active hedge positions with pagination"""
    try:
        positions = auto_hedging_service.get_active_hedges(portfolio_id)

        # Apply pagination
        total = len(positions)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_positions = positions[start_idx:end_idx]

        return {
            "positions": [pos.dict() for pos in paginated_positions],
            "count": total,
        }
    except Exception as e:
        logger.error(f"Error getting hedge positions: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get hedge positions: {str(e)}"
        )


# ===== Strategy Switching Routes =====


class StrategySwitchConfigRequest(BaseModel):
    """Strategy switching configuration request"""

    enabled: bool = True
    switch_on_regime_change: bool = True
    switch_on_performance: bool = True
    performance_threshold: float = Field(-0.10, ge=-1, le=0)
    check_interval_seconds: int = Field(3600, ge=60, le=86400)
    min_performance_period_hours: int = Field(24, ge=1, le=720)


@router.post("/strategy-switching/start", response_model=dict)
async def start_strategy_switching(
    bot_id: str,
    config: StrategySwitchConfigRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Start strategy switching monitoring for a bot"""
    try:
        switch_config = StrategySwitchConfig(**config.dict())
        success = await strategy_switching_service.start_monitoring(
            bot_id, switch_config
        )
        return {
            "success": success,
            "bot_id": bot_id,
            "config": switch_config.dict(),
            "message": (
                "Strategy switching started"
                if success
                else "Failed to start strategy switching"
            ),
        }
    except Exception as e:
        logger.error(f"Error starting strategy switching: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start strategy switching: {str(e)}"
        )


@router.post("/strategy-switching/stop", response_model=dict)
async def stop_strategy_switching(
    bot_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Stop strategy switching monitoring for a bot"""
    try:
        success = await strategy_switching_service.stop_monitoring(bot_id)
        return {
            "success": success,
            "bot_id": bot_id,
            "message": (
                "Strategy switching stopped"
                if success
                else "Failed to stop strategy switching"
            ),
        }
    except Exception as e:
        logger.error(f"Error stopping strategy switching: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to stop strategy switching: {str(e)}"
        )


@router.get("/strategy-switching/history", response_model=dict)
async def get_switch_history(
    current_user: Annotated[dict, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    bot_id: str | None = Query(None),
):
    """Get strategy switch history with pagination"""
    try:
        # Convert page/page_size to limit for service (fetch enough for current page)
        limit = page * page_size
        history = strategy_switching_service.get_switch_history(bot_id, limit)

        # Apply pagination
        total = len(history)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_history = history[start_idx:end_idx]

        return {
            "history": [switch.dict() for switch in paginated_history],
            "count": total,
        }
    except Exception as e:
        logger.error(f"Error getting switch history: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get switch history: {str(e)}"
        )


# ===== Smart Alerts Routes =====


class AlertRuleRequest(BaseModel):
    """Alert rule request"""

    id: str
    name: str
    type: AlertType
    priority: AlertPriority
    enabled: bool = True
    conditions: dict[str, Any]
    actions: list[str]
    cooldown_seconds: int = Field(3600, ge=60, le=86400)


@router.post("/alerts/rules", response_model=dict)
async def create_alert_rule(
    rule: AlertRuleRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Create a new alert rule"""
    try:
        alert_rule = AlertRule(**rule.dict())
        success = await smart_alerts_service.create_rule(alert_rule)
        return {
            "success": success,
            "rule": alert_rule.dict(),
            "message": (
                "Alert rule created" if success else "Failed to create alert rule"
            ),
        }
    except Exception as e:
        logger.error(f"Error creating alert rule: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create alert rule: {str(e)}"
        )


@router.put("/alerts/rules/{rule_id}", response_model=dict)
async def update_alert_rule(
    rule_id: str,
    updates: dict[str, Any],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Update an alert rule"""
    try:
        success = await smart_alerts_service.update_rule(rule_id, updates)
        return {
            "success": success,
            "rule_id": rule_id,
            "message": (
                "Alert rule updated" if success else "Failed to update alert rule"
            ),
        }
    except Exception as e:
        logger.error(f"Error updating alert rule: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update alert rule: {str(e)}"
        )


@router.delete("/alerts/rules/{rule_id}", response_model=dict)
async def delete_alert_rule(
    rule_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Delete an alert rule"""
    try:
        success = await smart_alerts_service.delete_rule(rule_id)
        return {
            "success": success,
            "rule_id": rule_id,
            "message": (
                "Alert rule deleted" if success else "Failed to delete alert rule"
            ),
        }
    except Exception as e:
        logger.error(f"Error deleting alert rule: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete alert rule: {str(e)}"
        )


@router.get("/alerts/active", response_model=dict)
@cached(ttl=60, prefix="automation_alerts")  # 60s TTL for automation alerts
async def get_active_alerts(
    current_user: Annotated[dict, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    priority: AlertPriority | None = Query(None),
):
    """Get active alerts with pagination"""
    try:
        alerts = smart_alerts_service.get_active_alerts(priority)

        # Apply pagination
        total = len(alerts)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_alerts = alerts[start_idx:end_idx]

        return {"alerts": [alert.dict() for alert in paginated_alerts], "count": total}
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get active alerts: {str(e)}"
        )


@router.post("/alerts/{alert_id}/acknowledge", response_model=dict)
async def acknowledge_alert(
    alert_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Acknowledge an alert"""
    try:
        success = await smart_alerts_service.acknowledge_alert(alert_id)
        return {
            "success": success,
            "alert_id": alert_id,
            "message": (
                "Alert acknowledged" if success else "Failed to acknowledge alert"
            ),
        }
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to acknowledge alert: {str(e)}"
        )


@router.get("/alerts/history", response_model=dict)
@cached(
    ttl=120, prefix="automation_alert_history"
)  # 120s TTL for automation alert history
async def get_alert_history(
    current_user: Annotated[dict, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    rule_id: str | None = Query(None),
):
    """Get alert history with pagination"""
    try:
        # Convert page/page_size to limit for service (fetch enough for current page)
        limit = page * page_size
        history = smart_alerts_service.get_alert_history(rule_id, limit)

        # Apply pagination
        total = len(history)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_history = history[start_idx:end_idx]

        return {
            "history": [alert.dict() for alert in paginated_history],
            "count": total,
        }
    except Exception as e:
        logger.error(f"Error getting alert history: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get alert history: {str(e)}"
        )


# ===== Portfolio Optimization Routes =====


class PortfolioOptimizationRequest(BaseModel):
    """Portfolio optimization request"""

    portfolio: dict[str, Any]
    goals: list[OptimizationGoal]
    preferences: dict[str, Any] | None = None


@router.post("/portfolio/optimize", response_model=dict)
async def optimize_portfolio(
    request: PortfolioOptimizationRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Analyze portfolio and generate optimization recommendations"""
    try:
        recommendations = await portfolio_optimizer.analyze_portfolio(
            request.portfolio, request.goals, request.preferences
        )
        return {
            "recommendations": [rec.dict() for rec in recommendations],
            "count": len(recommendations),
        }
    except Exception as e:
        logger.error(f"Error optimizing portfolio: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to optimize portfolio: {str(e)}"
        )
