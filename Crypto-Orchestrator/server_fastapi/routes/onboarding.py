"""
Onboarding API Routes
Endpoints for user onboarding, achievements, and feature unlocking
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Annotated
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies.auth import get_current_user
from ..database import get_db_session
from ..utils.route_helpers import _get_user_id
from ..services.onboarding_service import OnboardingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/onboarding", tags=["Onboarding"])


# Request/Response Models
class CompleteStepRequest(BaseModel):
    step_id: str = Field(..., description="Step identifier to complete")


class SkipStepRequest(BaseModel):
    step_id: str = Field(..., description="Step identifier to skip")


class OnboardingProgressResponse(BaseModel):
    user_id: int
    current_step: Optional[str]
    completed_steps: Dict[str, str]
    skipped_steps: Dict[str, str]
    progress_percentage: int
    total_steps: int
    is_completed: bool
    completed_at: Optional[str]


class AchievementResponse(BaseModel):
    id: int
    achievement_id: str
    achievement_name: str
    achievement_description: Optional[str]
    progress: int
    max_progress: int
    is_unlocked: bool
    unlocked_at: Optional[str]




@router.get("/progress", response_model=OnboardingProgressResponse)
async def get_onboarding_progress(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get onboarding progress for current user"""
    try:
        user_id = _get_user_id(current_user)
        service = OnboardingService(db)
        
        progress = await service.get_or_create_progress(user_id)
        
        return OnboardingProgressResponse(
            user_id=progress.user_id,
            current_step=progress.current_step,
            completed_steps=progress.completed_steps or {},
            skipped_steps=progress.skipped_steps or {},
            progress_percentage=progress.progress_percentage,
            total_steps=progress.total_steps,
            is_completed=progress.is_completed,
            completed_at=progress.completed_at.isoformat() if progress.completed_at else None,
        )
    except Exception as e:
        logger.error(f"Error getting onboarding progress: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get onboarding progress")


@router.post("/complete-step", response_model=OnboardingProgressResponse)
async def complete_step(
    request: CompleteStepRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Complete an onboarding step"""
    try:
        user_id = _get_user_id(current_user)
        service = OnboardingService(db)
        
        progress = await service.complete_step(user_id, request.step_id)
        
        return OnboardingProgressResponse(
            user_id=progress.user_id,
            current_step=progress.current_step,
            completed_steps=progress.completed_steps or {},
            skipped_steps=progress.skipped_steps or {},
            progress_percentage=progress.progress_percentage,
            total_steps=progress.total_steps,
            is_completed=progress.is_completed,
            completed_at=progress.completed_at.isoformat() if progress.completed_at else None,
        )
    except Exception as e:
        logger.error(f"Error completing step: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to complete step")


@router.post("/skip-step", response_model=OnboardingProgressResponse)
async def skip_step(
    request: SkipStepRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Skip an onboarding step"""
    try:
        user_id = _get_user_id(current_user)
        service = OnboardingService(db)
        
        progress = await service.skip_step(user_id, request.step_id)
        
        return OnboardingProgressResponse(
            user_id=progress.user_id,
            current_step=progress.current_step,
            completed_steps=progress.completed_steps or {},
            skipped_steps=progress.skipped_steps or {},
            progress_percentage=progress.progress_percentage,
            total_steps=progress.total_steps,
            is_completed=progress.is_completed,
            completed_at=progress.completed_at.isoformat() if progress.completed_at else None,
        )
    except Exception as e:
        logger.error(f"Error skipping step: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to skip step")


@router.post("/reset")
async def reset_onboarding(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Reset onboarding progress"""
    try:
        user_id = _get_user_id(current_user)
        service = OnboardingService(db)
        
        progress = await service.reset_progress(user_id)
        
        return {"success": True, "message": "Onboarding progress reset"}
    except Exception as e:
        logger.error(f"Error resetting onboarding: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to reset onboarding")


@router.get("/achievements", response_model=List[AchievementResponse])
async def get_achievements(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get all achievements for current user"""
    try:
        user_id = _get_user_id(current_user)
        service = OnboardingService(db)
        
        achievements = await service.get_user_achievements(user_id)
        
        return [
            AchievementResponse(
                id=a.id,
                achievement_id=a.achievement_id,
                achievement_name=a.achievement_name,
                achievement_description=a.achievement_description,
                progress=a.progress,
                max_progress=a.max_progress,
                is_unlocked=a.is_unlocked,
                unlocked_at=a.unlocked_at.isoformat() if a.unlocked_at else None,
            )
            for a in achievements
        ]
    except Exception as e:
        logger.error(f"Error getting achievements: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get achievements")


