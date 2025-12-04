"""
Logs Routes - Frontend log collection endpoint
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/logs", tags=["logs"])


class LogEntry(BaseModel):
    """Frontend log entry model"""
    level: str
    message: str
    timestamp: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@router.post("/")
async def receive_log(log_entry: LogEntry):
    """
    Receive log entries from frontend.
    This endpoint accepts logs from the client-side logger.
    """
    try:
        # In production, you might want to:
        # 1. Store logs in a database
        # 2. Send to a log aggregation service (e.g., Sentry, LogRocket)
        # 3. Filter sensitive information
        # 4. Rate limit to prevent abuse
        
        # For now, just log to server logs
        log_level = log_entry.level.lower()
        log_message = f"[Frontend] {log_entry.message}"
        
        if log_entry.data:
            log_message += f" | Data: {log_entry.data}"
        
        if log_level == "error":
            logger.error(log_message)
        elif log_level == "warn" or log_level == "warning":
            logger.warning(log_message)
        elif log_level == "info":
            logger.info(log_message)
        elif log_level == "debug":
            logger.debug(log_message)
        else:
            logger.info(log_message)
        
        return {"success": True, "message": "Log received"}
    except Exception as e:
        # Don't fail the frontend if logging fails
        logger.warning(f"Failed to process frontend log: {e}")
        return {"success": True, "message": "Log received"}

