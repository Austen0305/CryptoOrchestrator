"""
Log Search and Management API Endpoints
Provides endpoints for searching, filtering, and analyzing application logs.
"""

import logging
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies.auth import get_current_user
from ..services.logging.log_search import get_log_search_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Logs"])


@router.get("/search")
async def search_logs(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    query: str | None = Query(None, description="Text search query"),
    level: str | None = Query(
        None, description="Log level filter (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    ),
    user_id: str | None = Query(None, description="Filter by user ID"),
    request_id: str | None = Query(None, description="Filter by request ID"),
    trace_id: str | None = Query(None, description="Filter by trace ID"),
    start_time: datetime | None = Query(
        None, description="Start time for time range filter"
    ),
    end_time: datetime | None = Query(
        None, description="End time for time range filter"
    ),
    log_file: str = Query("app", description="Log file to search (app, errors, audit)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> dict[str, Any]:
    """
    Search application logs with various filters (admin only)

    Requires admin role to access log search functionality.
    """
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        search_service = get_log_search_service()
        results = search_service.search_logs(
            query=query,
            level=level,
            user_id=user_id,
            request_id=request_id,
            trace_id=trace_id,
            start_time=start_time,
            end_time=end_time,
            log_file=log_file,
            limit=limit,
            offset=offset,
        )
        return results
    except Exception as e:
        logger.error(f"Error searching logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to search logs: {str(e)}")


@router.get("/statistics")
async def get_log_statistics(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    start_time: datetime | None = Query(None, description="Start time for statistics"),
    end_time: datetime | None = Query(None, description="End time for statistics"),
    log_file: str = Query(
        "app", description="Log file to analyze (app, errors, audit)"
    ),
) -> dict[str, Any]:
    """
    Get log statistics for a time range (admin only)

    Returns counts by log level, error rate, and other metrics.
    """
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        search_service = get_log_search_service()
        stats = search_service.get_log_statistics(
            start_time=start_time, end_time=end_time, log_file=log_file
        )
        return stats
    except Exception as e:
        logger.error(f"Error getting log statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get log statistics: {str(e)}"
        )


@router.get("/tail")
async def tail_logs(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    log_file: str = Query("app", description="Log file to tail (app, errors, audit)"),
    lines: int = Query(50, ge=1, le=1000, description="Number of lines to return"),
) -> list[dict[str, Any]]:
    """
    Get the last N lines from a log file (admin only)

    Similar to `tail -n` command, returns the most recent log entries.
    """
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        search_service = get_log_search_service()
        entries = search_service.tail_logs(log_file=log_file, lines=lines)
        return entries
    except Exception as e:
        logger.error(f"Error tailing logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to tail logs: {str(e)}")
