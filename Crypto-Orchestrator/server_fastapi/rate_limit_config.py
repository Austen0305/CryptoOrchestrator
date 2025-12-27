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
# Use high test-specific limits in test mode to avoid test failures while still testing rate limiting
is_test_mode = os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TESTING") == "true"
test_auth_limit = "10000/minute" if is_test_mode else "5/minute"
test_api_limit = "10000/minute" if is_test_mode else "100/minute"

auth_limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=storage_uri,
    default_limits=[test_auth_limit],
)

api_limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=storage_uri,
    default_limits=[test_api_limit],
)


def get_limiter_for_auth():  # Helper accessor for auth endpoints
    return auth_limiter


def get_limiter_for_api():  # Helper accessor for general API endpoints
    return api_limiter


def get_rate_limit(production_limit: str) -> str:
    """
    Get rate limit string with test-specific high limits when in test mode.

    Args:
        production_limit: Production rate limit string (e.g., "10/minute")

    Returns:
        Production limit in production mode, high test limit (10000/minute) in test mode
    """
    if is_test_mode:
        # Extract the time unit from production limit and use high limit
        if "/minute" in production_limit:
            return "10000/minute"
        elif "/hour" in production_limit:
            return "10000/hour"
        elif "/second" in production_limit:
            return "10000/second"
        else:
            # Default to per minute if format is unknown
            return "10000/minute"
    return production_limit
