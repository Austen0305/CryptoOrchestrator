"""
Middleware Health and Monitoring Routes
Provides endpoints for monitoring middleware health and performance
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..middleware.performance_metrics import performance_monitor
from ..middleware.database_pool_monitor import pool_monitor
from ..middleware.security_enhanced import EnhancedSecurityMiddleware
from ..middleware.background_tasks_optimized import background_task_queue
from ..middleware.websocket_manager_enhanced import websocket_manager
from ..middleware.api_analytics import api_analytics
from ..middleware.rate_limiting_enhanced import EnhancedRateLimiter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/middleware/stats")
async def get_middleware_stats(request: Request) -> Dict[str, Any]:
    """Get comprehensive middleware statistics"""
    try:
        stats = {
            "performance": performance_monitor.get_all_stats(),
            "database_pool": pool_monitor.get_stats(),
            "background_tasks": background_task_queue.get_stats(),
            "websockets": websocket_manager.get_stats(),
            "api_analytics": api_analytics.get_analytics_summary(),
        }
        
        # Add security stats if available
        try:
            # This would need to be accessed from app state
            stats["security"] = {"note": "Security stats available via middleware instance"}
        except Exception:
            pass
        
        # Add rate limiting analytics if available
        try:
            # Rate limiter would be accessed from app state
            stats["rate_limiting"] = {"note": "Rate limiting analytics available via middleware instance"}
        except Exception:
            pass
        
        return stats
    except Exception as e:
        logger.error(f"Error getting middleware stats: {e}", exc_info=True)
        return JSONResponse(
            content={"error": str(e)},
            status_code=500,
        )


@router.get("/api/middleware/database-pool")
async def get_database_pool_stats() -> Dict[str, Any]:
    """Get database connection pool statistics"""
    try:
        return {
            "current_metrics": pool_monitor.get_current_metrics().__dict__ if pool_monitor.get_current_metrics() else None,
            "stats": pool_monitor.get_stats(),
            "leaks": pool_monitor.get_leaks(),
        }
    except Exception as e:
        logger.error(f"Error getting pool stats: {e}", exc_info=True)
        return JSONResponse(
            content={"error": str(e)},
            status_code=500,
        )


@router.get("/api/middleware/websockets")
async def get_websocket_stats() -> Dict[str, Any]:
    """Get WebSocket connection statistics"""
    try:
        return websocket_manager.get_stats()
    except Exception as e:
        logger.error(f"Error getting WebSocket stats: {e}", exc_info=True)
        return JSONResponse(
            content={"error": str(e)},
            status_code=500,
        )

