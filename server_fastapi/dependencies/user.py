"""
User dependencies for multi-tenant data isolation
"""

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..models.user import User
from ..utils.route_helpers import _get_user_id
from .auth import get_current_user

logger = logging.getLogger(__name__)


async def get_current_user_db(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    """
    Get current authenticated user from database.
    Use this when you need the full User model object.
    """
    try:
        user_id = _get_user_id(current_user)
        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user from database: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user",
        )


def require_subscription(plan: str | None = None):
    """
    Dependency factory for requiring active subscription.

    Usage:
        @router.post("/premium-feature")
        async def premium_feature(user: User = Depends(require_subscription("pro"))):
            ...
    """

    async def subscription_checker(
        user: Annotated[User, Depends(get_current_user_db)],
        db: Annotated[AsyncSession, Depends(get_db_session)],
    ) -> User:
        from ..billing import SubscriptionService

        subscription_service = SubscriptionService()
        is_active = await subscription_service.check_subscription_active(
            db=db, user_id=user.id
        )

        if not is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Active subscription required",
            )

        # Check specific plan if required
        if plan:
            subscription = await subscription_service.get_user_subscription(db, user.id)
            if not subscription or subscription.plan != plan:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"{plan.capitalize()} subscription required",
                )

        return user

    return subscription_checker


def require_admin():
    """Dependency for requiring admin role"""

    async def admin_checker(
        user: Annotated[User, Depends(get_current_user_db)],
    ) -> User:
        if user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
            )
        return user

    return admin_checker
