"""
Development Tools and Utilities
Provides utilities for development, debugging, and testing
"""

import json
import logging
import time
from datetime import UTC, datetime
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


class DevelopmentTools:
    """Development and debugging utilities"""

    @staticmethod
    def log_request_details(request, include_body: bool = False):
        """Log detailed request information for debugging"""
        details = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "client": request.client.host if request.client else None,
        }

        if include_body and request.method in ["POST", "PUT", "PATCH"]:
            # Note: Body would need to be stored in middleware
            details["body_note"] = "Body available in middleware"

        logger.debug(f"Request details: {json.dumps(details, indent=2, default=str)}")

    @staticmethod
    def log_response_details(response, include_body: bool = False):
        """Log detailed response information"""
        details = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
        }

        if include_body:
            # Note: Body would need to be read
            details["body_note"] = "Body available after reading"

        logger.debug(f"Response details: {json.dumps(details, indent=2, default=str)}")

    @staticmethod
    def format_error_for_debugging(
        error: Exception, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Format error with context for debugging"""
        return {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "timestamp": datetime.now(UTC).isoformat(),
        }


def debug_endpoint(func):
    """Decorator to add debug logging to endpoints"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()

        try:
            result = await func(*args, **kwargs)
            duration = time.perf_counter() - start_time

            logger.debug(
                f"Endpoint {func.__name__} completed in {duration * 1000:.2f}ms",
                extra={
                    "function": func.__name__,
                    "duration_ms": duration * 1000,
                },
            )

            return result
        except Exception as e:
            duration = time.perf_counter() - start_time
            logger.error(
                f"Endpoint {func.__name__} failed after {duration * 1000:.2f}ms: {e}",
                exc_info=True,
                extra={
                    "function": func.__name__,
                    "duration_ms": duration * 1000,
                    "error": str(e),
                },
            )
            raise

    return wrapper


def mock_external_service(service_name: str):
    """Decorator to mock external service calls in development"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if os.getenv("MOCK_EXTERNAL_SERVICES", "false").lower() == "true":
                logger.info(f"Mocking {service_name} call")
                # Return mock response
                return {"mocked": True, "service": service_name}
            return await func(*args, **kwargs)

        return wrapper

    return decorator


import os
