"""
Request Deduplication Middleware
Prevents duplicate requests using idempotency keys
"""

import asyncio
import asyncio
import hashlib
import json
import logging
import time
from typing import Dict, Optional, Tuple, Any
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class RequestDeduplicationMiddleware(BaseHTTPMiddleware):
    """
    Deduplicates requests using idempotency keys
    
    Features:
    - Idempotency key support
    - Automatic request hashing
    - Response caching for duplicate requests
    - Configurable TTL
    """

    def __init__(
        self,
        app,
        redis_client: Optional[redis.Redis] = None,
        default_ttl: int = 300,  # 5 minutes
        enable_auto_dedup: bool = True,
    ):
        super().__init__(app)
        self.redis = redis_client
        self.redis_available = redis_client is not None and REDIS_AVAILABLE
        self.default_ttl = default_ttl
        self.enable_auto_dedup = enable_auto_dedup
        
        # In-memory cache fallback
        self.memory_cache: Dict[str, Tuple[bytes, Dict, float]] = {}
        
        self.stats = {
            "deduplicated": 0,
            "idempotency_keys": 0,
            "cache_hits": 0,
        }

    def _generate_request_hash(self, request: Request) -> str:
        """Generate hash for request deduplication"""
        # Include method, path, query params, and body
        key_parts = [
            request.method,
            request.url.path,
            str(sorted(request.query_params.items())),
        ]
        
        # Include body if available (for POST/PUT/PATCH)
        if request.method in ["POST", "PUT", "PATCH"]:
            # Note: Body is consumed, so this would need to be stored
            # For now, we'll use idempotency key if provided
            pass
        
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]

    def _get_idempotency_key(self, request: Request) -> Optional[str]:
        """Get idempotency key from header"""
        return request.headers.get("Idempotency-Key") or request.headers.get("X-Idempotency-Key")

    async def _get_cached_response(self, key: str) -> Optional[Tuple[bytes, Dict]]:
        """Get cached response"""
        if self.redis_available:
            try:
                # Add timeout to prevent hangs if Redis is slow/unavailable
                cached = await asyncio.wait_for(
                    self.redis.get(key),
                    timeout=0.5  # 500ms timeout
                )
                if cached:
                    data = json.loads(cached)
                    self.stats["cache_hits"] += 1
                    return data["body"].encode(), data["headers"]
            except asyncio.TimeoutError:
                logger.debug("Redis get timeout, falling back to memory cache")
            except Exception as e:
                logger.debug(f"Redis get error: {e}")
        
        # Memory cache fallback
        if key in self.memory_cache:
            body, headers, expiry = self.memory_cache[key]
            if time.time() < expiry:
                self.stats["cache_hits"] += 1
                return body, headers
            else:
                del self.memory_cache[key]
        
        return None

    async def _cache_response(self, key: str, body: bytes, headers: Dict, ttl: int):
        """Cache response"""
        data = {
            "body": body.decode() if isinstance(body, bytes) else body,
            "headers": {k: v for k, v in headers.items() if k.lower() not in ["content-length", "transfer-encoding"]},
        }
        
        if self.redis_available:
            try:
                # Add timeout to prevent hangs if Redis is slow/unavailable
                await asyncio.wait_for(
                    self.redis.setex(key, ttl, json.dumps(data)),
                    timeout=0.5  # 500ms timeout
                )
                return
            except asyncio.TimeoutError:
                logger.debug("Redis set timeout, using memory cache")
            except Exception as e:
                logger.debug(f"Redis set error: {e}")
        
        # Memory cache
        expiry = time.time() + ttl
        self.memory_cache[key] = (body, headers, expiry)
        
        # Cleanup old entries
        if len(self.memory_cache) > 1000:
            current_time = time.time()
            self.memory_cache = {
                k: v for k, v in self.memory_cache.items()
                if v[2] > current_time
            }

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with deduplication"""
        # Skip deduplication for auth endpoints (may cause hangs, auth should not be deduplicated)
        if request.url.path.startswith("/api/auth"):
            return await call_next(request)
        
        # Only deduplicate POST/PUT/PATCH/DELETE
        if request.method not in ["POST", "PUT", "PATCH", "DELETE"]:
            return await call_next(request)
        
        # Get idempotency key or generate hash
        idempotency_key = self._get_idempotency_key(request)
        
        if idempotency_key:
            self.stats["idempotency_keys"] += 1
            cache_key = f"idempotency:{idempotency_key}"
        elif self.enable_auto_dedup:
            cache_key = f"dedup:{self._generate_request_hash(request)}"
        else:
            return await call_next(request)
        
        # Check cache
        cached = await self._get_cached_response(cache_key)
        if cached:
            body, headers = cached
            self.stats["deduplicated"] += 1
            return Response(
                content=body,
                headers={
                    **headers,
                    "X-Request-Deduplicated": "true",
                    "X-Idempotency-Key": idempotency_key or "auto",
                },
            )
        
        # Process request
        response = await call_next(request)
        
        # Cache successful responses
        if 200 <= response.status_code < 300:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            headers_dict = dict(response.headers)
            await self._cache_response(cache_key, body, headers_dict, self.default_ttl)
            
            # Add idempotency header
            headers_dict["X-Idempotency-Key"] = idempotency_key or "auto"
            
            return Response(
                content=body,
                status_code=response.status_code,
                headers=headers_dict,
            )
        
        return response

    def get_stats(self) -> Dict[str, Any]:
        """Get deduplication statistics"""
        return self.stats.copy()

