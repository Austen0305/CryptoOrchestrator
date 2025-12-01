"""
Enhanced Error Handling Middleware
Provides comprehensive error handling and structured error responses
"""
import logging
import traceback
from typing import Callable
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError
import json

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standardized error response format"""
    
    @staticmethod
    def create(
        status_code: int,
        error_code: str,
        message: str,
        details: dict = None,
        request_id: str = None
    ) -> dict:
        """Create a standardized error response"""
        response = {
            "error": {
                "code": error_code,
                "message": message,
                "status_code": status_code
            },
            "timestamp": None,  # Will be set by middleware
            "path": None  # Will be set by middleware
        }
        
        if details:
            response["error"]["details"] = details
        
        if request_id:
            response["request_id"] = request_id
        
        return response


async def enhanced_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Enhanced exception handler for unhandled exceptions
    
    Provides:
    - Structured error responses
    - Detailed logging
    - Request context
    - Error tracking
    """
    import time
    from datetime import datetime
    
    # Get request ID if available
    request_id = getattr(request.state, "request_id", None)
    
    # Log the full exception
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        exc_info=True,
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host if request.client else None
        }
    )
    
    # Create error response
    error_response = ErrorResponse.create(
        status_code=500,
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Please try again later.",
        request_id=request_id
    )
    
    # Add timestamp and path
    error_response["timestamp"] = datetime.utcnow().isoformat() + "Z"
    error_response["path"] = str(request.url.path)
    
    # In development, include traceback
    import os
    if os.getenv("ENVIRONMENT", "production") == "development":
        error_response["error"]["traceback"] = traceback.format_exc()
    
    return JSONResponse(
        status_code=500,
        content=error_response
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Enhanced HTTP exception handler
    
    Provides structured error responses for HTTP exceptions
    """
    import time
    from datetime import datetime
    
    request_id = getattr(request.state, "request_id", None)
    
    # Determine error code from status code
    error_codes = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT"
    }
    
    error_code = error_codes.get(exc.status_code, "HTTP_ERROR")
    
    # Get error message
    if isinstance(exc.detail, dict):
        message = exc.detail.get("message", exc.detail.get("detail", "An error occurred"))
        details = {k: v for k, v in exc.detail.items() if k not in ["message", "detail"]}
    elif isinstance(exc.detail, str):
        message = exc.detail
        details = None
    else:
        message = "An error occurred"
        details = None
    
    error_response = ErrorResponse.create(
        status_code=exc.status_code,
        error_code=error_code,
        message=message,
        details=details,
        request_id=request_id
    )
    
    error_response["timestamp"] = datetime.utcnow().isoformat() + "Z"
    error_response["path"] = str(request.url.path)
    
    # Log the error
    log_level = logging.WARNING if exc.status_code < 500 else logging.ERROR
    logger.log(
        log_level,
        f"HTTP {exc.status_code}: {message}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Enhanced validation exception handler
    
    Provides detailed validation error information
    """
    from datetime import datetime
    
    request_id = getattr(request.state, "request_id", None)
    
    # Extract validation errors
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []))
        errors.append({
            "field": field,
            "message": error.get("msg", "Validation error"),
            "type": error.get("type", "validation_error")
        })
    
    error_response = ErrorResponse.create(
        status_code=422,
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        details={"errors": errors},
        request_id=request_id
    )
    
    error_response["timestamp"] = datetime.utcnow().isoformat() + "Z"
    error_response["path"] = str(request.url.path)
    
    # Log validation errors (at info level, not error)
    logger.info(
        f"Validation error: {len(errors)} field(s) failed validation",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "validation_errors": errors
        }
    )
    
    return JSONResponse(
        status_code=422,
        content=error_response
    )


def setup_error_handlers(app):
    """
    Setup enhanced error handlers for the FastAPI application
    
    Args:
        app: FastAPI application instance
    """
    # Add exception handlers
    app.add_exception_handler(Exception, enhanced_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    logger.info("✅ Enhanced error handlers configured")
