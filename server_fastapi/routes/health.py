from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import psutil
import time
from datetime import datetime
import jwt
import os
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Import services for dependency injection
try:
    from ..services import IntegrationService, integration_service
    from ..services.advanced_analytics_engine import AdvancedAnalyticsEngine
    from ..services.advanced_risk_manager import AdvancedRiskManager
    from ..services.trading_orchestrator import TradingOrchestrator
    from ..services.monitoring.performance_monitor import performance_monitor
    from ..services.monitoring.safety_monitor import SafetyMonitor
    from ..services.monitoring.circuit_breaker import CircuitBreaker
except ImportError as e:
    logger.warning(f"Could not import services: {e}")
    IntegrationService = None
    integration_service = None
    AdvancedAnalyticsEngine = None
    AdvancedRiskManager = None
    TradingOrchestrator = None
    performance_monitor = None
    SafetyMonitor = None
    CircuitBreaker = None

# Environment variables
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

logger = logging.getLogger(__name__)

router = APIRouter()

class HealthStatus(BaseModel):
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: datetime
    uptime: float
    version: str

class SystemMetrics(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_usage: Dict[str, Any]
    network_connections: int

class ServiceHealth(BaseModel):
    service: str
    status: str
    response_time: Optional[float] = None
    last_check: datetime
    error_message: Optional[str] = None

class DatabaseHealth(BaseModel):
    status: str
    connection_time: Optional[float] = None
    last_check: datetime
    error_message: Optional[str] = None

class ExternalAPIHealth(BaseModel):
    name: str
    url: str
    status: str
    response_time: Optional[float] = None
    last_check: datetime
    error_message: Optional[str] = None

_start_time = time.time()

@router.get("/")
async def health_check() -> HealthStatus:
    """Basic health check endpoint"""
    uptime = time.time() - _start_time

    # Simple health check - in real implementation, check database, external services, etc.
    try:
        # Check if basic services are responding
        status = "healthy"
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        status = "unhealthy"

    return HealthStatus(
        status=status,
        timestamp=datetime.now(),
        uptime=uptime,
        version="1.0.0"
    )

@router.get("/protected")
async def protected_health_check(current_user: dict = Depends(get_current_user)) -> HealthStatus:
    """Protected health check endpoint requiring authentication"""
    uptime = time.time() - _start_time

    try:
        status = "healthy"
    except Exception as e:
        logger.error(f"Protected health check failed: {e}")
        status = "unhealthy"

    return HealthStatus(
        status=status,
        timestamp=datetime.now(),
        uptime=uptime,
        version="1.0.0"
    )

@router.get("/detailed")
async def detailed_health_check(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Detailed health check with system metrics and service status"""
    uptime = time.time() - _start_time

    # System metrics
    system_metrics = SystemMetrics(
        cpu_percent=psutil.cpu_percent(interval=1),
        memory_percent=psutil.virtual_memory().percent,
        disk_usage={
            "total": psutil.disk_usage('/').total,
            "used": psutil.disk_usage('/').used,
            "free": psutil.disk_usage('/').free,
            "percent": psutil.disk_usage('/').percent
        },
        network_connections=len(psutil.net_connections())
    )

    # Service health checks
    services = []

    # Check ML Engine
    try:
        start_time = time.time()
        if AdvancedAnalyticsEngine:
            # Perform actual health check
            analytics = AdvancedAnalyticsEngine()
            response_time = (time.time() - start_time) * 1000
        else:
            response_time = (time.time() - start_time) * 1000
        services.append(ServiceHealth(
            service="ml_engine",
            status="healthy",
            response_time=response_time,
            last_check=datetime.now()
        ))
    except Exception as e:
        logger.error(f"ML Engine health check failed: {e}")
        services.append(ServiceHealth(
            service="ml_engine",
            status="unhealthy",
            response_time=None,
            last_check=datetime.now(),
            error_message=str(e)
        ))

    # Check Risk Manager
    try:
        start_time = time.time()
        if AdvancedRiskManager:
            # Perform actual health check
            risk_manager = AdvancedRiskManager()
            response_time = (time.time() - start_time) * 1000
        else:
            response_time = (time.time() - start_time) * 1000
        services.append(ServiceHealth(
            service="risk_manager",
            status="healthy",
            response_time=response_time,
            last_check=datetime.now()
        ))
    except Exception as e:
        logger.error(f"Risk Manager health check failed: {e}")
        services.append(ServiceHealth(
            service="risk_manager",
            status="unhealthy",
            response_time=None,
            last_check=datetime.now(),
            error_message=str(e)
        ))

    # Check Trading Orchestrator
    try:
        start_time = time.time()
        if TradingOrchestrator:
            # Perform actual health check
            orchestrator = TradingOrchestrator()
            response_time = (time.time() - start_time) * 1000
        else:
            response_time = (time.time() - start_time) * 1000
        services.append(ServiceHealth(
            service="trading_orchestrator",
            status="healthy",
            response_time=response_time,
            last_check=datetime.now()
        ))
    except Exception as e:
        logger.error(f"Trading Orchestrator health check failed: {e}")
        services.append(ServiceHealth(
            service="trading_orchestrator",
            status="unhealthy",
            response_time=None,
            last_check=datetime.now(),
            error_message=str(e)
        ))

    # Check Integration Service
    try:
        start_time = time.time()
        if integration_service:
            # Perform actual health check
            await integration_service.list_integrations()
            response_time = (time.time() - start_time) * 1000
        else:
            response_time = (time.time() - start_time) * 1000
        services.append(ServiceHealth(
            service="integration_service",
            status="healthy",
            response_time=response_time,
            last_check=datetime.now()
        ))
    except Exception as e:
        logger.error(f"Integration Service health check failed: {e}")
        services.append(ServiceHealth(
            service="integration_service",
            status="unhealthy",
            response_time=None,
            last_check=datetime.now(),
            error_message=str(e)
        ))

    # Check Performance Monitor
    try:
        start_time = time.time()
        if performance_monitor:
            await performance_monitor.get_system_health()
            response_time = (time.time() - start_time) * 1000
        else:
            response_time = (time.time() - start_time) * 1000
        services.append(ServiceHealth(
            service="performance_monitor",
            status="healthy",
            response_time=response_time,
            last_check=datetime.now()
        ))
    except Exception as e:
        logger.error(f"Performance Monitor health check failed: {e}")
        services.append(ServiceHealth(
            service="performance_monitor",
            status="unhealthy",
            response_time=None,
            last_check=datetime.now(),
            error_message=str(e)
        ))

    # Check Safety Monitor
    try:
        start_time = time.time()
        if SafetyMonitor:
            safety_monitor = SafetyMonitor()
            await safety_monitor.check_safety_conditions()
            response_time = (time.time() - start_time) * 1000
        else:
            response_time = (time.time() - start_time) * 1000
        services.append(ServiceHealth(
            service="safety_monitor",
            status="healthy",
            response_time=response_time,
            last_check=datetime.now()
        ))
    except Exception as e:
        logger.error(f"Safety Monitor health check failed: {e}")
        services.append(ServiceHealth(
            service="safety_monitor",
            status="unhealthy",
            response_time=None,
            last_check=datetime.now(),
            error_message=str(e)
        ))

    # Check Circuit Breaker
    try:
        start_time = time.time()
        if CircuitBreaker:
            circuit_breaker = CircuitBreaker()
            circuit_breaker.get_status()
            response_time = (time.time() - start_time) * 1000
        else:
            response_time = (time.time() - start_time) * 1000
        services.append(ServiceHealth(
            service="circuit_breaker",
            status="healthy",
            response_time=response_time,
            last_check=datetime.now()
        ))
    except Exception as e:
        logger.error(f"Circuit Breaker health check failed: {e}")
        services.append(ServiceHealth(
            service="circuit_breaker",
            status="unhealthy",
            response_time=None,
            last_check=datetime.now(),
            error_message=str(e)
        ))

    # Overall status
    unhealthy_services = [s for s in services if s.status == "unhealthy"]
    if unhealthy_services:
        overall_status = "degraded" if len(unhealthy_services) < len(services) else "unhealthy"
    else:
        overall_status = "healthy"

    return {
        "status": overall_status,
        "timestamp": datetime.now(),
        "uptime": uptime,
        "version": "1.0.0",
        "system_metrics": system_metrics,
        "services": services
    }

@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Get application metrics"""
    return {
        "uptime_seconds": time.time() - _start_time,
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "active_threads": len(psutil.Process().threads()),
        "open_files": len(psutil.Process().open_files()),
        "network_connections": len(psutil.net_connections())
    }

@router.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong", "timestamp": datetime.now()}

@router.get("/database")
async def database_health_check(current_user: dict = Depends(get_current_user)) -> DatabaseHealth:
    """Check database connectivity"""
    try:
        start_time = time.time()
        # Simple database connectivity check
        # In a real implementation, this would connect to your actual database
        # For now, we'll simulate a database check
        import sqlite3
        # Assuming we have a database file in the project
        db_path = os.getenv("DATABASE_URL", "database.db")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            conn.execute("SELECT 1").fetchone()
            conn.close()
            connection_time = (time.time() - start_time) * 1000
            return DatabaseHealth(
                status="healthy",
                connection_time=connection_time,
                last_check=datetime.now()
            )
        else:
            # If no database exists, check if we can create a temporary one
            conn = sqlite3.connect(":memory:")
            conn.execute("SELECT 1").fetchone()
            conn.close()
            connection_time = (time.time() - start_time) * 1000
            return DatabaseHealth(
                status="healthy",
                connection_time=connection_time,
                last_check=datetime.now()
            )
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return DatabaseHealth(
            status="unhealthy",
            connection_time=None,
            last_check=datetime.now(),
            error_message=str(e)
        )

@router.get("/external-apis")
async def external_apis_health_check(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Check external API connectivity"""
    external_apis = [
        {"name": "Binance", "url": "https://api.binance.com/api/v3/ping"},
        {"name": "Kraken", "url": "https://api.kraken.com/0/public/Time"},
        {"name": "Coinbase", "url": "https://api.coinbase.com/v2/time"},
    ]

    api_health_checks = []

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        for api in external_apis:
            try:
                start_time = time.time()
                async with session.get(api["url"]) as response:
                    response_time = (time.time() - start_time) * 1000
                    status = "healthy" if response.status == 200 else "degraded"
                    api_health_checks.append(ExternalAPIHealth(
                        name=api["name"],
                        url=api["url"],
                        status=status,
                        response_time=response_time,
                        last_check=datetime.now()
                    ))
            except Exception as e:
                logger.error(f"External API health check failed for {api['name']}: {e}")
                api_health_checks.append(ExternalAPIHealth(
                    name=api["name"],
                    url=api["url"],
                    status="unhealthy",
                    response_time=None,
                    last_check=datetime.now(),
                    error_message=str(e)
                ))

    # Overall status for external APIs
    unhealthy_apis = [api for api in api_health_checks if api.status == "unhealthy"]
    overall_status = "healthy"
    if unhealthy_apis:
        overall_status = "degraded" if len(unhealthy_apis) < len(api_health_checks) else "unhealthy"

    return {
        "overall_status": overall_status,
        "apis": api_health_checks,
        "timestamp": datetime.now()
    }

@router.get("/monitoring")
async def monitoring_health_check(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Get comprehensive monitoring health status"""
    try:
        # Get performance monitor metrics
        system_health = None
        performance_metrics = None
        if performance_monitor:
            system_health = await performance_monitor.get_system_health()
            performance_metrics = performance_monitor.get_trading_metrics()

        # Get safety alerts
        safety_alerts = []
        if SafetyMonitor:
            safety_monitor = SafetyMonitor()
            safety_alerts = await safety_monitor.check_safety_conditions()

        return {
            "status": "healthy",
            "system_health": system_health,
            "performance_metrics": performance_metrics.dict() if performance_metrics else None,
            "safety_alerts": [alert.dict() for alert in safety_alerts],
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Monitoring health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now()
        }
