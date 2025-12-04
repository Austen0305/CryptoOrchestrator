from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import logging
import time
from datetime import datetime
from ..dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


class SystemStatus(BaseModel):
    status: str
    timestamp: str
    uptime: float
    version: str
    services: Dict[str, str]


@router.get("/")
async def get_status() -> SystemStatus:
    """Get basic system status"""
    try:
        return SystemStatus(
            status="running",
            timestamp=datetime.utcnow().isoformat(),
            uptime=time.time(),  # Would be actual uptime in real implementation
            version="1.0.0",
            services={
                "fastapi": "healthy",
                "database": "healthy",  # Mock
                "redis": "healthy",  # Mock
            },
        )
    except Exception as e:
        logger.error(f"Failed to get status: {e}", exc_info=True)
        # Return default status instead of 500 error
        return SystemStatus(
            status="degraded",
            timestamp=datetime.utcnow().isoformat(),
            uptime=0.0,
            version="1.0.0",
            services={
                "fastapi": "unknown",
                "database": "unknown",
                "redis": "unknown",
            },
        )


@router.get("/protected")
async def get_protected_status(
    current_user: dict = Depends(get_current_user),
) -> SystemStatus:
    """Get system status (authenticated endpoint)"""
    try:
        return SystemStatus(
            status="running",
            timestamp=datetime.utcnow().isoformat(),
            uptime=time.time(),
            version="1.0.0",
            services={
                "fastapi": "healthy",
                "database": "healthy",
                "redis": "healthy",
                "auth": "healthy",
            },
        )
    except Exception as e:
        logger.error(f"Failed to get protected status: {e}", exc_info=True)
        # Return default status instead of 500 error
        return SystemStatus(
            status="degraded",
            timestamp=datetime.utcnow().isoformat(),
            uptime=0.0,
            version="1.0.0",
            services={
                "fastapi": "unknown",
                "database": "unknown",
                "redis": "unknown",
                "auth": "unknown",
            },
        )
