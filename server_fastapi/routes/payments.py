"""
Payments Routes - Stripe payment processing and subscriptions
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from ..services.payments.stripe_service import stripe_service, SubscriptionTier
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payments", tags=["Payments"])


# Request/Response models
class CreateSubscriptionRequest(BaseModel):
    """Create subscription request"""
    tier: str
    payment_method_id: Optional[str] = None
    email: EmailStr


class UpdateSubscriptionRequest(BaseModel):
    """Update subscription request"""
    new_tier: str


class PaymentIntentRequest(BaseModel):
    """Payment intent request"""
    amount: int
    currency: str = "usd"
    metadata: Optional[Dict[str, Any]] = None


@router.post("/customers", response_model=Dict)
async def create_customer(
    email: EmailStr,
    name: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Create a Stripe customer"""
    try:
        customer = stripe_service.create_customer(
            email=email,
            name=name,
            metadata={'user_id': str(current_user['id'])}
        )
        
        if not customer:
            raise HTTPException(status_code=500, detail="Failed to create customer")
        
        return customer
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(status_code=500, detail="Failed to create customer")


@router.post("/subscriptions", response_model=Dict)
async def create_subscription(
    request: CreateSubscriptionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a subscription"""
    try:
        # Create customer if doesn't exist
        customer = stripe_service.create_customer(
            email=request.email,
            metadata={'user_id': str(current_user['id'])}
        )
        
        if not customer:
            raise HTTPException(status_code=500, detail="Failed to create customer")
        
        # Create subscription
        subscription = stripe_service.create_subscription(
            customer_id=customer['id'],
            tier=request.tier,
            payment_method_id=request.payment_method_id
        )
        
        if not subscription:
            raise HTTPException(status_code=500, detail="Failed to create subscription")
        
        return subscription
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to create subscription")


@router.get("/subscriptions/{subscription_id}", response_model=Dict)
async def get_subscription(
    subscription_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get subscription details"""
    try:
        subscription = stripe_service.get_subscription(subscription_id)
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        return subscription
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to get subscription")


@router.patch("/subscriptions/{subscription_id}", response_model=Dict)
async def update_subscription(
    subscription_id: str,
    request: UpdateSubscriptionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update subscription tier"""
    try:
        subscription = stripe_service.update_subscription(
            subscription_id=subscription_id,
            new_tier=request.new_tier
        )
        
        if not subscription:
            raise HTTPException(status_code=500, detail="Failed to update subscription")
        
        return subscription
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to update subscription")


@router.delete("/subscriptions/{subscription_id}", response_model=Dict)
async def cancel_subscription(
    subscription_id: str,
    cancel_immediately: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Cancel a subscription"""
    try:
        subscription = stripe_service.cancel_subscription(
            subscription_id=subscription_id,
            cancel_at_period_end=not cancel_immediately
        )
        
        if not subscription:
            raise HTTPException(status_code=500, detail="Failed to cancel subscription")
        
        return subscription
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error canceling subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")


@router.post("/payment-intents", response_model=Dict)
async def create_payment_intent(
    request: PaymentIntentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a payment intent for one-time payments"""
    try:
        intent = stripe_service.create_payment_intent(
            amount=request.amount,
            currency=request.currency,
            metadata={**(request.metadata or {}), 'user_id': str(current_user['id'])}
        )
        
        if not intent:
            raise HTTPException(status_code=500, detail="Failed to create payment intent")
        
        return intent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating payment intent: {e}")
        raise HTTPException(status_code=500, detail="Failed to create payment intent")


@router.post("/webhooks")
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature")
):
    """Handle Stripe webhook events"""
    try:
        payload = await request.body()
        
        if not stripe_signature:
            raise HTTPException(status_code=400, detail="Missing Stripe signature")
        
        event = stripe_service.handle_webhook(payload, stripe_signature)
        
        if not event:
            raise HTTPException(status_code=400, detail="Invalid webhook")
        
        # Process webhook event
        event_type = event.get('event')
        event_data = event.get('data', {})
        
        # In production, handle events (update database, send notifications, etc.)
        logger.info(f"Processed Stripe webhook: {event_type}")
        
        return {'received': True, 'event': event_type}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to handle webhook")


@router.get("/pricing", response_model=Dict)
async def get_pricing():
    """Get pricing information for all tiers"""
    try:
        pricing = {}
        for tier, config in stripe_service.PRICE_CONFIGS.items():
            pricing[tier] = {
                'tier': config.tier,
                'amount': config.amount,
                'amount_display': f"${config.amount / 100:.2f}",
                'currency': config.currency,
                'interval': config.interval,
                'features': config.features
            }
        return {'pricing': pricing}
    except Exception as e:
        logger.error(f"Error getting pricing: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pricing")
