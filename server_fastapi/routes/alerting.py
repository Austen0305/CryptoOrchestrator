"""
Alerting Routes
Endpoints for managing alerts, alerting rules, and incident management
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies.auth import get_current_user
from ..middleware.cache_manager import cached
from ..services.alerting.alerting_service import (
    AlertChannel,
    AlertSeverity,
    get_alerting_service,
)
from ..services.alerting.incident_management import (
    IncidentStatus,
    get_incident_management_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/alerting", tags=["Alerting"])


@router.get("/alerts")
@cached(ttl=60, prefix="active_alerts")  # 60s TTL for active alerts
async def get_active_alerts(
    current_user: Annotated[dict, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    severity: str | None = Query(None, description="Filter by severity"),
) -> list[dict[str, Any]]:
    """Get active alerts with pagination (admin only)"""
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    service = get_alerting_service()

    severity_enum = None
    if severity:
        try:
            severity_enum = AlertSeverity(severity.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")

    alerts = service.get_active_alerts(severity=severity_enum)

    # Apply pagination
    len(alerts)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_alerts = alerts[start_idx:end_idx]

    return [
        {
            "id": alert.id,
            "rule_name": alert.rule.name,
            "metric": alert.rule.metric,
            "current_value": alert.current_value,
            "threshold": alert.rule.threshold,
            "severity": alert.severity.value,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat(),
            "acknowledged": alert.acknowledged,
            "resolved": alert.resolved,
            "metadata": alert.metadata,
        }
        for alert in paginated_alerts
    ]


@router.get("/alerts/history")
@cached(ttl=120, prefix="alert_history")  # 120s TTL for alert history
async def get_alert_history(
    current_user: Annotated[dict, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    severity: str | None = Query(None),
) -> list[dict[str, Any]]:
    """Get alert history with pagination (admin only)"""
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    service = get_alerting_service()

    severity_enum = None
    if severity:
        try:
            severity_enum = AlertSeverity(severity.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")

    # Convert page/page_size to limit for service (fetch enough for current page)
    limit = page * page_size
    alerts = service.get_alert_history(limit=limit, severity=severity_enum)

    # Apply pagination
    len(alerts)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    alerts[start_idx:end_idx]

    return [
        {
            "id": alert.id,
            "rule_name": alert.rule.name,
            "metric": alert.rule.metric,
            "current_value": alert.current_value,
            "threshold": alert.rule.threshold,
            "severity": alert.severity.value,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat(),
            "acknowledged": alert.acknowledged,
            "resolved": alert.resolved,
        }
        for alert in alerts
    ]


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """Acknowledge an alert (admin only)"""
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    service = get_alerting_service()
    acknowledged_by = current_user.get("email") or current_user.get("id") or "admin"
    success = service.acknowledge_alert(alert_id, acknowledged_by=acknowledged_by)

    if success:
        return {"success": True, "message": "Alert acknowledged"}
    else:
        raise HTTPException(status_code=404, detail="Alert not found")


@router.post("/alerts/{rule_name}/resolve")
async def resolve_alert(
    rule_name: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """Resolve an active alert (admin only)"""
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    service = get_alerting_service()
    success = service.resolve_alert(rule_name)

    if success:
        return {"success": True, "message": f"Alert for rule '{rule_name}' resolved"}
    else:
        raise HTTPException(status_code=404, detail="Alert not found")


@router.get("/rules")
async def get_alert_rules(
    current_user: Annotated[dict, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> list[dict[str, Any]]:
    """Get all alert rules with pagination (admin only)"""
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    service = get_alerting_service()

    rules = service.get_alert_rules()

    # Apply pagination
    len(rules)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    rules[start_idx:end_idx]

    return [
        {
            "name": rule.name,
            "metric": rule.metric,
            "threshold": rule.threshold,
            "operator": rule.operator,
            "severity": rule.severity.value,
            "channels": [ch.value for ch in rule.channels],
            "duration": rule.duration,
            "cooldown": rule.cooldown,
            "last_triggered": (
                rule.last_triggered.isoformat() if rule.last_triggered else None
            ),
            "trigger_count": rule.trigger_count,
        }
        for rule in service.rules.values()
    ]


@router.post("/rules")
async def create_alert_rule(
    current_user: Annotated[dict, Depends(get_current_user)],
    rule_data: dict[str, Any],
) -> dict[str, Any]:
    """Create a new alert rule (admin only)"""
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    from ..services.alerting.alerting_service import AlertRule

    try:
        rule = AlertRule(
            name=rule_data["name"],
            metric=rule_data["metric"],
            threshold=rule_data["threshold"],
            operator=rule_data["operator"],
            severity=AlertSeverity(rule_data["severity"].lower()),
            channels=[AlertChannel(ch.lower()) for ch in rule_data.get("channels", [])],
            duration=rule_data.get("duration", 60),
            cooldown=rule_data.get("cooldown", 300),
        )

        service = get_alerting_service()
        service.register_rule(rule)

        return {"success": True, "rule": rule.name}
    except Exception as e:
        logger.error(f"Error creating alert rule: {e}", exc_info=True)
        raise HTTPException(
            status_code=400, detail=f"Failed to create alert rule: {str(e)}"
        )


@router.get("/fatigue-stats")
async def get_fatigue_stats(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """Get alert fatigue statistics (admin only)"""
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    service = get_alerting_service()
    return service.get_fatigue_stats()


@router.get("/incidents")
@cached(ttl=60, prefix="active_incidents")  # 60s TTL for active incidents
async def get_active_incidents(
    current_user: Annotated[dict, Depends(get_current_user)],
    severity: str | None = Query(None, description="Filter by severity"),
) -> list[dict[str, Any]]:
    """Get active incidents (admin only)"""
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    service = get_alerting_service()
    severity_enum = None
    if severity:
        try:
            severity_enum = AlertSeverity(severity.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
    incidents = service.get_active_incidents(severity=severity_enum)

    return [
        {
            "id": incident.id,
            "title": incident.title,
            "severity": incident.severity.value,
            "status": incident.status,
            "created_at": incident.created_at.isoformat(),
            "updated_at": incident.updated_at.isoformat(),
            "resolved_at": (
                incident.resolved_at.isoformat() if incident.resolved_at else None
            ),
            "assigned_to": incident.assigned_to,
            "related_alerts": incident.related_alerts,
            "metadata": incident.metadata,
        }
        for incident in incidents
    ]


@router.get("/incidents/{incident_id}")
async def get_incident(
    incident_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """Get incident details (admin only)"""
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    incident_service = get_incident_management_service()
    incident = incident_service.get_incident(incident_id)

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    return incident


@router.post("/incidents")
async def create_incident(
    current_user: Annotated[dict, Depends(get_current_user)],
    incident_data: dict[str, Any],
) -> dict[str, Any]:
    """Create a new incident (admin only)"""
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    incident_service = get_incident_management_service()

    try:
        incident = incident_service.create_incident(
            title=incident_data["title"],
            description=incident_data.get("description", ""),
            severity=incident_data["severity"],
            source=incident_data.get("source", "manual"),
            metadata=incident_data.get("metadata"),
        )
        return {"success": True, "incident": incident}
    except Exception as e:
        logger.error(f"Error creating incident: {e}", exc_info=True)
        raise HTTPException(
            status_code=400, detail=f"Failed to create incident: {str(e)}"
        )


@router.post("/incidents/{incident_id}/resolve")
async def resolve_incident(
    incident_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """Resolve an incident (admin only)"""
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    service = get_alerting_service()
    resolved_by = current_user.get("email") or current_user.get("id")
    success = service.resolve_incident(incident_id, resolved_by=resolved_by)

    if success:
        return {"success": True, "message": "Incident resolved"}
    else:
        raise HTTPException(status_code=404, detail="Incident not found")


@router.post("/incidents/{incident_id}/assign")
async def assign_incident(
    incident_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    assignee: str = Query(..., description="User to assign incident to"),
) -> dict[str, Any]:
    """Assign an incident to a user (admin only)"""
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    incident_service = get_incident_management_service()
    success = incident_service.assign_incident(incident_id, assignee)

    if success:
        return {"success": True, "message": f"Incident assigned to {assignee}"}
    else:
        raise HTTPException(status_code=404, detail="Incident not found")


@router.post("/incidents/{incident_id}/status")
async def update_incident_status(
    incident_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    status: str = Query(
        ...,
        description="New status (open, investigating, mitigating, resolved, closed)",
    ),
) -> dict[str, Any]:
    """Update incident status (admin only)"""
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        status_enum = IncidentStatus(status.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    incident_service = get_incident_management_service()
    updated_by = current_user.get("email") or current_user.get("id")
    success = incident_service.update_incident_status(
        incident_id, status_enum, updated_by=updated_by
    )

    if success:
        return {"success": True, "message": f"Incident status updated to {status}"}
    else:
        raise HTTPException(status_code=404, detail="Incident not found")
