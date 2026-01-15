"""
NPS Tracking API Endpoints
Net Promoter Score tracking and analysis
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies.auth import get_current_user, require_permission
from ..services.nps_tracking_service import NPSTrackingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nps", tags=["NPS Tracking"])


@router.post("/submit")
async def submit_nps(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    score: int = Query(..., ge=0, le=10, description="NPS score (0-10)"),
    response: str | None = Query(None, description="Optional feedback text"),
    context: str | None = Query(None, description="Context for the survey"),
) -> dict[str, Any]:
    """Submit an NPS score (authenticated users)"""
    try:
        user_id = current_user.get("id") if isinstance(current_user, dict) else None
        service = NPSTrackingService(db)
        satisfaction = await service.record_nps(
            user_id=user_id,
            score=score,
            response=response,
            context=context,
        )
        return {
            "success": True,
            "message": "NPS score recorded",
            "id": satisfaction.id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error submitting NPS: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit NPS score") from e


@router.get("/current")
async def get_current_nps(
    current_user: Annotated[dict, Depends(require_permission("admin:metrics"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
) -> dict[str, Any]:
    """Get current NPS score (admin only)"""
    try:
        start_date = datetime.now(UTC) - timedelta(days=days)
        service = NPSTrackingService(db)
        nps_data = await service.calculate_nps(start_date=start_date)
        return nps_data
    except Exception as e:
        logger.error(f"Error getting current NPS: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get NPS score") from e


@router.get("/trend")
async def get_nps_trend(
    current_user: Annotated[dict, Depends(require_permission("admin:metrics"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    days: int = Query(30, ge=1, le=365, description="Number of days"),
    period: str = Query(
        "daily", pattern="^(daily|weekly|monthly)$", description="Period grouping"
    ),
) -> list[dict[str, Any]]:
    """Get NPS trend over time (admin only)"""
    try:
        service = NPSTrackingService(db)
        trend = await service.get_nps_trend(days=days, period=period)
        return trend
    except Exception as e:
        logger.error(f"Error getting NPS trend: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get NPS trend") from e


@router.get("/breakdown")
async def get_nps_breakdown(
    current_user: Annotated[dict, Depends(require_permission("admin:metrics"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    start_date: str | None = Query(None, description="Start date (ISO format)"),
    end_date: str | None = Query(None, description="End date (ISO format)"),
) -> dict[str, Any]:
    """Get detailed NPS breakdown with feedback (admin only)"""
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        service = NPSTrackingService(db)
        breakdown = await service.get_nps_breakdown(start_date=start, end_date=end)
        return breakdown
    except Exception as e:
        logger.error(f"Error getting NPS breakdown: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to get NPS breakdown"
        ) from e


@router.get("/improvement-suggestions")
async def get_nps_improvement_suggestions(
    current_user: Annotated[dict, Depends(require_permission("admin:metrics"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    """Get NPS improvement suggestions based on feedback (admin only)"""
    try:
        service = NPSTrackingService(db)

        # Get recent NPS data
        nps_data = await service.calculate_nps()
        breakdown = await service.get_nps_breakdown()

        # Analyze feedback for common themes
        suggestions = []

        if nps_data.get("nps_score", 0) < 50:
            suggestions.append(
                {
                    "priority": "high",
                    "area": "Overall Experience",
                    "suggestion": "Focus on improving core user experience to increase promoter percentage",
                    "target": "Increase NPS to 50+",
                }
            )

        if breakdown.get("sample_feedback", {}).get("detractors"):
            detractor_count = len(breakdown["sample_feedback"]["detractors"])
            if detractor_count > 0:
                suggestions.append(
                    {
                        "priority": "high",
                        "area": "Detractor Feedback",
                        "suggestion": f"Address concerns from {detractor_count} detractor responses",
                        "action": "Review detractor feedback and prioritize improvements",
                    }
                )

        if nps_data.get("promoter_percentage", 0) < 50:
            suggestions.append(
                {
                    "priority": "medium",
                    "area": "Promoter Conversion",
                    "suggestion": "Focus on converting passives to promoters",
                    "target": "Increase promoter percentage to 50%+",
                }
            )

        return {
            "current_nps": nps_data.get("nps_score", 0),
            "suggestions": suggestions,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting improvement suggestions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to get improvement suggestions"
        ) from e
