"""
SaaS Billing Routes
Free subscription billing endpoints (no payment processing required)
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..billing import SubscriptionService
from ..database import get_db_session
from ..dependencies.auth import get_current_user
from ..middleware.cache_manager import cached
from ..models.user import User
from ..services.payments.free_subscription_service import (
    SubscriptionTier,
    free_subscription_service,
)
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["Billing"])


# Request Models
class CreateCheckoutRequest(BaseModel):
    price_id: str
    plan: str


# Response Models
class SubscriptionResponse(BaseModel):
    plan: str
    status: str
    current_period_start: str | None = None
    current_period_end: str | None = None
    cancel_at_period_end: bool = False
    limits: dict = {}


@router.get("/plans")
@cached(
    ttl=300, prefix="billing_plans"
)  # 5min TTL for subscription plans (static data)
async def get_plans():
    """Get available subscription plans (all free)"""
    try:
        plans = free_subscription_service.list_plans()
        # Convert to format expected by frontend
        formatted_plans = []
        for tier, config in plans.items():
            if config:
                formatted_plans.append(
                    {
                        "plan": tier,
                        "amount": config["amount"],
                        "currency": config["currency"],
                        "interval": config["interval"],
                        "features": config["features"],
                        # Remove Stripe-specific fields, add free indicator
                        "is_free": True,
                        "price_display": "Free",
                    }
                )
        return {"plans": formatted_plans}
    except Exception as e:
        logger.error(f"Failed to get plans: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get plans",
        )


@router.get("/subscription")
@cached(ttl=120, prefix="user_subscription")  # 120s TTL for user subscription
async def get_subscription(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get current user's subscription"""
    try:
        user_id = _get_user_id(current_user)
        subscription_service = SubscriptionService()
        subscription = await subscription_service.get_user_subscription(
            db=db, user_id=user_id
        )

        if not subscription:
            # Return free plan
            config = free_subscription_service.get_plan_config(SubscriptionTier.FREE)
            return SubscriptionResponse(
                plan="free",
                status="active",
                limits={},  # No limits for free plans
            )

        limits = await subscription_service.get_subscription_limits(db, user_id)

        return SubscriptionResponse(
            plan=subscription.plan,
            status=subscription.status,
            current_period_start=(
                subscription.current_period_start.isoformat()
                if subscription.current_period_start
                else None
            ),
            current_period_end=(
                subscription.current_period_end.isoformat()
                if subscription.current_period_end
                else None
            ),
            cancel_at_period_end=subscription.cancel_at_period_end,
            limits=limits,
        )

    except Exception as e:
        logger.error(f"Failed to get subscription: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get subscription",
        )


@router.post("/checkout")
async def create_checkout(
    request: CreateCheckoutRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Create subscription (free - no payment required)"""
    try:
        user_id = _get_user_id(current_user)
        subscription_service = SubscriptionService()

        # Get user to create customer
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Map plan string to SubscriptionTier
        tier_map = {
            "free": SubscriptionTier.FREE,
            "basic": SubscriptionTier.BASIC,
            "pro": SubscriptionTier.PRO,
            "enterprise": SubscriptionTier.ENTERPRISE,
        }
        tier = tier_map.get(request.plan.lower(), SubscriptionTier.FREE)

        # Create customer (free - just for tracking)
        customer = free_subscription_service.create_customer(
            email=user.email,
            name=f"{user.first_name} {user.last_name}".strip() or user.username,
            metadata={"user_id": str(user_id)},
        )

        # Create subscription immediately (free - no payment)
        subscription_data = free_subscription_service.create_subscription(
            customer_id=customer["id"],
            tier=tier,
            metadata={"user_id": str(user_id), "plan": request.plan},
        )

        # Save to database
        from ..models.subscription import Subscription as SubscriptionModel

        db_subscription = await subscription_service.get_user_subscription(db, user_id)

        if not db_subscription:
            db_subscription = SubscriptionModel(
                user_id=user_id,
                plan=request.plan,
                status="active",
            )
            db.add(db_subscription)
        else:
            db_subscription.plan = request.plan
            db_subscription.status = "active"

        await db.commit()
        await db.refresh(db_subscription)

        # Return success URL (no Stripe redirect needed)
        return {
            "checkout_url": "/billing/success",  # Frontend success page
            "session_id": subscription_data["id"],
            "subscription_id": subscription_data["id"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create subscription: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subscription",
        )


@router.post("/portal")
async def create_portal(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get billing portal URL (redirects to billing page)"""
    try:
        user_id = _get_user_id(current_user)
        subscription_service = SubscriptionService()

        subscription = await subscription_service.get_user_subscription(db, user_id)

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active subscription found",
            )

        # Return billing page URL (no external portal needed)
        return {
            "portal_url": "/billing",  # Frontend billing page
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create portal session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create portal session",
        )


@router.post("/cancel")
async def cancel_subscription(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    immediately: bool = False,
):
    """Cancel user subscription"""
    try:
        user_id = _get_user_id(current_user)
        subscription_service = SubscriptionService()

        success = await subscription_service.cancel_subscription(
            db=db,
            user_id=user_id,
            immediately=immediately,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to cancel subscription",
            )

        return {
            "success": True,
            "message": "Subscription cancelled successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription",
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Webhook endpoint (deprecated - no webhooks needed for free subscriptions)"""
    # Free subscriptions don't need webhooks - subscriptions are managed directly
    logger.info("Webhook received but not needed for free subscriptions")
    return {"received": True, "message": "Webhooks not needed for free subscriptions"}


async def _handle_subscription_created(
    db: AsyncSession, event_data: dict, subscription_service: SubscriptionService
):
    """Handle subscription.created event (deprecated - kept for backward compatibility)"""
    # Free subscriptions don't use webhooks
    logger.info(
        "Subscription created event received (not needed for free subscriptions)"
    )


async def _handle_subscription_updated(
    db: AsyncSession, event_data: dict, subscription_service: SubscriptionService
):
    """Handle subscription.updated event"""
    await _handle_subscription_created(db, event_data, subscription_service)


async def _handle_subscription_deleted(
    db: AsyncSession, event_data: dict, subscription_service: SubscriptionService
):
    """Handle subscription.deleted event (deprecated - kept for backward compatibility)"""
    logger.info(
        "Subscription deleted event received (not needed for free subscriptions)"
    )


async def _handle_payment_succeeded(
    db: AsyncSession, event_data: dict, subscription_service: SubscriptionService
):
    """Handle payment.succeeded event (deprecated - kept for backward compatibility)"""
    logger.info("Payment succeeded event received (not needed for free subscriptions)")


async def _handle_payment_failed(
    db: AsyncSession, event_data: dict, subscription_service: SubscriptionService
):
    """Handle payment.failed event (deprecated - kept for backward compatibility)"""
    logger.info("Payment failed event received (not needed for free subscriptions)")
