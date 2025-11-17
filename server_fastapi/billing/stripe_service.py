"""
Stripe Service for SaaS Subscription Billing
Complete Stripe integration for subscription management
"""
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    stripe = None
    logger.warning("Stripe not installed. Payment processing will be disabled.")

# Stripe configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Initialize Stripe
if STRIPE_AVAILABLE and STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


class SubscriptionPlan(str, Enum):
    """Subscription plan tiers"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# Plan configurations
PLAN_CONFIGS = {
    SubscriptionPlan.FREE: {
        "name": "Free",
        "price_monthly": 0,
        "price_yearly": 0,
        "stripe_price_id_monthly": None,
        "stripe_price_id_yearly": None,
        "features": [
            "5 bots max",
            "Paper trading only",
            "Basic strategies",
            "Community support",
        ],
        "limits": {
            "max_bots": 5,
            "max_strategies": 10,
            "max_backtests_per_month": 20,
        },
    },
    SubscriptionPlan.BASIC: {
        "name": "Basic",
        "price_monthly": 29,  # $29/month
        "price_yearly": 290,  # $290/year (2 months free)
        "stripe_price_id_monthly": os.getenv("STRIPE_PRICE_BASIC_MONTHLY", ""),
        "stripe_price_id_yearly": os.getenv("STRIPE_PRICE_BASIC_YEARLY", ""),
        "features": [
            "20 bots max",
            "Live trading",
            "All strategies",
            "Email support",
            "Basic ML models",
        ],
        "limits": {
            "max_bots": 20,
            "max_strategies": 50,
            "max_backtests_per_month": 100,
        },
    },
    SubscriptionPlan.PRO: {
        "name": "Pro",
        "price_monthly": 99,  # $99/month
        "price_yearly": 990,  # $990/year (2 months free)
        "stripe_price_id_monthly": os.getenv("STRIPE_PRICE_PRO_MONTHLY", ""),
        "stripe_price_id_yearly": os.getenv("STRIPE_PRICE_PRO_YEARLY", ""),
        "features": [
            "Unlimited bots",
            "Live trading",
            "All strategies",
            "Advanced ML models",
            "Priority support",
            "API access",
            "Custom integrations",
        ],
        "limits": {
            "max_bots": -1,  # Unlimited
            "max_strategies": -1,
            "max_backtests_per_month": -1,
        },
    },
    SubscriptionPlan.ENTERPRISE: {
        "name": "Enterprise",
        "price_monthly": 299,  # $299/month
        "price_yearly": 2990,  # $2990/year
        "stripe_price_id_monthly": os.getenv("STRIPE_PRICE_ENTERPRISE_MONTHLY", ""),
        "stripe_price_id_yearly": os.getenv("STRIPE_PRICE_ENTERPRISE_YEARLY", ""),
        "features": [
            "Unlimited everything",
            "Dedicated support",
            "Custom integrations",
            "SLA guarantee",
            "On-premise deployment",
        ],
        "limits": {
            "max_bots": -1,
            "max_strategies": -1,
            "max_backtests_per_month": -1,
        },
    },
}


class StripeService:
    """Service for Stripe payment processing"""
    
    def __init__(self):
        if not STRIPE_AVAILABLE:
            logger.warning("Stripe SDK not available")
        self.secret_key = STRIPE_SECRET_KEY
        self.publishable_key = STRIPE_PUBLISHABLE_KEY
        self.webhook_secret = STRIPE_WEBHOOK_SECRET
    
    def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Create Stripe customer"""
        if not STRIPE_AVAILABLE or not self.secret_key:
            logger.warning("Stripe not available")
            return None
        
        try:
            customer_data = {
                "email": email,
                "metadata": metadata or {},
            }
            if name:
                customer_data["name"] = name
            
            customer = stripe.Customer.create(**customer_data)
            logger.info(f"Created Stripe customer: {customer.id} for {email}")
            return {
                "id": customer.id,
                "email": customer.email,
                "name": customer.name,
            }
        except Exception as e:
            logger.error(f"Failed to create Stripe customer: {e}", exc_info=True)
            return None
    
    def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Create Stripe Checkout session"""
        if not STRIPE_AVAILABLE or not self.secret_key:
            logger.warning("Stripe not available")
            return None
        
        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[{
                    "price": price_id,
                    "quantity": 1,
                }],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata or {},
                allow_promotion_codes=True,
            )
            logger.info(f"Created checkout session: {session.id}")
            return {
                "id": session.id,
                "url": session.url,
            }
        except Exception as e:
            logger.error(f"Failed to create checkout session: {e}", exc_info=True)
            return None
    
    def create_portal_session(
        self,
        customer_id: str,
        return_url: str
    ) -> Optional[Dict[str, Any]]:
        """Create Stripe Customer Portal session"""
        if not STRIPE_AVAILABLE or not self.secret_key:
            logger.warning("Stripe not available")
            return None
        
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            logger.info(f"Created portal session: {session.id}")
            return {
                "url": session.url,
            }
        except Exception as e:
            logger.error(f"Failed to create portal session: {e}", exc_info=True)
            return None
    
    def get_subscription(
        self,
        subscription_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get Stripe subscription"""
        if not STRIPE_AVAILABLE or not self.secret_key:
            return None
        
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": subscription.id,
                "status": subscription.status,
                "customer": subscription.customer,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "items": [{
                    "price_id": item.price.id,
                    "plan": item.price.nickname or "",
                } for item in subscription.items.data],
            }
        except Exception as e:
            logger.error(f"Failed to get subscription: {e}", exc_info=True)
            return None
    
    def cancel_subscription(
        self,
        subscription_id: str,
        immediately: bool = False
    ) -> bool:
        """Cancel Stripe subscription"""
        if not STRIPE_AVAILABLE or not self.secret_key:
            return False
        
        try:
            if immediately:
                stripe.Subscription.delete(subscription_id)
            else:
                stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            logger.info(f"Cancelled subscription: {subscription_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel subscription: {e}", exc_info=True)
            return False
    
    def handle_webhook(
        self,
        payload: bytes,
        signature: str
    ) -> Optional[Dict[str, Any]]:
        """Handle Stripe webhook event"""
        if not STRIPE_AVAILABLE or not self.webhook_secret:
            logger.warning("Stripe webhook handling not available")
            return None
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            
            event_type = event["type"]
            event_data = event["data"]["object"]
            
            logger.info(f"Received Stripe webhook: {event_type}")
            
            return {
                "type": event_type,
                "data": event_data,
                "id": event["id"],
            }
        except ValueError as e:
            logger.error(f"Invalid payload in Stripe webhook: {e}")
            return None
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature in Stripe webhook: {e}")
            return None
        except Exception as e:
            logger.error(f"Webhook handling error: {e}", exc_info=True)
            return None
    
    @staticmethod
    def get_plan_config(plan: str) -> Optional[Dict[str, Any]]:
        """Get plan configuration"""
        return PLAN_CONFIGS.get(SubscriptionPlan(plan))
    
    @staticmethod
    def list_plans() -> List[Dict[str, Any]]:
        """List all available plans"""
        return [
            {
                "plan": plan.value,
                **config
            }
            for plan, config in PLAN_CONFIGS.items()
        ]

