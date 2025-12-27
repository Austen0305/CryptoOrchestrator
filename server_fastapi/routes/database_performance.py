"""
Database Performance Monitoring Routes
Provides endpoints for monitoring database performance, connection pools, and query metrics.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional, Annotated, List
import logging

from ..dependencies.auth import get_current_user
from ..database.pool_monitoring import get_pool_monitor
from ..database.connection_pool import db_pool
from ..database.read_replica import read_replica_manager
from ..utils.query_optimizer import IndexOptimizer
from ..database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/database", tags=["Database Performance"])


@router.get("/pool/metrics")
async def get_pool_metrics(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Dict[str, Any]:
    """
    Get connection pool metrics (admin only)

    Returns current pool statistics including size, utilization, and health.
    """
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        monitor = get_pool_monitor(db_pool.engine if db_pool.engine else None)
        metrics = await monitor.get_pool_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting pool metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get pool metrics: {str(e)}"
        )


@router.get("/pool/health")
async def get_pool_health(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Dict[str, Any]:
    """
    Get connection pool health status (admin only)

    Returns health status with warnings and recommendations.
    """
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        monitor = get_pool_monitor(db_pool.engine if db_pool.engine else None)
        health = await monitor.check_pool_health()
        return health
    except Exception as e:
        logger.error(f"Error checking pool health: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to check pool health: {str(e)}"
        )


@router.get("/pool/history")
async def get_pool_history(
    current_user: Annotated[dict, Depends(get_current_user)],
    limit: int = Query(100, ge=1, le=1000, description="Number of historical entries"),
) -> Dict[str, Any]:
    """
    Get connection pool metrics history (admin only)
    """
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        monitor = get_pool_monitor(db_pool.engine if db_pool.engine else None)
        history = monitor.get_metrics_history(limit=limit)
        summary = monitor.get_metrics_summary()

        return {"history": history, "summary": summary}
    except Exception as e:
        logger.error(f"Error getting pool history: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get pool history: {str(e)}"
        )


@router.get("/read-replicas/health")
async def get_read_replica_health(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Dict[str, Any]:
    """
    Get read replica health status (admin only)
    """
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        health = await read_replica_manager.health_check()
        return {
            "read_replicas_enabled": len(read_replica_manager.read_engines) > 0,
            "read_replica_count": len(read_replica_manager.read_engines),
            "health": health,
        }
    except Exception as e:
        logger.error(f"Error checking read replica health: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to check read replica health: {str(e)}"
        )


@router.get("/indexes/usage")
async def get_index_usage(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    table_name: str = Query(..., description="Table name to analyze"),
) -> Dict[str, Any]:
    """
    Analyze index usage for a table (admin only, PostgreSQL only)
    """
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        optimizer = IndexOptimizer()
        usage = await optimizer.analyze_index_usage(db, table_name)
        return usage
    except Exception as e:
        logger.error(f"Error analyzing index usage: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze index usage: {str(e)}"
        )


@router.get("/indexes/unused")
async def get_unused_indexes(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    min_scans: int = Query(
        10, ge=0, description="Minimum scans to consider index as used"
    ),
) -> List[Dict[str, Any]]:
    """
    Find unused or rarely used indexes (admin only, PostgreSQL only)
    """
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        optimizer = IndexOptimizer()
        unused = await optimizer.get_unused_indexes(db, min_scans=min_scans)
        return unused
    except Exception as e:
        logger.error(f"Error finding unused indexes: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to find unused indexes: {str(e)}"
        )


@router.get("/indexes/missing")
async def get_missing_indexes(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> List[Dict[str, Any]]:
    """
    Find potential missing indexes (admin only, PostgreSQL only)
    """
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        optimizer = IndexOptimizer()
        missing = await optimizer.get_missing_indexes(db)
        return missing
    except Exception as e:
        logger.error(f"Error finding missing indexes: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to find missing indexes: {str(e)}"
        )
