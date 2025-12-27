"""
Integration tests for background jobs API endpoints
Tests Celery task monitoring, batching, and rate limiting
"""

import pytest
from httpx import AsyncClient
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio


class TestBackgroundJobsRoutes:
    """Integration tests for background jobs API endpoints"""

    async def test_get_job_status(
        self, client: AsyncClient, admin_headers: Dict[str, str]
    ):
        """Test getting job status"""
        # Try with a test job ID (may not exist)
        response = await client.get(
            "/api/background-jobs/status",
            headers=admin_headers,
            params={"job_id": "test-job-id"},
        )

        # May return 200 with status or 404 if job doesn't exist
        assert response.status_code in [200, 404]

    async def test_get_job_status_non_admin_forbidden(
        self, client: AsyncClient, auth_headers: Dict[str, str]
    ):
        """Test getting job status without admin access"""
        response = await client.get(
            "/api/background-jobs/status",
            headers=auth_headers,
            params={"job_id": "test-job-id"},
        )

        assert response.status_code == 403

    async def test_get_tasks(self, client: AsyncClient, admin_headers: Dict[str, str]):
        """Test getting task list"""
        response = await client.get(
            "/api/background-jobs/tasks",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    async def test_get_job_stats(
        self, client: AsyncClient, admin_headers: Dict[str, str]
    ):
        """Test getting job statistics"""
        response = await client.get(
            "/api/background-jobs/stats",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    async def test_get_queue_depth(
        self, client: AsyncClient, admin_headers: Dict[str, str]
    ):
        """Test getting queue depth"""
        response = await client.get(
            "/api/background-jobs/queue-depth",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    async def test_get_batching_stats(
        self, client: AsyncClient, admin_headers: Dict[str, str]
    ):
        """Test getting batching statistics"""
        response = await client.get(
            "/api/background-jobs/batching/stats",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    async def test_flush_batching(
        self, client: AsyncClient, admin_headers: Dict[str, str]
    ):
        """Test flushing batched tasks"""
        response = await client.post(
            "/api/background-jobs/batching/flush",
            headers=admin_headers,
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert isinstance(data, dict)

    async def test_get_rate_limits(
        self, client: AsyncClient, admin_headers: Dict[str, str]
    ):
        """Test getting rate limits"""
        response = await client.get(
            "/api/background-jobs/rate-limits",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    async def test_reset_rate_limit(
        self, client: AsyncClient, admin_headers: Dict[str, str]
    ):
        """Test resetting rate limit for a task"""
        response = await client.post(
            "/api/background-jobs/rate-limits/test_task/reset",
            headers=admin_headers,
        )

        assert response.status_code in [200, 201, 404]
        if response.status_code in [200, 201]:
            data = response.json()
            assert isinstance(data, dict)
