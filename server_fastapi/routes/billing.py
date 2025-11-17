"""
SaaS Billing Routes
Stripe subscription billing endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from ..database import get_db_session
from ..dependencies.auth import get_current_user
from ..billing import StripeService, SubscriptionService
from ..models.user import User

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
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False
    limits: dict = {}


@router.get("/plans")
async def get_plans():
    """Get available subscription plans"""
    try:
        plans = StripeService.list_plans()
        return {"plans": plans}
    except Exception as e:
        logger.error(f"Failed to get plans: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get plans"
        )


@router.get("/subscription")
async def get_subscription(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get current user's subscription"""
    try:
        subscription_service = SubscriptionService()
        subscription = await subscription_service.get_user_subscription(
            db=db,
            user_id=current_user["id"]
        )
        
        if not subscription:
            # Return free plan
            config = StripeService.get_plan_config("free")
            return SubscriptionResponse(
                plan="free",
                status="active",
                limits=config.get("limits", {}) if config else {},
            )
        
        limits = await subscription_service.get_subscription_limits(db, current_user["id"])
        
        return SubscriptionResponse(
            plan=subscription.plan,
            status=subscription.status,
            current_period_start=subscription.current_period_start.isoformat() if subscription.current_period_start else None,
            current_period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            cancel_at_period_end=subscription.cancel_at_period_end,
            limits=limits,
        )
        
    except Exception as e:
        logger.error(f"Failed to get subscription: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get subscription"
        )


@router.post("/checkout")
async def create_checkout(
    request: CreateCheckoutRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Create Stripe checkout session"""
    try:
        subscription_service = SubscriptionService()
        
        session = await subscription_service.create_checkout_session(
            db=db,
            user_id=current_user["id"],
            price_id=request.price_id,
            plan=request.plan,
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create checkout session"
            )
        
        return {
            "checkout_url": session["url"],
            "session_id": session["id"],
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create checkout: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


@router.post("/portal")
async def create_portal(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Create Stripe Customer Portal session"""
    try:
        subscription_service = SubscriptionService()
        
        session = await subscription_service.create_portal_session(
            db=db,
            user_id=current_user["id"],
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active subscription found"
            )
        
        return {
            "portal_url": session["url"],
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create portal session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create portal session"
        )


@router.post("/cancel")
async def cancel_subscription(
    immediately: bool = False,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Cancel user subscription"""
    try:
        subscription_service = SubscriptionService()
        
        success = await subscription_service.cancel_subscription(
            db=db,
            user_id=current_user["id"],
            immediately=immediately,
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to cancel subscription"
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
            detail="Failed to cancel subscription"
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    """Handle Stripe webhook events"""
    try:
        stripe_service = StripeService()
        subscription_service = SubscriptionService()
        
        payload = await request.body()
        signature = request.headers.get("stripe-signature", "")
        
        event = stripe_service.handle_webhook(payload, signature)
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook signature"
            )
        
        event_type = event["type"]
        event_data = event["data"]
        
        # Handle different event types
        if event_type == "customer.subscription.created":
            await _handle_subscription_created(db, event_data, subscription_service)
        elif event_type == "customer.subscription.updated":
            await _handle_subscription_updated(db, event_data, subscription_service)
        elif event_type == "customer.subscription.deleted":
            await _handle_subscription_deleted(db, event_data, subscription_service)
        elif event_type == "invoice.payment_succeeded":
            await _handle_payment_succeeded(db, event_data, subscription_service)
        elif event_type == "invoice.payment_failed":
            await _handle_payment_failed(db, event_data, subscription_service)
        
        return {"received": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook handling failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


async def _handle_subscription_created(
    db: AsyncSession,
    event_data: dict,
    subscription_service: SubscriptionService
):
    """Handle subscription.created event"""
    subscription = event_data
    customer_id = subscription["customer"]
    
    # Find user by customer_id
    from ..models.subscription import Subscription as SubscriptionModel
    result = await db.execute(
        select(SubscriptionModel).where(SubscriptionModel.stripe_customer_id == customer_id)
    )
    db_subscription = result.scalar_one_or_none()
    
    if db_subscription:
        await subscription_service.update_subscription_from_stripe(
            db=db,
            user_id=db_subscription.user_id,
            stripe_subscription_id=subscription["id"],
            stripe_customer_id=customer_id,
        )


async def _handle_subscription_updated(
    db: AsyncSession,
    event_data: dict,
    subscription_service: SubscriptionService
):
    """Handle subscription.updated event"""
    await _handle_subscription_created(db, event_data, subscription_service)


async def _handle_subscription_deleted(
    db: AsyncSession,
    event_data: dict,
    subscription_service: SubscriptionService
):
    """Handle subscription.deleted event"""
    subscription = event_data
    customer_id = subscription["customer"]
    
    from ..models.subscription import Subscription as SubscriptionModel
    result = await db.execute(
        select(SubscriptionModel).where(SubscriptionModel.stripe_customer_id == customer_id)
    )
    db_subscription = result.scalar_one_or_none()
    
    if db_subscription:
        db_subscription.status = "canceled"
        db_subscription.stripe_subscription_id = None
        await db.commit()


async def _handle_payment_succeeded(
    db: AsyncSession,
    event_data: dict,
    subscription_service: SubscriptionService
):
    """Handle payment.succeeded event"""
    invoice = event_data
    customer_id = invoice.get("customer")
    
    if customer_id:
        from ..models.subscription import Subscription as SubscriptionModel
        result = await db.execute(
            select(SubscriptionModel).where(SubscriptionModel.stripe_customer_id == customer_id)
        )
        db_subscription = result.scalar_one_or_none()
        
        if db_subscription and db_subscription.stripe_subscription_id:
            await subscription_service.update_subscription_from_stripe(
                db=db,
                user_id=db_subscription.user_id,
                stripe_subscription_id=db_subscription.stripe_subscription_id,
                stripe_customer_id=customer_id,
            )


async def _handle_payment_failed(
    db: AsyncSession,
    event_data: dict,
    subscription_service: SubscriptionService
):
    """Handle payment.failed event"""
    invoice = event_data
    customer_id = invoice.get("customer")
    
    if customer_id:
        from ..models.subscription import Subscription as SubscriptionModel
        result = await db.execute(
            select(SubscriptionModel).where(SubscriptionModel.stripe_customer_id == customer_id)
        )
        db_subscription = result.scalar_one_or_none()
        
        if db_subscription:
            db_subscription.status = "past_due"
            await db.commit()

