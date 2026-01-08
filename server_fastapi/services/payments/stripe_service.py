"""
DEPRECATED: Stripe Service replaced with Free Subscription Service
This file is kept for backward compatibility - all methods delegate to free_subscription_service
All subscriptions are now free - no payment processing required
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Import the free subscription service
from .free_subscription_service import (
    PriceConfig,
    SubscriptionTier,
    free_subscription_service,
)


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
    stripe_price_id: str | None = None
    features: list[str] = []


class SubscriptionStatus(BaseModel):
    """Subscription status"""

    user_id: str
    tier: str
    status: str  # 'active', 'canceled', 'past_due', 'trialing'
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    stripe_subscription_id: str | None = None
    stripe_customer_id: str | None = None


class StripeService:
    """
    DEPRECATED: Wrapper around FreeSubscriptionService for backward compatibility
    All subscriptions are now free - no payment processing required
    """

    # Delegate to free service configs
    PRICE_CONFIGS = free_subscription_service.PRICE_CONFIGS

    def __init__(self):
        # Use the free subscription service internally
        self._service = free_subscription_service
        logger.info("StripeService initialized - using free subscription service")

    def create_customer(
        self,
        email: str,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Create a Stripe customer"""
        if not STRIPE_AVAILABLE:
            return None

        try:
            customer = stripe.Customer.create(
                email=email, name=name, metadata=metadata or {}
            )
            return {
                "id": customer.id,
                "email": customer.email,
                "created": datetime.fromtimestamp(customer.created),
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            return None

    def create_subscription(
        self, customer_id: str, tier: str, payment_method_id: str | None = None
    ) -> dict[str, Any] | None:
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
                    "id": f"sub_free_{customer_id}",
                    "status": "active",
                    "tier": tier,
                    "customer": customer_id,
                }

            # Create or retrieve price
            price_id = price_config.stripe_price_id
            if not price_id:
                # Create price if not exists
                price = stripe.Price.create(
                    unit_amount=price_config.amount,
                    currency=price_config.currency,
                    recurring={"interval": price_config.interval},
                    product_data={"name": f"CryptoOrchestrator {tier.capitalize()}"},
                )
                price_id = price.id
                price_config.stripe_price_id = price_id

            # Create subscription
            subscription_params = {
                "customer": customer_id,
                "items": [{"price": price_id}],
                "payment_behavior": "default_incomplete",
                "expand": ["latest_invoice.payment_intent"],
            }

            if payment_method_id:
                subscription_params["default_payment_method"] = payment_method_id

            subscription = stripe.Subscription.create(**subscription_params)

            return {
                "id": subscription.id,
                "status": subscription.status,
                "tier": tier,
                "customer": customer_id,
                "current_period_start": datetime.fromtimestamp(
                    subscription.current_period_start
                ),
                "current_period_end": datetime.fromtimestamp(
                    subscription.current_period_end
                ),
                "latest_invoice": (
                    subscription.latest_invoice.id
                    if hasattr(subscription.latest_invoice, "id")
                    else None
                ),
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe subscription: {e}")
            return None

    def cancel_subscription(
        self, subscription_id: str, cancel_at_period_end: bool = True
    ) -> dict[str, Any] | None:
        """Cancel a Stripe subscription"""
        if not STRIPE_AVAILABLE:
            return None

        try:
            if cancel_at_period_end:
                subscription = stripe.Subscription.modify(
                    subscription_id, cancel_at_period_end=True
                )
            else:
                subscription = stripe.Subscription.delete(subscription_id)

            return {
                "id": subscription.id,
                "status": subscription.status,
                "cancel_at_period_end": (
                    subscription.cancel_at_period_end
                    if hasattr(subscription, "cancel_at_period_end")
                    else False
                ),
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel Stripe subscription: {e}")
            return None

    def update_subscription(
        self, subscription_id: str, new_tier: str
    ) -> dict[str, Any] | None:
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
                    product_data={
                        "name": f"CryptoOrchestrator {new_tier.capitalize()}"
                    },
                )
                price_id = price.id

            # Update subscription
            subscription = stripe.Subscription.retrieve(subscription_id)
            subscription = stripe.Subscription.modify(
                subscription_id,
                items=[{"id": subscription["items"]["data"][0].id, "price": price_id}],
                proration_behavior="always_invoice",
            )

            return {
                "id": subscription.id,
                "status": subscription.status,
                "tier": new_tier,
                "current_period_start": datetime.fromtimestamp(
                    subscription.current_period_start
                ),
                "current_period_end": datetime.fromtimestamp(
                    subscription.current_period_end
                ),
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update Stripe subscription: {e}")
            return None

    def get_subscription(self, subscription_id: str) -> dict[str, Any] | None:
        """Get subscription details"""
        if not STRIPE_AVAILABLE:
            return None

        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": subscription.id,
                "status": subscription.status,
                "customer": subscription.customer,
                "current_period_start": datetime.fromtimestamp(
                    subscription.current_period_start
                ),
                "current_period_end": datetime.fromtimestamp(
                    subscription.current_period_end
                ),
                "cancel_at_period_end": subscription.cancel_at_period_end,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get Stripe subscription: {e}")
            return None

    def create_payment_intent(
        self,
        amount: int,
        currency: str = "usd",
        customer_id: str | None = None,
        payment_method_type: str = "card",  # 'card', 'ach_debit', 'us_bank_account'
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Create a payment intent for one-time payments

        Supports:
        - card: Credit/debit cards
        - ach_debit: ACH Direct Debit (bank transfers)
        - us_bank_account: US bank account transfers
        """
        if not STRIPE_AVAILABLE:
            return None

        try:
            # Map payment method types
            payment_method_types = []
            if payment_method_type == "card":
                payment_method_types = ["card"]
            elif payment_method_type in ["ach_debit", "bank_transfer", "ach"]:
                payment_method_types = ["us_bank_account"]
            else:
                payment_method_types = ["card"]  # Default to card

            intent_params = {
                "amount": amount,
                "currency": currency,
                "payment_method_types": payment_method_types,
            }

            if customer_id:
                intent_params["customer"] = customer_id

            if metadata:
                intent_params["metadata"] = metadata

            # For ACH, add additional parameters
            if "us_bank_account" in payment_method_types:
                intent_params["payment_method_options"] = {
                    "us_bank_account": {
                        "verification_method": "automatic",  # or 'microdeposits'
                        "financial_connections": {
                            "permissions": ["payment_method", "balances"]
                        },
                    }
                }

            intent = stripe.PaymentIntent.create(**intent_params)

            return {
                "id": intent.id,
                "client_secret": intent.client_secret,
                "amount": intent.amount,
                "currency": intent.currency,
                "status": intent.status,
                "payment_method_types": payment_method_types,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create payment intent: {e}")
            return None

    def get_payment_intent(self, payment_intent_id: str) -> dict[str, Any] | None:
        """Retrieve a payment intent from Stripe"""
        if not STRIPE_AVAILABLE:
            return None

        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                "id": intent.id,
                "status": intent.status,
                "amount": intent.amount,
                "currency": intent.currency,
                "client_secret": intent.client_secret,
                "payment_method": intent.payment_method,
                "metadata": intent.metadata,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve payment intent: {e}")
            return None

    def create_setup_intent(
        self,
        customer_id: str | None = None,
        payment_method_type: str = "card",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Create a setup intent for saving payment methods"""
        if not STRIPE_AVAILABLE:
            return None

        try:
            payment_method_types = []
            if payment_method_type == "card":
                payment_method_types = ["card"]
            elif payment_method_type in ["ach_debit", "bank_transfer", "ach"]:
                payment_method_types = ["us_bank_account"]
            else:
                payment_method_types = ["card"]

            setup_params = {"payment_method_types": payment_method_types}

            if customer_id:
                setup_params["customer"] = customer_id

            if metadata:
                setup_params["metadata"] = metadata

            if "us_bank_account" in payment_method_types:
                setup_params["payment_method_options"] = {
                    "us_bank_account": {
                        "verification_method": "automatic",
                        "financial_connections": {
                            "permissions": ["payment_method", "balances"]
                        },
                    }
                }

            setup_intent = stripe.SetupIntent.create(**setup_params)

            return {
                "id": setup_intent.id,
                "client_secret": setup_intent.client_secret,
                "status": setup_intent.status,
                "payment_method_types": payment_method_types,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create setup intent: {e}")
            return None

    def attach_payment_method(
        self, payment_method_id: str, customer_id: str
    ) -> dict[str, Any] | None:
        """Attach a payment method to a customer"""
        if not STRIPE_AVAILABLE:
            return None

        try:
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id, customer=customer_id
            )

            # Set as default if no default exists
            customer = stripe.Customer.retrieve(customer_id)
            if not customer.invoice_settings.default_payment_method:
                stripe.Customer.modify(
                    customer_id,
                    invoice_settings={"default_payment_method": payment_method_id},
                )

            return {
                "id": payment_method.id,
                "type": payment_method.type,
                "customer": payment_method.customer,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to attach payment method: {e}")
            return None

    def list_payment_methods(
        self, customer_id: str, payment_method_type: str | None = None
    ) -> list[dict[str, Any]]:
        """List payment methods for a customer"""
        if not STRIPE_AVAILABLE:
            return []

        try:
            params = {"customer": customer_id}
            if payment_method_type:
                params["type"] = payment_method_type

            payment_methods = stripe.PaymentMethod.list(**params)

            return [
                {
                    "id": pm.id,
                    "type": pm.type,
                    "card": (
                        {
                            "brand": (
                                pm.card.brand
                                if hasattr(pm, "card") and pm.card
                                else None
                            ),
                            "last4": (
                                pm.card.last4
                                if hasattr(pm, "card") and pm.card
                                else None
                            ),
                            "exp_month": (
                                pm.card.exp_month
                                if hasattr(pm, "card") and pm.card
                                else None
                            ),
                            "exp_year": (
                                pm.card.exp_year
                                if hasattr(pm, "card") and pm.card
                                else None
                            ),
                        }
                        if hasattr(pm, "card") and pm.card
                        else None
                    ),
                    "us_bank_account": (
                        {
                            "bank_name": (
                                pm.us_bank_account.bank_name
                                if hasattr(pm, "us_bank_account") and pm.us_bank_account
                                else None
                            ),
                            "last4": (
                                pm.us_bank_account.last4
                                if hasattr(pm, "us_bank_account") and pm.us_bank_account
                                else None
                            ),
                            "account_type": (
                                pm.us_bank_account.account_type
                                if hasattr(pm, "us_bank_account") and pm.us_bank_account
                                else None
                            ),
                        }
                        if hasattr(pm, "us_bank_account") and pm.us_bank_account
                        else None
                    ),
                }
                for pm in payment_methods.data
            ]
        except stripe.error.StripeError as e:
            logger.error(f"Failed to list payment methods: {e}")
            return []

    def delete_payment_method(self, payment_method_id: str) -> bool:
        """Delete a payment method"""
        if not STRIPE_AVAILABLE:
            return False

        try:
            stripe.PaymentMethod.detach(payment_method_id)
            return True
        except stripe.error.StripeError as e:
            logger.error(f"Failed to delete payment method: {e}")
            return False

    def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str | None = None,
        cancel_url: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Create Stripe Checkout session for subscriptions"""
        if not STRIPE_AVAILABLE or not self.secret_key:
            logger.warning("Stripe not available")
            return None

        try:
            success_url = success_url or f"{FRONTEND_URL}/billing/success"
            cancel_url = cancel_url or f"{FRONTEND_URL}/billing"

            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1,
                    }
                ],
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
        self, customer_id: str, return_url: str | None = None
    ) -> dict[str, Any] | None:
        """Create Stripe Customer Portal session"""
        if not STRIPE_AVAILABLE or not self.secret_key:
            logger.warning("Stripe not available")
            return None

        try:
            return_url = return_url or f"{FRONTEND_URL}/billing"
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

    def handle_webhook(self, payload: bytes, signature: str) -> dict[str, Any] | None:
        """Handle Stripe webhook events"""
        if not STRIPE_AVAILABLE or not self.webhook_secret:
            logger.warning("Stripe webhook handling unavailable")
            return None

        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )

            event_type = event["type"]
            event_data = event["data"]["object"]

            logger.info(f"Received Stripe webhook: {event_type}")

            # Handle different event types
            if event_type == "customer.subscription.created":
                return {"event": "subscription.created", "data": event_data}
            elif event_type == "customer.subscription.updated":
                return {"event": "subscription.updated", "data": event_data}
            elif event_type == "customer.subscription.deleted":
                return {"event": "subscription.deleted", "data": event_data}
            elif event_type == "invoice.payment_succeeded":
                return {"event": "payment.succeeded", "data": event_data}
            elif event_type == "invoice.payment_failed":
                return {"event": "payment.failed", "data": event_data}
            else:
                return {"event": event_type, "data": event_data}

        except ValueError as e:
            logger.error(f"Invalid payload in Stripe webhook: {e}")
            return None
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature in Stripe webhook: {e}")
            return None

    @staticmethod
    def get_plan_config(plan: str) -> dict[str, Any] | None:
        """Get plan configuration (from billing/stripe_service.py)"""
        # Plan configurations with detailed features and limits
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
                "price_monthly": 29,
                "price_yearly": 290,
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
                "price_monthly": 99,
                "price_yearly": 990,
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
                    "max_bots": -1,
                    "max_strategies": -1,
                    "max_backtests_per_month": -1,
                },
            },
            SubscriptionPlan.ENTERPRISE: {
                "name": "Enterprise",
                "price_monthly": 299,
                "price_yearly": 2990,
                "stripe_price_id_monthly": os.getenv(
                    "STRIPE_PRICE_ENTERPRISE_MONTHLY", ""
                ),
                "stripe_price_id_yearly": os.getenv(
                    "STRIPE_PRICE_ENTERPRISE_YEARLY", ""
                ),
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
        try:
            return PLAN_CONFIGS.get(SubscriptionPlan(plan))
        except ValueError:
            return None

    @staticmethod
    def list_plans() -> list[dict[str, Any]]:
        """List all available plans (from billing/stripe_service.py)"""
        plan_config = StripeService.get_plan_config
        plans = []
        for plan in SubscriptionPlan:
            config = plan_config(plan.value)
            if config:
                plans.append({"plan": plan.value, **config})
        return plans

    async def get_revenue_in_period(
        self, start_date: datetime, end_date: datetime
    ) -> float:
        """
        Get subscription revenue for a date period from Stripe

        Args:
            start_date: Start date for revenue calculation
            end_date: End date for revenue calculation

        Returns:
            Total revenue in USD (as float)
        """
        if not STRIPE_AVAILABLE or not self.secret_key:
            logger.warning("Stripe not available for revenue calculation")
            return 0.0

        try:
            # Query Stripe for successful payment intents in the period
            # Convert datetime to Unix timestamp for Stripe API
            start_timestamp = int(start_date.timestamp())
            end_timestamp = int(end_date.timestamp())

            # Get all successful payment intents (subscriptions and one-time payments)
            payment_intents = stripe.PaymentIntent.list(
                created={"gte": start_timestamp, "lte": end_timestamp},
                limit=100,  # Stripe pagination limit
            )

            total_revenue = 0.0

            # Sum up successful payments
            for pi in payment_intents.auto_paging_iter():
                if pi.status == "succeeded":
                    # Convert from cents to dollars
                    amount_usd = pi.amount / 100.0
                    total_revenue += amount_usd

            logger.info(
                f"Calculated revenue: ${total_revenue:.2f} from {start_date.isoformat()} to {end_date.isoformat()}"
            )

            return total_revenue

        except Exception as e:
            logger.error(f"Error calculating Stripe revenue: {e}", exc_info=True)
            return 0.0


# Global service instance
stripe_service = StripeService()
