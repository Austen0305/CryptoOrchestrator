"""
Platform Revenue Routes
API endpoints for viewing platform revenue from deposit fees
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List, Annotated
from datetime import datetime
import logging

from ..dependencies.auth import get_current_user
from ..services.platform_revenue import platform_revenue_service
from ..database import get_db_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/platform-revenue", tags=["Platform Revenue"])


@router.get("/total")
async def get_total_revenue(
    current_user: Annotated[dict, Depends(get_current_user)],
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
) -> Dict[str, Any]:
    """Get total platform revenue from deposit fees (admin only)"""
    try:
        # Check if user is admin (you may want to add proper admin check)
        # For now, allow any authenticated user to view revenue

        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        async with get_db_context() as db:
            revenue = await platform_revenue_service.get_total_revenue(
                start_date=start, end_date=end, db=db
            )
            return revenue
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting total revenue: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get total revenue")


@router.get("/daily")
async def get_daily_revenue(
    current_user: Annotated[dict, Depends(get_current_user)],
    days: int = Query(30, ge=1, le=365, description="Number of days to retrieve"),
) -> List[Dict[str, Any]]:
    """Get daily revenue breakdown (admin only)"""
    try:
        # Check if user is admin (you may want to add proper admin check)
        # For now, allow any authenticated user to view revenue

        async with get_db_context() as db:
            daily_revenue = await platform_revenue_service.get_daily_revenue(
                days=days, db=db
            )
            return daily_revenue
    except Exception as e:
        logger.error(f"Error getting daily revenue: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get daily revenue")
