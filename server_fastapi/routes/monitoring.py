"""
Monitoring and Alerting Routes
Provides endpoints for monitoring system and alerts
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from ..services.monitoring_alerting import monitoring_system, AlertLevel
from ..middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitoring", tags=["Monitoring"])


class AlertResponse(BaseModel):
    """Alert response model"""
    id: str
    level: str
    title: str
    message: str
    source: str
    timestamp: str
    resolved: bool
    resolved_at: Optional[str] = None


@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    level: Optional[str] = Query(None, description="Filter by alert level"),
    resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of alerts"),
    current_user: dict = Depends(get_current_user),
):
    """Get alerts"""
    try:
        alert_level = AlertLevel(level) if level else None
        alerts = monitoring_system.get_alerts(
            level=alert_level,
            resolved=resolved,
            limit=limit,
        )

        return [
            AlertResponse(
                id=alert.id,
                level=alert.level.value,
                title=alert.title,
                message=alert.message,
                source=alert.source,
                timestamp=alert.timestamp.isoformat(),
                resolved=alert.resolved,
                resolved_at=alert.resolved_at.isoformat() if alert.resolved_at else None,
            )
            for alert in alerts
        ]
    except Exception as e:
        logger.error(f"Error getting alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alerts: {str(e)}",
        )


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Resolve an alert"""
    try:
        monitoring_system.resolve_alert(alert_id)
        return {"message": "Alert resolved successfully"}
    except Exception as e:
        logger.error(f"Error resolving alert: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve alert: {str(e)}",
        )


@router.get("/stats")
async def get_monitoring_stats(
    current_user: dict = Depends(get_current_user),
):
    """Get monitoring statistics"""
    try:
        return monitoring_system.get_stats()
    except Exception as e:
        logger.error(f"Error getting monitoring stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitoring stats: {str(e)}",
        )
