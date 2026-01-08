"""
Admin Panel Routes
Admin-only endpoints for managing users, subscriptions, and system
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies.user import require_admin
from ..middleware.cache_manager import cached
from ..models.bot import Bot
from ..models.subscription import Subscription
from ..models.trade import Trade
from ..models.user import User
from ..services.marketplace_analytics_service import MarketplaceAnalyticsService
from ..utils.query_optimizer import QueryOptimizer

try:
    from ..rate_limit_config import get_rate_limit, limiter
except ImportError:
    limiter = None
    get_rate_limit = lambda x: x

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


# Request/Response Models
class UserSummary(BaseModel):
    id: int
    email: str
    username: str
    role: str
    is_active: bool
    is_email_verified: bool
    created_at: str
    last_login_at: str | None = None
    subscription_plan: str | None = None
    subscription_status: str | None = None
    bot_count: int = 0
    trade_count: int = 0


class AdminStats(BaseModel):
    total_users: int
    active_users: int
    verified_users: int
    total_subscriptions: int
    active_subscriptions: int
    total_bots: int
    active_bots: int
    total_trades: int
    revenue_by_plan: dict[str, int]


@router.get("/stats")
@cached(ttl=120, prefix="admin_stats")  # 120s TTL for admin statistics
async def get_admin_stats(
    admin: Annotated[User, Depends(require_admin())],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get admin dashboard statistics"""
    try:
        # User statistics
        total_users_result = await db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar() or 0

        active_users_result = await db.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        active_users = active_users_result.scalar() or 0

        verified_users_result = await db.execute(
            select(func.count(User.id)).where(User.is_email_verified == True)
        )
        verified_users = verified_users_result.scalar() or 0

        # Subscription statistics
        total_subscriptions_result = await db.execute(
            select(func.count(Subscription.id))
        )
        total_subscriptions = total_subscriptions_result.scalar() or 0

        active_subscriptions_result = await db.execute(
            select(func.count(Subscription.id)).where(Subscription.status == "active")
        )
        active_subscriptions = active_subscriptions_result.scalar() or 0

        # Bot statistics
        total_bots_result = await db.execute(select(func.count(Bot.id)))
        total_bots = total_bots_result.scalar() or 0

        active_bots_result = await db.execute(
            select(func.count(Bot.id)).where(Bot.active == True)
        )
        active_bots = active_bots_result.scalar() or 0

        # Trade statistics
        total_trades_result = await db.execute(select(func.count(Trade.id)))
        total_trades = total_trades_result.scalar() or 0

        # Revenue by plan (mock for now - integrate with Stripe if needed)
        revenue_by_plan = {
            "free": 0,
            "basic": 0,
            "pro": 0,
            "enterprise": 0,
        }

        return AdminStats(
            total_users=total_users,
            active_users=active_users,
            verified_users=verified_users,
            total_subscriptions=total_subscriptions,
            active_subscriptions=active_subscriptions,
            total_bots=total_bots,
            active_bots=active_bots,
            total_trades=total_trades,
            revenue_by_plan=revenue_by_plan,
        )

    except Exception as e:
        logger.error(f"Failed to get admin stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get admin statistics",
        )


