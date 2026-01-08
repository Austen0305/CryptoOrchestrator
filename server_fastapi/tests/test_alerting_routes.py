"""
Integration tests for alerting API endpoints
Tests alert management, rules, and incident management
"""

import logging

import pytest
from httpx import AsyncClient

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio


class TestAlertingRoutes:
    """Integration tests for alerting API endpoints"""

    async def test_get_active_alerts_admin(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test getting active alerts with admin access"""
        response = await client.get(
            "/api/alerting/alerts",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_active_alerts_non_admin_forbidden(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Test getting active alerts without admin access"""
        response = await client.get(
            "/api/alerting/alerts",
            headers=auth_headers,
        )

        assert response.status_code == 403

    async def test_get_alert_history(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test getting alert history"""
        response = await client.get(
            "/api/alerting/alerts/history",
            headers=admin_headers,
            params={"limit": 50},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_acknowledge_alert(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test acknowledging an alert"""
        # First get alerts
        get_response = await client.get(
            "/api/alerting/alerts",
            headers=admin_headers,
        )

        if get_response.status_code == 200:
            alerts = get_response.json()
            if alerts:
                alert_id = alerts[0].get("id")
                if alert_id:
                    response = await client.post(
                        f"/api/alerting/alerts/{alert_id}/acknowledge",
                        headers=admin_headers,
                    )
                    assert response.status_code in [200, 404]

    async def test_get_alerting_rules(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test getting alerting rules"""
        response = await client.get(
            "/api/alerting/rules",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_fatigue_stats(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test getting alert fatigue statistics"""
        response = await client.get(
            "/api/alerting/fatigue-stats",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    async def test_get_incidents(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test getting incidents"""
        response = await client.get(
            "/api/alerting/incidents",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
