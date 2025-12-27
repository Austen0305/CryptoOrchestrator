"""
Notification service dependencies to ensure shared DB sessions per request.
Uses Annotated pattern for better type hints and dependency injection.
"""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..services.notification_service import NotificationService
from ..repositories.user_repository import UserRepository
from ..repositories.push_subscription_repository import PushSubscriptionRepository


async def get_notification_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> NotificationService:
    """Provide notification service with injected repositories."""
    # ✅ Inject repositories via dependency injection (Service Layer Pattern)
    user_repository = UserRepository()
    # Note: PushSubscriptionRepository takes db in __init__
    push_subscription_repository = PushSubscriptionRepository(db)

    return NotificationService(
        db=db,
        user_repository=user_repository,
        push_subscription_repository=push_subscription_repository,
    )
