"""
Cache Management and Monitoring Endpoints
Provides control over caching system
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cache", tags=["Cache Management"])


class CacheInfoResponse(BaseModel):
    """Cache system information"""
    available: bool
    stats: Optional[dict] = None
    redis: Optional[dict] = None
    warming: Optional[dict] = None
    error: Optional[str] = None


class InvalidateRequest(BaseModel):
    """Request to invalidate cache entries"""
    pattern: str


@router.get("/info", response_model=CacheInfoResponse)
async def get_cache_information():
    """
    Get comprehensive cache system information
    
    Returns:
    - Hit/miss statistics
    - Redis memory usage
    - Cache warming status
    - Performance metrics
    """
    try:
        from ..middleware.cache_manager import get_cache_info
        
        info = await get_cache_info()
        return CacheInfoResponse(**info)
        
    except Exception as e:
        logger.error(f"Error getting cache info: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve cache information"
        )


@router.post("/invalidate/pattern")
async def invalidate_cache_pattern(request: InvalidateRequest):
    """
    Invalidate all cache entries matching a pattern
    
    Example patterns:
    - "market_data:*" - All market data
    - "user:123:*" - All data for user 123
    - "*BTC*" - All entries containing BTC
    """
    try:
        from ..middleware.cache_manager import invalidate_pattern
        
        await invalidate_pattern(request.pattern)
        
        return {
            "success": True,
            "message": f"Cache entries matching '{request.pattern}' invalidated",
            "pattern": request.pattern
        }
        
    except Exception as e:
        logger.error(f"Error invalidating cache pattern: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to invalidate cache"
        )


@router.post("/clear")
async def clear_all_cache():
    """
    Clear entire cache (use with caution)
    
    This will delete all cached entries and may cause
    temporary performance degradation until cache repopulates.
    """
    try:
        from ..middleware.cache_manager import clear_all_cache
        
        await clear_all_cache()
        
        logger.warning("All cache cleared by admin action")
        
        return {
            "success": True,
            "message": "All cache entries cleared"
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to clear cache"
        )


@router.post("/warming/{name}/start")
async def start_cache_warming(name: str):
    """
    Start cache warming for a specific entry
    
    Cache warming proactively refreshes cache entries
    before they expire, preventing cache misses.
    """
    try:
        from ..middleware.cache_manager import cache_warmer
        
        # This would need to be configured with actual functions to warm
        # For now, return status
        
        return {
            "success": False,
            "message": "Cache warming must be configured programmatically",
            "hint": "Use @cached_with_warming decorator in your code"
        }
        
    except Exception as e:
        logger.error(f"Error starting cache warming: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to start cache warming"
        )


@router.post("/warming/{name}/stop")
async def stop_cache_warming(name: str):
    """Stop cache warming for a specific entry"""
    try:
        from ..middleware.cache_manager import cache_warmer
        
        cache_warmer.stop_warming(name)
        
        return {
            "success": True,
            "message": f"Cache warming stopped for '{name}'"
        }
        
    except Exception as e:
        logger.error(f"Error stopping cache warming: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to stop cache warming"
        )


@router.get("/stats")
async def get_cache_stats():
    """
    Get detailed cache statistics
    
    Includes:
    - Hit rate percentage
    - Total hits/misses
    - Error count
    - Warming task status
    """
    try:
        from ..middleware.cache_manager import cache_stats, cache_warmer
        
        return {
            "cache_performance": cache_stats.get_stats(),
            "warming_status": cache_warmer.get_status()
        }
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve cache statistics"
        )


@router.post("/stats/reset")
async def reset_cache_stats():
    """Reset cache statistics counters"""
    try:
        from ..middleware.cache_manager import cache_stats
        
        cache_stats.reset()
        
        return {
            "success": True,
            "message": "Cache statistics reset"
        }
        
    except Exception as e:
        logger.error(f"Error resetting cache stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to reset cache statistics"
        )
