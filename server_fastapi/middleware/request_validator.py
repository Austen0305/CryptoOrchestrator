"""
Request Validation Middleware
Validates and sanitizes incoming requests for security and data integrity
Consolidated from request_validation.py and request_validator.py
"""

import json
import logging
import re
from collections.abc import Callable

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestValidatorMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request validation
    Validates headers, body size, content type, and sanitizes inputs
    Includes SQL injection and XSS protection
    """

    # Patterns for potentially dangerous content (from request_validation.py)
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|;|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
    ]

    def __init__(
        self,
        app: ASGIApp,
        max_body_size: int = 10 * 1024 * 1024,  # 10MB default
        max_header_size: int = 8192,  # 8KB default
        allowed_content_types: list | None = None,
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
        # Skip validation for certain paths
        skip_paths = ["/docs", "/openapi.json", "/redoc", "/health", "/healthz"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)

        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_body_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Request body too large. Maximum size: {self.max_body_size / 1024 / 1024}MB",
                    )
            except ValueError:
                pass  # Invalid content-length header, let it pass

        # Validate content type for POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not any(ct in content_type for ct in self.allowed_content_types):
                # Allow empty content type for some endpoints
                if content_type and not content_type.startswith("multipart/"):
                    logger.warning(
                        f"Invalid content type: {content_type} for {request.url.path}"
                    )

        # Validate headers
        for header_name, header_value in request.headers.items():
            if len(header_value) > self.max_header_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Header {header_name} too long",
                )

        # Validate query parameters for SQL injection and XSS
        query_params = dict(request.query_params)
        for key, value in query_params.items():
            if self._contains_sql_injection(value) or self._contains_xss(value):
                logger.warning(
                    f"Potential security threat in query param {key}: {value}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid request parameters",
                )

        # Validate query string length
        query_string = str(request.url.query)
        if len(query_string) > 2048:  # 2KB limit for query string
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Query string too long"
            )

        # Sanitize path (basic check for path traversal)
        path = request.url.path
        if ".." in path or "//" in path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid path"
            )

        # Validate and sanitize request body for POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    # Parse JSON if content-type is JSON
                    content_type = request.headers.get("content-type", "")
                    if "application/json" in content_type:
                        try:
                            body_json = json.loads(body.decode())
                            # Recursively validate and sanitize
                            sanitized = self._sanitize_data(body_json)

                            # Replace request body with sanitized version
                            request._body = json.dumps(sanitized).encode()
                        except json.JSONDecodeError:
                            pass  # Not JSON, skip validation
            except Exception as e:
                logger.warning(f"Request body validation error: {e}")

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
                detail="Request validation failed",
            )

    def _sanitize_data(self, data):
        """Recursively sanitize data structures"""
        if isinstance(data, dict):
            return {k: self._sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        elif isinstance(data, str):
            # Remove potentially dangerous content
            sanitized = data
            for pattern in self.SQL_INJECTION_PATTERNS + self.XSS_PATTERNS:
                sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
            return sanitized.strip()
        else:
            return data

    def _contains_sql_injection(self, value: str) -> bool:
        """Check if value contains SQL injection patterns"""
        if not isinstance(value, str):
            return False
        value_upper = value.upper()
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                return True
        return False

    def _contains_xss(self, value: str) -> bool:
        """Check if value contains XSS patterns"""
        if not isinstance(value, str):
            return False
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False


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
            detail="JSON structure too deeply nested",
        )

    if isinstance(body, dict):
        return {
            sanitize_string(str(k), 100): (
                validate_json_body(v, max_depth, current_depth + 1)
                if isinstance(v, (dict, list))
                else sanitize_string(str(v), 10000)
            )
            for k, v in body.items()
        }
    elif isinstance(body, list):
        return [
            (
                validate_json_body(item, max_depth, current_depth + 1)
                if isinstance(item, (dict, list))
                else sanitize_string(str(item), 10000)
            )
            for item in body[:100]  # Limit array size
        ]
    else:
        return sanitize_string(str(body), 10000)
