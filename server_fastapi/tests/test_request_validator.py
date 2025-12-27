"""
Tests for request validation middleware
"""

import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
class TestRequestValidator:
    """Test request validation middleware"""

    async def test_body_size_limit(self, client: AsyncClient, auth_headers: dict):
        """Test that oversized request bodies are rejected"""
        # Create a large body (exceeds 10MB default limit)
        large_data = "x" * (11 * 1024 * 1024)  # 11MB
        response = await client.post(
            "/api/bots/", json={"data": large_data}, headers=auth_headers
        )
        # Should either reject or handle gracefully
        assert response.status_code in [400, 413, 422]

    async def test_header_size_limit(self, client: AsyncClient):
        """Test that oversized headers are rejected"""
        # Create oversized header (exceeds 8KB default limit)
        large_header = "x" * (9 * 1024)  # 9KB
        response = await client.get(
            "/api/bots/", headers={"X-Custom-Header": large_header}
        )
        # Should either reject or handle gracefully
        assert response.status_code in [400, 431]

    async def test_path_traversal_protection(self, client: AsyncClient):
        """Test that path traversal attempts are blocked"""
        malicious_paths = [
            "/api/../../etc/passwd",
            "/api/..//etc/passwd",
            "/api/....//etc/passwd",
        ]

        for path in malicious_paths:
            response = await client.get(path)
            assert response.status_code in [400, 404]

    async def test_query_string_limit(self, client: AsyncClient):
        """Test that oversized query strings are rejected"""
        # Create oversized query string (exceeds 2KB limit)
        large_query = "&".join([f"param{i}=value{i}" for i in range(1000)])
        response = await client.get(f"/api/bots/?{large_query}")
        # Should either reject or handle gracefully
        assert response.status_code in [400, 414]

    async def test_content_type_validation(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that invalid content types are handled"""
        response = await client.post(
            "/api/bots/",
            content="invalid content",
            headers={**auth_headers, "Content-Type": "application/xml"},
        )
        # Should either reject or handle gracefully
        assert response.status_code in [200, 400, 415, 422]

    async def test_valid_request_passes(self, client: AsyncClient, auth_headers: dict):
        """Test that valid requests pass validation"""
        valid_bot = {
            "name": "Test Bot",
            "exchange": "kraken",
            "symbol": "BTC/USD",
            "strategy": "momentum",
        }
        response = await client.post("/api/bots/", json=valid_bot, headers=auth_headers)
        # Should not be rejected by validator (may fail for other reasons)
        assert response.status_code != 413  # Not "Payload Too Large"
        assert response.status_code != 431  # Not "Request Header Fields Too Large"
