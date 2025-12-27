from typing import Callable
from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

from server_fastapi.services.logging_config import REQUEST_ID_CTX
import uuid


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Bind request-scoped logging context (request_id, trace_id) into contextvars.

    This ensures the logging formatter can include `request_id` automatically
    without needing to pass `extra` through every logger call.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Use existing request.state.request_id if present, else fallback to header or None
        request_id = getattr(request.state, "request_id", None)

        if request_id is None:
            request_id = request.headers.get("X-Request-ID")

        if request_id is None:
            # Generate a stable uuid for this request if nothing provided
            request_id = str(uuid.uuid4())

        # Make request_id available to formatters via ContextVar
        token = REQUEST_ID_CTX.set(request_id)

        # Ensure downstream middleware/handlers can access the same id
        try:
            setattr(request.state, "request_id", request_id)
        except Exception:
            # best-effort; not critical
            pass

        try:
            response = await call_next(request)
            return response
        finally:
            REQUEST_ID_CTX.reset(token)
