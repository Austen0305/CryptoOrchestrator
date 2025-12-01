"""
Enhanced Error Handler
Provides helpful error messages with context and suggestions
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)


class EnhancedErrorHandler:
    """Enhanced error handler with helpful messages"""
    
    ERROR_SUGGESTIONS = {
        "validation_error": "Please check your request data and ensure all required fields are provided.",
        "authentication_error": "Please log in or check your authentication token.",
        "authorization_error": "You don't have permission to perform this action.",
        "not_found": "The requested resource was not found. Please check the ID or path.",
        "rate_limit_exceeded": "Too many requests. Please wait a moment and try again.",
        "database_error": "A database error occurred. Please try again later.",
        "external_api_error": "An external service error occurred. Please try again later.",
    }
    
    @staticmethod
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError
    ) -> JSONResponse:
        """Handle validation errors with helpful messages"""
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error.get("loc", []))
            message = error.get("msg", "Validation error")
            error_type = error.get("type", "validation_error")
            
            errors.append({
                "field": field,
                "message": message,
                "type": error_type,
                "suggestion": EnhancedErrorHandler.ERROR_SUGGESTIONS.get("validation_error")
            })
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "errors": errors,
                    "suggestion": EnhancedErrorHandler.ERROR_SUGGESTIONS.get("validation_error")
                },
                "status_code": 422,
                "request_id": getattr(request.state, "request_id", None)
            }
        )
    
    @staticmethod
    async def http_exception_handler(
        request: Request,
        exc: HTTPException
    ) -> JSONResponse:
        """Handle HTTP exceptions with helpful messages"""
        status_code = exc.status_code
        detail = exc.detail
        
        # Determine error type
        if status_code == 401:
            error_code = "AUTHENTICATION_ERROR"
            suggestion = EnhancedErrorHandler.ERROR_SUGGESTIONS.get("authentication_error")
        elif status_code == 403:
            error_code = "AUTHORIZATION_ERROR"
            suggestion = EnhancedErrorHandler.ERROR_SUGGESTIONS.get("authorization_error")
        elif status_code == 404:
            error_code = "NOT_FOUND"
            suggestion = EnhancedErrorHandler.ERROR_SUGGESTIONS.get("not_found")
        elif status_code == 429:
            error_code = "RATE_LIMIT_EXCEEDED"
            suggestion = EnhancedErrorHandler.ERROR_SUGGESTIONS.get("rate_limit_exceeded")
        else:
            error_code = "HTTP_ERROR"
            suggestion = None
        
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "error": {
                    "code": error_code,
                    "message": detail if isinstance(detail, str) else str(detail),
                    "suggestion": suggestion
                },
                "status_code": status_code,
                "request_id": getattr(request.state, "request_id", None)
            }
        )
    
    @staticmethod
    async def generic_exception_handler(
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions with helpful messages"""
        is_development = os.getenv("NODE_ENV") == "development"
        
        # Log the error
        logger.error(
            f"Unhandled exception: {exc}",
            exc_info=True,
            extra={
                "path": request.url.path,
                "method": request.method,
                "request_id": getattr(request.state, "request_id", None)
            }
        )
        
        # Prepare error response
        error_detail = {
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "suggestion": "Please try again later. If the problem persists, contact support."
        }
        
        if is_development:
            error_detail["details"] = {
                "error": str(exc),
                "type": type(exc).__name__,
                "traceback": traceback.format_exc()
            }
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": error_detail,
                "status_code": 500,
                "request_id": getattr(request.state, "request_id", None)
            }
        )


def register_enhanced_error_handlers(app):
    """Register enhanced error handlers with FastAPI app"""
    app.add_exception_handler(
        RequestValidationError,
        EnhancedErrorHandler.validation_error_handler
    )
    app.add_exception_handler(
        HTTPException,
        EnhancedErrorHandler.http_exception_handler
    )
    app.add_exception_handler(
        Exception,
        EnhancedErrorHandler.generic_exception_handler
    )

