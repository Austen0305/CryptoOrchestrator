"""
Integration tests for cache management API endpoints
Tests cache analytics, versioning, and preloading
"""

import logging

import pytest
from httpx import AsyncClient

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio


class TestCacheManagementRoutes:
    """Integration tests for cache management API endpoints"""

    async def test_get_cache_analytics_admin(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test getting cache analytics with admin access"""
        response = await client.get(
            "/api/cache/analytics",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    async def test_get_cache_analytics_non_admin_forbidden(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Test getting cache analytics without admin access"""
        response = await client.get(
            "/api/cache/analytics",
            headers=auth_headers,
        )

        assert response.status_code == 403

    async def test_get_pattern_analytics(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test getting analytics for a specific pattern"""
        response = await client.get(
            "/api/cache/analytics/pattern/bots:*",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    async def test_get_cache_versions(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test getting cache versions"""
        response = await client.get(
            "/api/cache/versions",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    async def test_increment_cache_version(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test incrementing cache version"""
        response = await client.post(
            "/api/cache/versions/bots/increment",
            headers=admin_headers,
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert isinstance(data, dict)

    async def test_invalidate_all_cache(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test invalidating all cache"""
        response = await client.post(
            "/api/cache/versions/invalidate-all",
            headers=admin_headers,
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert "success" in data or "message" in data

    async def test_get_preloader_stats(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test getting preloader statistics"""
        response = await client.get(
            "/api/cache/preloader/stats",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    async def test_preload_frequent_keys(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test preloading frequent keys"""
        response = await client.post(
            "/api/cache/preloader/preload-frequent",
            headers=admin_headers,
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert isinstance(data, dict)

    async def test_get_cache_metrics(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test getting cache metrics"""
        response = await client.get(
            "/api/cache/metrics",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    async def test_reset_cache_analytics(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test resetting cache analytics"""
        response = await client.post(
            "/api/cache/analytics/reset",
            headers=admin_headers,
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert "success" in data or "message" in data
