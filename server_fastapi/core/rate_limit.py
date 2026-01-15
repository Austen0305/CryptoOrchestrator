from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter

from server_fastapi.config.settings import get_settings

settings = get_settings()


@asynccontextmanager
async def rate_limit_lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Initialize Rate Limiter with Redis connection.
    Safe to use alongside other lifespan handlers.
    """
    # Create Redis connection
    # decoding_responses=True is crucial for some backends, but FastAPILimiter handles both
    r = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)

    # Initialize the Global Rate Limiter
    # Using defaults: Sliding Window (Token Bucket approximate)
    # If Redis Cell module were guaranteed, we would use a custom Lua script here.
    await FastAPILimiter.init(r)

    yield

    # Close Redis connection on shutdown
    await r.close()
