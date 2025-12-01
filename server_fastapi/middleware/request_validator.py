"""
Request Validation Middleware
Validates and sanitizes incoming requests for security and data integrity
"""
import logging
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import json
import re

logger = logging.getLogger(__name__)


class RequestValidatorMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request validation
    Validates headers, body size, content type, and sanitizes inputs
    """
    
    def __init__(
        self,
        app: ASGIApp,
        max_body_size: int = 10 * 1024 * 1024,  # 10MB default
        max_header_size: int = 8192,  # 8KB default
        allowed_content_types: Optional[list] = None,
    ):
        super().__init__(app)
        self.max_body_size = max_body_size
        self.max_header_size = max_header_size
        self.allowed_content_types = allowed_content_types or [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_body_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Request body too large. Maximum size: {self.max_body_size / 1024 / 1024}MB"
                    )
            except ValueError:
                pass  # Invalid content-length header, let it pass
        
        # Validate content type for POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not any(ct in content_type for ct in self.allowed_content_types):
                # Allow empty content type for some endpoints
                if content_type and not content_type.startswith("multipart/"):
                    logger.warning(f"Invalid content type: {content_type} for {request.url.path}")
        
        # Validate headers
        for header_name, header_value in request.headers.items():
            if len(header_value) > self.max_header_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Header {header_name} too long"
                )
        
        # Validate query parameters
        query_string = str(request.url.query)
        if len(query_string) > 2048:  # 2KB limit for query string
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query string too long"
            )
        
        # Sanitize path (basic check for path traversal)
        path = request.url.path
        if ".." in path or "//" in path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid path"
            )
        
        # Continue with request
        try:
            response = await call_next(request)
            return response
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Request validation error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Request validation failed"
            )


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize a string value.
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return str(value)
    
    # Remove null bytes
    value = value.replace("\x00", "")
    
    # Truncate if too long
    if len(value) > max_length:
        value = value[:max_length]
    
    # Remove potentially dangerous characters (basic)
    value = re.sub(r'[<>"\']', "", value)
    
    return value.strip()


def validate_json_body(body: dict, max_depth: int = 10, current_depth: int = 0) -> dict:
    """
    Validate and sanitize JSON body.
    
    Args:
        body: JSON body to validate
        max_depth: Maximum nesting depth
        current_depth: Current nesting depth
    
    Returns:
        Validated and sanitized body
    """
    if current_depth > max_depth:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="JSON structure too deeply nested"
        )
    
    if isinstance(body, dict):
        return {
            sanitize_string(str(k), 100): validate_json_body(v, max_depth, current_depth + 1)
            if isinstance(v, (dict, list)) else sanitize_string(str(v), 10000)
            for k, v in body.items()
        }
    elif isinstance(body, list):
        return [
            validate_json_body(item, max_depth, current_depth + 1)
            if isinstance(item, (dict, list)) else sanitize_string(str(item), 10000)
            for item in body[:100]  # Limit array size
        ]
    else:
        return sanitize_string(str(body), 10000)

