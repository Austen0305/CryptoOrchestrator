"""
Audit Logs Routes
Provides access to audit logs for compliance and security
"""

import logging
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer
from pydantic import BaseModel

from ..dependencies.auth import get_current_user
from ..middleware.cache_manager import cached
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit-logs", tags=["audit-logs"])
security = HTTPBearer()

# Audit log directory
AUDIT_LOG_DIR = Path("logs")
AUDIT_LOG_FILE = AUDIT_LOG_DIR / "audit.log"


class AuditLogEntry(BaseModel):
    timestamp: str
    event_type: str
    user_id: int | None
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    details: dict[str, Any] | None = None
    status: str  # "success" or "failure"
    error_message: str | None = None


class AuditLogResponse(BaseModel):
    entries: list[AuditLogEntry]
    total: int
    page: int
    page_size: int


@router.get("/", response_model=AuditLogResponse)
@cached(ttl=60, prefix="audit_logs")  # 60s TTL for audit logs
async def get_audit_logs(
    current_user: Annotated[dict, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    event_type: str | None = None,
    status: str | None = None,
):
    """Get audit logs for the current user (admin can see all logs)"""
    try:
        user_id = _get_user_id(current_user)
        user_role = current_user.get("role", "user")

        # Only admins can view audit logs
        if user_role != "admin":
            raise HTTPException(
                status_code=403, detail="Only admins can view audit logs"
            )

        # Read audit log file
        if not AUDIT_LOG_FILE.exists():
            return AuditLogResponse(
                entries=[],
                total=0,
                page=page,
                page_size=page_size,
            )

        # Parse log entries
        entries = []
        try:
            with open(AUDIT_LOG_FILE) as f:
                lines = f.readlines()

                for line in lines:
                    if not line.strip():
                        continue

                    try:
                        # Try to parse as JSON (if it's a JSON log entry)
                        import json

                        # Log entries might be in format: "timestamp - logger - level - message"
                        # Or JSON format: {"timestamp": "...", ...}

                        # Check if line contains JSON
                        if line.strip().startswith("{"):
                            entry_data = json.loads(line.strip())
                            # Ensure required fields
                            if "action" not in entry_data:
                                entry_data["action"] = entry_data.get(
                                    "event_type", "unknown"
                                )
                            if "status" not in entry_data:
                                entry_data["status"] = (
                                    "success"
                                    if entry_data.get("success", True)
                                    else "failure"
                                )
                        else:
                            # Parse text format: "timestamp - logger - level - message"
                            parts = line.split(" - ", 3)
                            if len(parts) >= 4:
                                timestamp_str = parts[0]
                                logger_name = parts[1]
                                level = parts[2]
                                message = parts[3].strip()

                                # Try to parse message as JSON
                                try:
                                    entry_data = json.loads(message)
                                    # Ensure required fields
                                    if "action" not in entry_data:
                                        entry_data["action"] = entry_data.get(
                                            "event_type", "unknown"
                                        )
                                    if "status" not in entry_data:
                                        entry_data["status"] = (
                                            "success"
                                            if entry_data.get("success", True)
                                            else "failure"
                                        )
                                except:
                                    # If not JSON, create a basic entry
                                    entry_data = {
                                        "timestamp": timestamp_str,
                                        "event_type": "log_entry",
                                        "action": "log_entry",
                                        "message": message,
                                        "level": level,
                                        "status": "success",
                                    }
                            else:
                                continue

                        # Filter by event type if provided
                        if event_type and entry_data.get("event_type") != event_type:
                            continue

                        # Filter by status if provided
                        if status and entry_data.get("status") != status:
                            continue

                        # Filter by user_id if not admin (already checked above, but keep for safety)
                        if (
                            user_role != "admin"
                            and entry_data.get("user_id") != user_id
                        ):
                            continue

                        # Create audit log entry
                        entry = AuditLogEntry(
                            timestamp=entry_data.get("timestamp", ""),
                            event_type=entry_data.get("event_type", "unknown"),
                            user_id=entry_data.get("user_id"),
                            action=entry_data.get(
                                "action", entry_data.get("message", "")
                            ),
                            resource_type=entry_data.get("resource_type"),
                            resource_id=entry_data.get("resource_id"),
                            details=entry_data.get("details"),
                            status=entry_data.get("status", "success"),
                            error_message=entry_data.get("error_message"),
                        )

                        entries.append(entry)
                    except Exception as e:
                        logger.warning(f"Failed to parse audit log entry: {e}")
                        continue
        except Exception as e:
            logger.error(f"Failed to read audit log file: {e}")
            raise HTTPException(status_code=500, detail="Failed to read audit logs")

        # Sort by timestamp (most recent first)
        entries.sort(key=lambda x: x.timestamp, reverse=True)

        # Paginate
        total = len(entries)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_entries = entries[start_idx:end_idx]

        return AuditLogResponse(
            entries=paginated_entries,
            total=total,
            page=page,
            page_size=page_size,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
@cached(ttl=120, prefix="audit_log_stats")  # 120s TTL for audit log statistics
async def get_audit_log_stats(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get audit log statistics"""
    try:
        user_id = _get_user_id(current_user)
        user_role = current_user.get("role", "user")

        # Only admins can view audit log stats
        if user_role != "admin":
            raise HTTPException(
                status_code=403, detail="Only admins can view audit log stats"
            )

        # Read audit log file
        if not AUDIT_LOG_FILE.exists():
            return {
                "total_entries": 0,
                "by_event_type": {},
                "by_status": {},
                "by_user": {},
            }

        # Parse log entries for stats
        event_types = {}
        statuses = {}
        users = {}

        try:
            with open(AUDIT_LOG_FILE) as f:
                lines = f.readlines()

                for line in lines:
                    if not line.strip():
                        continue

                    try:
                        import json

                        # Parse line (same logic as get_audit_logs)
                        if line.strip().startswith("{"):
                            entry_data = json.loads(line.strip())
                        else:
                            parts = line.split(" - ", 3)
                            if len(parts) >= 4:
                                message = parts[3].strip()
                                try:
                                    entry_data = json.loads(message)
                                except:
                                    continue
                            else:
                                continue

                        # Count event types
                        event_type = entry_data.get("event_type", "unknown")
                        event_types[event_type] = event_types.get(event_type, 0) + 1

                        # Count statuses
                        status = entry_data.get("status", "success")
                        statuses[status] = statuses.get(status, 0) + 1

                        # Count users
                        entry_user_id = entry_data.get("user_id")
                        if entry_user_id:
                            users[str(entry_user_id)] = (
                                users.get(str(entry_user_id), 0) + 1
                            )
                    except Exception as e:
                        logger.warning(
                            f"Failed to parse audit log entry for stats: {e}"
                        )
                        continue
        except Exception as e:
            logger.error(f"Failed to read audit log file for stats: {e}")
            raise HTTPException(status_code=500, detail="Failed to read audit logs")

        return {
            "total_entries": sum(event_types.values()),
            "by_event_type": event_types,
            "by_status": statuses,
            "by_user": users,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audit log stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
