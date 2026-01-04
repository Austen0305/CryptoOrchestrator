"""
Payments Routes - Free subscription management (no payment processing required)
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Header
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, Annotated
from datetime import datetime
import logging

from ..services.payments.free_subscription_service import (
    free_subscription_service,
    SubscriptionTier,
)
from ..dependencies.auth import get_current_user
from ..utils.route_helpers import _get_user_id

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
    payment_method_type: str = "card"  # 'card', 'ach', 'bank_transfer'
    metadata: Optional[Dict[str, Any]] = None


@router.post("/customers", response_model=Dict)
async def create_customer(
    email: EmailStr,
    current_user: Annotated[dict, Depends(get_current_user)],
    name: Optional[str] = None,
):
    """Create a customer (free - no external service needed)"""
    try:
        user_id = _get_user_id(current_user)
        customer = free_subscription_service.create_customer(
            email=email, name=name, metadata={"user_id": str(user_id)}
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
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Create a subscription (free - no payment required)"""
    try:
        user_id = _get_user_id(current_user)
        # Create customer if doesn't exist
        customer = free_subscription_service.create_customer(
            email=request.email, metadata={"user_id": str(user_id)}
        )

        if not customer:
            raise HTTPException(status_code=500, detail="Failed to create customer")

        # Map tier string to SubscriptionTier
        tier_map = {
            "free": SubscriptionTier.FREE,
            "basic": SubscriptionTier.BASIC,
            "pro": SubscriptionTier.PRO,
            "enterprise": SubscriptionTier.ENTERPRISE,
        }
        tier = tier_map.get(request.tier.lower(), SubscriptionTier.FREE)

        # Create subscription (free - no payment method needed)
        subscription = free_subscription_service.create_subscription(
            customer_id=customer["id"],
            tier=tier,
            metadata={"user_id": str(user_id)},
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
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get subscription details"""
    try:
        subscription = free_subscription_service.get_subscription(subscription_id)

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
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Update subscription tier"""
    try:
        # Map tier string to SubscriptionTier
        tier_map = {
            "free": SubscriptionTier.FREE,
            "basic": SubscriptionTier.BASIC,
            "pro": SubscriptionTier.PRO,
            "enterprise": SubscriptionTier.ENTERPRISE,
        }
        tier = tier_map.get(request.new_tier.lower(), SubscriptionTier.FREE)
        
        subscription = free_subscription_service.update_subscription(
            subscription_id=subscription_id, tier=tier
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
    current_user: Annotated[dict, Depends(get_current_user)],
    cancel_immediately: bool = False,
):
    """Cancel a subscription"""
    try:
        subscription = free_subscription_service.cancel_subscription(
            subscription_id=subscription_id, immediately=cancel_immediately
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
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Create a payment intent (deprecated - all subscriptions are free)"""
    # Free subscriptions don't need payment intents
    raise HTTPException(
        status_code=400,
        detail="Payment intents not needed - all subscriptions are free"
    )


@router.post("/webhooks")
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
):
    """Handle Stripe webhook events"""
    try:
        payload = await request.body()

        if not stripe_signature:
            raise HTTPException(status_code=400, detail="Missing Stripe signature")

        # Note: Webhook handling for wallet deposits may still be needed
        # For free subscriptions, webhooks aren't needed, but we keep this for wallet deposits
        # If you need wallet deposits, you'll need to implement a different payment processor
        
        # Try to parse webhook data if it exists (for wallet deposits)
        try:
            import json
            event_data_raw = json.loads(payload.decode()) if payload else {}
            event_type = event_data_raw.get("type") or event_data_raw.get("event")
            event_data = event_data_raw.get("data", {})
        except:
            event_type = None
            event_data = {}

        # Handle payment events for wallet deposits
        if (
            event_type == "payment_intent.succeeded"
            or event_type == "payment.succeeded"
        ):
            payment_intent_id = event_data.get("id") or event_data.get("payment_intent")
            if payment_intent_id:
                try:
                    from ..services.deposit_safety import deposit_safety_service
                    from sqlalchemy import select
                    from ..models.wallet import WalletTransaction
                    from ..database import get_db_context
                    from decimal import Decimal

                    async with get_db_context() as db:
                        # Find transaction by payment intent ID
                        stmt = select(WalletTransaction).where(
                            WalletTransaction.payment_intent_id == payment_intent_id
                        )
                        result = await db.execute(stmt)
                        transaction = result.scalar_one_or_none()

                        if transaction:
                            # Use safe deposit processing to ensure no money is lost
                            # This verifies payment, prevents duplicates, and ensures atomic operations
                            amount_decimal = Decimal(str(transaction.amount))

                            success, processed_txn_id, error_msg = (
                                await deposit_safety_service.process_deposit_safely(
                                    user_id=transaction.user_id,
                                    amount=amount_decimal,
                                    currency=transaction.currency,
                                    payment_intent_id=payment_intent_id,
                                    db=db,
                                )
                            )

                            if success:
                                logger.info(
                                    f"[OK] Deposit confirmed safely via webhook: payment_intent {payment_intent_id}, "
                                    f"transaction {processed_txn_id}"
                                )
                            else:
                                logger.error(
                                    f"[ERROR] Failed to confirm deposit safely: payment_intent {payment_intent_id}, "
                                    f"error: {error_msg}"
                                )
                        else:
                            logger.warning(
                                f"No transaction found for payment_intent {payment_intent_id}. "
                                f"This may be a new deposit that needs to be created first."
                            )
                except Exception as e:
                    logger.error(
                        f"Error processing payment webhook: {e}", exc_info=True
                    )

        if event_type:
            logger.info(f"Processed webhook: {event_type}")

        return {"received": True, "event": event_type or "free_subscription"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to handle webhook")


@router.get("/pricing", response_model=Dict)
async def get_pricing():
    """Get pricing information for all tiers (all free)"""
    try:
        pricing = {}
        for tier, config in free_subscription_service.PRICE_CONFIGS.items():
            pricing[tier.value] = {
                "tier": config.tier,
                "amount": config.amount,  # Always 0
                "amount_display": "Free",
                "currency": config.currency,
                "interval": config.interval,
                "features": config.features,
            }
        return {"pricing": pricing}
    except Exception as e:
        logger.error(f"Error getting pricing: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pricing")
