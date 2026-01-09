"""
Logging Aggregation Routes
Provides endpoints for log viewing and analysis
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..dependencies.auth import get_current_user, require_admin
from ..utils.logging_aggregation import LogLevel, log_aggregator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/logs", tags=["Logging"])


@router.post("/")
async def post_logs(
    log_data: dict,
    current_user: dict = Depends(get_current_user),
):
    """Accept client-side logs (for debugging/monitoring)"""
    try:
        # Store or process client-side logs if needed
        # For now, just acknowledge receipt
        logger.debug(f"Client log received: {log_data}")
        return {"success": True, "message": "Log received"}
    except Exception as e:
        logger.error(f"Error processing client log: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@router.get("/")
async def get_logs(
    level: str | None = Query(None, description="Filter by log level"),
    source: str | None = Query(None, description="Filter by source"),
    start_time: str | None = Query(None, description="Start time (ISO format)"),
    end_time: str | None = Query(None, description="End time (ISO format)"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of logs"),
    current_user: dict = Depends(get_current_user),
):
    """Get logs with filtering"""
    try:
        log_level = LogLevel(level) if level else None
        start = datetime.fromisoformat(start_time) if start_time else None
        end = datetime.fromisoformat(end_time) if end_time else None

        logs = log_aggregator.get_logs(
            level=log_level,
            source=source,
            start_time=start,
            end_time=end,
            limit=limit,
        )

        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        logger.error(f"Error getting logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get logs: {str(e)}",
        )


@router.get("/stats")
async def get_log_stats(
    current_user: dict = Depends(get_current_user),
):
    """Get logging statistics"""
    try:
        return log_aggregator.get_stats()
    except Exception as e:
        logger.error(f"Error getting log stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get log stats: {str(e)}",
        )


@router.get("/search")
async def search_logs(
    query: str = Query(..., description="Search query"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    current_user: dict = Depends(get_current_user),
):
    """Search logs"""
    try:
        logs = log_aggregator.search_logs(query, limit=limit)
        return {"logs": logs, "count": len(logs), "query": query}
    except Exception as e:
        logger.error(f"Error searching logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search logs: {str(e)}",
        )


@router.get("/export")
async def export_logs(
    format: str = Query("json", description="Export format (json, csv, txt)"),
    start_time: str | None = Query(None, description="Start time (ISO format)"),
    end_time: str | None = Query(None, description="End time (ISO format)"),
    current_user: dict = Depends(get_current_user),
):
    """Export logs"""
    try:
        from fastapi.responses import Response

        start = datetime.fromisoformat(start_time) if start_time else None
        end = datetime.fromisoformat(end_time) if end_time else None

        exported = log_aggregator.export_logs(
            format=format, start_time=start, end_time=end
        )

        content_type_map = {
            "json": "application/json",
            "csv": "text/csv",
            "txt": "text/plain",
        }

        return Response(
            content=exported,
            media_type=content_type_map.get(format, "text/plain"),
            headers={
                "Content-Disposition": f'attachment; filename="logs.{format}"',
            },
        )
    except Exception as e:
        logger.error(f"Error exporting logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export logs: {str(e)}",
        )
