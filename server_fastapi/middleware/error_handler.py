"""
Structured error handling middleware for consistent error responses.
"""

import logging
from typing import Any, Dict, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
import os

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base API error with structured error information"""
    
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(APIError):
    """Validation error (400)"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class AuthenticationError(APIError):
    """Authentication error (401)"""
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationError(APIError):
    """Authorization error (403)"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN
        )


class NotFoundError(APIError):
    """Not found error (404)"""
    def __init__(self, resource: str = "Resource"):
        super().__init__(
            message=f"{resource} not found",
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource}
        )


class ConflictError(APIError):
    """Conflict error (409)"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class RateLimitError(APIError):
    """Rate limit error (429)"""
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        )


def create_error_response(
    error: APIError,
    request: Optional[Request] = None,
    include_traceback: bool = False
) -> JSONResponse:
    """
    Create a structured error response.
    
    Args:
        error: APIError instance
        request: FastAPI request object (optional)
        include_traceback: Whether to include traceback in development
    
    Returns:
        JSONResponse with structured error format
    """
    is_development = os.getenv("NODE_ENV") == "development"
    
    response_data = {
        "error": {
            "code": error.code,
            "message": error.message,
            "status_code": error.status_code,
            "details": error.details
        }
    }
    
    # Include request ID if available
    if request and hasattr(request.state, "request_id"):
        response_data["error"]["request_id"] = request.state.request_id
    
    # Include traceback in development
    if include_traceback or is_development:
        response_data["error"]["traceback"] = traceback.format_exc()
    
    return JSONResponse(
        status_code=error.status_code,
        content=response_data
    )


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handler for APIError exceptions"""
    logger.error(
        f"API Error: {exc.code} - {exc.message}",
        extra={
            "error_code": exc.code,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return create_error_response(exc, request, include_traceback=False)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handler for HTTPException"""
    error = APIError(
        message=exc.detail,
        code=f"HTTP_{exc.status_code}",
        status_code=exc.status_code
    )
    
    return create_error_response(error, request)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handler for validation errors"""
    errors = exc.errors()
    error_details = {
        "validation_errors": [
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            }
            for error in errors
        ]
    }
    
    error = ValidationError(
        message="Validation failed",
        details=error_details
    )
    
    logger.warning(
        f"Validation error: {exc.errors()}",
        extra={"path": request.url.path, "method": request.method}
    )
    
    return create_error_response(error, request)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for unexpected exceptions"""
    # Import here to avoid circular dependency
    from .log_sanitizer import LogSanitizer
    
    # Sanitize error message to prevent sensitive data leakage
    sanitized_error_msg = LogSanitizer.sanitize_error_message(exc)
    
    logger.error(
        f"Unhandled exception: {sanitized_error_msg}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__
        }
    )
    
    # Don't expose internal errors in production
    is_development = os.getenv("NODE_ENV") == "development"
    
    if is_development:
        message = str(exc)
        traceback_info = traceback.format_exc()
    else:
        message = "An unexpected error occurred"
        traceback_info = None
    
    error = APIError(
        message=message,
        code="INTERNAL_ERROR",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details={"exception_type": type(exc).__name__}
    )
    
    response = create_error_response(error, request, include_traceback=is_development)
    
    if traceback_info:
        response.body = response.body.replace(
            b'"traceback": null',
            f'"traceback": {traceback_info!r}'.encode()
        )
    
    return response


def register_error_handlers(app):
    """Register all error handlers with FastAPI app"""
    # Register custom APIError handler
    app.add_exception_handler(APIError, api_error_handler)
    
    # Register HTTPException handler
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # Register validation error handler
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # Register generic exception handler (catches everything else)
    app.add_exception_handler(Exception, generic_exception_handler)

