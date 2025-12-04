"""
Health Check and System Status Endpoints
Provides comprehensive health monitoring for the application
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Optional, List, Any
from datetime import datetime
import logging
import asyncio

from ..database import get_db_context
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/health", tags=["Health"])


class HealthStatus(BaseModel):
    """Health status response"""

    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    version: str
    uptime_seconds: float
    checks: Dict[str, Dict[str, Any]]


class ComponentHealth(BaseModel):
    """Individual component health"""

    status: str
    message: Optional[str] = None
    response_time_ms: Optional[float] = None
    details: Optional[Dict] = None


# Track application start time
import time

_app_start_time = time.time()


async def check_database() -> ComponentHealth:
    """Check database connectivity"""
    start_time = time.time()
    try:
        async with get_db_context() as db:
            result = await db.execute(text("SELECT 1"))
            result.scalar()
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                status="healthy",
                message="Database connection successful",
                response_time_ms=round(response_time, 2),
            )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.error(f"Database health check failed: {e}", exc_info=True)
        return ComponentHealth(
            status="unhealthy",
            message=f"Database connection failed: {str(e)}",
            response_time_ms=round(response_time, 2),
        )


async def check_redis() -> ComponentHealth:
    """Check Redis connectivity (optional)"""
    start_time = time.time()
    try:
        from ..services.cache_service import cache_service

        if cache_service and cache_service.redis_available:
            # Try a simple ping operation
            test_key = "__health_check__"
            await cache_service.set(test_key, "ok", ttl=1)
            value = await cache_service.get(test_key)
            await cache_service.delete(test_key)
            response_time = (time.time() - start_time) * 1000

            if value == "ok":
                return ComponentHealth(
                    status="healthy",
                    message="Redis connection successful",
                    response_time_ms=round(response_time, 2),
                )
            else:
                return ComponentHealth(
                    status="degraded",
                    message="Redis connection test failed",
                    response_time_ms=round(response_time, 2),
                )
        else:
            return ComponentHealth(
                status="degraded",
                message="Redis not configured (using memory cache)",
                response_time_ms=0,
            )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.warning(f"Redis health check failed: {e}")
        return ComponentHealth(
            status="degraded",
            message=f"Redis unavailable: {str(e)}",
            response_time_ms=round(response_time, 2),
        )


async def check_exchange_apis() -> ComponentHealth:
    """Check exchange API connectivity"""
    start_time = time.time()
    try:
        from ..services.exchange_service import default_exchange

        # Try to get a simple market price (non-blocking)
        pairs = await default_exchange.get_all_trading_pairs()
        response_time = (time.time() - start_time) * 1000

        if pairs and len(pairs) > 0:
            return ComponentHealth(
                status="healthy",
                message=f"Exchange API accessible ({len(pairs)} pairs available)",
                response_time_ms=round(response_time, 2),
                details={"available_pairs": len(pairs)},
            )
        else:
            return ComponentHealth(
                status="degraded",
                message="Exchange API accessible but no pairs returned",
                response_time_ms=round(response_time, 2),
            )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.warning(f"Exchange API health check failed: {e}")
        return ComponentHealth(
            status="degraded",
            message=f"Exchange API unavailable: {str(e)}",
            response_time_ms=round(response_time, 2),
        )


async def check_trading_safety() -> ComponentHealth:
    """Check trading safety service"""
    start_time = time.time()
    try:
        from ..services.trading.trading_safety_service import get_trading_safety_service

        service = get_trading_safety_service()
        status_data = service.get_safety_status()
        response_time = (time.time() - start_time) * 1000

        return ComponentHealth(
            status="healthy",
            message=f"Trading safety service operational (Kill switch: {status_data['kill_switch_active']})",
            response_time_ms=round(response_time, 2),
            details={
                "kill_switch_active": status_data["kill_switch_active"],
                "trades_today": status_data["trades_today"],
                "daily_pnl": status_data["daily_pnl"],
            },
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.warning(f"Trading safety health check failed: {e}")
        return ComponentHealth(
            status="degraded",
            message=f"Trading safety service unavailable: {str(e)}",
            response_time_ms=round(response_time, 2),
        )


async def check_sl_tp_service() -> ComponentHealth:
    """Check stop-loss/take-profit service"""
    start_time = time.time()
    try:
        from ..services.trading.sl_tp_service import get_sl_tp_service

        service = get_sl_tp_service()
        active_orders = service.get_active_orders()
        response_time = (time.time() - start_time) * 1000

        return ComponentHealth(
            status="healthy",
            message=f"SL/TP service operational ({len(active_orders)} active orders)",
            response_time_ms=round(response_time, 2),
            details={"active_orders": len(active_orders)},
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.warning(f"SL/TP health check failed: {e}")
        return ComponentHealth(
            status="degraded",
            message=f"SL/TP service unavailable: {str(e)}",
            response_time_ms=round(response_time, 2),
        )


async def check_price_monitor() -> ComponentHealth:
    """Check price monitoring service"""
    start_time = time.time()
    try:
        from ..services.trading.price_monitor import get_price_monitor

        monitor = get_price_monitor()
        monitor_status = monitor.get_monitoring_status()
        response_time = (time.time() - start_time) * 1000

        status = "healthy" if monitor_status["monitoring"] else "idle"

        return ComponentHealth(
            status=status,
            message=f"Price monitor {'active' if monitor_status['monitoring'] else 'idle'}",
            response_time_ms=round(response_time, 2),
            details=monitor_status,
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.warning(f"Price monitor health check failed: {e}")
        return ComponentHealth(
            status="degraded",
            message=f"Price monitor unavailable: {str(e)}",
            response_time_ms=round(response_time, 2),
        )


@router.get("/", response_model=HealthStatus)
async def get_health():
    """
    Comprehensive health check endpoint

    Returns:
    - Overall system status
    - Individual component health
    - Response times
    - System uptime
    """
    try:
        # Run all health checks in parallel
        checks = await asyncio.gather(
            check_database(),
            check_redis(),
            check_exchange_apis(),
            check_trading_safety(),
            check_sl_tp_service(),
            check_price_monitor(),
            return_exceptions=True,
        )

        # Process results
        health_checks = {
            "database": (
                checks[0].dict()
                if not isinstance(checks[0], Exception)
                else {"status": "unhealthy", "message": str(checks[0])}
            ),
            "redis": (
                checks[1].dict()
                if not isinstance(checks[1], Exception)
                else {"status": "degraded", "message": str(checks[1])}
            ),
            "exchange_apis": (
                checks[2].dict()
                if not isinstance(checks[2], Exception)
                else {"status": "degraded", "message": str(checks[2])}
            ),
            "trading_safety": (
                checks[3].dict()
                if not isinstance(checks[3], Exception)
                else {"status": "degraded", "message": str(checks[3])}
            ),
            "sl_tp_service": (
                checks[4].dict()
                if not isinstance(checks[4], Exception)
                else {"status": "degraded", "message": str(checks[4])}
            ),
            "price_monitor": (
                checks[5].dict()
                if not isinstance(checks[5], Exception)
                else {"status": "degraded", "message": str(checks[5])}
            ),
        }

        # Determine overall status
        statuses = [check.get("status", "unknown") for check in health_checks.values()]
        if "unhealthy" in statuses:
            overall_status = "unhealthy"
        elif "degraded" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        # Calculate uptime
        uptime_seconds = time.time() - _app_start_time

        return HealthStatus(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat() + "Z",
            version="1.0.0",  # Could be read from config or package.json
            uptime_seconds=round(uptime_seconds, 2),
            checks=health_checks,
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@router.get("/ready")
async def get_readiness():
    """
    Kubernetes readiness probe endpoint

    Returns 200 if the service is ready to accept traffic
    Returns 503 if the service is not ready
    """
    try:
        # Check critical dependencies only
        db_health = await check_database()

        if db_health.status == "healthy":
            return {"status": "ready", "timestamp": datetime.utcnow().isoformat() + "Z"}
        else:
            raise HTTPException(
                status_code=503, detail="Service not ready: database unavailable"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")


@router.get("/live")
async def get_liveness():
    """
    Kubernetes liveness probe endpoint

    Returns 200 if the service is alive
    Returns 503 if the service should be restarted
    """
    try:
        # Simple check - just verify the service is responding
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "uptime_seconds": round(time.time() - _app_start_time, 2),
        }
    except Exception as e:
        logger.error(f"Liveness check failed: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Service not alive: {str(e)}")


@router.get("/startup")
async def get_startup():
    """
    Kubernetes startup probe endpoint

    Returns 200 if the service has finished starting up
    Returns 503 if the service is still starting
    """
    try:
        # Check if critical services are initialized
        from ..services.exchange_service import default_exchange

        db_health = await check_database()

        if db_health.status == "healthy" and default_exchange:
            return {
                "status": "started",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        else:
            raise HTTPException(status_code=503, detail="Service still starting up")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Startup check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=503, detail=f"Service startup check failed: {str(e)}"
        )
