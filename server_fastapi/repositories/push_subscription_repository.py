"""
Push Subscription Repository
Data access layer for push notification subscriptions
"""

import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from ..models.push_subscription import PushSubscription

logger = logging.getLogger(__name__)


class PushSubscriptionRepository:
    """Repository for push subscription data access"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_subscription(
        self,
        user_id: int,
        expo_push_token: Optional[str] = None,
        endpoint: Optional[str] = None,
        p256dh_key: Optional[str] = None,
        auth_key: Optional[str] = None,
        platform: str = "unknown",
        device_id: Optional[str] = None,
        app_version: Optional[str] = None,
    ) -> PushSubscription:
        """Create a new push subscription"""
        subscription = PushSubscription(
            user_id=user_id,
            expo_push_token=expo_push_token,
            endpoint=endpoint,
            p256dh_key=p256dh_key,
            auth_key=auth_key,
            platform=platform,
            device_id=device_id,
            app_version=app_version,
            is_active=True,
        )
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)
        return subscription

    async def get_user_subscriptions(
        self, user_id: int, active_only: bool = True
    ) -> List[PushSubscription]:
        """Get all push subscriptions for a user"""
        stmt = select(PushSubscription).where(PushSubscription.user_id == user_id)

        if active_only:
            stmt = stmt.where(PushSubscription.is_active == True)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_subscription_by_token(
        self, expo_push_token: str
    ) -> Optional[PushSubscription]:
        """Get subscription by Expo push token"""
        stmt = select(PushSubscription).where(
            PushSubscription.expo_push_token == expo_push_token
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_subscription_by_endpoint(
        self, endpoint: str
    ) -> Optional[PushSubscription]:
        """Get subscription by Web Push endpoint"""
        stmt = select(PushSubscription).where(PushSubscription.endpoint == endpoint)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_subscription(
        self, subscription_id: int, **updates
    ) -> Optional[PushSubscription]:
        """Update a push subscription"""
        stmt = select(PushSubscription).where(PushSubscription.id == subscription_id)
        result = await self.db.execute(stmt)
        subscription = result.scalar_one_or_none()

        if not subscription:
            return None

        for key, value in updates.items():
            if hasattr(subscription, key):
                setattr(subscription, key, value)

        await self.db.commit()
        await self.db.refresh(subscription)
        return subscription

    async def deactivate_subscription(self, subscription_id: int) -> bool:
        """Deactivate a push subscription"""
        subscription = await self.get_subscription_by_id(subscription_id)
        if not subscription:
            return False

        subscription.is_active = False
        await self.db.commit()
        return True

    async def delete_subscription(self, subscription_id: int) -> bool:
        """Delete a push subscription"""
        stmt = select(PushSubscription).where(PushSubscription.id == subscription_id)
        result = await self.db.execute(stmt)
        subscription = result.scalar_one_or_none()

        if not subscription:
            return False

        await self.db.delete(subscription)
        await self.db.commit()
        return True

    async def get_subscription_by_id(
        self, subscription_id: int
    ) -> Optional[PushSubscription]:
        """Get subscription by ID"""
        stmt = select(PushSubscription).where(PushSubscription.id == subscription_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_subscriptions_for_notification_type(
        self,
        user_id: int,
        notification_type: str,  # 'trade', 'bot', 'risk', 'price_alert'
    ) -> List[PushSubscription]:
        """Get active subscriptions that should receive a specific notification type"""
        stmt = select(PushSubscription).where(
            and_(
                PushSubscription.user_id == user_id,
                PushSubscription.is_active == True,
                PushSubscription.push_notifications_enabled == True,
            )
        )

        # Filter by notification type preference
        if notification_type == "trade":
            stmt = stmt.where(PushSubscription.trade_notifications_enabled == True)
        elif notification_type == "bot":
            stmt = stmt.where(PushSubscription.bot_notifications_enabled == True)
        elif notification_type == "risk":
            stmt = stmt.where(PushSubscription.risk_notifications_enabled == True)
        elif notification_type == "price_alert":
            stmt = stmt.where(PushSubscription.price_alerts_enabled == True)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_last_notification_sent(
        self, subscription_id: int, error: Optional[str] = None
    ) -> None:
        """Update last notification sent timestamp and error count"""
        subscription = await self.get_subscription_by_id(subscription_id)
        if not subscription:
            return

        subscription.last_notification_sent_at = datetime.utcnow()
        if error:
            subscription.last_error = error
            subscription.error_count += 1
        else:
            subscription.last_error = None
            subscription.error_count = 0

        await self.db.commit()
