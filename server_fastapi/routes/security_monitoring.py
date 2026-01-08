"""
Security Monitoring API Routes
Endpoints for security event logging and monitoring
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies.auth import require_permission
from ..services.security_monitoring_service import SecurityMonitoringService

router = APIRouter(prefix="/api/security/monitoring", tags=["Security Monitoring"])


# Pydantic Models
class SecurityEventRequest(BaseModel):
    event_type: str
    severity: str  # low, medium, high, critical
    description: str
    user_id: int | None = None
    ip_address: str | None = None
    metadata: dict[str, Any] | None = None


@router.post("/events")
async def log_security_event(
    request: SecurityEventRequest,
    current_user: dict = Depends(require_permission("admin:security")),
    db: AsyncSession = Depends(get_db_session),
):
    """Log a security event (Admin only)"""
    service = SecurityMonitoringService(db)

    event = await service.log_security_event(
        event_type=request.event_type,
        severity=request.severity,
        description=request.description,
        user_id=request.user_id,
        ip_address=request.ip_address,
        metadata=request.metadata,
    )

    return event


@router.get("/events")
async def get_security_events(
    event_type: str | None = Query(None),
    severity: str | None = Query(None),
    user_id: int | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    limit: int = Query(100, le=1000),
    current_user: dict = Depends(require_permission("admin:security")),
    db: AsyncSession = Depends(get_db_session),
):
    """Get security events (Admin only)"""
    service = SecurityMonitoringService(db)

    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None

    events = await service.get_security_events(
        event_type=event_type,
        severity=severity,
        user_id=user_id,
        start_date=start,
        end_date=end,
        limit=limit,
    )

    return {"events": events, "count": len(events)}


@router.get("/summary")
async def get_security_summary(
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(require_permission("admin:security")),
    db: AsyncSession = Depends(get_db_session),
):
    """Get security summary (Admin only)"""
    service = SecurityMonitoringService(db)

    summary = await service.get_security_summary(days=days)
    return summary
