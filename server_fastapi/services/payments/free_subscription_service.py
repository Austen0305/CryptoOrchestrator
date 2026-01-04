"""
Free Subscription Service - Replaces Stripe
Simple in-app subscription management without external payment processing
All subscriptions are free - no payment processing required
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, EmailStr
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SubscriptionTier(str, Enum):
    """Subscription tiers - all free"""

    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class PriceConfig(BaseModel):
    """Price configuration for subscription tiers"""

    tier: str
    amount: int  # Always 0 (free)
    currency: str = "usd"
    interval: str = "month"
    features: List[str] = []


class FreeSubscriptionService:
    """Free subscription service - no payment processing required"""

    # All tiers are free
    PRICE_CONFIGS = {
        SubscriptionTier.FREE: PriceConfig(
            tier="free",
            amount=0,
            currency="usd",
            interval="month",
            features=["Basic trading", "Paper trading", "5 bots max"],
        ),
        SubscriptionTier.BASIC: PriceConfig(
            tier="basic",
            amount=0,
            currency="usd",
            interval="month",
            features=[
                "All Free features",
                "Live trading",
                "20 bots max",
                "Priority support",
            ],
        ),
        SubscriptionTier.PRO: PriceConfig(
            tier="pro",
            amount=0,
            currency="usd",
            interval="month",
            features=[
                "All Basic features",
                "Unlimited bots",
                "Advanced ML models",
                "API access",
            ],
        ),
        SubscriptionTier.ENTERPRISE: PriceConfig(
            tier="enterprise",
            amount=0,
            currency="usd",
            interval="month",
            features=[
                "All Pro features",
                "Dedicated support",
                "Custom integrations",
                "SLA",
            ],
        ),
    }

    def __init__(self):
        logger.info("FreeSubscriptionService initialized - all subscriptions are free")

    def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a customer (free - no external service needed)
        Just returns a customer ID for database tracking
        """
        # Generate a simple customer ID (in production, use database)
        customer_id = f"cust_{email.replace('@', '_').replace('.', '_')}"
        
        return {
            "id": customer_id,
            "email": email,
            "name": name,
            "created": int(datetime.now().timestamp()),
            "metadata": metadata or {},
        }

    def create_subscription(
        self,
        customer_id: str,
        tier: SubscriptionTier = SubscriptionTier.FREE,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a subscription (free - no payment required)
        """
        config = self.PRICE_CONFIGS.get(tier, self.PRICE_CONFIGS[SubscriptionTier.FREE])
        
        subscription_id = f"sub_{customer_id}_{int(datetime.now().timestamp())}"
        now = int(datetime.now().timestamp())
        
        return {
            "id": subscription_id,
            "customer_id": customer_id,
            "status": "active",  # All subscriptions are active (free)
            "tier": tier.value,
            "current_period_start": now,
            "current_period_end": now + (30 * 24 * 60 * 60),  # 30 days
            "cancel_at_period_end": False,
            "metadata": metadata or {},
            "features": config.features,
        }

    def cancel_subscription(
        self, subscription_id: str, immediately: bool = False
    ) -> Dict[str, Any]:
        """
        Cancel a subscription
        """
        return {
            "id": subscription_id,
            "status": "canceled" if immediately else "active",
            "canceled_at": int(datetime.now().timestamp()) if immediately else None,
            "cancel_at_period_end": not immediately,
        }

    def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """
        Get subscription details
        In production, fetch from database
        """
        # This would query the database in production
        # For now, return None (caller should handle)
        return None

    def update_subscription(
        self,
        subscription_id: str,
        tier: Optional[SubscriptionTier] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Update subscription tier
        """
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")

        if tier:
            config = self.PRICE_CONFIGS.get(tier, self.PRICE_CONFIGS[SubscriptionTier.FREE])
            subscription["tier"] = tier.value
            subscription["features"] = config.features

        if metadata:
            subscription["metadata"] = {**subscription.get("metadata", {}), **metadata}

        return subscription

    @staticmethod
    def get_plan_config(tier: SubscriptionTier) -> Optional[Dict[str, Any]]:
        """Get plan configuration"""
        config = FreeSubscriptionService.PRICE_CONFIGS.get(tier)
        if config:
            return {
                "tier": config.tier,
                "amount": config.amount,
                "currency": config.currency,
                "interval": config.interval,
                "features": config.features,
            }
        return None

    @staticmethod
    def list_plans() -> Dict[str, Dict[str, Any]]:
        """List all available plans"""
        return {
            tier.value: FreeSubscriptionService.get_plan_config(tier)
            for tier in SubscriptionTier
            if FreeSubscriptionService.get_plan_config(tier)
        }

    def create_checkout_session(
        self,
        customer_id: str,
        tier: SubscriptionTier,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create checkout session (free - just returns success URL)
        """
        # Since it's free, we can immediately create the subscription
        subscription = self.create_subscription(customer_id, tier, metadata)
        
        return {
            "id": f"session_{subscription['id']}",
            "url": success_url or "/billing/success",
            "subscription_id": subscription["id"],
        }

    def create_portal_session(
        self, customer_id: str, return_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create customer portal session (free - just returns URL)
        """
        return {
            "url": return_url or "/billing",
        }

    def handle_webhook(
        self, payload: bytes, signature: str
    ) -> Optional[Dict[str, Any]]:
        """
        Handle webhook events (not needed for free subscriptions)
        """
        logger.info("Webhook received but not needed for free subscriptions")
        return None

    def calculate_revenue(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """
        Calculate revenue (always 0 for free subscriptions)
        """
        return {
            "total_revenue": 0,
            "currency": "usd",
            "period_start": int(start_date.timestamp()),
            "period_end": int(end_date.timestamp()),
            "subscription_count": 0,
        }


# Singleton instance
free_subscription_service = FreeSubscriptionService()
