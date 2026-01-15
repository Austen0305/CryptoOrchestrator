"""
Platform Health Metrics API
System health dashboard with uptime, error rates, performance, and resource usage
"""

import logging
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies.auth import require_permission
from ..services.health_monitor import HealthMonitor
from ..services.monitoring.performance_monitor import PerformanceMonitor
from ..services.monitoring.production_monitor import production_monitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/platform-health", tags=["Platform Health"])

# Initialize monitors
health_monitor = HealthMonitor()
performance_monitor = PerformanceMonitor()


@router.get("/dashboard")
async def get_platform_health_dashboard(
    current_user: Annotated[dict, Depends(require_permission("admin:metrics"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    """Get comprehensive platform health dashboard (admin only)"""
    try:
        # Get system health
        system_health = await production_monitor.get_system_health()

        # Get performance metrics
        performance_metrics = await performance_monitor.collect_system_metrics()

        # Get database health
        db_health = await health_monitor.check_database()

        # Get Redis health
        redis_health = await health_monitor.check_redis()

        # Get uptime
        uptime_seconds = (
            datetime.now(UTC) - production_monitor.start_time
        ).total_seconds()
        uptime_days = uptime_seconds / 86400

        # Get error rates (from production monitor)
        error_rate = production_monitor.error_rate_24h

        return {
            "overall_status": system_health.get("status", "unknown"),
            "uptime": {
                "seconds": uptime_seconds,
                "days": round(uptime_days, 2),
                "formatted": f"{int(uptime_days)} days, {int((uptime_seconds % 86400) / 3600)} hours",
            },
            "system_resources": {
                "cpu_percent": performance_metrics.cpu_usage,
                "memory_percent": performance_metrics.memory_usage,
                "disk_usage_percent": performance_metrics.disk_usage,
                "network_io": performance_metrics.network_io,
            },
            "services": {
                "database": db_health,
                "redis": redis_health,
                "api_server": {
                    "status": "healthy",
                    "uptime_seconds": uptime_seconds,
                },
            },
            "error_rates": {
                "error_rate_24h": error_rate,
                "total_errors_24h": production_monitor.total_errors_24h,
            },
            "performance": {
                "average_response_time_ms": performance_metrics.average_response_time_ms,
                "requests_per_second": performance_metrics.requests_per_second,
                "cache_hit_rate": performance_metrics.cache_hit_rate,
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting platform health dashboard: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get platform health dashboard: {str(e)}"
        )


@router.get("/uptime")
async def get_uptime_metrics(
    current_user: Annotated[dict, Depends(require_permission("admin:metrics"))],
) -> dict[str, Any]:
    """Get system uptime metrics (admin only)"""
    try:
        uptime_seconds = (
            datetime.now(UTC) - production_monitor.start_time
        ).total_seconds()
        uptime_days = uptime_seconds / 86400
        uptime_hours = uptime_seconds / 3600

        return {
            "uptime_seconds": uptime_seconds,
            "uptime_days": round(uptime_days, 2),
            "uptime_hours": round(uptime_hours, 2),
            "formatted": f"{int(uptime_days)} days, {int((uptime_seconds % 86400) / 3600)} hours, {int((uptime_seconds % 3600) / 60)} minutes",
            "start_time": production_monitor.start_time.isoformat(),
            "current_time": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting uptime metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get uptime metrics: {str(e)}"
        )


@router.get("/error-rates")
async def get_error_rates(
    current_user: Annotated[dict, Depends(require_permission("admin:metrics"))],
    hours: int = Query(24, ge=1, le=168, description="Number of hours to analyze"),
) -> dict[str, Any]:
    """Get error rates and error analysis (admin only)"""
    try:
        # Get error rate from production monitor
        error_rate = production_monitor.error_rate_24h
        total_errors = production_monitor.total_errors_24h

        # Get error breakdown by type (if available)
        error_breakdown = {
            "database_errors": 0,  # Would come from error tracking
            "api_errors": 0,
            "external_service_errors": 0,
            "other_errors": 0,
        }

        return {
            "period_hours": hours,
            "error_rate_percent": round(error_rate, 2),
            "total_errors": total_errors,
            "error_breakdown": error_breakdown,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting error rates: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get error rates: {str(e)}"
        )


@router.get("/performance")
async def get_performance_metrics(
    current_user: Annotated[dict, Depends(require_permission("admin:metrics"))],
) -> dict[str, Any]:
    """Get performance metrics (admin only)"""
    try:
        metrics = await performance_monitor.collect_system_metrics()

        return {
            "system": {
                "cpu_usage_percent": metrics.cpu_usage,
                "memory_usage_percent": metrics.memory_usage,
                "disk_usage_percent": metrics.disk_usage,
                "network_io": metrics.network_io,
            },
            "application": {
                "average_response_time_ms": metrics.average_response_time_ms,
                "requests_per_second": metrics.requests_per_second,
                "cache_hit_rate": metrics.cache_hit_rate,
                "active_connections": metrics.active_connections,
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get performance metrics: {str(e)}"
        )


@router.get("/resource-usage")
async def get_resource_usage(
    current_user: Annotated[dict, Depends(require_permission("admin:metrics"))],
) -> dict[str, Any]:
    """Get resource usage metrics (admin only)"""
    try:
        metrics = await performance_monitor.collect_system_metrics()

        return {
            "cpu": {
                "usage_percent": metrics.cpu_usage,
                "status": (
                    "critical"
                    if metrics.cpu_usage > 90
                    else "warning"
                    if metrics.cpu_usage > 70
                    else "normal"
                ),
            },
            "memory": {
                "usage_percent": metrics.memory_usage,
                "status": (
                    "critical"
                    if metrics.memory_usage > 90
                    else "warning"
                    if metrics.memory_usage > 70
                    else "normal"
                ),
            },
            "disk": {
                "usage_percent": metrics.disk_usage,
                "status": (
                    "critical"
                    if metrics.disk_usage > 90
                    else "warning"
                    if metrics.disk_usage > 70
                    else "normal"
                ),
            },
            "network": {
                "io": metrics.network_io,
                "status": "normal",  # Would calculate based on thresholds
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting resource usage: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get resource usage: {str(e)}"
        )


@router.get("/services")
async def get_services_health(
    current_user: Annotated[dict, Depends(require_permission("admin:metrics"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    """Get health status of all services (admin only)"""
    try:
        # Check all services
        db_health = await health_monitor.check_database()
        redis_health = await health_monitor.check_redis()

        # Determine overall status
        all_healthy = (
            db_health.get("status") == "healthy"
            and redis_health.get("status") == "healthy"
        )

        return {
            "overall_status": "healthy" if all_healthy else "degraded",
            "services": {
                "database": db_health,
                "redis": redis_health,
                "api_server": {
                    "status": "healthy",
                    "message": "API server is running",
                },
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting services health: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get services health: {str(e)}"
        )
