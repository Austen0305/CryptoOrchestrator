"""
Tests for Marketplace Analytics API Routes
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from server_fastapi.models.indicator import (
    IndicatorStatus,
)
from server_fastapi.models.signal_provider import CuratorStatus, SignalProvider
from server_fastapi.models.user import User

pytestmark = pytest.mark.asyncio


class TestMarketplaceAnalyticsRoutes:
    """Tests for marketplace analytics API routes"""

    async def test_get_marketplace_overview_admin(
        self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession
    ):
        """Test getting marketplace overview (admin only)"""
        response = await client.get(
            "/admin/marketplace/overview",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "copy_trading" in data
        assert "indicators" in data
        assert "timestamp" in data

        # Verify structure
        assert "total_providers" in data["copy_trading"]
        assert "total_indicators" in data["indicators"]

    async def test_get_marketplace_overview_non_admin_forbidden(
        self, client: AsyncClient, test_user_with_auth: dict
    ):
        """Test that non-admin users cannot access marketplace overview"""
        headers = {"Authorization": f"Bearer {test_user_with_auth['token']}"}

        response = await client.get(
            "/admin/marketplace/overview",
            headers=headers,
        )

        assert response.status_code == 403

    async def test_get_top_providers(
        self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession
    ):
        """Test getting top providers"""
        response = await client.get(
            "/admin/marketplace/top-providers?limit=10&sort_by=total_return",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert "limit" in data
        assert "sort_by" in data
        assert isinstance(data["providers"], list)

    async def test_get_top_providers_different_sorts(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test getting top providers with different sort options"""
        sort_options = ["total_return", "sharpe_ratio", "follower_count", "rating"]

        for sort_by in sort_options:
            response = await client.get(
                f"/admin/marketplace/top-providers?limit=5&sort_by={sort_by}",
                headers=admin_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["sort_by"] == sort_by

    async def test_get_top_indicators(self, client: AsyncClient, admin_headers: dict):
        """Test getting top indicators"""
        response = await client.get(
            "/admin/marketplace/top-indicators?limit=10&sort_by=purchase_count",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "indicators" in data
        assert "limit" in data
        assert "sort_by" in data
        assert isinstance(data["indicators"], list)

    async def test_get_revenue_trends(self, client: AsyncClient, admin_headers: dict):
        """Test getting revenue trends"""
        response = await client.get(
            "/admin/marketplace/revenue-trends?days=30",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "copy_trading" in data
        assert "indicators" in data
        assert "period_days" in data
        assert data["period_days"] == 30

    async def test_get_revenue_trends_different_periods(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test getting revenue trends with different periods"""
        periods = [7, 30, 90, 365]

        for days in periods:
            response = await client.get(
                f"/admin/marketplace/revenue-trends?days={days}",
                headers=admin_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["period_days"] == days


class TestDeveloperAnalyticsRoutes:
    """Tests for developer analytics API routes"""

    async def test_get_developer_analytics(
        self, client: AsyncClient, test_user_with_auth: dict, db: AsyncSession
    ):
        """Test getting developer analytics"""
        headers = {"Authorization": f"Bearer {test_user_with_auth['token']}"}

        response = await client.get(
            "/api/indicators/analytics/developer",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "developer_id" in data
        assert "total_indicators" in data
        assert "total_purchases" in data
        assert "total_revenue" in data
        assert "developer_earnings" in data
        assert "indicators" in data

    async def test_get_indicator_analytics_owner(
        self, client: AsyncClient, test_user_with_auth: dict, db: AsyncSession
    ):
        """Test getting analytics for own indicator"""
        headers = {"Authorization": f"Bearer {test_user_with_auth['token']}"}
        user_id = test_user_with_auth["user_id"]

        # Create an indicator for this user
        from ..models.indicator import Indicator

        indicator = Indicator(
            name="Test Indicator",
            code="values = [1.0]",
            developer_id=user_id,
            status=IndicatorStatus.APPROVED.value,
            is_free=True,
        )
        db_session.add(indicator)
        await db_session.commit()
        await db_session.refresh(indicator)

        response = await client.get(
            f"/api/indicators/analytics/indicator/{indicator.id}",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["indicator_id"] == indicator.id
        assert "purchases" in data
        assert "total_revenue" in data
        assert "developer_earnings" in data

    async def test_get_indicator_analytics_not_owner_forbidden(
        self, client: AsyncClient, test_user_with_auth: dict, db: AsyncSession
    ):
        """Test that non-owners cannot access indicator analytics"""
        headers = {"Authorization": f"Bearer {test_user_with_auth['token']}"}

        # Create another user and indicator
        other_user = User(
            email="other@test.com",
            username="other_user",
            hashed_password="hashed",
        )
        db_session.add(other_user)
        await db_session.commit()
        await db.refresh(other_user)

        from ..models.indicator import Indicator

        indicator = Indicator(
            name="Other User Indicator",
            code="values = [1.0]",
            developer_id=other_user.id,
            status=IndicatorStatus.APPROVED.value,
            is_free=True,
        )
        db_session.add(indicator)
        await db_session.commit()
        await db_session.refresh(indicator)

        response = await client.get(
            f"/api/indicators/analytics/indicator/{indicator.id}",
            headers=headers,
        )

        assert response.status_code == 403


class TestProviderAnalyticsRoutes:
    """Tests for provider analytics API routes"""

    async def test_get_provider_analytics_owner(
        self, client: AsyncClient, test_user_with_auth: dict, db: AsyncSession
    ):
        """Test getting analytics for own provider"""
        headers = {"Authorization": f"Bearer {test_user_with_auth['token']}"}
        user_id = test_user_with_auth["user_id"]

        # Create a signal provider for this user
        provider = SignalProvider(
            user_id=user_id,
            curator_status=CuratorStatus.APPROVED.value,
            is_public=True,
        )
        db_session.add(provider)
        await db_session.commit()
        await db_session.refresh(provider)

        response = await client.get(
            f"/api/marketplace/analytics/provider/{provider.id}",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["provider_id"] == provider.id
        assert "total_return" in data
        assert "follower_count" in data
        assert "total_earnings" in data
        assert "recent_payouts" in data
        assert "recent_ratings" in data

    async def test_get_provider_analytics_not_owner_forbidden(
        self, client: AsyncClient, test_user_with_auth: dict, db: AsyncSession
    ):
        """Test that non-owners cannot access provider analytics"""
        headers = {"Authorization": f"Bearer {test_user_with_auth['token']}"}

        # Create another user and provider
        other_user = User(
            email="other2@test.com",
            username="other_user2",
            hashed_password="hashed",
        )
        db_session.add(other_user)
        await db_session.commit()
        await db.refresh(other_user)

        provider = SignalProvider(
            user_id=other_user.id,
            curator_status=CuratorStatus.APPROVED.value,
            is_public=True,
        )
        db_session.add(provider)
        await db_session.commit()
        await db_session.refresh(provider)

        response = await client.get(
            f"/api/marketplace/analytics/provider/{provider.id}",
            headers=headers,
        )

        assert response.status_code == 403

    async def test_get_provider_analytics_not_found(
        self, client: AsyncClient, test_user_with_auth: dict
    ):
        """Test getting analytics for non-existent provider"""
        headers = {"Authorization": f"Bearer {test_user_with_auth['token']}"}

        response = await client.get(
            "/api/marketplace/analytics/provider/99999",
            headers=headers,
        )

        assert response.status_code == 404
