"""
Comprehensive Request/Response Logging Middleware
Provides detailed logging of requests and responses for debugging and auditing
"""

import logging
import json
import time
from typing import Dict, Any, Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from datetime import datetime

logger = logging.getLogger(__name__)


class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive request/response logging
    
    Features:
    - Request logging (method, path, headers, body)
    - Response logging (status, headers, body)
    - Performance timing
    - Error logging
    - Configurable log levels
    - Sensitive data filtering
    """

    def __init__(
        self,
        app,
        log_request_body: bool = False,
        log_response_body: bool = False,
        log_headers: bool = True,
        sensitive_headers: Optional[list] = None,
        sensitive_fields: Optional[list] = None,
    ):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.log_headers = log_headers
        self.sensitive_headers = sensitive_headers or [
            "authorization",
            "cookie",
            "x-api-key",
            "x-auth-token",
        ]
        self.sensitive_fields = sensitive_fields or [
            "password",
            "secret",
            "token",
            "api_key",
            "private_key",
        ]

    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Sanitize sensitive headers"""
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        return sanitized

    def _sanitize_body(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive fields in body"""
        if not isinstance(body, dict):
            return body

        sanitized = {}
        for key, value in body.items():
            if any(sensitive in key.lower() for sensitive in self.sensitive_fields):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_body(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_body(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with comprehensive logging"""
        start_time = time.perf_counter()

        # Log request
        request_id = getattr(request.state, "request_id", "unknown")
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client": request.client.host if request.client else "unknown",
        }

        if self.log_headers:
            log_data["headers"] = self._sanitize_headers(dict(request.headers))

        # Log request body if enabled
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    body_data = json.loads(body.decode())
                    log_data["body"] = self._sanitize_body(body_data)
            except Exception:
                pass

        logger.info(f"Request: {request.method} {request.url.path}", extra=log_data)

        # Process request
        try:
            response = await call_next(request)
            duration = time.perf_counter() - start_time

            # Log response
            response_log = {
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": duration * 1000,
            }

            if self.log_headers:
                response_log["headers"] = self._sanitize_headers(dict(response.headers))

            # Log response body if enabled
            if self.log_response_body and 200 <= response.status_code < 300:
                try:
                    # Read response body
                    body = b""
                    async for chunk in response.body_iterator:
                        body += chunk

                    if body:
                        body_data = json.loads(body.decode())
                        response_log["body"] = self._sanitize_body(body_data)

                    # Recreate response
                    response = Response(
                        content=body,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                    )
                except Exception:
                    pass

            logger.info(
                f"Response: {request.method} {request.url.path} {response.status_code}",
                extra=response_log,
            )

            return response

        except Exception as e:
            duration = time.perf_counter() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "duration_ms": duration * 1000,
                },
                exc_info=True,
            )
            raise

