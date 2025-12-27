"""
API Analytics Routes
Provides endpoints for viewing API usage analytics
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from ..middleware.api_analytics import api_analytics

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/analytics/summary")
async def get_analytics_summary() -> Dict[str, Any]:
    """Get API analytics summary"""
    try:
        return api_analytics.get_analytics_summary()
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}", exc_info=True)
        return JSONResponse(
            content={"error": str(e)},
            status_code=500,
        )


@router.get("/api/analytics/endpoints")
async def get_endpoint_analytics(
    endpoint: Optional[str] = Query(None, description="Specific endpoint to get stats for")
) -> Dict[str, Any]:
    """Get endpoint analytics"""
    try:
        return api_analytics.get_endpoint_stats(endpoint)
    except Exception as e:
        logger.error(f"Error getting endpoint analytics: {e}", exc_info=True)
        return JSONResponse(
            content={"error": str(e)},
            status_code=500,
        )


@router.get("/api/analytics/popular")
async def get_popular_endpoints(
    limit: int = Query(10, ge=1, le=100, description="Number of endpoints to return")
) -> Dict[str, Any]:
    """Get most popular endpoints"""
    try:
        return {
            "popular_endpoints": api_analytics.get_popular_endpoints(limit),
        }
    except Exception as e:
        logger.error(f"Error getting popular endpoints: {e}", exc_info=True)
        return JSONResponse(
            content={"error": str(e)},
            status_code=500,
        )

