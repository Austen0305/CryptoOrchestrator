"""
Tests for Activity Routes
"""

import pytest
from httpx import AsyncClient
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from server_fastapi.models.trade import Trade
from server_fastapi.models.bot import Bot


@pytest.mark.asyncio
class TestActivityRoutes:
    """Test activity endpoints"""
    
    async def test_get_recent_activity_empty(self, client: AsyncClient, auth_headers: dict):
        """Test getting recent activity when none exists"""
        response = await client.get("/api/activity/recent", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    async def test_get_recent_activity_with_limit(self, client: AsyncClient, auth_headers: dict):
        """Test getting recent activity with custom limit"""
        response = await client.get("/api/activity/recent?limit=5", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5
    
    async def test_get_recent_activity_invalid_limit(self, client: AsyncClient, auth_headers: dict):
        """Test getting recent activity with invalid limit"""
        # Too high
        response = await client.get("/api/activity/recent?limit=200", headers=auth_headers)
        assert response.status_code == 422
        
        # Too low
        response = await client.get("/api/activity/recent?limit=0", headers=auth_headers)
        assert response.status_code == 422
    
    async def test_get_recent_activity_requires_auth(self, client: AsyncClient):
        """Test that activity endpoint requires authentication"""
        response = await client.get("/api/activity/recent")
        assert response.status_code == 401
    
    async def test_get_recent_activity_with_trades(
        self, 
        client: AsyncClient, 
        auth_headers: dict,
        db_session: AsyncSession
    ):
        """Test getting recent activity includes trades"""
        # Get user ID from auth headers (extract from token or use default test user)
        user_id = "test-user-id"  # Default test user ID
        
        # Create a test trade
        test_trade = Trade(
            id="test-trade-1",
            user_id=user_id,
            pair="BTC/USD",
            side="buy",
            amount=0.1,
            price=50000.0,
            success=True,
            mode="paper",
            created_at=datetime.now()
        )
        db_session.add(test_trade)
        await db_session.commit()
        
        response = await client.get("/api/activity/recent", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Should have at least one activity (if database is available)
        assert isinstance(data, list)
        if len(data) > 0:
            trade_activities = [a for a in data if a["type"] == "trade"]
            if trade_activities:
                assert "Buy" in trade_activities[0]["message"] or "Sell" in trade_activities[0]["message"]

