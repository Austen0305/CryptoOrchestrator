import asyncio
import logging
import os
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class TimeoutMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce a per-request timeout.

    Uses `asyncio.wait_for` to bound the time spent handling a request.
    If the inner handler exceeds the timeout, a 504 response is returned.
    """

    def __init__(self, app, timeout_seconds: int = None):
        super().__init__(app)
        env_timeout = os.getenv("REQUEST_TIMEOUT")
        try:
            self.timeout_seconds = (
                int(env_timeout) if env_timeout is not None else timeout_seconds or 30
            )
        except Exception:
            self.timeout_seconds = timeout_seconds or 30

    async def dispatch(self, request: Request, call_next: Callable):
        try:
            # Bound the entire request handling including downstream middleware
            response = await asyncio.wait_for(
                call_next(request), timeout=self.timeout_seconds
            )
            return response
        except TimeoutError:
            logger.warning(
                f"Request timed out after {self.timeout_seconds}s: {request.method} {request.url.path}"
            )
            return JSONResponse(
                status_code=504,
                content={
                    "detail": "Request timed out. Please try again later.",
                    "timeout_seconds": self.timeout_seconds,
                },
            )
        except Exception:
            # Let other exceptions propagate to the app's exception handlers
            raise
