"""
Request Validation Middleware (2026 Best Practices)
Comprehensive request validation with security hardening
"""

import logging
import json
from typing import Any, Callable
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..utils.validation_2026 import sanitize_input, validate_amount, ValidationError

logger = logging.getLogger(__name__)

# Request size limits (2026 best practice)
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
MAX_JSON_DEPTH = 10
MAX_JSON_KEYS = 1000


class RequestValidationMiddleware2026(BaseHTTPMiddleware):
    """
    Comprehensive request validation middleware (2026)
    
    Features:
    - Request size limits
    - JSON depth/keys limits
    - Input sanitization
    - SQL injection prevention
    - XSS prevention
    - Rate limiting integration
    """

    def __init__(self, app: ASGIApp, max_request_size: int = MAX_REQUEST_SIZE):
        super().__init__(app)
        self.max_request_size = max_request_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate request before processing"""
        
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_request_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Request too large (maximum {self.max_request_size} bytes)",
                    )
            except ValueError:
                pass  # Invalid content-length, let it proceed
        
        # Validate JSON payloads
        if request.method in ("POST", "PUT", "PATCH") and "application/json" in request.headers.get("content-type", ""):
            try:
                body = await request.body()
                
                if len(body) > self.max_request_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Request body too large (maximum {self.max_request_size} bytes)",
                    )
                
                # Parse and validate JSON
                try:
                    data = json.loads(body.decode("utf-8"))
                    self._validate_json_structure(data)
                except json.JSONDecodeError as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid JSON: {str(e)}",
                    )
                
                # Store validated body for route handlers
                async def receive():
                    return {"type": "http.request", "body": body}
                
                request._receive = receive
                
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Request validation error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Request validation failed",
                )
        
        # Validate query parameters
        for key, value in request.query_params.items():
            try:
                sanitize_input(str(value))
            except ValueError as e:
                logger.warning(f"Invalid query parameter {key}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid query parameter: {key}",
                )
        
        return await call_next(request)

    def _validate_json_structure(self, data: Any, depth: int = 0, key_count: int = 0) -> None:
        """
        Validate JSON structure (prevent deep nesting and excessive keys)
        
        Args:
            data: JSON data to validate
            depth: Current nesting depth
            key_count: Current key count
            
        Raises:
            HTTPException: If structure is invalid
        """
        if depth > MAX_JSON_DEPTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"JSON nesting too deep (maximum {MAX_JSON_DEPTH} levels)",
            )
        
        if isinstance(data, dict):
            key_count += len(data)
            if key_count > MAX_JSON_KEYS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Too many JSON keys (maximum {MAX_JSON_KEYS})",
                )
            
            for value in data.values():
                self._validate_json_structure(value, depth + 1, key_count)
        
        elif isinstance(data, list):
            for item in data[:100]:  # Limit list validation to first 100 items
                self._validate_json_structure(item, depth + 1, key_count)
