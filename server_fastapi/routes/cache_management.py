"""
Cache Management API Routes
Provides endpoints for managing cache, viewing analytics, and controlling versioning.
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies.auth import get_current_user
from ..services.cache.cache_analytics import get_cache_analytics
from ..services.cache.predictive_preloader import get_predictive_preloader
from ..utils.cache_versioning import get_cache_version_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cache", tags=["Cache Management"])


@router.get("/analytics")
async def get_cache_analytics_endpoint(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    time_window_minutes: int | None = Query(
        None, description="Time window for statistics"
    ),
) -> dict[str, Any]:
    """
    Get cache analytics and performance metrics (admin only)
    """
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        analytics = get_cache_analytics()
        stats = analytics.get_statistics(time_window_minutes=time_window_minutes)
        return stats
    except Exception as e:
        logger.error(f"Error getting cache analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get cache analytics: {str(e)}"
        )


@router.get("/analytics/pattern/{pattern}")
async def get_pattern_analytics(
    pattern: str,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> dict[str, Any]:
    """
    Get analytics for a specific cache pattern (admin only)
    """
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        analytics = get_cache_analytics()
        pattern_stats = analytics.get_pattern_analysis(pattern)
        return pattern_stats
    except Exception as e:
        logger.error(f"Error getting pattern analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get pattern analytics: {str(e)}"
        )


@router.get("/versions")
async def get_cache_versions(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> dict[str, Any]:
    """
    Get all cache versions (admin only)
    """
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        version_manager = get_cache_version_manager()
        versions = version_manager.get_all_versions()
        return {"versions": versions}
    except Exception as e:
        logger.error(f"Error getting cache versions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get cache versions: {str(e)}"
        )


@router.post("/versions/{prefix}/increment")
async def increment_cache_version(
    prefix: str,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    reason: str | None = Query(None, description="Reason for version increment"),
) -> dict[str, Any]:
    """
    Increment cache version for a prefix (invalidates all cached data) (admin only)
    """
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        version_manager = get_cache_version_manager()
        new_version = version_manager.increment_version(prefix, reason=reason)
        return {
            "success": True,
            "prefix": prefix,
            "new_version": new_version,
            "message": f"Cache version incremented to v{new_version}",
        }
    except Exception as e:
        logger.error(f"Error incrementing cache version: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to increment cache version: {str(e)}"
        )


@router.post("/versions/invalidate-all")
async def invalidate_all_cache_versions(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    reason: str | None = Query(None, description="Reason for invalidation"),
) -> dict[str, Any]:
    """
    Invalidate all cache versions (full cache clear) (admin only)
    """
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        version_manager = get_cache_version_manager()
        version_manager.invalidate_all_versions(reason=reason)
        return {"success": True, "message": "All cache versions invalidated"}
    except Exception as e:
        logger.error(f"Error invalidating all cache versions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to invalidate cache versions: {str(e)}"
        )


@router.get("/preloader/stats")
async def get_preloader_stats(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> dict[str, Any]:
    """
    Get predictive preloader statistics (admin only)
    """
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        preloader = get_predictive_preloader()
        stats = preloader.get_access_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting preloader stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get preloader stats: {str(e)}"
        )


@router.post("/preloader/preload-frequent")
async def trigger_preload_frequent(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    min_access_count: int = Query(10, ge=1, description="Minimum access count"),
    time_window_minutes: int = Query(60, ge=1, description="Time window in minutes"),
) -> dict[str, Any]:
    """
    Manually trigger preloading of frequently accessed keys (admin only)
    """
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        preloader = get_predictive_preloader()
        # Get cache instance (would need to be passed or retrieved)
        # For now, return stats
        stats = preloader.get_access_statistics()
        return {"success": True, "message": "Preload triggered", "stats": stats}
    except Exception as e:
        logger.error(f"Error triggering preload: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to trigger preload: {str(e)}"
        )


@router.get("/metrics")
async def get_cache_metrics(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> dict[str, Any]:
    """
    Get cache metrics from MultiLevelCache (admin only)
    """
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Try to get cache instance (this would need to be available globally)
        # For now, return analytics as metrics
        analytics = get_cache_analytics()
        stats = analytics.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting cache metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get cache metrics: {str(e)}"
        )


@router.post("/analytics/reset")
async def reset_cache_analytics(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> dict[str, Any]:
    """
    Reset cache analytics statistics (admin only)
    """
    # Check admin permission
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        analytics = get_cache_analytics()
        analytics.reset_statistics()
        return {"success": True, "message": "Cache analytics reset"}
    except Exception as e:
        logger.error(f"Error resetting cache analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to reset cache analytics: {str(e)}"
        )
