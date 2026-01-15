"""
Webhook Service
Manages webhook subscriptions and deliveries
"""

import hashlib
import hmac
import json
import logging
from datetime import UTC, datetime
from typing import Any

import aiohttp
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.webhooks import Webhook, WebhookDelivery

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for webhook management"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_webhook(
        self,
        user_id: int,
        name: str,
        url: str,
        events: list[str],
        secret: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> tuple[Webhook, str]:
        """
        Create a webhook

        Returns:
            Tuple of (webhook, secret) - secret is only returned once
        """
        if not secret:
            secret = self._generate_secret()

        webhook = Webhook(
            user_id=user_id,
            name=name,
            url=url,
            secret=secret,
            events=events,
            config=config or {},
            is_active=True,
        )

        self.db.add(webhook)
        await self.db.commit()
        await self.db.refresh(webhook)

        logger.info(f"Webhook created: {webhook.id} for user {user_id}")

        return webhook, secret

    def _generate_secret(self) -> str:
        """Generate a webhook secret"""
        import secrets

        return secrets.token_urlsafe(32)

    async def trigger_webhook(
        self,
        event_type: str,
        payload: dict[str, Any],
        user_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Trigger webhooks for an event

        Returns:
            List of delivery results
        """
        # Find active webhooks subscribed to this event
        stmt = select(Webhook).where(
            and_(
                Webhook.is_active,
                Webhook.events.contains([event_type]),
            )
        )

        if user_id:
            stmt = stmt.where(Webhook.user_id == user_id)

        result = await self.db.execute(stmt)
        webhooks = result.scalars().all()

        delivery_results = []

        for webhook in webhooks:
            try:
                delivery = await self._deliver_webhook(webhook, event_type, payload)
                delivery_results.append(
                    {
                        "webhook_id": webhook.id,
                        "status": delivery.status,
                        "status_code": delivery.status_code,
                    }
                )
            except Exception as e:
                logger.error(f"Error delivering webhook {webhook.id}: {e}")
                delivery_results.append(
                    {
                        "webhook_id": webhook.id,
                        "status": "failed",
                        "error": str(e),
                    }
                )

        return delivery_results

    async def _deliver_webhook(
        self,
        webhook: Webhook,
        event_type: str,
        payload: dict[str, Any],
    ) -> WebhookDelivery:
        """Deliver a webhook"""
        # Create delivery record
        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event_type=event_type,
            payload=payload,
            status="pending",
            attempted_at=datetime.now(UTC),
        )
        self.db.add(delivery)
        await self.db.flush()

        # Generate signature
        signature = self._generate_signature(webhook.secret, payload)

        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": event_type,
            "X-Webhook-Signature": signature,
            "X-Webhook-Delivery-Id": str(delivery.id),
        }

        # Send webhook
        try:
            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response,
            ):
                delivery.status_code = response.status
                delivery.status = "success" if response.status < 400 else "failed"
                delivery.response_body = await response.text()
                delivery.completed_at = datetime.now(UTC)
        except Exception as e:
            delivery.status = "failed"
            delivery.response_body = str(e)
            delivery.completed_at = datetime.now(UTC)
            logger.error(f"Webhook delivery failed: {e}")

        # Update webhook last triggered
        webhook.last_triggered = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(delivery)

        return delivery

    def _generate_signature(self, secret: str, payload: dict[str, Any]) -> str:
        """Generate webhook signature"""
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={signature}"

    async def get_webhook_deliveries(
        self,
        webhook_id: int,
        limit: int = 50,
    ) -> list[WebhookDelivery]:
        """Get webhook delivery history"""
        stmt = (
            select(WebhookDelivery)
            .where(WebhookDelivery.webhook_id == webhook_id)
            .order_by(desc(WebhookDelivery.created_at))
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())
