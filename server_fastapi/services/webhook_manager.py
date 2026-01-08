"""
Webhook Management System
Manages webhook subscriptions, delivery, and retries
"""

import asyncio
import hashlib
import hmac
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class WebhookStatus(str, Enum):
    """Webhook delivery status"""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class WebhookSubscription:
    """Webhook subscription"""

    id: str
    url: str
    events: list[str]
    secret: str | None = None
    active: bool = True
    created_at: datetime = None
    last_delivery: datetime | None = None
    failure_count: int = 0
    max_retries: int = 3
    timeout: int = 10

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class WebhookDelivery:
    """Webhook delivery attempt"""

    id: str
    subscription_id: str
    event_type: str
    payload: dict[str, Any]
    status: WebhookStatus
    attempts: int = 0
    created_at: datetime = None
    delivered_at: datetime | None = None
    error: str | None = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class WebhookManager:
    """
    Webhook management system

    Features:
    - Subscription management
    - Event filtering
    - Secure delivery with signatures
    - Automatic retries
    - Delivery tracking
    """

    def __init__(self):
        self.subscriptions: dict[str, WebhookSubscription] = {}
        self.deliveries: list[WebhookDelivery] = []
        self._delivery_task: asyncio.Task | None = None
        self._running = False

    def subscribe(
        self,
        url: str,
        events: list[str],
        secret: str | None = None,
        max_retries: int = 3,
        timeout: int = 10,
    ) -> WebhookSubscription:
        """Subscribe to webhook events"""
        subscription_id = hashlib.sha256(
            f"{url}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]

        subscription = WebhookSubscription(
            id=subscription_id,
            url=url,
            events=events,
            secret=secret,
            max_retries=max_retries,
            timeout=timeout,
        )

        self.subscriptions[subscription_id] = subscription
        logger.info(f"Webhook subscribed: {subscription_id} for events: {events}")

        return subscription

    def unsubscribe(self, subscription_id: str):
        """Unsubscribe from webhook events"""
        if subscription_id in self.subscriptions:
            self.subscriptions[subscription_id].active = False
            logger.info(f"Webhook unsubscribed: {subscription_id}")

    async def deliver(self, event_type: str, payload: dict[str, Any]):
        """Deliver webhook event to all matching subscriptions"""
        matching_subscriptions = [
            sub
            for sub in self.subscriptions.values()
            if sub.active and event_type in sub.events
        ]

        if not matching_subscriptions:
            logger.debug(f"No subscriptions for event: {event_type}")
            return

        for subscription in matching_subscriptions:
            delivery = WebhookDelivery(
                id=hashlib.sha256(
                    f"{subscription.id}:{event_type}:{datetime.utcnow().isoformat()}".encode()
                ).hexdigest()[:16],
                subscription_id=subscription.id,
                event_type=event_type,
                payload=payload,
                status=WebhookStatus.PENDING,
            )

            self.deliveries.append(delivery)
            asyncio.create_task(self._deliver_webhook(subscription, delivery))

    async def _deliver_webhook(
        self, subscription: WebhookSubscription, delivery: WebhookDelivery
    ):
        """Deliver webhook with retries"""
        while delivery.attempts < subscription.max_retries:
            delivery.attempts += 1
            delivery.status = (
                WebhookStatus.RETRYING
                if delivery.attempts > 1
                else WebhookStatus.PENDING
            )

            try:
                # Prepare payload
                webhook_payload = {
                    "event": delivery.event_type,
                    "data": delivery.payload,
                    "timestamp": datetime.utcnow().isoformat(),
                    "delivery_id": delivery.id,
                }

                # Generate signature if secret provided
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "CryptoOrchestrator-Webhook/1.0",
                }

                if subscription.secret:
                    signature = self._generate_signature(
                        json.dumps(webhook_payload, sort_keys=True),
                        subscription.secret,
                    )
                    headers["X-Webhook-Signature"] = signature

                # Deliver
                async with httpx.AsyncClient(timeout=subscription.timeout) as client:
                    response = await client.post(
                        subscription.url,
                        json=webhook_payload,
                        headers=headers,
                    )

                    if response.is_success:
                        delivery.status = WebhookStatus.SUCCESS
                        delivery.delivered_at = datetime.utcnow()
                        subscription.last_delivery = datetime.utcnow()
                        subscription.failure_count = 0
                        logger.info(f"Webhook delivered: {delivery.id}")
                        return
                    else:
                        delivery.error = f"HTTP {response.status_code}: {response.text}"
                        logger.warning(f"Webhook delivery failed: {delivery.error}")

            except httpx.TimeoutException:
                delivery.error = "Request timeout"
                logger.warning(f"Webhook delivery timeout: {subscription.url}")
            except Exception as e:
                delivery.error = str(e)
                logger.error(f"Webhook delivery error: {e}", exc_info=True)

            # Wait before retry
            if delivery.attempts < subscription.max_retries:
                wait_time = min(
                    2**delivery.attempts, 60
                )  # Exponential backoff, max 60s
                await asyncio.sleep(wait_time)

        # All retries failed
        delivery.status = WebhookStatus.FAILED
        subscription.failure_count += 1
        logger.error(
            f"Webhook delivery failed after {delivery.attempts} attempts: {delivery.id}"
        )

    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook"""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

    def verify_signature(self, payload: str, signature: str, secret: str) -> bool:
        """Verify webhook signature"""
        expected = self._generate_signature(payload, secret)
        return hmac.compare_digest(expected, signature)

    def get_subscriptions(self, active_only: bool = True) -> list[WebhookSubscription]:
        """Get all subscriptions"""
        subscriptions = list(self.subscriptions.values())
        if active_only:
            subscriptions = [s for s in subscriptions if s.active]
        return subscriptions

    def get_deliveries(
        self,
        subscription_id: str | None = None,
        status: WebhookStatus | None = None,
        limit: int = 100,
    ) -> list[WebhookDelivery]:
        """Get delivery history"""
        deliveries = self.deliveries
        if subscription_id:
            deliveries = [d for d in deliveries if d.subscription_id == subscription_id]
        if status:
            deliveries = [d for d in deliveries if d.status == status]
        return deliveries[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """Get webhook statistics"""
        total_deliveries = len(self.deliveries)
        successful = len(
            [d for d in self.deliveries if d.status == WebhookStatus.SUCCESS]
        )
        failed = len([d for d in self.deliveries if d.status == WebhookStatus.FAILED])

        return {
            "total_subscriptions": len(self.subscriptions),
            "active_subscriptions": len(
                [s for s in self.subscriptions.values() if s.active]
            ),
            "total_deliveries": total_deliveries,
            "successful_deliveries": successful,
            "failed_deliveries": failed,
            "success_rate": (successful / total_deliveries * 100)
            if total_deliveries > 0
            else 0,
        }


# Global webhook manager instance
webhook_manager = WebhookManager()
