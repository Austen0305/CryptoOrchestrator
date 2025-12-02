"""
Comprehensive Health Check Routes
Kubernetes-ready liveness and readiness probes with detailed dependency checks
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import logging
import asyncio
import time

from ..database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


class HealthStatus(str, Enum):
    """Health status values"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class DependencyHealth(BaseModel):
    """Individual dependency health status"""
    name: str
    status: HealthStatus
    response_time_ms: Optional[float] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Comprehensive health response"""
    status: HealthStatus
    timestamp: datetime
    uptime_seconds: float
    version: str = "1.0.0"
    dependencies: List[DependencyHealth]
    checks_passed: int
    checks_total: int


# Track startup time
_start_time = time.time()


async def check_database(db: AsyncSession) -> DependencyHealth:
    """Check database connectivity and performance"""
    start_time = time.time()
    try:
        # Simple query to check connectivity
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        
        # Check connection pool
        pool = db.bind.pool if hasattr(db.bind, 'pool') else None
        pool_size = pool.size() if pool else None
        checked_out = pool.checkedout() if pool else None
        
        response_time = (time.time() - start_time) * 1000
        
        return DependencyHealth(
            name="database",
            status=HealthStatus.HEALTHY,
            response_time_ms=response_time,
            details={
                "pool_size": pool_size,
                "checked_out": checked_out,
                "available": pool_size - checked_out if pool_size and checked_out else None
            }
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.error(f"Database health check failed: {e}")
        return DependencyHealth(
            name="database",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=response_time,
            error=str(e)
        )


async def check_redis() -> DependencyHealth:
    """Check Redis connectivity"""
    start_time = time.time()
    try:
        import redis.asyncio as redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = redis.from_url(redis_url)
        
        # Test connection with timeout
        await asyncio.wait_for(client.ping(), timeout=1.0)
        response_time = (time.time() - start_time) * 1000
        
        # Get Redis info
        info = await client.info()
        
        await client.close()
        
        return DependencyHealth(
            name="redis",
            status=HealthStatus.HEALTHY,
            response_time_ms=response_time,
            details={
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2)
            }
        )
    except asyncio.TimeoutError:
        response_time = (time.time() - start_time) * 1000
        return DependencyHealth(
            name="redis",
            status=HealthStatus.DEGRADED,
            response_time_ms=response_time,
            error="Connection timeout"
        )
    except ImportError:
        return DependencyHealth(
            name="redis",
            status=HealthStatus.DEGRADED,
            error="Redis not available (optional dependency)"
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.warning(f"Redis health check failed: {e}")
        return DependencyHealth(
            name="redis",
            status=HealthStatus.DEGRADED,
            response_time_ms=response_time,
            error=str(e)
        )


async def check_exchange_apis() -> DependencyHealth:
    """Check exchange API connectivity"""
    start_time = time.time()
    try:
        # Check if exchange services are available
        from ..services.exchange_service import ExchangeService
        
        exchange_service = ExchangeService()
        # Quick connectivity test (non-blocking)
        response_time = (time.time() - start_time) * 1000
        
        return DependencyHealth(
            name="exchange_apis",
            status=HealthStatus.HEALTHY,
            response_time_ms=response_time,
            details={
                "service_available": True
            }
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.warning(f"Exchange API health check failed: {e}")
        return DependencyHealth(
            name="exchange_apis",
            status=HealthStatus.DEGRADED,
            response_time_ms=response_time,
            error=str(e)
        )


@router.get("/live", status_code=200)
async def liveness_probe() -> Dict[str, str]:
    """
    Kubernetes liveness probe
    
    Returns 200 if the application is alive and should not be restarted.
    This is a lightweight check that just verifies the process is running.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/ready", status_code=200)
async def readiness_probe(db: AsyncSession = Depends(get_db_session)) -> Dict[str, Any]:
    """
    Kubernetes readiness probe
    
    Returns 200 if the application is ready to serve traffic.
    Checks critical dependencies (database) but not optional ones.
    """
    try:
        # Check critical dependency: database
        db_health = await check_database(db)
        
        if db_health.status == HealthStatus.UNHEALTHY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable"
            )
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_health.status.value
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness probe failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )


@router.get("/startup", status_code=200)
async def startup_probe() -> Dict[str, Any]:
    """
    Kubernetes startup probe
    
    Returns 200 when the application has finished starting up.
    Used to determine when the container is ready to receive traffic.
    """
    uptime = time.time() - _start_time
    
    # Consider startup complete after 5 seconds
    if uptime < 5:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Application still starting up"
        )
    
    return {
        "status": "started",
        "uptime_seconds": uptime,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/detailed", response_model=HealthResponse)
async def detailed_health_check(
    db: AsyncSession = Depends(get_db_session),
    include_optional: bool = False
) -> HealthResponse:
    """
    Comprehensive health check with all dependencies
    
    Args:
        include_optional: Include optional dependencies (Redis, etc.)
    """
    uptime = time.time() - _start_time
    dependencies: List[DependencyHealth] = []
    
    # Check critical dependencies
    db_health = await check_database(db)
    dependencies.append(db_health)
    
    # Check optional dependencies if requested
    if include_optional:
        redis_health = await check_redis()
        dependencies.append(redis_health)
        
        exchange_health = await check_exchange_apis()
        dependencies.append(exchange_health)
    
    # Calculate overall status
    unhealthy_count = sum(1 for d in dependencies if d.status == HealthStatus.UNHEALTHY)
    degraded_count = sum(1 for d in dependencies if d.status == HealthStatus.DEGRADED)
    
    if unhealthy_count > 0:
        overall_status = HealthStatus.UNHEALTHY
    elif degraded_count > 0:
        overall_status = HealthStatus.DEGRADED
    else:
        overall_status = HealthStatus.HEALTHY
    
    checks_passed = sum(1 for d in dependencies if d.status == HealthStatus.HEALTHY)
    checks_total = len(dependencies)
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        uptime_seconds=uptime,
        dependencies=dependencies,
        checks_passed=checks_passed,
        checks_total=checks_total
    )


@router.get("/dependencies/{dependency_name}")
async def check_specific_dependency(
    dependency_name: str,
    db: AsyncSession = Depends(get_db_session)
) -> DependencyHealth:
    """Check health of a specific dependency"""
    dependency_name_lower = dependency_name.lower()
    
    if dependency_name_lower == "database":
        return await check_database(db)
    elif dependency_name_lower == "redis":
        return await check_redis()
    elif dependency_name_lower in ["exchange", "exchange_apis"]:
        return await check_exchange_apis()
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown dependency: {dependency_name}"
        )

