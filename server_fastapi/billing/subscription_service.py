"""
Subscription Service for SaaS
Manages user subscriptions using free subscription service (no payment processing)
"""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.subscription import Subscription
from ..models.user import User
from ..services.payments.free_subscription_service import (
    SubscriptionTier,
    free_subscription_service,
)

logger = logging.getLogger(__name__)

# Backward compatibility
SubscriptionPlan = SubscriptionTier
FRONTEND_URL = "http://localhost:5173"  # Default, can be overridden by env var


class SubscriptionService:
    """Service for managing user subscriptions"""

    def __init__(self):
        self.free_service = free_subscription_service

    async def get_user_subscription(
        self, db: AsyncSession, user_id: int
    ) -> Subscription | None:
        """Get user's subscription"""
        try:
            result = await db.execute(
                select(Subscription)
                .where(Subscription.user_id == user_id)
                .options(selectinload(Subscription.user))
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get subscription: {e}", exc_info=True)
            return None

    async def get_or_create_subscription(
        self, db: AsyncSession, user_id: int
    ) -> Subscription:
        """Get or create subscription for user"""
        subscription = await self.get_user_subscription(db, user_id)

        if not subscription:
            # Create free subscription
            subscription = Subscription(
                user_id=user_id,
                plan=SubscriptionTier.FREE.value,
                status="active",
            )
            db.add(subscription)
            await db.commit()
            await db.refresh(subscription)

        return subscription

    async def update_subscription_from_stripe(
        self,
        db: AsyncSession,
        user_id: int,
        stripe_subscription_id: str | None = None,
        stripe_customer_id: str | None = None,
    ) -> Subscription | None:
        """Update subscription (deprecated - kept for backward compatibility)"""
        # Free subscriptions don't use Stripe, so this just updates the database record
        try:
            subscription = await self.get_or_create_subscription(db, user_id)

            if stripe_customer_id:
                subscription.stripe_customer_id = stripe_customer_id
            if stripe_subscription_id:
                subscription.stripe_subscription_id = stripe_subscription_id

            subscription.status = "active"

            await db.commit()
            await db.refresh(subscription)

            logger.info(
                f"Updated subscription for user {user_id}: {subscription.plan} - {subscription.status}"
            )
            return subscription

        except Exception as e:
            logger.error(f"Failed to update subscription: {e}", exc_info=True)
            await db.rollback()
            return None

    async def cancel_subscription(
        self, db: AsyncSession, user_id: int, immediately: bool = False
    ) -> bool:
        """Cancel user subscription"""
        try:
            subscription = await self.get_user_subscription(db, user_id)
            if not subscription:
                return False

            # Cancel subscription (free - no external service needed)
            if immediately:
                subscription.status = "canceled"
            else:
                subscription.cancel_at_period_end = True

            await db.commit()

            logger.info(f"Cancelled subscription for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel subscription: {e}", exc_info=True)
            await db.rollback()
            return False

    async def check_subscription_active(self, db: AsyncSession, user_id: int) -> bool:
        """Check if user has active subscription"""
        subscription = await self.get_user_subscription(db, user_id)

        if not subscription:
            return False

        # Check status
        if subscription.status not in ["active", "trialing"]:
            return False

        # Check if period ended
        return not (subscription.current_period_end and subscription.current_period_end < datetime.now(UTC))

    async def get_subscription_limits(
        self, db: AsyncSession, user_id: int
    ) -> dict[str, Any]:
        """Get subscription limits for user"""
        subscription = await self.get_user_subscription(db, user_id)

        plan = subscription.plan if subscription else SubscriptionTier.FREE.value
        # Map plan string to tier
        tier_map = {
            "free": SubscriptionTier.FREE,
            "basic": SubscriptionTier.BASIC,
            "pro": SubscriptionTier.PRO,
            "enterprise": SubscriptionTier.ENTERPRISE,
        }
        tier = tier_map.get(plan.lower(), SubscriptionTier.FREE)
        self.free_service.get_plan_config(tier)

        return {}  # No limits for free subscriptions

    def _map_price_id_to_plan(self, price_id: str) -> str | None:
        """Map price ID to plan name (deprecated - kept for backward compatibility)"""
        # Free subscriptions don't use price IDs
        return None

    async def create_checkout_session(
        self, db: AsyncSession, user_id: int, price_id: str, plan: str
    ) -> dict[str, Any] | None:
        """Create subscription (free - no payment required)"""
        try:
            user = await db.get(User, user_id)
            if not user:
                return None

            # Map plan string to tier
            tier_map = {
                "free": SubscriptionTier.FREE,
                "basic": SubscriptionTier.BASIC,
                "pro": SubscriptionTier.PRO,
                "enterprise": SubscriptionTier.ENTERPRISE,
            }
            tier = tier_map.get(plan.lower(), SubscriptionTier.FREE)

            # Create customer (free - just for tracking)
            customer = self.free_service.create_customer(
                email=user.email,
                name=f"{user.first_name} {user.last_name}".strip() or user.username,
                metadata={"user_id": str(user_id)},
            )

            # Create subscription immediately (free - no payment)
            subscription_data = self.free_service.create_subscription(
                customer_id=customer["id"],
                tier=tier,
                metadata={"user_id": str(user_id), "plan": plan},
            )

            # Save to database
            subscription = await self.get_user_subscription(db, user_id)
            if not subscription:
                subscription = Subscription(
                    user_id=user_id,
                    plan=plan,
                    status="active",
                )
                db.add(subscription)
            else:
                subscription.plan = plan
                subscription.status = "active"

            await db.commit()
            await db.refresh(subscription)

            # Return session data (no Stripe redirect needed)
            return {
                "id": subscription_data["id"],
                "url": f"{FRONTEND_URL}/billing/success",
            }

        except Exception as e:
            logger.error(f"Failed to create subscription: {e}", exc_info=True)
            return None

    async def create_portal_session(
        self, db: AsyncSession, user_id: int
    ) -> dict[str, Any] | None:
        """Get billing portal URL (redirects to billing page)"""
        try:
            subscription = await self.get_user_subscription(db, user_id)
            if not subscription:
                return None

            # Return billing page URL (no external portal needed)
            return {
                "url": f"{FRONTEND_URL}/billing",
            }

        except Exception as e:
            logger.error(f"Failed to create portal session: {e}", exc_info=True)
            return None
