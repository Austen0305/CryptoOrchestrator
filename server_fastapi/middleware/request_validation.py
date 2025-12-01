"""
Request Validation Middleware
Validates and sanitizes incoming requests
"""

import logging
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import json
import re

logger = logging.getLogger(__name__)


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate and sanitize requests"""
    
    # Patterns for potentially dangerous content
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
    
    async def dispatch(self, request: Request, call_next):
        # Skip validation for certain paths
        skip_paths = ["/docs", "/openapi.json", "/redoc", "/health"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        # Validate request body for POST/PUT/PATCH
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
                logger.warning(f"Request validation error: {e}")
        
        # Validate query parameters
        query_params = dict(request.query_params)
        for key, value in query_params.items():
            if self._contains_sql_injection(value) or self._contains_xss(value):
                logger.warning(f"Potential security threat in query param {key}: {value}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid request parameters"
                )
        
        response = await call_next(request)
        return response
    
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

