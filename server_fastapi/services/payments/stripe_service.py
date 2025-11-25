"""
Stripe Service - Payment processing and subscription management
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, EmailStr
from datetime import datetime
from enum import Enum
import logging
import os

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    logging.warning("Stripe not available; payment processing will be disabled.")

logger = logging.getLogger(__name__)

# Initialize Stripe with API key from environment
if STRIPE_AVAILABLE:
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")


class SubscriptionTier(str, Enum):
    """Subscription tiers"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class PriceConfig(BaseModel):
    """Price configuration for subscription tiers"""
    tier: str
    amount: int  # Amount in cents
    currency: str = "usd"
    interval: str = "month"  # 'month' or 'year'
    stripe_price_id: Optional[str] = None
    features: List[str] = []


class SubscriptionStatus(BaseModel):
    """Subscription status"""
    user_id: str
    tier: str
    status: str  # 'active', 'canceled', 'past_due', 'trialing'
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None


class StripeService:
    """Service for Stripe payment processing"""
    
    # Price configurations for each tier
    PRICE_CONFIGS = {
        SubscriptionTier.FREE: PriceConfig(
            tier="free",
            amount=0,
            currency="usd",
            interval="month",
            features=["Basic trading", "Paper trading", "5 bots max"]
        ),
        SubscriptionTier.BASIC: PriceConfig(
            tier="basic",
            amount=4900,  # $49.00
            currency="usd",
            interval="month",
            features=["All Free features", "Live trading", "20 bots max", "Priority support"]
        ),
        SubscriptionTier.PRO: PriceConfig(
            tier="pro",
            amount=9900,  # $99.00
            currency="usd",
            interval="month",
            features=["All Basic features", "Unlimited bots", "Advanced ML models", "API access"]
        ),
        SubscriptionTier.ENTERPRISE: PriceConfig(
            tier="enterprise",
            amount=29900,  # $299.00
            currency="usd",
            interval="month",
            features=["All Pro features", "Dedicated support", "Custom integrations", "SLA"]
        )
    }
    
    def __init__(self):
        if not STRIPE_AVAILABLE:
            logger.warning("Stripe service initialized without Stripe SDK")
    
    def create_customer(self, email: str, name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Create a Stripe customer"""
        if not STRIPE_AVAILABLE:
            return None
        
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
            return {
                'id': customer.id,
                'email': customer.email,
                'created': datetime.fromtimestamp(customer.created)
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            return None
    
    def create_subscription(
        self,
        customer_id: str,
        tier: str,
        payment_method_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a Stripe subscription"""
        if not STRIPE_AVAILABLE:
            return None
        
        try:
            price_config = self.PRICE_CONFIGS.get(tier)
            if not price_config:
                raise ValueError(f"Invalid tier: {tier}")
            
            # If free tier, return mock subscription
            if tier == SubscriptionTier.FREE:
                return {
                    'id': f'sub_free_{customer_id}',
                    'status': 'active',
                    'tier': tier,
                    'customer': customer_id
                }
            
            # Create or retrieve price
            price_id = price_config.stripe_price_id
            if not price_id:
                # Create price if not exists
                price = stripe.Price.create(
                    unit_amount=price_config.amount,
                    currency=price_config.currency,
                    recurring={"interval": price_config.interval},
                    product_data={"name": f"CryptoOrchestrator {tier.capitalize()}"}
                )
                price_id = price.id
                price_config.stripe_price_id = price_id
            
            # Create subscription
            subscription_params = {
                'customer': customer_id,
                'items': [{'price': price_id}],
                'payment_behavior': 'default_incomplete',
                'expand': ['latest_invoice.payment_intent']
            }
            
            if payment_method_id:
                subscription_params['default_payment_method'] = payment_method_id
            
            subscription = stripe.Subscription.create(**subscription_params)
            
            return {
                'id': subscription.id,
                'status': subscription.status,
                'tier': tier,
                'customer': customer_id,
                'current_period_start': datetime.fromtimestamp(subscription.current_period_start),
                'current_period_end': datetime.fromtimestamp(subscription.current_period_end),
                'latest_invoice': subscription.latest_invoice.id if hasattr(subscription.latest_invoice, 'id') else None
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe subscription: {e}")
            return None
    
    def cancel_subscription(self, subscription_id: str, cancel_at_period_end: bool = True) -> Optional[Dict[str, Any]]:
        """Cancel a Stripe subscription"""
        if not STRIPE_AVAILABLE:
            return None
        
        try:
            if cancel_at_period_end:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                subscription = stripe.Subscription.delete(subscription_id)
            
            return {
                'id': subscription.id,
                'status': subscription.status,
                'cancel_at_period_end': subscription.cancel_at_period_end if hasattr(subscription, 'cancel_at_period_end') else False
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel Stripe subscription: {e}")
            return None
    
    def update_subscription(self, subscription_id: str, new_tier: str) -> Optional[Dict[str, Any]]:
        """Update subscription tier"""
        if not STRIPE_AVAILABLE:
            return None
        
        try:
            price_config = self.PRICE_CONFIGS.get(new_tier)
            if not price_config:
                raise ValueError(f"Invalid tier: {new_tier}")
            
            # Get or create price for new tier
            price_id = price_config.stripe_price_id
            if not price_id:
                price = stripe.Price.create(
                    unit_amount=price_config.amount,
                    currency=price_config.currency,
                    recurring={"interval": price_config.interval},
                    product_data={"name": f"CryptoOrchestrator {new_tier.capitalize()}"}
                )
                price_id = price.id
            
            # Update subscription
            subscription = stripe.Subscription.retrieve(subscription_id)
            subscription = stripe.Subscription.modify(
                subscription_id,
                items=[{
                    'id': subscription['items']['data'][0].id,
                    'price': price_id
                }],
                proration_behavior='always_invoice'
            )
            
            return {
                'id': subscription.id,
                'status': subscription.status,
                'tier': new_tier,
                'current_period_start': datetime.fromtimestamp(subscription.current_period_start),
                'current_period_end': datetime.fromtimestamp(subscription.current_period_end)
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update Stripe subscription: {e}")
            return None
    
    def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get subscription details"""
        if not STRIPE_AVAILABLE:
            return None
        
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                'id': subscription.id,
                'status': subscription.status,
                'customer': subscription.customer,
                'current_period_start': datetime.fromtimestamp(subscription.current_period_start),
                'current_period_end': datetime.fromtimestamp(subscription.current_period_end),
                'cancel_at_period_end': subscription.cancel_at_period_end
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get Stripe subscription: {e}")
            return None
    
    def create_payment_intent(
        self,
        amount: int,
        currency: str = "usd",
        customer_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a payment intent for one-time payments"""
        if not STRIPE_AVAILABLE:
            return None
        
        try:
            intent_params = {
                'amount': amount,
                'currency': currency,
                'payment_method_types': ['card']
            }
            
            if customer_id:
                intent_params['customer'] = customer_id
            
            if metadata:
                intent_params['metadata'] = metadata
            
            intent = stripe.PaymentIntent.create(**intent_params)
            
            return {
                'id': intent.id,
                'client_secret': intent.client_secret,
                'amount': intent.amount,
                'currency': intent.currency,
                'status': intent.status
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create payment intent: {e}")
            return None
    
    def handle_webhook(self, payload: bytes, signature: str) -> Optional[Dict[str, Any]]:
        """Handle Stripe webhook events"""
        if not STRIPE_AVAILABLE or not stripe_webhook_secret:
            logger.warning("Stripe webhook handling unavailable")
            return None
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, stripe_webhook_secret
            )
            
            event_type = event['type']
            event_data = event['data']['object']
            
            logger.info(f"Received Stripe webhook: {event_type}")
            
            # Handle different event types
            if event_type == 'customer.subscription.created':
                return {'event': 'subscription.created', 'data': event_data}
            elif event_type == 'customer.subscription.updated':
                return {'event': 'subscription.updated', 'data': event_data}
            elif event_type == 'customer.subscription.deleted':
                return {'event': 'subscription.deleted', 'data': event_data}
            elif event_type == 'invoice.payment_succeeded':
                return {'event': 'payment.succeeded', 'data': event_data}
            elif event_type == 'invoice.payment_failed':
                return {'event': 'payment.failed', 'data': event_data}
            else:
                return {'event': event_type, 'data': event_data}
        
        except ValueError as e:
            logger.error(f"Invalid payload in Stripe webhook: {e}")
            return None
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature in Stripe webhook: {e}")
            return None


# Global service instance
stripe_service = StripeService()
