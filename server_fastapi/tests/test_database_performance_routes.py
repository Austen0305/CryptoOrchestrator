"""
Integration tests for database performance API endpoints
Tests pool metrics, health checks, and index optimization
"""

import logging

import pytest
from httpx import AsyncClient

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio


class TestDatabasePerformanceRoutes:
    """Integration tests for database performance API endpoints"""

    async def test_get_pool_metrics_admin(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test getting pool metrics with admin access"""
        response = await client.get(
            "/api/database/pool/metrics",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    async def test_get_pool_metrics_non_admin_forbidden(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Test getting pool metrics without admin access"""
        response = await client.get(
            "/api/database/pool/metrics",
            headers=auth_headers,
        )

        assert response.status_code == 403

    async def test_get_pool_health(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test getting pool health status"""
        response = await client.get(
            "/api/database/pool/health",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "status" in data or "health" in data

    async def test_get_pool_history(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test getting pool history"""
        response = await client.get(
            "/api/database/pool/history",
            headers=admin_headers,
            params={"hours": 24},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    async def test_get_read_replicas_health(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test getting read replicas health"""
        response = await client.get(
            "/api/database/read-replicas/health",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    async def test_get_index_usage(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test getting index usage statistics"""
        response = await client.get(
            "/api/database/indexes/usage",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    async def test_get_unused_indexes(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test getting unused indexes"""
        response = await client.get(
            "/api/database/indexes/unused",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_missing_indexes(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test getting missing indexes recommendations"""
        response = await client.get(
            "/api/database/indexes/missing",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
