"""
Admin Panel Routes
Admin-only endpoints for managing users, subscriptions, and system
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..database import get_db_session
from ..dependencies.user import get_current_user_db, require_admin
from ..models.user import User
from ..models.subscription import Subscription
from ..models.bot import Bot
from ..models.trade import Trade
from ..billing import SubscriptionService

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
    last_login_at: Optional[str] = None
    subscription_plan: Optional[str] = None
    subscription_status: Optional[str] = None
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
    revenue_by_plan: Dict[str, int]


@router.get("/stats")
async def get_admin_stats(
    admin: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db_session),
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
        total_subscriptions_result = await db.execute(select(func.count(Subscription.id)))
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
            detail="Failed to get admin statistics"
        )


@router.get("/users")
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    admin: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db_session),
):
    """Get list of users with pagination"""
    try:
        query = select(User)
        
        # Apply filters
        if search:
            query = query.where(
                (User.email.ilike(f"%{search}%")) |
                (User.username.ilike(f"%{search}%"))
            )
        
        if role:
            query = query.where(User.role == role)
        
        # Get total count
        count_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar() or 0
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
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
            
            user_summaries.append(UserSummary(
                id=user.id,
                email=user.email,
                username=user.username,
                role=user.role,
                is_active=user.is_active,
                is_email_verified=user.is_email_verified,
                created_at=user.created_at.isoformat(),
                last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
                subscription_plan=subscription.plan if subscription else None,
                subscription_status=subscription.status if subscription else None,
                bot_count=bot_count,
                trade_count=trade_count,
            ))
        
        return {
            "users": user_summaries,
            "total": total,
            "skip": skip,
            "limit": limit,
        }
        
    except Exception as e:
        logger.error(f"Failed to get users: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get users"
        )


@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    admin: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db_session),
):
    """Get detailed user information"""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get subscription
        sub_result = await db.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )
        subscription = sub_result.scalar_one_or_none()
        
        # Get user bots
        bots_result = await db.execute(
            select(Bot).where(Bot.user_id == user.id)
        )
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
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                "login_count": user.login_count,
            },
            "subscription": {
                "plan": subscription.plan if subscription else None,
                "status": subscription.status if subscription else None,
                "current_period_end": subscription.current_period_end.isoformat() if subscription and subscription.current_period_end else None,
            } if subscription else None,
            "bots": [bot.to_dict() for bot in bots],
            "recent_trades": [trade.to_dict() for trade in trades] if hasattr(Trade, 'to_dict') else [],
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: int,
    admin: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db_session),
):
    """Activate a user account"""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = True
        await db.commit()
        
        return {
            "success": True,
            "message": "User activated"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate user"
        )


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    admin: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db_session),
):
    """Deactivate a user account"""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = False
        
        # Stop all user's bots
        bots_result = await db.execute(select(Bot).where(Bot.user_id == user.id))
        bots = bots_result.scalars().all()
        for bot in bots:
            bot.active = False
            bot.status = "stopped"
        
        await db.commit()
        
        return {
            "success": True,
            "message": "User deactivated and bots stopped"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )


@router.get("/logs")
async def get_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    level: Optional[str] = None,
    admin: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db_session),
):
    """Get system logs (if stored in database)"""
    # TODO: Implement log storage and retrieval
    return {
        "logs": [],
        "total": 0,
        "skip": skip,
        "limit": limit,
    }

