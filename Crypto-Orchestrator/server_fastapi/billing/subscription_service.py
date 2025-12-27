"""
Subscription Service for SaaS
Manages user subscriptions and integrates with Stripe
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..models.user import User
from ..models.subscription import Subscription
from .stripe_service import StripeService, SubscriptionPlan, FRONTEND_URL

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for managing user subscriptions"""

    def __init__(self):
        self.stripe_service = StripeService()

    async def get_user_subscription(
        self, db: AsyncSession, user_id: int
    ) -> Optional[Subscription]:
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
                plan=SubscriptionPlan.FREE.value,
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
        stripe_subscription_id: str,
        stripe_customer_id: str,
    ) -> Optional[Subscription]:
        """Update subscription from Stripe webhook"""
        try:
            subscription = await self.get_or_create_subscription(db, user_id)

            # Get Stripe subscription data
            stripe_sub = self.stripe_service.get_subscription(stripe_subscription_id)
            if not stripe_sub:
                logger.warning(
                    f"Stripe subscription not found: {stripe_subscription_id}"
                )
                return None

            # Update subscription
            subscription.stripe_subscription_id = stripe_subscription_id
            subscription.stripe_customer_id = stripe_customer_id
            subscription.status = stripe_sub["status"]
            subscription.current_period_start = stripe_sub["current_period_start"]
            subscription.current_period_end = stripe_sub["current_period_end"]
            subscription.cancel_at_period_end = stripe_sub["cancel_at_period_end"]

            # Extract plan from price_id
            if stripe_sub["items"]:
                price_id = stripe_sub["items"][0]["price_id"]
                # Map price_id to plan
                plan = self._map_price_id_to_plan(price_id)
                if plan:
                    subscription.plan = plan

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

            # Cancel in Stripe if subscription exists
            if subscription.stripe_subscription_id:
                self.stripe_service.cancel_subscription(
                    subscription.stripe_subscription_id, immediately=immediately
                )

            # Update status
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
        if (
            subscription.current_period_end
            and subscription.current_period_end < datetime.now(timezone.utc)
        ):
            return False

        return True

    async def get_subscription_limits(
        self, db: AsyncSession, user_id: int
    ) -> Dict[str, Any]:
        """Get subscription limits for user"""
        subscription = await self.get_user_subscription(db, user_id)

        plan = subscription.plan if subscription else SubscriptionPlan.FREE.value
        config = StripeService.get_plan_config(plan) or StripeService.get_plan_config(
            SubscriptionPlan.FREE.value
        )

        return config.get("limits", {}) if config else {}

    def _map_price_id_to_plan(self, price_id: str) -> Optional[str]:
        """Map Stripe price ID to plan name"""
        for plan, config in StripeService.list_plans():
            if config.get("stripe_price_id_monthly") == price_id:
                return plan
            if config.get("stripe_price_id_yearly") == price_id:
                return plan
        return None

    async def create_checkout_session(
        self, db: AsyncSession, user_id: int, price_id: str, plan: str
    ) -> Optional[Dict[str, Any]]:
        """Create Stripe checkout session for subscription"""
        try:
            user = await db.get(User, user_id)
            if not user:
                return None

            # Get or create Stripe customer
            customer_id = None
            subscription = await self.get_user_subscription(db, user_id)
            if subscription and subscription.stripe_customer_id:
                customer_id = subscription.stripe_customer_id
            else:
                # Create new customer
                customer = self.stripe_service.create_customer(
                    email=user.email,
                    name=f"{user.first_name} {user.last_name}".strip() or user.username,
                    metadata={"user_id": str(user_id)},
                )
                if customer:
                    customer_id = customer["id"]
                    if subscription:
                        subscription.stripe_customer_id = customer_id
                        await db.commit()

            if not customer_id:
                return None

            # Create checkout session
            success_url = (
                f"{FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
            )
            cancel_url = f"{FRONTEND_URL}/billing/cancel"

            session = self.stripe_service.create_checkout_session(
                customer_id=customer_id,
                price_id=price_id,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"user_id": str(user_id), "plan": plan},
            )

            return session

        except Exception as e:
            logger.error(f"Failed to create checkout session: {e}", exc_info=True)
            return None

    async def create_portal_session(
        self, db: AsyncSession, user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Create Stripe Customer Portal session"""
        try:
            subscription = await self.get_user_subscription(db, user_id)
            if not subscription or not subscription.stripe_customer_id:
                return None

            return_url = f"{FRONTEND_URL}/account/settings"

            session = self.stripe_service.create_portal_session(
                customer_id=subscription.stripe_customer_id,
                return_url=return_url,
            )

            return session

        except Exception as e:
            logger.error(f"Failed to create portal session: {e}", exc_info=True)
            return None