@router.get("/users")
@cached(ttl=120, prefix="admin_users")  # 120s TTL for user list
async def get_users(
    admin: Annotated[User, Depends(require_admin())],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = None,
    role: str | None = None,
):
    """Get list of users with pagination"""
    try:
        query = select(User)

        # Apply filters
        if search:
            query = query.where(
                (User.email.ilike(f"%{search}%")) | (User.username.ilike(f"%{search}%"))
            )

        if role:
            query = query.where(User.role == role)

        # Get total count
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        # Apply pagination using QueryOptimizer
        query = QueryOptimizer.paginate_query(query, page=page, page_size=page_size)

        result = await db.execute(query)
        users = result.scalars().all()

        # Get subscription and bot counts for each user
        user_summaries = []
        for user in users:
            # Get subscription
            sub_result = await db.execute(
                select(Subscription).where(Subscription.user_id == user.id)
            )
            subscription = sub_result.scalar_one_or_none()

            # Get bot count
            bot_count_result = await db.execute(
                select(func.count(Bot.id)).where(Bot.user_id == user.id)
            )
            bot_count = bot_count_result.scalar() or 0

            # Get trade count
            trade_count_result = await db.execute(
                select(func.count(Trade.id)).where(Trade.user_id == user.id)
            )
            trade_count = trade_count_result.scalar() or 0

            user_summaries.append(
                UserSummary(
                    id=user.id,
                    email=user.email,
                    username=user.username,
                    role=user.role,
                    is_active=user.is_active,
                    is_email_verified=user.is_email_verified,
                    created_at=user.created_at.isoformat(),
                    last_login_at=(
                        user.last_login_at.isoformat() if user.last_login_at else None
                    ),
                    subscription_plan=subscription.plan if subscription else None,
                    subscription_status=subscription.status if subscription else None,
                    bot_count=bot_count,
                    trade_count=trade_count,
                )
            )

        return {
            "users": user_summaries,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    except Exception as e:
        logger.error(f"Failed to get users: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get users",
        )


@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    admin: Annotated[User, Depends(require_admin())],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get detailed user information"""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Get subscription
        sub_result = await db.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )
        subscription = sub_result.scalar_one_or_none()

        # Get user bots
        bots_result = await db.execute(select(Bot).where(Bot.user_id == user.id))
        bots = bots_result.scalars().all()

        # Get user trades
        trades_result = await db.execute(
            select(Trade).where(Trade.user_id == user.id).limit(10)
        )
        trades = trades_result.scalars().all()

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "is_active": user.is_active,
                "is_email_verified": user.is_email_verified,
                "created_at": user.created_at.isoformat(),
                "last_login_at": (
                    user.last_login_at.isoformat() if user.last_login_at else None
                ),
                "login_count": user.login_count,
            },
            "subscription": (
                {
                    "plan": subscription.plan if subscription else None,
                    "status": subscription.status if subscription else None,
                    "current_period_end": (
                        subscription.current_period_end.isoformat()
                        if subscription and subscription.current_period_end
                        else None
                    ),
                }
                if subscription
                else None
            ),
            "bots": [bot.to_dict() for bot in bots],
            "recent_trades": (
                [trade.to_dict() for trade in trades]
                if hasattr(Trade, "to_dict")
                else []
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user",
        )


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: int,
    admin: Annotated[User, Depends(require_admin())],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Activate a user account"""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        user.is_active = True
        await db.commit()

        return {"success": True, "message": "User activated"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate user",
        )


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    admin: Annotated[User, Depends(require_admin())],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Deactivate a user account"""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        user.is_active = False

        # Stop all user's bots
        bots_result = await db.execute(select(Bot).where(Bot.user_id == user.id))
        bots = bots_result.scalars().all()
        for bot in bots:
            bot.active = False
            bot.status = "stopped"

        await db.commit()

        return {"success": True, "message": "User deactivated and bots stopped"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user",
        )


@router.get("/logs")
@cached(ttl=60, prefix="admin_logs")  # 60s TTL for admin logs
async def get_logs(
    admin: Annotated[User, Depends(require_admin())],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    level: str | None = None,
):
    """Get system logs with pagination (if stored in database)"""
    try:
        # Get recent audit logs (last 7 days by default)
        # Note: This is a simplified implementation - full implementation would query database
        logs = []
        try:
            # Try to get logs from audit logger if it supports retrieval
            # For now, return empty as audit logger may not have retrieval method
            # Full implementation would query the audit_logs table
            pass
        except Exception as e:
            logger.debug(f"Log retrieval not fully implemented: {e}")

        # Apply pagination
        total = len(logs)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_logs = logs[start_idx:end_idx]

        return {
            "logs": paginated_logs,
            "total": total,
            "page": page,
            "page_size": page_size,
            "note": "Log storage retrieval requires database integration with audit_logs table",
        }
    except Exception as e:
        logger.error(f"Failed to get system logs: {e}", exc_info=True)
        return {
            "logs": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "error": "Log retrieval not available",
        }


@router.get("/marketplace/overview")
@cached(ttl=300, prefix="admin_marketplace_overview")
async def get_marketplace_overview(
    request: Request,
    admin: Annotated[User, Depends(require_admin())],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    if limiter:
        limiter.limit(get_rate_limit("30/minute"))(get_marketplace_overview)
    """Get marketplace overview statistics (admin only)"""
    try:
        analytics_service = MarketplaceAnalyticsService(db)
        overview = await analytics_service.get_marketplace_overview()
        return overview
    except Exception as e:
        logger.error(f"Failed to get marketplace overview: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get marketplace overview",
        )


@router.get("/marketplace/top-providers")
@cached(ttl=300, prefix="admin_top_providers")
async def get_top_providers(
    admin: Annotated[User, Depends(require_admin())],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(10, ge=1, le=50, description="Number of top providers"),
    sort_by: str = Query(
        "total_return",
        description="Sort by: total_return, sharpe_ratio, follower_count, rating",
    ),
):
    """Get top performing signal providers (admin only)"""
    try:
        analytics_service = MarketplaceAnalyticsService(db)
        top_providers = await analytics_service.get_top_providers(
            limit=limit, sort_by=sort_by
        )
        return {"providers": top_providers, "limit": limit, "sort_by": sort_by}
    except Exception as e:
        logger.error(f"Failed to get top providers: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get top providers",
        )


@router.get("/marketplace/top-indicators")
@cached(ttl=300, prefix="admin_top_indicators")
async def get_top_indicators(
    request: Request,
    admin: Annotated[User, Depends(require_admin())],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(10, ge=1, le=50, description="Number of top indicators"),
    sort_by: str = Query(
        "purchase_count", description="Sort by: purchase_count, rating, price"
    ),
):
    """Get top performing indicators (admin only)"""
    try:
        analytics_service = MarketplaceAnalyticsService(db)
        top_indicators = await analytics_service.get_top_indicators(
            limit=limit, sort_by=sort_by
        )
        return {"indicators": top_indicators, "limit": limit, "sort_by": sort_by}
    except Exception as e:
        logger.error(f"Failed to get top indicators: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get top indicators",
        )


@router.get("/marketplace/revenue-trends")
@cached(ttl=600, prefix="admin_revenue_trends")
async def get_revenue_trends(
    request: Request,
    admin: Annotated[User, Depends(require_admin())],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
):
    """Get revenue trends over time (admin only)"""
    try:
        analytics_service = MarketplaceAnalyticsService(db)
        trends = await analytics_service.get_revenue_trends(days=days)
        return trends
    except Exception as e:
        logger.error(f"Failed to get revenue trends: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get revenue trends",
        )
