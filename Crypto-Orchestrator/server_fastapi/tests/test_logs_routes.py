"""
Integration tests for logs API endpoints
Tests log search, statistics, and tail functionality
"""

import pytest
from httpx import AsyncClient
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio


class TestLogsRoutes:
    """Integration tests for logs API endpoints"""

    async def test_search_logs_admin_success(
        self, client: AsyncClient, admin_headers: Dict[str, str]
    ):
        """Test log search with admin access"""
        response = await client.get(
            "/api/logs/search",
            headers=admin_headers,
            params={"query": "test", "limit": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        assert isinstance(data["results"], list)

    async def test_search_logs_non_admin_forbidden(
        self, client: AsyncClient, auth_headers: Dict[str, str]
    ):
        """Test log search without admin access"""
        response = await client.get(
            "/api/logs/search",
            headers=auth_headers,
            params={"query": "test"},
        )

        assert response.status_code == 403

    async def test_search_logs_unauthenticated(self, client: AsyncClient):
        """Test log search without authentication"""
        response = await client.get("/api/logs/search", params={"query": "test"})

        assert response.status_code in [401, 403]

    async def test_search_logs_with_filters(
        self, client: AsyncClient, admin_headers: Dict[str, str]
    ):
        """Test log search with various filters"""
        response = await client.get(
            "/api/logs/search",
            headers=admin_headers,
            params={
                "query": "error",
                "level": "ERROR",
                "limit": 20,
                "offset": 0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    async def test_get_log_statistics(
        self, client: AsyncClient, admin_headers: Dict[str, str]
    ):
        """Test getting log statistics"""
        response = await client.get(
            "/api/logs/statistics",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    async def test_tail_logs(self, client: AsyncClient, admin_headers: Dict[str, str]):
        """Test tailing logs"""
        response = await client.get(
            "/api/logs/tail",
            headers=admin_headers,
            params={"lines": 50, "log_file": "app"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "lines" in data
        assert isinstance(data["lines"], list)
