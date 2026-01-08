"""
Request ID Middleware with Trace Correlation
Adds unique request IDs and trace correlation to all requests for better observability
"""

import logging
import uuid
from collections.abc import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Try to import trace correlation service
try:
    from ..services.monitoring.trace_correlation import get_trace_correlation_service

    trace_correlation_available = True
except ImportError:
    trace_correlation_available = False


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add unique request IDs and trace correlation to all requests

    Adds:
    - X-Request-ID header to responses
    - X-Trace-ID and X-Span-ID for distributed tracing (if available)
    - request_id, trace_id, span_id to request.state for logging
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Extract or create trace context
        trace_id = None
        span_id = None

        if trace_correlation_available:
            try:
                trace_correlation = get_trace_correlation_service()

                # Extract trace context from headers
                trace_context = trace_correlation.extract_trace_context(
                    dict(request.headers)
                )

                if trace_context:
                    trace_id = trace_context.get("trace_id")
                    span_id = trace_context.get("span_id")
                else:
                    # Create new trace context
                    new_context = trace_correlation.create_trace_context()
                    trace_id = new_context["trace_id"]
                    span_id = new_context["span_id"]
                    trace_correlation.set_trace_context(
                        trace_id=trace_id, span_id=span_id, request_id=request_id
                    )
            except Exception as e:
                logger.debug(f"Trace correlation not available: {e}")
                # Fallback: generate simple trace ID
                trace_id = str(uuid.uuid4())
                span_id = str(uuid.uuid4())
        else:
            # Fallback: generate simple trace ID
            trace_id = str(uuid.uuid4())
            span_id = str(uuid.uuid4())

        # Store in request state for use in handlers and logging
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        request.state.span_id = span_id

        try:
            # Process request
            response = await call_next(request)
        except Exception:
            # Ensure responses from exceptions also carry request id
            raise
        finally:
            # Add correlation headers to response (even on exceptions)
            pass

        # Add correlation headers to response
        response.headers["X-Request-ID"] = request_id
        if trace_id:
            response.headers["X-Trace-ID"] = trace_id
        if span_id:
            response.headers["X-Span-ID"] = span_id

        return response
