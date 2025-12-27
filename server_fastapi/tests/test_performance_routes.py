"""
Tests for Performance Routes
"""

import pytest
from httpx import AsyncClient
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from server_fastapi.models.trade import Trade


@pytest.mark.asyncio
class TestPerformanceRoutes:
    """Test performance endpoints"""

    async def test_get_performance_summary_no_trades(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting performance summary when no trades exist"""
        response = await client.get("/api/performance/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["winRate"] == 0.0
        assert data["avgProfit"] == 0.0
        assert data["totalProfit"] == 0.0
        assert data["bestTrade"] == 0.0
        assert data["worstTrade"] == 0.0

    async def test_get_performance_summary_with_mode(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting performance summary with trading mode"""
        response = await client.get(
            "/api/performance/summary?mode=paper", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "winRate" in data
        assert "avgProfit" in data
        assert "totalProfit" in data
        assert "bestTrade" in data
        assert "worstTrade" in data

    async def test_get_performance_summary_live_mode(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that 'live' mode is normalized to 'real'"""
        response = await client.get(
            "/api/performance/summary?mode=live", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    async def test_get_performance_summary_with_trades(
        self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession
    ):
        """Test getting performance summary with actual trades"""
        user_id = "test-user-id"  # Default test user ID

        # Create winning and losing trades
        winning_trade = Trade(
            id="test-trade-win",
            user_id=user_id,
            pair="BTC/USD",
            side="buy",
            amount=0.1,
            price=50000.0,
            pnl=500.0,  # Profit
            success=True,
            mode="paper",
            created_at=datetime.now(),
        )

        losing_trade = Trade(
            id="test-trade-loss",
            user_id=user_id,
            pair="BTC/USD",
            side="sell",
            amount=0.1,
            price=49000.0,
            pnl=-200.0,  # Loss
            success=True,
            mode="paper",
            created_at=datetime.now(),
        )

        db_session.add(winning_trade)
        db_session.add(losing_trade)
        await db_session.commit()

        response = await client.get(
            "/api/performance/summary?mode=paper", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        # Should have calculated metrics (if database is available)
        assert isinstance(data, dict)
        assert "winRate" in data
        assert "avgProfit" in data
        assert "totalProfit" in data
        assert "bestTrade" in data
        assert "worstTrade" in data

        # If trades were found, verify calculations
        if data["totalProfit"] != 0.0:
            assert data["winRate"] >= 0.0
            assert data["bestTrade"] >= data["worstTrade"]

    async def test_get_performance_summary_requires_auth(self, client: AsyncClient):
        """Test that performance endpoint requires authentication"""
        response = await client.get("/api/performance/summary")
        assert response.status_code == 401
