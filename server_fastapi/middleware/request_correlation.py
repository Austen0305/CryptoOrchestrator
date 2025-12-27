"""
Request Correlation Middleware
Enhances request correlation with distributed tracing support
"""

import uuid
import logging
from typing import Dict, Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """
    Enhanced request correlation with:
    - Request ID propagation
    - Trace ID correlation
    - Span ID generation
    - Parent-child relationships
    - Distributed tracing support
    """

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with correlation IDs"""
        # Get or generate correlation IDs
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())
        span_id = request.headers.get("X-Span-ID") or str(uuid.uuid4())
        parent_span_id = request.headers.get("X-Parent-Span-ID")
        
        # Store in request state
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        request.state.span_id = span_id
        if parent_span_id:
            request.state.parent_span_id = parent_span_id
        
        # Process request
        response = await call_next(request)
        
        # Add correlation headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Span-ID"] = span_id
        
        if parent_span_id:
            response.headers["X-Parent-Span-ID"] = parent_span_id
        
        return response

