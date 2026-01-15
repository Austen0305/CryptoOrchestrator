"""
Social & Community API Routes
Endpoints for strategy sharing, social feed, profiles, achievements, and challenges
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies.auth import get_current_user, get_optional_user
from ..models.social import StrategyVisibility
from ..services.social_service import SocialService
from ..utils.route_helpers import _get_user_id

router = APIRouter(prefix="/api/social", tags=["Social & Community"])


# Pydantic Models
class ShareStrategyRequest(BaseModel):
    name: str
    strategy_config: dict[str, Any]
    description: str | None = None
    visibility: str = "public"  # public, private, unlisted
    tags: list[str] | None = None
    category: str | None = None


class CommentRequest(BaseModel):
    content: str
    parent_comment_id: int | None = None


class UpdateProfileRequest(BaseModel):
    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    website_url: str | None = None
    twitter_handle: str | None = None
    telegram_handle: str | None = None
    is_public: bool | None = None
    show_trading_stats: bool | None = None


class CreateChallengeRequest(BaseModel):
    name: str
    description: str
    challenge_type: str
    rules: dict[str, Any]
    start_date: str  # ISO format
    end_date: str  # ISO format
    prizes: dict[str, Any] | None = None


# Strategy Sharing Routes
@router.post("/strategies/share")
async def share_strategy(
    request: ShareStrategyRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Share a trading strategy"""
    service = SocialService(db)

    visibility = StrategyVisibility[request.visibility.upper()]

    strategy = await service.share_strategy(
        user_id=_get_user_id(current_user),
        name=request.name,
        strategy_config=request.strategy_config,
        description=request.description,
        visibility=visibility,
        tags=request.tags,
        category=request.category,
    )

    return {
        "id": strategy.id,
        "name": strategy.name,
        "share_token": strategy.share_token,
        "visibility": strategy.visibility.value,
    }


@router.get("/strategies")
async def get_strategies(
    category: str | None = Query(None),
    featured_only: bool = Query(False),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get shared strategies"""
    service = SocialService(db)

    user_id = _get_user_id(current_user) if current_user else None

    strategies = await service.get_strategies(
        user_id=user_id,
        category=category,
        featured_only=featured_only,
        limit=limit,
        offset=offset,
    )

    return {"strategies": strategies, "count": len(strategies)}


@router.post("/strategies/{strategy_id}/like")
async def like_strategy(
    strategy_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Like/unlike a strategy"""
    service = SocialService(db)

    is_liked = await service.like_strategy(
        user_id=_get_user_id(current_user),
        strategy_id=strategy_id,
    )

    return {"liked": is_liked}


@router.post("/strategies/{strategy_id}/comment")
async def comment_on_strategy(
    strategy_id: int,
    request: CommentRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Comment on a strategy"""
    service = SocialService(db)

    comment = await service.comment_on_strategy(
        user_id=_get_user_id(current_user),
        strategy_id=strategy_id,
        content=request.content,
        parent_comment_id=request.parent_comment_id,
    )

    return {"id": comment.id, "content": comment.content}


# Social Feed Routes
@router.get("/feed")
async def get_feed(
    following_only: bool = Query(False),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get social feed"""
    service = SocialService(db)

    user_id = _get_user_id(current_user) if current_user else None

    feed = await service.get_feed(
        user_id=user_id,
        following_only=following_only,
        limit=limit,
        offset=offset,
    )

    return {"events": feed, "count": len(feed)}


# User Profile Routes
@router.get("/profiles/me")
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get current user's profile"""
    service = SocialService(db)

    profile = await service.get_or_create_profile(_get_user_id(current_user))
    return profile


@router.get("/profiles/{user_id}")
async def get_user_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Get user profile (public)"""
    service = SocialService(db)

    profile = await service.get_or_create_profile(user_id)

    if not profile.is_public:
        raise HTTPException(status_code=404, detail="Profile not found")

    return profile


@router.put("/profiles/me")
async def update_profile(
    request: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Update user profile"""
    service = SocialService(db)

    profile = await service.update_profile(
        user_id=_get_user_id(current_user),
        display_name=request.display_name,
        bio=request.bio,
        avatar_url=request.avatar_url,
        website_url=request.website_url,
        twitter_handle=request.twitter_handle,
        telegram_handle=request.telegram_handle,
        is_public=request.is_public,
        show_trading_stats=request.show_trading_stats,
    )

    return profile


@router.post("/profiles/me/refresh-stats")
async def refresh_profile_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Refresh cached profile statistics"""
    service = SocialService(db)

    profile = await service.update_profile_stats(_get_user_id(current_user))
    return profile


# Achievement Routes
@router.get("/achievements")
async def get_achievements(
    current_user: dict = Depends(get_current_user),
    completed_only: bool = Query(False),
    db: AsyncSession = Depends(get_db_session),
):
    """Get user achievements"""
    service = SocialService(db)

    achievements = await service.get_user_achievements(
        user_id=_get_user_id(current_user),
        completed_only=completed_only,
    )

    return {"achievements": achievements}


@router.post("/achievements/check")
async def check_achievements(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Check and award achievements"""
    service = SocialService(db)

    newly_awarded = await service.check_and_award_achievements(
        _get_user_id(current_user)
    )

    return {
        "newly_awarded": newly_awarded,
        "count": len(newly_awarded),
    }


# Community Challenge Routes
@router.post("/challenges")
async def create_challenge(
    request: CreateChallengeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a community challenge"""
    service = SocialService(db)

    challenge = await service.create_challenge(
        name=request.name,
        description=request.description,
        challenge_type=request.challenge_type,
        rules=request.rules,
        start_date=datetime.fromisoformat(request.start_date),
        end_date=datetime.fromisoformat(request.end_date),
        created_by_user_id=_get_user_id(current_user),
        prizes=request.prizes,
    )

    return {"id": challenge.id, "name": challenge.name}


@router.get("/challenges")
async def get_challenges(
    active_only: bool = Query(True),
    featured_only: bool = Query(False),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
):
    """Get community challenges"""
    from sqlalchemy import and_, select

    from ..models.social import CommunityChallenge

    stmt = select(CommunityChallenge)

    if active_only:
        now = datetime.now(UTC)
        stmt = stmt.where(
            and_(
                CommunityChallenge.is_active,
                CommunityChallenge.start_date <= now,
                CommunityChallenge.end_date >= now,
            )
        )

    if featured_only:
        stmt = stmt.where(CommunityChallenge.is_featured)

    stmt = stmt.order_by(CommunityChallenge.start_date.desc())
    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    challenges = result.scalars().all()

    return {"challenges": challenges, "count": len(challenges)}


@router.post("/challenges/{challenge_id}/join")
async def join_challenge(
    challenge_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Join a community challenge"""
    service = SocialService(db)

    participant = await service.join_challenge(
        user_id=_get_user_id(current_user),
        challenge_id=challenge_id,
    )

    return {"id": participant.id, "challenge_id": challenge_id}


@router.get("/challenges/{challenge_id}/leaderboard")
async def get_challenge_leaderboard(
    challenge_id: int,
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db_session),
):
    """Get challenge leaderboard"""
    service = SocialService(db)

    leaderboard = await service.get_challenge_leaderboard(
        challenge_id=challenge_id,
        limit=limit,
    )

    return {"leaderboard": leaderboard, "count": len(leaderboard)}
