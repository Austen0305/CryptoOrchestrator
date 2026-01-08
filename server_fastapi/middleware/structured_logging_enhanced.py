"""
Enhanced Structured Logging Middleware
Provides comprehensive request/response logging with structured format
"""

import json
import logging
import time
from datetime import datetime
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class EnhancedStructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    Enhanced structured logging middleware with comprehensive request/response logging

    Logs:
    - Request method, path, query params
    - Request headers (sanitized)
    - Request body size
    - Response status code
    - Response time
    - Error details (if any)
    """

    def __init__(
        self, app, log_request_body: bool = False, log_response_body: bool = False
    ):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and log structured information"""
        start_time = time.perf_counter()
        request_id = getattr(request.state, "request_id", None)

        # Extract request information
        request_info = await self._extract_request_info(request, request_id)

        # Log request
        logger.info(
            "Incoming request",
            extra={
                **request_info,
                "event_type": "request_start",
            },
        )

        # Process request
        response = None
        error = None
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            error = {
                "type": type(e).__name__,
                "message": str(e),
            }
            raise
        finally:
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Extract response information
            response_info = self._extract_response_info(
                response, duration_ms, error, request_id
            )

            # Log response
            log_level = (
                logging.ERROR
                if error
                else (
                    logging.WARNING
                    if response_info.get("status_code", 200) >= 400
                    else logging.INFO
                )
            )

            logger.log(
                log_level,
                "Request completed",
                extra={
                    **request_info,
                    **response_info,
                    "event_type": "request_complete",
                },
            )

    async def _extract_request_info(
        self, request: Request, request_id: str | None
    ) -> dict[str, Any]:
        """Extract structured request information"""
        info = {
            "request_id": request_id,
            "method": request.method,
            "path": str(request.url.path),
            "query_params": dict(request.query_params),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }

        # Add request body info if enabled
        if self.log_request_body:
            try:
                body = await request.body()
                info["body_size"] = len(body)
                if len(body) < 1000:  # Only log small bodies
                    try:
                        info["body"] = json.loads(body.decode())
                    except:
                        info["body_preview"] = body.decode()[:100]
            except Exception:
                pass

        # Sanitize headers (remove sensitive info)
        headers = dict(request.headers)
        sensitive_headers = ["authorization", "cookie", "x-api-key", "x-auth-token"]
        for header in sensitive_headers:
            if header in headers:
                headers[header] = "[REDACTED]"

        info["headers"] = headers

        return info

    def _extract_response_info(
        self,
        response: Response | None,
        duration_ms: float,
        error: dict | None,
        request_id: str | None,
    ) -> dict[str, Any]:
        """Extract structured response information"""
        info = {
            "request_id": request_id,
            "duration_ms": round(duration_ms, 2),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        if error:
            info["error"] = error
            info["status_code"] = 500
        elif response:
            info["status_code"] = response.status_code

            # Add response headers (sanitized)
            headers = dict(response.headers)
            sensitive_headers = ["set-cookie", "authorization"]
            for header in sensitive_headers:
                if header in headers:
                    headers[header] = "[REDACTED]"

            info["response_headers"] = headers

            # Add response body info if enabled
            if self.log_response_body and hasattr(response, "body"):
                try:
                    body = response.body
                    info["response_body_size"] = len(body) if body else 0
                except Exception:
                    pass

        return info
