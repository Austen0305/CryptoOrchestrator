"""
Cache Warmer Routes
API endpoints for managing cache warmup tasks
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..dependencies.auth import get_current_user
from ..services.cache_warmer_service import (
    cache_warmer_service,
    register_default_warmup_tasks,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cache-warmer", tags=["Cache Warmer"])


class RegisterTaskRequest(BaseModel):
    """Request to register a cache warmup task"""

    name: str
    ttl: int = 300
    interval: int = 60
    enabled: bool = True


@router.get("/status")
async def get_cache_warmer_status(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Get cache warmer service status"""
    try:
        return cache_warmer_service.get_status()
    except Exception as e:
        logger.error(f"Error getting cache warmer status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get status")


@router.post("/warmup")
async def trigger_warmup(
    current_user: Annotated[dict, Depends(get_current_user)],
    task_name: str | None = None,
) -> dict:
    """Manually trigger cache warmup"""
    try:
        results = await cache_warmer_service.warmup_now(task_name)
        return {
            "success": True,
            "results": results,
            "message": f"Warmup triggered for {len(results)} task(s)",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error triggering warmup: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to trigger warmup")


@router.post("/start")
async def start_cache_warmer(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Start the cache warmer service"""
    try:
        # Register default tasks if not already registered
        if len(cache_warmer_service.tasks) == 0:
            register_default_warmup_tasks()

        await cache_warmer_service.start()
        return {
            "success": True,
            "message": "Cache warmer service started",
            "status": cache_warmer_service.get_status(),
        }
    except Exception as e:
        logger.error(f"Error starting cache warmer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start cache warmer")


@router.post("/stop")
async def stop_cache_warmer(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Stop the cache warmer service"""
    try:
        await cache_warmer_service.stop()
        return {"success": True, "message": "Cache warmer service stopped"}
    except Exception as e:
        logger.error(f"Error stopping cache warmer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to stop cache warmer")
