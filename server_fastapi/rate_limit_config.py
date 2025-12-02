"""Rate limiting configuration with resilient fallback.

Primary storage attempts Redis. If Redis is unavailable (tests, dev env
without service), we fall back to in-memory storage to avoid raising
connection errors during request handling. This ensures integration tests
run green without requiring external infrastructure while preserving
production behavior when Redis is present.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
import os

try:  # Attempt Redis usage, fall back gracefully
    from redis import Redis  # type: ignore
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    storage_uri = REDIS_URL
    try:
        _redis_client = Redis.from_url(REDIS_URL)
        _redis_client.ping()  # Validate connectivity
    except Exception:
        _redis_client = None
        storage_uri = "memory://"  # Fallback for tests / offline
except Exception:  # Redis import failure
    _redis_client = None
    storage_uri = "memory://"

# Base limiter (no default limits so routers can specify decorators)
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=storage_uri,
    strategy="fixed-window",
)

# Specialized limiters; keep same fallback storage
auth_limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=storage_uri,
    default_limits=["5/minute"],
)

api_limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=storage_uri,
    default_limits=["100/minute"],
)

def get_limiter_for_auth():  # Helper accessor for auth endpoints
    return auth_limiter

def get_limiter_for_api():  # Helper accessor for general API endpoints
    return api_limiter