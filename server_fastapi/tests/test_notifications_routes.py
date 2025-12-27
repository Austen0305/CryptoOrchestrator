"""
Integration tests for push notifications API endpoints
Tests subscription and unsubscription
"""

import pytest
from httpx import AsyncClient
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio


class TestNotificationsRoutes:
    """Integration tests for push notifications API endpoints"""

    async def test_subscribe_push_notifications(
        self, client: AsyncClient, auth_headers: Dict[str, str]
    ):
        """Test subscribing to push notifications"""
        subscription_data = {
            "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint",
            "keys": {
                "p256dh": "test-p256dh-key",
                "auth": "test-auth-key",
            },
        }

        response = await client.post(
            "/api/notifications/subscribe",
            json=subscription_data,
            headers=auth_headers,
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert "success" in data or "message" in data

    async def test_subscribe_push_notifications_unauthenticated(
        self, client: AsyncClient
    ):
        """Test subscribing without authentication"""
        subscription_data = {
            "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint",
            "keys": {
                "p256dh": "test-p256dh-key",
                "auth": "test-auth-key",
            },
        }

        response = await client.post(
            "/api/notifications/subscribe",
            json=subscription_data,
        )

        assert response.status_code in [401, 403]

    async def test_unsubscribe_push_notifications(
        self, client: AsyncClient, auth_headers: Dict[str, str]
    ):
        """Test unsubscribing from push notifications"""
        response = await client.post(
            "/api/notifications/unsubscribe",
            headers=auth_headers,
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "success" in data or "message" in data
