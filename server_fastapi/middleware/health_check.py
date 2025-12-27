"""
Middleware Health Check
Provides health check endpoints for middleware components
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .performance_metrics import performance_monitor
from .config import middleware_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health/middleware")
async def middleware_health_check(request: Request) -> Dict[str, Any]:
    """
    Health check endpoint for middleware components
    
    Returns:
        Dictionary with middleware health status
    """
    health_status = {
        "status": "healthy",
        "timestamp": None,
        "middleware": {},
        "performance": {},
    }
    
    try:
        from datetime import datetime
        health_status["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        # Check middleware configuration
        enabled_middlewares = middleware_manager.get_enabled_middlewares()
        health_status["middleware"] = {
            "total_enabled": len(enabled_middlewares),
            "middlewares": [mw.name for mw in enabled_middlewares],
        }
        
        # Get performance metrics
        try:
            perf_stats = performance_monitor.get_all_stats()
            health_status["performance"] = perf_stats
            
            # Check for slow middleware
            slow_middleware = performance_monitor.get_slow_middleware(threshold_ms=100)
            if slow_middleware:
                health_status["warnings"] = {
                    "slow_middleware": slow_middleware,
                }
                health_status["status"] = "degraded"
        except Exception as e:
            logger.warning(f"Failed to get performance metrics: {e}")
            health_status["performance"] = {"error": str(e)}
        
    except Exception as e:
        logger.error(f"Middleware health check failed: {e}", exc_info=True)
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)


@router.get("/health/middleware/performance")
async def middleware_performance_check() -> Dict[str, Any]:
    """
    Get middleware performance metrics
    
    Returns:
        Dictionary with performance statistics
    """
    try:
        all_stats = performance_monitor.get_all_stats()
        slow_middleware = performance_monitor.get_slow_middleware(threshold_ms=100)
        
        # Get cache stats if available
        cache_stats = {}
        try:
            from .optimized_caching import OptimizedCacheMiddleware
            # This would need to be accessed from app state in real implementation
            cache_stats = {"note": "Cache stats available via middleware instance"}
        except ImportError:
            pass
        
        # Get profiler stats if available
        profiler_stats = {}
        try:
            from ..utils.performance_profiler import get_profiler
            profiler = get_profiler()
            profiler_stats = {
                "slow_functions": [
                    {
                        "name": p.function_name,
                        "avg_time_ms": p.avg_time * 1000,
                        "call_count": p.call_count,
                    }
                    for p in profiler.get_slow_functions(threshold_ms=100)
                ]
            }
        except Exception:
            pass
        
        return {
            "status": "ok",
            "statistics": all_stats,
            "slow_middleware": slow_middleware,
            "cache_stats": cache_stats,
            "profiler_stats": profiler_stats,
        }
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}", exc_info=True)
        return JSONResponse(
            content={"status": "error", "error": str(e)},
            status_code=500,
        )

