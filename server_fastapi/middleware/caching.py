"""
Request caching middleware for FastAPI application.

Implements intelligent caching for high-traffic endpoints to improve
performance and reduce database load.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import MutableHeaders
from typing import Optional, Dict, Any, Callable
import hashlib
import json
import logging
import time

logger = logging.getLogger(__name__)

# Try to import Redis, fall back to in-memory cache
try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory cache")


class CacheMiddleware(BaseHTTPMiddleware):
    """Middleware to cache GET requests for configured endpoints."""

    def __init__(
        self,
        app,
        redis_client: Optional[Any] = None,
        default_ttl: int = 300,  # 5 minutes default
        cache_config: Optional[Dict[str, int]] = None,
    ):
        """
        Initialize cache middleware.

        Args:
            app: The FastAPI application
            redis_client: Redis client instance (optional)
            default_ttl: Default cache TTL in seconds
            cache_config: Dictionary mapping path patterns to TTL values
        """
        super().__init__(app)
        self.redis_client = redis_client
        self.default_ttl = default_ttl
        self.cache_config = cache_config or self._get_default_cache_config()

        # In-memory cache fallback
        self.memory_cache: Dict[str, tuple[Any, float]] = {}
        self.use_redis = redis_client is not None and REDIS_AVAILABLE

    def _get_default_cache_config(self) -> Dict[str, int]:
        """
        Get default cache configuration for common endpoints.

        Returns:
            Dictionary mapping endpoint patterns to TTL values
        """
        return {
            # Market data - cache for 5 minutes
            "/api/markets": 300,
            "/api/markets/ticker": 60,
            "/api/markets/orderbook": 30,
            # Portfolio data - cache for 30 seconds
            "/api/portfolio": 30,
            "/api/portfolio/summary": 30,
            "/api/portfolio/positions": 30,
            # Performance data - cache for 1 minute
            "/api/performance/summary": 60,
            "/api/performance/metrics": 60,
            "/api/performance/advanced": 120,
            # Historical data - cache for 15 minutes
            "/api/performance/daily_pnl": 900,
            "/api/performance/drawdown_history": 900,
            # Bot data - cache for 1 minute
            "/api/bots": 60,
            "/api/bots/active": 30,
            # Favorites - cache for 2 minutes
            "/api/favorites": 120,
            "/api/favorites/summary": 120,
            # Static data - cache for 1 hour
            "/api/exchanges": 3600,
            "/api/exchanges/supported": 3600,
        }

    def _should_cache(self, path: str, method: str) -> Optional[int]:
        """
        Determine if a request should be cached and return TTL.

        Args:
            path: Request path
            method: HTTP method

        Returns:
            TTL in seconds if should cache, None otherwise
        """
        if method != "GET":
            return None

        for pattern, ttl in self.cache_config.items():
            if path.startswith(pattern):
                return ttl

        return None

    def _generate_cache_key(self, request: Request) -> str:
        """
        Generate a unique cache key for the request.

        Args:
            request: The FastAPI request

        Returns:
            Cache key string
        """
        key_parts = [
            request.url.path,
            str(sorted(request.query_params.items())),
            request.headers.get("Authorization", "")[:20],  # Include user context
        ]
        key_string = "|".join(key_parts)
        return f"cache:{hashlib.md5(key_string.encode()).hexdigest()}"

    async def _get_from_cache(self, key: str) -> Optional[tuple[bytes, Dict[str, str]]]:
        """
        Retrieve value from cache (Redis or memory).

        Args:
            key: Cache key

        Returns:
            Tuple of (content, headers) if found, None otherwise
        """
        if self.use_redis:
            try:
                cached = await self.redis_client.get(key)
                if cached:
                    data = json.loads(cached)
                    logger.debug(f"Cache hit (Redis): {key}")
                    return data["content"].encode(), data["headers"]
            except Exception as e:
                logger.error(f"Redis get error: {e}")

        # Fallback to memory cache
        if key in self.memory_cache:
            content, expiry = self.memory_cache[key]
            if time.time() < expiry:
                logger.debug(f"Cache hit (memory): {key}")
                return content["content"].encode(), content["headers"]
            else:
                # Expired, remove from cache
                del self.memory_cache[key]

        return None

    async def _set_in_cache(
        self, key: str, content: bytes, headers: Dict[str, str], ttl: int
    ):
        """
        Store value in cache (Redis or memory).

        Args:
            key: Cache key
            content: Response content
            headers: Response headers
            ttl: Time to live in seconds
        """
        data = {"content": content.decode(), "headers": headers}

        if self.use_redis:
            try:
                await self.redis_client.setex(key, ttl, json.dumps(data))
                logger.debug(f"Cached in Redis: {key} (TTL: {ttl}s)")
                return
            except Exception as e:
                logger.error(f"Redis set error: {e}")

        # Fallback to memory cache
        expiry = time.time() + ttl
        self.memory_cache[key] = (data, expiry)
        logger.debug(f"Cached in memory: {key} (TTL: {ttl}s)")

        # Clean up old entries if memory cache is getting large
        if len(self.memory_cache) > 1000:
            self._cleanup_memory_cache()

    def _cleanup_memory_cache(self):
        """Remove expired entries from memory cache."""
        current_time = time.time()
        expired_keys = [
            key
            for key, (_, expiry) in self.memory_cache.items()
            if current_time >= expiry
        ]
        for key in expired_keys:
            del self.memory_cache[key]
        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with caching logic.

        Args:
            request: The request
            call_next: Next middleware/route handler

        Returns:
            Response object
        """
        # Check if this request should be cached
        ttl = self._should_cache(request.url.path, request.method)

        if ttl is None:
            # Not cacheable, pass through
            return await call_next(request)

        # Generate cache key
        cache_key = self._generate_cache_key(request)

        # Try to get from cache
        cached_response = await self._get_from_cache(cache_key)
        if cached_response:
            content, headers = cached_response
            return Response(
                content=content,
                headers={
                    **headers,
                    "X-Cache": "HIT",
                    "Cache-Control": f"max-age={ttl}",
                },
            )

        # Cache miss, call the actual endpoint
        response = await call_next(request)

        # Only cache successful responses
        if 200 <= response.status_code < 300:
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            # Store in cache
            headers_dict = {
                key: value
                for key, value in response.headers.items()
                if key.lower() not in ["content-length", "transfer-encoding"]
            }
            await self._set_in_cache(cache_key, body, headers_dict, ttl)

            # Create new response with cached body
            return Response(
                content=body,
                status_code=response.status_code,
                headers={
                    **headers_dict,
                    "X-Cache": "MISS",
                    "Cache-Control": f"max-age={ttl}",
                },
            )

        return response


async def cache_invalidate(redis_client: Optional[Any], pattern: str):
    """
    Invalidate cache entries matching a pattern.

    Args:
        redis_client: Redis client instance
        pattern: Key pattern to match (e.g., "cache:/api/bots*")
    """
    if redis_client and REDIS_AVAILABLE:
        try:
            keys = await redis_client.keys(pattern)
            if keys:
                await redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries matching {pattern}")
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
