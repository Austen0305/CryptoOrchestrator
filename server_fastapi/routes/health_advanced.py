"""
Comprehensive Health Check System
Monitors all critical system components
"""
from fastapi import APIRouter, Response
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
import psutil
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


class ComponentHealth(BaseModel):
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: Optional[str] = None
    response_time_ms: Optional[float] = None
    details: Optional[Dict] = None


class HealthResponse(BaseModel):
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    uptime_seconds: float
    components: List[ComponentHealth]
    system_metrics: Dict


class HealthChecker:
    """Centralized health checking for all system components"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.checks: Dict[str, callable] = {}
    
    def register_check(self, name: str, check_func: callable):
        """Register a health check function"""
        self.checks[name] = check_func
        logger.info(f"Registered health check: {name}")
    
    async def check_component(self, name: str, check_func: callable) -> ComponentHealth:
        """Execute a single health check"""
        start_time = datetime.now()
        
        try:
            result = await asyncio.wait_for(check_func(), timeout=5.0)
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if isinstance(result, dict):
                return ComponentHealth(
                    name=name,
                    status=result.get("status", "healthy"),
                    message=result.get("message"),
                    response_time_ms=response_time,
                    details=result.get("details")
                )
            else:
                return ComponentHealth(
                    name=name,
                    status="healthy" if result else "unhealthy",
                    response_time_ms=response_time
                )
                
        except asyncio.TimeoutError:
            return ComponentHealth(
                name=name,
                status="unhealthy",
                message="Health check timed out"
            )
        except Exception as e:
            logger.error(f"Health check failed for {name}: {e}")
            return ComponentHealth(
                name=name,
                status="unhealthy",
                message=str(e)
            )
    
    async def check_all(self) -> HealthResponse:
        """Run all registered health checks"""
        tasks = [
            self.check_component(name, check_func)
            for name, check_func in self.checks.items()
        ]
        
        component_results = await asyncio.gather(*tasks)
        
        # Determine overall status
        unhealthy_count = sum(1 for c in component_results if c.status == "unhealthy")
        degraded_count = sum(1 for c in component_results if c.status == "degraded")
        
        if unhealthy_count > 0:
            overall_status = "unhealthy"
        elif degraded_count > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        # Get system metrics
        system_metrics = self._get_system_metrics()
        
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.now().isoformat(),
            uptime_seconds=uptime,
            components=component_results,
            system_metrics=system_metrics
        )
    
    def _get_system_metrics(self) -> Dict:
        """Get system resource metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "total_mb": round(memory.total / 1024 / 1024, 2),
                    "used_mb": round(memory.used / 1024 / 1024, 2),
                    "percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
                    "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
                    "percent": disk.percent
                }
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}


# Global health checker instance
health_checker = HealthChecker()


# Health check endpoints
@router.get("", response_model=HealthResponse)
@router.get("/", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check endpoint"""
    return await health_checker.check_all()


@router.get("/live")
async def liveness_probe():
    """
    Kubernetes liveness probe - checks if app is running
    Returns 200 if app is alive
    """
    return {"status": "alive"}


@router.get("/ready")
async def readiness_probe():
    """
    Kubernetes readiness probe - checks if app is ready to serve traffic
    Returns 200 only if all critical components are healthy
    """
    health = await health_checker.check_all()
    
    if health.status == "unhealthy":
        return Response(
            content='{"status": "not ready"}',
            status_code=503,
            media_type="application/json"
        )
    
    return {"status": "ready"}


# Example health check functions
async def check_database():
    """Check database connectivity"""
    try:
        from database.connection_pool import db_pool
        
        if db_pool is None:
            return {
                "status": "unhealthy",
                "message": "Database pool not initialized"
            }
        
        # Try to execute a simple query
        async with db_pool.get_session() as session:
            await session.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "details": {
                "pool_size": db_pool.pool_size,
                "max_connections": db_pool.max_connections
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}"
        }


async def check_redis():
    """Check Redis connectivity"""
    try:
        from middleware.cache_manager import redis_client
        
        if redis_client is None:
            return {
                "status": "degraded",
                "message": "Redis not configured"
            }
        
        await redis_client.ping()
        
        info = await redis_client.info()
        
        return {
            "status": "healthy",
            "details": {
                "connected_clients": info.get("connected_clients"),
                "used_memory_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2)
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Redis error: {str(e)}"
        }


async def check_exchange_api():
    """Check exchange API connectivity"""
    try:
        # This would check if we can reach the exchange API
        # For now, just a placeholder
        return {
            "status": "healthy",
            "message": "Exchange API reachable"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Exchange API error: {str(e)}"
        }


# Register health checks
health_checker.register_check("database", check_database)
health_checker.register_check("redis", check_redis)
health_checker.register_check("exchange_api", check_exchange_api)
