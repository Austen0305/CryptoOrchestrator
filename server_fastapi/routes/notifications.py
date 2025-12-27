"""
Push Notification Routes
Handles push notification subscription and unsubscription.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Annotated, Optional
from pydantic import BaseModel, Field
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies.auth import get_current_user
from ..database import get_db_session
from ..repositories.push_subscription_repository import PushSubscriptionRepository
from ..utils.route_helpers import _get_user_id
from ..middleware.cache_manager import cached

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


class PushSubscriptionRequest(BaseModel):
    """Push subscription request model"""

    endpoint: Optional[str] = None
    keys: Optional[Dict[str, str]] = None
    expo_push_token: Optional[str] = Field(
        None, description="Expo push token (e.g., ExponentPushToken[xxxxx])"
    )
    platform: Optional[str] = Field(
        "unknown", description="Platform: 'ios', 'android', 'web'"
    )
    device_id: Optional[str] = None
    app_version: Optional[str] = None


@router.post("/subscribe")
async def subscribe_push_notifications(
    subscription: PushSubscriptionRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Dict[str, Any]:
    """
    Subscribe user to push notifications.

    Stores push subscription for the authenticated user.
    Supports both Expo push tokens and Web Push subscriptions.
    """
    try:
        user_id = _get_user_id(current_user)

        # Validate that we have either Expo token or Web Push subscription
        if not subscription.expo_push_token and not subscription.endpoint:
            raise HTTPException(
                status_code=400,
                detail="Either expo_push_token or endpoint (with keys) must be provided",
            )

        repository = PushSubscriptionRepository(db)

        # Check if subscription already exists
        existing_subscription = None
        if subscription.expo_push_token:
            existing_subscription = await repository.get_subscription_by_token(
                subscription.expo_push_token
            )
        elif subscription.endpoint:
            existing_subscription = await repository.get_subscription_by_endpoint(
                subscription.endpoint
            )

        if existing_subscription:
            # Update existing subscription
            if existing_subscription.user_id != user_id:
                raise HTTPException(
                    status_code=403, detail="This subscription belongs to another user"
                )

            # Reactivate and update
            updated = await repository.update_subscription(
                existing_subscription.id,
                is_active=True,
                platform=subscription.platform or existing_subscription.platform,
                device_id=subscription.device_id or existing_subscription.device_id,
                app_version=subscription.app_version
                or existing_subscription.app_version,
                error_count=0,  # Reset error count
                last_error=None,  # Clear last error
            )
            logger.info(
                f"Updated push subscription for user {user_id}",
                extra={"user_id": user_id, "subscription_id": updated.id},
            )
            return {
                "success": True,
                "message": "Push notifications subscription updated",
                "subscription_id": updated.id,
            }
        else:
            # Create new subscription
            new_subscription = await repository.create_subscription(
                user_id=user_id,
                expo_push_token=subscription.expo_push_token,
                endpoint=subscription.endpoint,
                p256dh_key=(
                    subscription.keys.get("p256dh") if subscription.keys else None
                ),
                auth_key=subscription.keys.get("auth") if subscription.keys else None,
                platform=subscription.platform or "unknown",
                device_id=subscription.device_id,
                app_version=subscription.app_version,
            )
            logger.info(
                f"Created push subscription for user {user_id}",
                extra={"user_id": user_id, "subscription_id": new_subscription.id},
            )
            return {
                "success": True,
                "message": "Push notifications subscribed successfully",
                "subscription_id": new_subscription.id,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error subscribing to push notifications: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to subscribe to push notifications"
        )


@router.post("/unsubscribe")
async def unsubscribe_push_notifications(
    subscription: Dict[str, Any],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Dict[str, Any]:
    """
    Unsubscribe user from push notifications.

    Removes or deactivates push subscription for the authenticated user.
    """
    try:
        user_id = _get_user_id(current_user)

        endpoint = subscription.get("endpoint")
        expo_push_token = subscription.get("expo_push_token")

        if not endpoint and not expo_push_token:
            raise HTTPException(
                status_code=400,
                detail="Either endpoint or expo_push_token must be provided",
            )

        repository = PushSubscriptionRepository(db)

        # Find subscription
        existing_subscription = None
        if expo_push_token:
            existing_subscription = await repository.get_subscription_by_token(
                expo_push_token
            )
        elif endpoint:
            existing_subscription = await repository.get_subscription_by_endpoint(
                endpoint
            )

        if not existing_subscription:
            logger.warning(
                f"Subscription not found for user {user_id}",
                extra={
                    "user_id": user_id,
                    "endpoint": endpoint,
                    "expo_token": expo_push_token,
                },
            )
            return {
                "success": True,
                "message": "Subscription not found (may already be removed)",
            }

        # Verify ownership
        if existing_subscription.user_id != user_id:
            raise HTTPException(
                status_code=403, detail="This subscription belongs to another user"
            )

        # Deactivate subscription (soft delete)
        await repository.deactivate_subscription(existing_subscription.id)

        logger.info(
            f"Deactivated push subscription for user {user_id}",
            extra={"user_id": user_id, "subscription_id": existing_subscription.id},
        )

        return {
            "success": True,
            "message": "Push notifications unsubscribed successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsubscribing from push notifications: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to unsubscribe from push notifications"
        )


@router.get("/subscriptions")
@cached(ttl=120, prefix="push_subscriptions")  # 120s TTL for push subscriptions list
async def get_user_subscriptions(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> Dict[str, Any]:
    """
    Get all push notification subscriptions for the current user with pagination.
    """
    try:
        user_id = _get_user_id(current_user)

        repository = PushSubscriptionRepository(db)
        subscriptions = await repository.get_user_subscriptions(
            user_id, active_only=False
        )

        # Apply pagination
        total = len(subscriptions)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_subscriptions = subscriptions[start_idx:end_idx]

        return {
            "success": True,
            "subscriptions": [
                {
                    "id": sub.id,
                    "platform": sub.platform,
                    "device_id": sub.device_id,
                    "app_version": sub.app_version,
                    "is_active": sub.is_active,
                    "push_notifications_enabled": sub.push_notifications_enabled,
                    "trade_notifications_enabled": sub.trade_notifications_enabled,
                    "bot_notifications_enabled": sub.bot_notifications_enabled,
                    "risk_notifications_enabled": sub.risk_notifications_enabled,
                    "price_alerts_enabled": sub.price_alerts_enabled,
                    "created_at": (
                        sub.created_at.isoformat() if sub.created_at else None
                    ),
                    "last_notification_sent_at": (
                        sub.last_notification_sent_at.isoformat()
                        if sub.last_notification_sent_at
                        else None
                    ),
                }
                for sub in subscriptions
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user subscriptions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get subscriptions")
