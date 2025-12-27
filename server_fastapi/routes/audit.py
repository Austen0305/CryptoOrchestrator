"""
Audit Log Routes
API endpoints for retrieving and exporting audit logs
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from typing_extensions import Annotated
import logging

from ..dependencies.auth import get_current_user
from ..services.audit.audit_logger import audit_logger
from ..utils.route_helpers import _get_user_id
from ..middleware.cache_manager import cached
from ..utils.query_optimizer import QueryOptimizer
from ..utils.response_optimizer import ResponseOptimizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit", tags=["Audit Logs"])


class AuditLogResponse(BaseModel):
    """Response model for audit log entry"""

    event_type: str
    timestamp: str
    user_id: int
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    status: Optional[str] = None
    success: Optional[bool] = None
    details: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class AuditLogSearchRequest(BaseModel):
    """Request model for searching audit logs"""

    user_id: Optional[int] = None
    event_type: Optional[str] = None
    start_date: Optional[str] = None  # ISO format
    end_date: Optional[str] = None  # ISO format
    limit: int = 100


@router.get("/logs", response_model=List[AuditLogResponse], tags=["Audit Logs"])
@cached(ttl=60, prefix="audit_logs")  # 60s TTL for audit logs
async def get_audit_logs(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of logs to return"
    ),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> List[AuditLogResponse]:
    """
    Get audit logs with filtering

    Users can only view their own audit logs unless they are admin.
    """
    try:
        # Parse dates
        start_datetime = None
        end_datetime = None

        if start_date:
            try:
                start_datetime = datetime.fromisoformat(
                    start_date.replace("Z", "+00:00")
                )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use ISO format (e.g., 2025-12-06T00:00:00Z)",
                )

        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use ISO format (e.g., 2025-12-06T23:59:59Z)",
                )

        # Check permissions - users can only see their own logs unless admin
        current_user_id = _get_user_id(current_user)
        is_admin = current_user.get("role") == "admin" or current_user.get(
            "is_admin", False
        )

        if not is_admin and user_id and int(user_id) != int(current_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own audit logs",
            )

        # If not admin and no user_id specified, default to current user
        if not is_admin:
            user_id = int(current_user_id)

        # Get logs (fetch more than needed for pagination)
        max_limit = page * page_size  # Fetch enough for current page
        logs = audit_logger.get_audit_logs(
            user_id=user_id,
            event_type=event_type,
            start_date=start_datetime,
            end_date=end_datetime,
            limit=max_limit,
        )

        # Apply pagination
        total = len(logs)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_logs = logs[start_idx:end_idx]

        return [AuditLogResponse(**log) for log in paginated_logs]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving audit logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs",
        )


@router.post("/logs/export", tags=["Audit Logs"])
async def export_audit_logs(
    request: AuditLogSearchRequest,
    format: str = Query("json", pattern="^(json|csv)$", description="Export format"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> Dict[str, Any]:
    """
    Export audit logs to JSON or CSV format

    Returns file path and download information.
    """
    try:
        # Check permissions
        current_user_id = _get_user_id(current_user)
        is_admin = current_user.get("role") == "admin" or current_user.get(
            "is_admin", False
        )

        if (
            not is_admin
            and request.user_id
            and int(request.user_id) != int(current_user_id)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only export your own audit logs",
            )

        # Parse dates
        start_datetime = None
        end_datetime = None

        if request.start_date:
            try:
                start_datetime = datetime.fromisoformat(
                    request.start_date.replace("Z", "+00:00")
                )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format",
                )

        if request.end_date:
            try:
                end_datetime = datetime.fromisoformat(
                    request.end_date.replace("Z", "+00:00")
                )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format",
                )

        # If not admin, default to current user
        if not is_admin:
            request.user_id = int(current_user_id)

        # Export logs
        filepath = audit_logger.export_audit_logs(
            user_id=request.user_id,
            event_type=request.event_type,
            start_date=start_datetime,
            end_date=end_datetime,
            format=format,
        )

        return {
            "success": True,
            "filepath": filepath,
            "format": format,
            "message": f"Audit logs exported to {filepath}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting audit logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export audit logs",
        )


@router.post("/logs/cleanup", tags=["Audit Logs"])
async def cleanup_audit_logs(
    retention_days: int = Query(
        90, ge=1, le=365, description="Number of days to retain logs"
    ),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> Dict[str, Any]:
    """
    Clean up old audit logs (admin only)

    Removes audit logs older than the specified retention period.
    """
    try:
        # Check admin permissions
        is_admin = current_user.get("role") == "admin" or current_user.get(
            "is_admin", False
        )
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can clean up audit logs",
            )

        # Cleanup logs
        audit_logger.cleanup_old_logs(retention_days=retention_days)

        return {
            "success": True,
            "message": f"Cleaned up audit logs older than {retention_days} days",
            "retention_days": retention_days,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up audit logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clean up audit logs",
        )
