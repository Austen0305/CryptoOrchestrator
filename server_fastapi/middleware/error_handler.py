"""
Standardized Error Handling Middleware
Provides consistent error response format across all endpoints
"""

import logging
import os
import traceback
import uuid

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class StandardizedErrorResponse:
    """Standardized error response format"""

    @staticmethod
    def create_error_response(
        code: str,
        message: str,
        status_code: int,
        details: dict | None = None,
        request_id: str | None = None,
    ) -> dict:
        """
        Create standardized error response

        Args:
            code: Error code (e.g., "VALIDATION_ERROR")
            message: Human-readable error message
            status_code: HTTP status code
            details: Additional error details
            request_id: Request ID for correlation

        Returns:
            Standardized error response dictionary
        """
        return {
            "error": {
                "code": code,
                "message": message,
                "status_code": status_code,
                "details": details or {},
                "request_id": request_id,
            }
        }

    @staticmethod
    def from_http_exception(
        exc: Exception,
        request_id: str | None = None,
    ) -> dict:
        """Convert HTTPException to standardized format"""
        from fastapi import HTTPException

        if isinstance(exc, HTTPException):
            return StandardizedErrorResponse.create_error_response(
                code=f"HTTP_{exc.status_code}",
                message=exc.detail,
                status_code=exc.status_code,
                request_id=request_id,
            )

        return StandardizedErrorResponse.create_error_response(
            code="INTERNAL_ERROR",
            message=str(exc),
            status_code=500,
            request_id=request_id,
        )

    @staticmethod
    def from_validation_error(
        exc: RequestValidationError,
        request_id: str | None = None,
    ) -> dict:
        """Convert validation error to standardized format"""
        errors = []
        for error in exc.errors():
            errors.append(
                {
                    "field": ".".join(str(loc) for loc in error.get("loc", [])),
                    "message": error.get("msg", "Validation error"),
                    "type": error.get("type", "value_error"),
                }
            )

        return StandardizedErrorResponse.create_error_response(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            status_code=422,
            details={"validation_errors": errors},
            request_id=request_id,
        )


async def get_request_id(request: Request) -> str:
    """Get or generate request ID"""
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())
    return request_id


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle validation errors with standardized format"""
    request_id = await get_request_id(request)

    error_response = StandardizedErrorResponse.from_validation_error(exc, request_id)

    logger.warning(
        f"Validation error: {exc.errors()}",
        extra={"request_id": request_id, "path": request.url.path},
    )

    return JSONResponse(
        status_code=422,
        content=error_response,
        headers={"X-Request-ID": request_id},
    )


async def http_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle HTTP exceptions with standardized format"""
    from fastapi import HTTPException

    request_id = await get_request_id(request)

    error_response = StandardizedErrorResponse.from_http_exception(exc, request_id)
    status_code = exc.status_code if isinstance(exc, HTTPException) else 500

    logger.warning(
        f"HTTP exception: {exc.detail if isinstance(exc, HTTPException) else str(exc)}",
        extra={
            "request_id": request_id,
            "status_code": status_code,
            "path": request.url.path,
        },
    )

    return JSONResponse(
        status_code=status_code,
        content=error_response,
        headers={"X-Request-ID": request_id},
    )


async def general_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle general exceptions with standardized format"""
    request_id = await get_request_id(request)

    # Log full exception with traceback
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={"request_id": request_id, "path": request.url.path},
    )

    # In production, don't expose internal error details
    is_production = os.getenv("NODE_ENV") == "production"

    if is_production:
        message = "An internal error occurred. Please try again later."
        details = {}
    else:
        message = str(exc)
        details = {
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc() if not is_production else None,
        }

    error_response = StandardizedErrorResponse.create_error_response(
        code="INTERNAL_ERROR",
        message=message,
        status_code=500,
        details=details,
        request_id=request_id,
    )

    return JSONResponse(
        status_code=500,
        content=error_response,
        headers={"X-Request-ID": request_id},
    )
