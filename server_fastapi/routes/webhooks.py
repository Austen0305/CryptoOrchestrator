"""
Webhook Management Routes
Provides endpoints for managing webhook subscriptions
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, HttpUrl

from ..dependencies.auth import get_current_user
from ..services.webhook_manager import webhook_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


class WebhookSubscriptionRequest(BaseModel):
    """Webhook subscription request"""

    url: HttpUrl
    events: list[str]
    secret: str | None = None
    max_retries: int = 3
    timeout: int = 10


class WebhookSubscriptionResponse(BaseModel):
    """Webhook subscription response"""

    id: str
    url: str
    events: list[str]
    active: bool
    created_at: str
    last_delivery: str | None = None
    failure_count: int = 0


@router.post("/subscribe", response_model=WebhookSubscriptionResponse)
async def subscribe_webhook(
    request: WebhookSubscriptionRequest,
    current_user: dict = Depends(get_current_user),
):
    """Subscribe to webhook events"""
    try:
        subscription = webhook_manager.subscribe(
            url=str(request.url),
            events=request.events,
            secret=request.secret,
            max_retries=request.max_retries,
            timeout=request.timeout,
        )

        return WebhookSubscriptionResponse(
            id=subscription.id,
            url=subscription.url,
            events=subscription.events,
            active=subscription.active,
            created_at=subscription.created_at.isoformat(),
            last_delivery=(
                subscription.last_delivery.isoformat()
                if subscription.last_delivery
                else None
            ),
            failure_count=subscription.failure_count,
        )
    except Exception as e:
        logger.error(f"Error subscribing webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to subscribe webhook: {str(e)}",
        )


@router.delete("/{subscription_id}")
async def unsubscribe_webhook(
    subscription_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Unsubscribe from webhook events"""
    try:
        webhook_manager.unsubscribe(subscription_id)
        return {"message": "Webhook unsubscribed successfully"}
    except Exception as e:
        logger.error(f"Error unsubscribing webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unsubscribe webhook: {str(e)}",
        )


@router.get("/", response_model=list[WebhookSubscriptionResponse])
async def list_webhooks(
    active_only: bool = Query(True, description="Show only active subscriptions"),
    current_user: dict = Depends(get_current_user),
):
    """List webhook subscriptions"""
    try:
        subscriptions = webhook_manager.get_subscriptions(active_only=active_only)
        return [
            WebhookSubscriptionResponse(
                id=sub.id,
                url=sub.url,
                events=sub.events,
                active=sub.active,
                created_at=sub.created_at.isoformat(),
                last_delivery=(
                    sub.last_delivery.isoformat() if sub.last_delivery else None
                ),
                failure_count=sub.failure_count,
            )
            for sub in subscriptions
        ]
    except Exception as e:
        logger.error(f"Error listing webhooks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list webhooks: {str(e)}",
        )


@router.get("/stats")
async def get_webhook_stats(
    current_user: dict = Depends(get_current_user),
):
    """Get webhook statistics"""
    try:
        return webhook_manager.get_stats()
    except Exception as e:
        logger.error(f"Error getting webhook stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get webhook stats: {str(e)}",
        )


@router.get("/deliveries")
async def get_webhook_deliveries(
    subscription_id: str | None = Query(None, description="Filter by subscription ID"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of deliveries to return"
    ),
    current_user: dict = Depends(get_current_user),
):
    """Get webhook delivery history"""
    try:
        deliveries = webhook_manager.get_deliveries(
            subscription_id=subscription_id,
            limit=limit,
        )
        return [
            {
                "id": d.id,
                "subscription_id": d.subscription_id,
                "event_type": d.event_type,
                "status": d.status.value,
                "attempts": d.attempts,
                "created_at": d.created_at.isoformat(),
                "delivered_at": d.delivered_at.isoformat() if d.delivered_at else None,
                "error": d.error,
            }
            for d in deliveries
        ]
    except Exception as e:
        logger.error(f"Error getting webhook deliveries: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get webhook deliveries: {str(e)}",
        )
