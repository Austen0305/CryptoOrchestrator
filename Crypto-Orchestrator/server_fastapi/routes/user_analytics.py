"""
User Analytics API Routes
Endpoints for tracking and retrieving user analytics
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from ..database import get_db_session
from ..dependencies.auth import get_optional_user
from ..models.user import User
from ..services.user_analytics_service import UserAnalyticsService

router = APIRouter(prefix="/api/analytics/user", tags=["User Analytics"])


# Pydantic Models
class TrackEventRequest(BaseModel):
    session_id: Optional[str] = None
    event_type: str
    event_name: str
    event_category: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    page_url: Optional[str] = None
    page_title: Optional[str] = None
    referrer: Optional[str] = None
    duration_ms: Optional[int] = None


class TrackFeatureUsageRequest(BaseModel):
    feature_name: str
    action: str
    feature_category: Optional[str] = None
    duration_seconds: Optional[int] = None
    success: bool = True
    properties: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class TrackFunnelStageRequest(BaseModel):
    session_id: Optional[str] = None
    funnel_name: str
    stage: str
    stage_order: int
    time_to_stage_seconds: Optional[int] = None
    time_in_stage_seconds: Optional[int] = None
    properties: Optional[Dict[str, Any]] = None
    source: Optional[str] = None


class TrackJourneyStepRequest(BaseModel):
    session_id: str
    journey_type: str
    step_name: str
    step_order: int
    previous_step: Optional[str] = None
    next_step: Optional[str] = None
    path: Optional[List[str]] = None
    time_to_step_seconds: Optional[int] = None
    time_in_step_seconds: Optional[int] = None
    properties: Optional[Dict[str, Any]] = None


class RecordSatisfactionRequest(BaseModel):
    survey_type: str  # nps, csat, ces
    score: int
    question: Optional[str] = None
    response: Optional[str] = None
    context: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


# Event Tracking Routes
@router.post("/events/track")
async def track_event(
    request: TrackEventRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Track a user event"""
    service = UserAnalyticsService(db)
    
    # Get user agent and IP from request headers (would need middleware)
    event = await service.track_event(
        user_id=current_user.id if current_user else None,
        session_id=request.session_id,
        event_type=request.event_type,
        event_name=request.event_name,
        event_category=request.event_category,
        properties=request.properties,
        page_url=request.page_url,
        page_title=request.page_title,
        referrer=request.referrer,
        duration_ms=request.duration_ms,
    )
    
    return {"success": True, "event_id": event.id}


@router.get("/events")
async def get_user_events(
    event_type: Optional[str] = Query(None),
    event_category: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    current_user: Optional[dict] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get user events"""
    service = UserAnalyticsService(db)
    
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    events = await service.get_user_events(
        user_id=current_user.id if current_user else None,
        event_type=event_type,
        event_category=event_category,
        start_date=start,
        end_date=end,
        limit=limit,
        offset=offset,
    )
    
    return {"events": events, "count": len(events)}


@router.get("/events/analytics")
async def get_event_analytics(
    event_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
):
    """Get aggregated event analytics"""
    service = UserAnalyticsService(db)
    
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    analytics = await service.get_event_analytics(
        event_type=event_type,
        start_date=start,
        end_date=end,
    )
    
    return analytics


# Feature Usage Routes
@router.post("/features/track")
async def track_feature_usage(
    request: TrackFeatureUsageRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Track feature usage"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    service = UserAnalyticsService(db)
    
    usage = await service.track_feature_usage(
        user_id=current_user.id,
        feature_name=request.feature_name,
        action=request.action,
        feature_category=request.feature_category,
        duration_seconds=request.duration_seconds,
        success=request.success,
        properties=request.properties,
        error_message=request.error_message,
    )
    
    return {"success": True, "usage_id": usage.id}


@router.get("/features/stats")
async def get_feature_usage_stats(
    feature_name: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
):
    """Get feature usage statistics"""
    service = UserAnalyticsService(db)
    
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    stats = await service.get_feature_usage_stats(
        feature_name=feature_name,
        start_date=start,
        end_date=end,
    )
    
    return stats


# Conversion Funnel Routes
@router.post("/funnels/track")
async def track_funnel_stage(
    request: TrackFunnelStageRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Track a conversion funnel stage"""
    service = UserAnalyticsService(db)
    
    funnel = await service.track_funnel_stage(
        user_id=current_user.id if current_user else None,
        session_id=request.session_id,
        funnel_name=request.funnel_name,
        stage=request.stage,
        stage_order=request.stage_order,
        time_to_stage_seconds=request.time_to_stage_seconds,
        time_in_stage_seconds=request.time_in_stage_seconds,
        properties=request.properties,
        source=request.source,
    )
    
    return {"success": True, "funnel_id": funnel.id}


@router.post("/funnels/complete")
async def complete_funnel(
    funnel_name: str,
    session_id: Optional[str] = Query(None),
    current_user: Optional[dict] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Mark a funnel as completed"""
    service = UserAnalyticsService(db)
    
    success = await service.complete_funnel(
        user_id=current_user.id if current_user else None,
        session_id=session_id,
        funnel_name=funnel_name,
    )
    
    return {"success": success}


@router.get("/funnels/{funnel_name}/analytics")
async def get_funnel_analytics(
    funnel_name: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
):
    """Get conversion funnel analytics"""
    service = UserAnalyticsService(db)
    
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    analytics = await service.get_funnel_analytics(
        funnel_name=funnel_name,
        start_date=start,
        end_date=end,
    )
    
    return analytics


# User Journey Routes
@router.post("/journeys/track")
async def track_journey_step(
    request: TrackJourneyStepRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Track a user journey step"""
    service = UserAnalyticsService(db)
    
    journey = await service.track_journey_step(
        user_id=current_user.id if current_user else None,
        session_id=request.session_id,
        journey_type=request.journey_type,
        step_name=request.step_name,
        step_order=request.step_order,
        previous_step=request.previous_step,
        next_step=request.next_step,
        path=request.path,
        time_to_step_seconds=request.time_to_step_seconds,
        time_in_step_seconds=request.time_in_step_seconds,
        properties=request.properties,
    )
    
    return {"success": True, "journey_id": journey.id}


@router.post("/journeys/complete")
async def complete_journey(
    journey_type: str,
    session_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Mark a journey as completed"""
    service = UserAnalyticsService(db)
    
    success = await service.complete_journey(
        session_id=session_id,
        journey_type=journey_type,
    )
    
    return {"success": success}


@router.get("/journeys/analytics")
async def get_journey_analytics(
    journey_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
):
    """Get user journey analytics"""
    service = UserAnalyticsService(db)
    
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    analytics = await service.get_journey_analytics(
        journey_type=journey_type,
        start_date=start,
        end_date=end,
    )
    
    return analytics


# User Satisfaction Routes
@router.post("/satisfaction/record")
async def record_satisfaction(
    request: RecordSatisfactionRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Record user satisfaction score"""
    service = UserAnalyticsService(db)
    
    satisfaction = await service.record_satisfaction(
        user_id=current_user.id if current_user else None,
        survey_type=request.survey_type,
        score=request.score,
        question=request.question,
        response=request.response,
        context=request.context,
        properties=request.properties,
    )
    
    return {"success": True, "satisfaction_id": satisfaction.id}


@router.get("/satisfaction/metrics")
async def get_satisfaction_metrics(
    survey_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
):
    """Get user satisfaction metrics"""
    service = UserAnalyticsService(db)
    
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    metrics = await service.get_satisfaction_metrics(
        survey_type=survey_type,
        start_date=start,
        end_date=end,
    )
    
    return metrics
