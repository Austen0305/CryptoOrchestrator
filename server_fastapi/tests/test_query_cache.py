"""
Tests for query result caching decorator
"""

from unittest.mock import AsyncMock, patch

import pytest

from server_fastapi.middleware.query_cache import cache_query_result


@pytest.mark.asyncio
class TestQueryCache:
    """Test query caching functionality"""

    async def test_cache_hit(self):
        """Test that cached results are returned"""
        call_count = 0

        @cache_query_result(ttl=60, key_prefix="test")
        async def test_function(param: str):
            nonlocal call_count
            call_count += 1
            return {"result": param, "count": call_count}

        # Mock cache service
        with patch("server_fastapi.middleware.query_cache.cache_service") as mock_cache:
            mock_cache.get = AsyncMock(return_value={"result": "cached", "count": 0})

            result = await test_function("test")
            assert result["result"] == "cached"
            assert call_count == 0  # Function not called due to cache hit

    async def test_cache_miss(self):
        """Test that function is called on cache miss"""
        call_count = 0

        @cache_query_result(ttl=60, key_prefix="test")
        async def test_function(param: str):
            nonlocal call_count
            call_count += 1
            return {"result": param, "count": call_count}

        # Mock cache service
        with patch("server_fastapi.middleware.query_cache.cache_service") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)  # Cache miss
            mock_cache.set = AsyncMock()

            result = await test_function("test")
            assert result["result"] == "test"
            assert call_count == 1  # Function called once
            mock_cache.set.assert_called_once()

    async def test_cache_without_redis(self):
        """Test that function works when Redis is unavailable"""
        call_count = 0

        @cache_query_result(ttl=60, key_prefix="test")
        async def test_function(param: str):
            nonlocal call_count
            call_count += 1
            return {"result": param, "count": call_count}

        # Mock Redis unavailable
        with patch("server_fastapi.middleware.query_cache.REDIS_AVAILABLE", False):
            result = await test_function("test")
            assert result["result"] == "test"
            assert call_count == 1  # Function called normally

    async def test_cache_key_includes_params(self):
        """Test that cache key includes function parameters"""

        @cache_query_result(ttl=60, key_prefix="test", include_params=True)
        async def test_function(param1: str, param2: int):
            return {"result": f"{param1}_{param2}"}

        # Mock cache service
        with patch("server_fastapi.middleware.query_cache.cache_service") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()

            await test_function("test1", 1)
            await test_function("test2", 2)

            # Should be called twice with different cache keys
            assert mock_cache.set.call_count == 2

    async def test_cache_ttl(self):
        """Test that TTL is respected"""

        @cache_query_result(ttl=300, key_prefix="test")
        async def test_function():
            return {"result": "test"}

        # Mock cache service
        with patch("server_fastapi.middleware.query_cache.cache_service") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()

            await test_function()

            # Verify TTL was passed to cache.set
            call_args = mock_cache.set.call_args
            assert call_args[1]["ttl"] == 300
