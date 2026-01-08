"""
Performance Profiling API Endpoints
Exposes slow query and endpoint profiling data
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies.auth import require_permission
from ..services.monitoring.performance_profiler import get_performance_profiler
from ..services.observability.opentelemetry_setup import record_metric

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/slow-queries")
async def get_slow_queries(
    current_user: Annotated[dict, Depends(require_permission("admin:performance"))],
    limit: int = Query(
        50, ge=1, le=500, description="Maximum number of queries to return"
    ),
):
    """Get slow database queries (admin only)"""
    try:
        profiler = get_performance_profiler()
        slow_queries = profiler.get_slow_queries(limit=limit)

        # Record metric
        record_metric("slow_queries_queried", len(slow_queries))

        return {
            "slow_queries": slow_queries,
            "count": len(slow_queries),
            "limit": limit,
        }
    except Exception as e:
        logger.error(f"Error getting slow queries: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get slow queries: {str(e)}"
        )


@router.get("/slow-endpoints")
async def get_slow_endpoints(
    current_user: Annotated[dict, Depends(require_permission("admin:performance"))],
    limit: int = Query(
        50, ge=1, le=500, description="Maximum number of endpoints to return"
    ),
):
    """Get slow API endpoints (admin only)"""
    try:
        profiler = get_performance_profiler()
        slow_endpoints = profiler.get_slow_endpoints(limit=limit)

        # Record metric
        record_metric("slow_endpoints_queried", len(slow_endpoints))

        return {
            "slow_endpoints": slow_endpoints,
            "count": len(slow_endpoints),
            "limit": limit,
        }
    except Exception as e:
        logger.error(f"Error getting slow endpoints: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get slow endpoints: {str(e)}"
        )


@router.get("/query-statistics")
async def get_query_statistics(
    current_user: Annotated[dict, Depends(require_permission("admin:performance"))],
    query: str | None = Query(None, description="Specific query to analyze"),
):
    """Get query performance statistics (admin only)"""
    try:
        profiler = get_performance_profiler()
        stats = profiler.get_query_statistics(query=query)

        return {"statistics": stats, "query": query[:200] if query else "all_queries"}
    except Exception as e:
        logger.error(f"Error getting query statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get query statistics: {str(e)}"
        )


@router.get("/endpoint-statistics")
async def get_endpoint_statistics(
    current_user: Annotated[dict, Depends(require_permission("admin:performance"))],
    method: str | None = Query(None, description="HTTP method"),
    path: str | None = Query(None, description="Endpoint path"),
):
    """Get endpoint performance statistics (admin only)"""
    try:
        profiler = get_performance_profiler()
        stats = profiler.get_endpoint_statistics(method=method, path=path)

        return {"statistics": stats, "method": method, "path": path}
    except Exception as e:
        logger.error(f"Error getting endpoint statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get endpoint statistics: {str(e)}"
        )


@router.post("/clear-old-entries")
async def clear_old_profiling_entries(
    current_user: Annotated[dict, Depends(require_permission("admin:performance"))],
    max_age_hours: int = Query(24, ge=1, le=168, description="Maximum age in hours"),
):
    """Clear old profiling entries (admin only)"""
    try:
        profiler = get_performance_profiler()
        profiler.clear_old_entries(max_age_hours=max_age_hours)

        return {
            "message": f"Cleared profiling entries older than {max_age_hours} hours",
            "max_age_hours": max_age_hours,
        }
    except Exception as e:
        logger.error(f"Error clearing old entries: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to clear old entries: {str(e)}"
        )


@router.get("/summary")
async def get_performance_summary(
    current_user: Annotated[dict, Depends(require_permission("admin:performance"))],
):
    """Get performance profiling summary (admin only)"""
    try:
        profiler = get_performance_profiler()

        slow_queries = profiler.get_slow_queries(limit=10)
        slow_endpoints = profiler.get_slow_endpoints(limit=10)
        query_stats = profiler.get_query_statistics()
        endpoint_stats = profiler.get_endpoint_statistics()

        return {
            "slow_queries": {"count": len(slow_queries), "top_10": slow_queries},
            "slow_endpoints": {"count": len(slow_endpoints), "top_10": slow_endpoints},
            "query_statistics": query_stats,
            "endpoint_statistics": endpoint_stats,
        }
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get performance summary: {str(e)}"
        )
