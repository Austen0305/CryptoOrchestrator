"""
Tests for Health Check Endpoints
"""
import pytest
from httpx import AsyncClient
from fastapi import status
from unittest.mock import patch, AsyncMock
import time


@pytest.mark.asyncio
class TestHealthEndpoints:
    """Test health check endpoints"""
    
    async def test_health_endpoint_success(self, client: AsyncClient):
        """Test comprehensive health check endpoint"""
        response = await client.get("/api/health/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "timestamp" in data
        assert "version" in data
        assert "uptime_seconds" in data
        assert "checks" in data
        
        # Check component health
        checks = data["checks"]
        assert "database" in checks
        assert "redis" in checks
        assert "exchange_apis" in checks
        
        # Verify response has request ID
        assert "X-Request-ID" in response.headers
    
    async def test_health_endpoint_components(self, client: AsyncClient):
        """Test that health check includes all components"""
        response = await client.get("/api/health/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        checks = data["checks"]
        
        # Database check
        assert "status" in checks["database"]
        assert "message" in checks["database"]
        
        # Redis check (may be degraded if not configured)
        assert "status" in checks["redis"]
        
        # Exchange APIs check
        assert "status" in checks["exchange_apis"]
    
    async def test_readiness_probe_healthy(self, client: AsyncClient):
        """Test readiness probe when database is healthy"""
        response = await client.get("/api/health/ready")
        # Should be 200 if database is healthy, 503 if not
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "ready"
            assert "timestamp" in data
    
    async def test_liveness_probe(self, client: AsyncClient):
        """Test liveness probe"""
        response = await client.get("/api/health/live")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["status"] == "alive"
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["uptime_seconds"] >= 0
    
    async def test_startup_probe(self, client: AsyncClient):
        """Test startup probe"""
        response = await client.get("/api/health/startup")
        # Should be 200 if services are initialized, 503 if not
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "started"
            assert "timestamp" in data
    
    async def test_health_check_response_times(self, client: AsyncClient):
        """Test that health checks include response times"""
        response = await client.get("/api/health/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        checks = data["checks"]
        
        # Database should have response time
        if "response_time_ms" in checks["database"]:
            assert isinstance(checks["database"]["response_time_ms"], (int, float))
            assert checks["database"]["response_time_ms"] >= 0
        
        # Redis may have response time
        if "response_time_ms" in checks["redis"]:
            assert isinstance(checks["redis"]["response_time_ms"], (int, float))
    
    async def test_health_check_request_id(self, client: AsyncClient):
        """Test that health check responses include request ID"""
        response = await client.get("/api/health/")
        assert "X-Request-ID" in response.headers
        
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) == 36  # UUID format
        assert request_id.count("-") == 4  # UUID has 4 hyphens
    
    async def test_health_check_custom_request_id(self, client: AsyncClient):
        """Test that custom request ID from client is used"""
        custom_request_id = "custom-request-id-12345"
        response = await client.get(
            "/api/health/",
            headers={"X-Request-ID": custom_request_id}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["X-Request-ID"] == custom_request_id

