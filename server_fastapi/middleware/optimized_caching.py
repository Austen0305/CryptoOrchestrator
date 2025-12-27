"""
Optimized Response Caching Middleware
High-performance caching with intelligent invalidation and compression
"""

import hashlib
import json
import logging
import time
from typing import Optional, Dict, Any, Callable, Set
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import gzip

logger = logging.getLogger(__name__)

# Try to import Redis
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class OptimizedCacheMiddleware(BaseHTTPMiddleware):
    """
    Optimized caching middleware with:
    - Fast cache key generation
    - Compressed cache storage
    - Smart invalidation
    - Cache statistics
    - Early returns for cache hits
    """

    def __init__(
        self,
        app,
        redis_client: Optional[Any] = None,
        default_ttl: int = 300,
        cache_config: Optional[Dict[str, int]] = None,
        compress_threshold: int = 1024,  # Compress responses > 1KB
        enable_stats: bool = True,
    ):
        super().__init__(app)
        self.redis_client = redis_client
        self.default_ttl = default_ttl
        self.cache_config = cache_config or self._get_optimized_cache_config()
        self.compress_threshold = compress_threshold
        self.enable_stats = enable_stats
        
        # In-memory cache with LRU-like behavior
        self.memory_cache: Dict[str, tuple[Any, float]] = {}
        self.cache_access_times: Dict[str, float] = {}
        self.max_memory_entries = 500  # Limit memory cache size
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "compressed": 0,
            "errors": 0,
        }
        
        self.use_redis = redis_client is not None and REDIS_AVAILABLE

    def _get_optimized_cache_config(self) -> Dict[str, int]:
        """Optimized cache configuration with longer TTLs for stable data"""
        return {
            # Market data - aggressive caching
            "/api/markets": 60,
            "/api/markets/ticker": 30,
            "/api/markets/orderbook": 15,
            "/api/markets/history": 300,
            # Portfolio - shorter cache for real-time data
            "/api/portfolio": 10,
            "/api/portfolio/summary": 15,
            "/api/portfolio/positions": 10,
            # Performance - moderate caching
            "/api/performance/summary": 30,
            "/api/performance/metrics": 60,
            "/api/performance/advanced": 120,
            # Historical - long cache
            "/api/performance/daily_pnl": 600,
            "/api/performance/drawdown_history": 600,
            # Bot data - short cache for active bots
            "/api/bots": 30,
            "/api/bots/active": 15,
            "/api/bots/inactive": 300,
            # Static data - very long cache
            "/api/exchanges": 3600,
            "/api/exchanges/supported": 3600,
            "/api/indicators": 1800,
        }

    def _should_cache(self, path: str, method: str) -> Optional[int]:
        """Fast path matching with early returns"""
        if method != "GET":
            return None
        
        # Fast exact match first
        if path in self.cache_config:
            return self.cache_config[path]
        
        # Then prefix matching
        for pattern, ttl in self.cache_config.items():
            if path.startswith(pattern):
                return ttl
        
        return None

    def _generate_cache_key(self, request: Request) -> str:
        """Optimized cache key generation using faster hashing"""
        # Use faster hash function for cache keys
        path = request.url.path
        query = str(sorted(request.query_params.items()))
        auth = request.headers.get("Authorization", "")[:20]
        
        # Fast key generation
        key_string = f"{path}|{query}|{auth}"
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]
        return f"cache:{key_hash}"

    def _compress_data(self, data: bytes) -> tuple[bytes, bool]:
        """Compress data if it exceeds threshold"""
        if len(data) < self.compress_threshold:
            return data, False
        
        try:
            compressed = gzip.compress(data, compresslevel=6)
            if len(compressed) < len(data) * 0.8:  # Only use if >20% reduction
                return compressed, True
        except Exception as e:
            logger.debug(f"Compression failed: {e}")
        
        return data, False

    def _decompress_data(self, data: bytes, is_compressed: bool) -> bytes:
        """Decompress data if needed"""
        if not is_compressed:
            return data
        
        try:
            return gzip.decompress(data)
        except Exception as e:
            logger.error(f"Decompression failed: {e}")
            return data

    async def _get_from_cache(self, key: str) -> Optional[tuple[bytes, Dict[str, str], bool]]:
        """Fast cache retrieval with compression support"""
        # Try Redis first (faster for distributed systems)
        if self.use_redis:
            try:
                cached = await self.redis_client.get(key)
                if cached:
                    data = json.loads(cached)
                    content = data["content"].encode() if isinstance(data["content"], str) else data["content"]
                    is_compressed = data.get("compressed", False)
                    content = self._decompress_data(content, is_compressed)
                    
                    if self.enable_stats:
                        self.stats["hits"] += 1
                    
                    return content, data["headers"], is_compressed
            except Exception as e:
                logger.debug(f"Redis get error: {e}")
                if self.enable_stats:
                    self.stats["errors"] += 1

        # Fallback to memory cache
        if key in self.memory_cache:
            content_data, expiry = self.memory_cache[key]
            if time.time() < expiry:
                self.cache_access_times[key] = time.time()
                
                if self.enable_stats:
                    self.stats["hits"] += 1
                
                content = content_data["content"]
                is_compressed = content_data.get("compressed", False)
                content = self._decompress_data(content, is_compressed)
                return content, content_data["headers"], is_compressed
            else:
                # Expired, remove
                del self.memory_cache[key]
                if key in self.cache_access_times:
                    del self.cache_access_times[key]

        if self.enable_stats:
            self.stats["misses"] += 1
        
        return None

    async def _set_in_cache(
        self, key: str, content: bytes, headers: Dict[str, str], ttl: int
    ):
        """Fast cache storage with compression"""
        # Compress if beneficial
        compressed_content, is_compressed = self._compress_data(content)
        
        if is_compressed and self.enable_stats:
            self.stats["compressed"] += 1
        
        data = {
            "content": compressed_content.decode() if isinstance(compressed_content, bytes) else compressed_content,
            "headers": headers,
            "compressed": is_compressed,
        }

        # Store in Redis
        if self.use_redis:
            try:
                await self.redis_client.setex(key, ttl, json.dumps(data))
                return
            except Exception as e:
                logger.debug(f"Redis set error: {e}")

        # Store in memory with LRU-like eviction
        expiry = time.time() + ttl
        self.memory_cache[key] = (data, expiry)
        self.cache_access_times[key] = time.time()
        
        # Evict least recently used if cache is full
        if len(self.memory_cache) > self.max_memory_entries:
            self._evict_lru()

    def _evict_lru(self):
        """Evict least recently used entries"""
        if not self.cache_access_times:
            # Fallback: remove oldest entries
            sorted_entries = sorted(
                self.memory_cache.items(),
                key=lambda x: x[1][1]  # Sort by expiry
            )
            # Remove 10% of entries
            to_remove = max(1, len(sorted_entries) // 10)
            for key, _ in sorted_entries[:to_remove]:
                del self.memory_cache[key]
            return
        
        # Remove least recently accessed
        sorted_by_access = sorted(
            self.cache_access_times.items(),
            key=lambda x: x[1]
        )
        to_remove = max(1, len(sorted_by_access) // 10)
        for key, _ in sorted_by_access[:to_remove]:
            if key in self.memory_cache:
                del self.memory_cache[key]
            del self.cache_access_times[key]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Optimized request processing with fast cache path"""
        # Fast path: check if cacheable
        ttl = self._should_cache(request.url.path, request.method)
        
        if ttl is None:
            return await call_next(request)

        # Generate cache key
        cache_key = self._generate_cache_key(request)

        # Try cache (fast path)
        cached = await self._get_from_cache(cache_key)
        if cached:
            content, headers, is_compressed = cached
            response_headers = {
                **headers,
                "X-Cache": "HIT",
                "Cache-Control": f"max-age={ttl}",
            }
            if is_compressed:
                response_headers["Content-Encoding"] = "gzip"
            
            return Response(content=content, headers=response_headers)

        # Cache miss - process request
        response = await call_next(request)

        # Only cache successful responses
        if 200 <= response.status_code < 300:
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            # Store in cache
            headers_dict = {
                k: v for k, v in response.headers.items()
                if k.lower() not in ["content-length", "transfer-encoding", "content-encoding"]
            }
            await self._set_in_cache(cache_key, body, headers_dict, ttl)

            # Return response
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

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0
        
        return {
            **self.stats,
            "hit_rate": hit_rate,
            "memory_entries": len(self.memory_cache),
        }

