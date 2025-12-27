"""
API Endpoint Testing Suite
Tests critical API endpoints to ensure they work correctly
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from server_fastapi.main import app


# Test client for synchronous tests
client = TestClient(app)


class TestHealthEndpoints:
    """Test health check and status endpoints"""

    def test_health_check(self):
        """Test basic health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_advanced_health_check(self):
        """Test advanced health check endpoint"""
        response = client.get("/api/health-advanced/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "components" in data

    def test_status_endpoint(self):
        """Test system status endpoint"""
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestAuthEndpoints:
    """Test authentication endpoints"""

    def test_register_endpoint_exists(self):
        """Test that registration endpoint exists"""
        response = client.post("/api/auth/register", json={})
        # Should return validation error (422) not 404
        assert response.status_code in [400, 422, 500]

    def test_login_endpoint_exists(self):
        """Test that login endpoint exists"""
        response = client.post("/api/auth/login", json={})
        # Should return validation error (422) not 404
        assert response.status_code in [400, 422, 500]

    def test_refresh_token_endpoint(self):
        """Test token refresh endpoint"""
        response = client.post("/api/auth/refresh", json={})
        # Should return error without valid token
        assert response.status_code in [400, 401, 422]


class TestMarketEndpoints:
    """Test market data endpoints"""

    def test_get_tickers(self):
        """Test get tickers endpoint"""
        response = client.get("/api/markets/tickers")
        assert response.status_code in [200, 401, 500]
        # If authenticated, should return 200 with ticker data
        # If not authenticated, should return 401

    def test_get_market_summary(self):
        """Test market summary endpoint"""
        response = client.get("/api/markets/summary")
        assert response.status_code in [200, 401, 500]


class TestPortfolioEndpoints:
    """Test portfolio endpoints"""

    def test_get_portfolio_endpoint_exists(self):
        """Test portfolio endpoint exists"""
        response = client.get("/api/portfolio?mode=paper")
        # Should return 401 without auth or 200 with auth
        assert response.status_code in [200, 401, 403]


class TestBotEndpoints:
    """Test bot management endpoints"""

    def test_get_bots_endpoint_exists(self):
        """Test get bots endpoint exists"""
        response = client.get("/api/bots")
        # Should return 401 without auth or 200 with auth
        assert response.status_code in [200, 401, 403]


class TestStrategyEndpoints:
    """Test strategy endpoints"""

    def test_get_strategies_endpoint_exists(self):
        """Test get strategies endpoint exists"""
        response = client.get("/api/strategies")
        assert response.status_code in [200, 401, 403]


class TestAnalyticsEndpoints:
    """Test analytics endpoints"""

    def test_get_analytics_endpoint_exists(self):
        """Test analytics endpoint exists"""
        response = client.get("/api/analytics")
        assert response.status_code in [200, 401, 403]


class TestRiskManagementEndpoints:
    """Test risk management endpoints"""

    def test_get_risk_metrics_endpoint_exists(self):
        """Test risk metrics endpoint exists"""
        response = client.get("/api/risk-management/metrics")
        assert response.status_code in [200, 401, 403]

    def test_get_risk_alerts_endpoint_exists(self):
        """Test risk alerts endpoint exists"""
        response = client.get("/api/risk-management/alerts")
        assert response.status_code in [200, 401, 403]


@pytest.mark.asyncio
class TestAsyncEndpoints:
    """Test async endpoints using AsyncClient"""

    async def test_async_health_check(self):
        """Test async health check"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/health")
            assert response.status_code == 200


# Pytest configuration
@pytest.fixture(scope="module")
def test_app():
    """Provide test app instance"""
    return app


@pytest.fixture(scope="module")
def test_client():
    """Provide test client instance"""
    return client
