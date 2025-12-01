"""
Request ID Middleware
Adds unique request IDs to all requests for better traceability
"""
import uuid
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add unique request IDs to all requests
    
    Adds:
    - X-Request-ID header to responses
    - request_id to request.state for logging
    """
    
    async def dispatch(self, request: Request, call_next):
        # Get request ID from header or generate new one
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Store in request state for use in handlers
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
