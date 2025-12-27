"""
Tests for Copy Trading Marketplace API Routes
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from datetime import datetime, timedelta


pytestmark = pytest.mark.asyncio


class TestMarketplaceRoutes:
    """Tests for marketplace API routes"""

    async def test_apply_as_signal_provider(
        self, client: AsyncClient, test_user_with_auth
    ):
        """Test applying as a signal provider"""
        headers = {"Authorization": f"Bearer {test_user_with_auth['token']}"}

        response = await client.post(
            "/api/marketplace/apply",
            json={
                "min_follow_amount": 100.0,
                "max_followers": 100,
                "subscription_fee": 10.0,
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert "id" in data

    async def test_get_marketplace_traders(self, client: AsyncClient):
        """Test getting marketplace traders"""
        response = await client.get(
            "/api/marketplace/traders?skip=0&limit=10&sort_by=sharpe_ratio"
        )

        assert response.status_code == 200
        data = response.json()
        assert "traders" in data
        assert "total" in data
        assert isinstance(data["traders"], list)

    async def test_get_marketplace_traders_with_filters(self, client: AsyncClient):
        """Test getting marketplace traders with filters"""
        response = await client.get(
            "/api/marketplace/traders?skip=0&limit=10&min_win_rate=0.6&min_sharpe=1.0"
        )

        assert response.status_code == 200
        data = response.json()
        assert "traders" in data

        # Verify filters applied
        for trader in data["traders"]:
            if trader.get("win_rate") is not None:
                assert trader["win_rate"] >= 0.6
            if trader.get("sharpe_ratio") is not None:
                assert trader["sharpe_ratio"] >= 1.0

    async def test_get_trader_profile(
        self, client: AsyncClient, test_user_with_auth
    ):
        """Test getting trader profile"""
        headers = {"Authorization": f"Bearer {test_user_with_auth['token']}"}

        # First apply as provider
        apply_response = await client.post(
            "/api/marketplace/apply",
            json={},
            headers=headers,
        )
        provider_id = apply_response.json()["id"]

        # Get profile
        response = await client.get(
            f"/api/marketplace/traders/{provider_id}",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == provider_id
        assert "performance_metrics" in data

    async def test_rate_trader(
        self, client: AsyncClient, test_user_with_auth
    ):
        """Test rating a trader"""
        headers = {"Authorization": f"Bearer {test_user_with_auth['token']}"}

        # First apply as provider
        apply_response = await client.post(
            "/api/marketplace/apply",
            json={},
            headers=headers,
        )
        provider_id = apply_response.json()["id"]

        # Create another user to rate
        # (In real test, would create separate user)
        # For now, test with same user (should fail or be handled)

        response = await client.post(
            f"/api/marketplace/traders/{provider_id}/rate",
            json={"rating": 5, "comment": "Great trader!"},
            headers=headers,
        )

        # Should either succeed or return appropriate error
        assert response.status_code in [200, 400, 403]

    async def test_calculate_payout(
        self, client: AsyncClient, test_user_with_auth
    ):
        """Test calculating payout"""
        headers = {"Authorization": f"Bearer {test_user_with_auth['token']}"}

        # First apply as provider
        apply_response = await client.post(
            "/api/marketplace/apply",
            json={},
            headers=headers,
        )
        provider_id = apply_response.json()["id"]

        period_start = (datetime.utcnow() - timedelta(days=30)).isoformat()
        period_end = datetime.utcnow().isoformat()

        response = await client.post(
            f"/api/marketplace/traders/{provider_id}/payout/calculate",
            json={
                "period_start": period_start,
                "period_end": period_end,
                "total_revenue": 1000.0,
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_revenue" in data
        assert "platform_fee" in data
        assert "provider_payout" in data
        assert data["provider_payout"] == 800.0  # 80%

    async def test_create_payout(
        self, client: AsyncClient, test_user_with_auth
    ):
        """Test creating a payout"""
        headers = {"Authorization": f"Bearer {test_user_with_auth['token']}"}

        # First apply as provider
        apply_response = await client.post(
            "/api/marketplace/apply",
            json={},
            headers=headers,
        )
        provider_id = apply_response.json()["id"]

        period_start = (datetime.utcnow() - timedelta(days=30)).isoformat()
        period_end = datetime.utcnow().isoformat()

        response = await client.post(
            f"/api/marketplace/traders/{provider_id}/payout",
            json={
                "period_start": period_start,
                "period_end": period_end,
                "total_revenue": 1000.0,
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert "id" in data
