"""
Enhanced Error Handler
Provides helpful error messages with context and suggestions
Consolidated from error_handler.py, error_handlers.py, and error_handling.py
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import os

logger = logging.getLogger(__name__)

# Error rate tracking (in-memory, would use Redis in production)
_error_rate_tracker: Dict[str, list] = defaultdict(list)
_error_rate_window = 60  # Track errors per minute


class ErrorResponse:
    """Standardized error response format"""

    @staticmethod
    def create(
        status_code: int,
        error_code: str,
        message: str,
        details: dict = None,
        request_id: str = None,
        suggestion: str = None,
    ) -> dict:
        """Create a standardized error response"""
        response = {
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
                "status_code": status_code,
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        if details:
            response["error"]["details"] = details

        if suggestion:
            response["error"]["suggestion"] = suggestion

        if request_id:
            response["request_id"] = request_id

        return response


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
        "integrity_error": "Database integrity constraint violated. The resource may already exist.",
        "trading_error": "A trading operation error occurred. Please check your balance and try again.",
    }

    @staticmethod
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle validation errors with helpful messages"""
        is_production = os.getenv("NODE_ENV") == "production"
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error.get("loc", []))
            message = error.get("msg", "Validation error")
            error_type = error.get("type", "validation_error")

            # Sanitize field values in production (don't expose request body)
            sanitized_message = EnhancedErrorHandler._sanitize_error_message(
                message, is_production
            )

            errors.append(
                {
                    "field": field,
                    "message": sanitized_message,
                    "type": error_type,
                    "suggestion": EnhancedErrorHandler.ERROR_SUGGESTIONS.get(
                        "validation_error"
                    ),
                }
            )

        # Track error rate
        EnhancedErrorHandler._track_error_rate("VALIDATION_ERROR", request.url.path)

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "classification": "user_error",
                    "errors": errors,
                    "suggestion": EnhancedErrorHandler.ERROR_SUGGESTIONS.get(
                        "validation_error"
                    ),
                },
                "status_code": 422,
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    @staticmethod
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        """Handle HTTP exceptions with helpful messages"""
        status_code = exc.status_code
        detail = exc.detail
        is_production = os.getenv("NODE_ENV") == "production"

        # Determine error type
        if status_code == 401:
            error_code = "AUTHENTICATION_ERROR"
            suggestion = EnhancedErrorHandler.ERROR_SUGGESTIONS.get(
                "authentication_error"
            )
            error_classification = "security_error"
        elif status_code == 403:
            error_code = "AUTHORIZATION_ERROR"
            suggestion = EnhancedErrorHandler.ERROR_SUGGESTIONS.get(
                "authorization_error"
            )
            error_classification = "security_error"
        elif status_code == 404:
            error_code = "NOT_FOUND"
            suggestion = EnhancedErrorHandler.ERROR_SUGGESTIONS.get("not_found")
            error_classification = "user_error"
        elif status_code == 429:
            error_code = "RATE_LIMIT_EXCEEDED"
            suggestion = EnhancedErrorHandler.ERROR_SUGGESTIONS.get(
                "rate_limit_exceeded"
            )
            error_classification = "security_error"
        else:
            error_code = "HTTP_ERROR"
            suggestion = None
            error_classification = EnhancedErrorHandler._classify_error(
                exc, status_code
            )

        # Sanitize error message
        detail_str = detail if isinstance(detail, str) else str(detail)
        sanitized_message = EnhancedErrorHandler._sanitize_error_message(
            detail_str, is_production
        )

        # Track error rate
        EnhancedErrorHandler._track_error_rate(error_code, request.url.path)

        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "error": {
                    "code": error_code,
                    "message": sanitized_message,
                    "classification": error_classification,
                    "suggestion": suggestion,
                },
                "status_code": status_code,
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    @staticmethod
    def _classify_error(exc: Exception, status_code: int) -> str:
        """Classify error type: user_error, system_error, security_error"""
        if status_code < 500:
            # 4xx errors are typically user errors
            if status_code in [401, 403]:
                return "security_error"
            return "user_error"
        else:
            # 5xx errors are system errors
            return "system_error"

    @staticmethod
    def _sanitize_error_message(message: str, is_production: bool) -> str:
        """Sanitize error messages to remove sensitive data in production"""
        if not is_production:
            return message

        # Remove potential sensitive patterns
        import re

        # Remove API keys, tokens, passwords
        message = re.sub(
            r"(?i)(api[_-]?key|token|password|secret|private[_-]?key)\s*[:=]\s*[\w\-]+",
            r"\1: [REDACTED]",
            message,
        )
        # Remove email addresses (keep domain)
        message = re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "[EMAIL_REDACTED]",
            message,
        )
        # Remove IP addresses
        message = re.sub(
            r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "[IP_REDACTED]", message
        )

        return message

    @staticmethod
    def _track_error_rate(error_code: str, path: str):
        """Track error rate for monitoring"""
        try:
            now = datetime.utcnow()
            key = f"{error_code}:{path}"

            # Clean old entries (older than window)
            cutoff = now - timedelta(seconds=_error_rate_window)
            _error_rate_tracker[key] = [
                ts for ts in _error_rate_tracker[key] if ts > cutoff
            ]

            # Add current error
            _error_rate_tracker[key].append(now)

            # Log if error rate is high
            error_count = len(_error_rate_tracker[key])
            if error_count > 10:  # Threshold for alerting
                logger.warning(
                    f"High error rate detected: {error_count} {error_code} errors on {path} in last {_error_rate_window}s",
                    extra={
                        "error_code": error_code,
                        "path": path,
                        "error_count": error_count,
                        "window_seconds": _error_rate_window,
                    },
                )
        except Exception as e:
            logger.debug(f"Error rate tracking failed: {e}")

    @staticmethod
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions with helpful messages"""
        is_development = os.getenv("NODE_ENV") == "development"
        is_production = os.getenv("NODE_ENV") == "production"

        # Classify error
        error_classification = EnhancedErrorHandler._classify_error(exc, 500)

        # Sanitize error message
        error_message = str(exc) if exc else "An unexpected error occurred"
        sanitized_message = EnhancedErrorHandler._sanitize_error_message(
            error_message, is_production
        )

        # Log the error (with full details in logs, sanitized in response)
        logger.error(
            f"Unhandled exception: {exc}",
            exc_info=True,
            extra={
                "path": request.url.path,
                "method": request.method,
                "request_id": getattr(request.state, "request_id", None),
                "error_classification": error_classification,
            },
        )

        # Track error rate
        EnhancedErrorHandler._track_error_rate("INTERNAL_ERROR", request.url.path)

        # Prepare error response
        error_detail = {
            "code": "INTERNAL_ERROR",
            "message": (
                sanitized_message if is_production else "An unexpected error occurred"
            ),
            "classification": error_classification,
            "suggestion": "Please try again later. If the problem persists, contact support.",
        }

        if is_development:
            error_detail["details"] = {
                "error": str(exc),
                "type": type(exc).__name__,
                "traceback": traceback.format_exc(),
            }

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": error_detail,
                "status_code": 500,
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    @staticmethod
    async def database_exception_handler(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        """Handle database-related errors"""
        request_id = getattr(request.state, "request_id", None)
        is_production = os.getenv("NODE_ENV") == "production"

        logger.error(
            f"Database error on {request.url.path}: {str(exc)}",
            exc_info=True,
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
            },
        )

        # Track error rate
        EnhancedErrorHandler._track_error_rate("DATABASE_ERROR", request.url.path)

        # Check for specific database errors
        if isinstance(exc, IntegrityError):
            error_response = ErrorResponse.create(
                status_code=status.HTTP_409_CONFLICT,
                error_code="INTEGRITY_ERROR",
                message="Database integrity constraint violated. The resource may already exist.",
                request_id=request_id,
                suggestion=EnhancedErrorHandler.ERROR_SUGGESTIONS.get(
                    "integrity_error"
                ),
            )
            error_response["error"]["classification"] = "user_error"
            error_response["path"] = str(request.url.path)
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT, content=error_response
            )

        error_response = ErrorResponse.create(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            message="A database error occurred. Please try again later.",
            request_id=request_id,
            suggestion=EnhancedErrorHandler.ERROR_SUGGESTIONS.get("database_error"),
        )
        error_response["error"]["classification"] = "system_error"
        error_response["path"] = str(request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error_response
        )

    @staticmethod
    def handle_trading_error(exc: Exception, request: Request) -> Dict[str, Any]:
        """Handle trading-specific errors with appropriate messages"""
        request_id = getattr(request.state, "request_id", None)

        error_mapping = {
            "InsufficientBalanceError": {
                "message": str(exc),
                "code": "INSUFFICIENT_BALANCE",
                "status_code": status.HTTP_400_BAD_REQUEST,
            },
            "InvalidSymbolError": {
                "message": str(exc),
                "code": "INVALID_SYMBOL",
                "status_code": status.HTTP_400_BAD_REQUEST,
            },
            "OrderExecutionError": {
                "message": str(exc),
                "code": "ORDER_EXECUTION_FAILED",
                "status_code": status.HTTP_502_BAD_GATEWAY,
            },
            "ExchangeConnectionError": {
                "message": "Unable to connect to exchange. Please try again later.",
                "code": "EXCHANGE_CONNECTION_ERROR",
                "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
            },
        }

        error_name = exc.__class__.__name__
        error_info = error_mapping.get(
            error_name,
            {
                "message": (
                    str(exc)
                    if str(exc)
                    else "An error occurred during trading operation"
                ),
                "code": "TRADING_ERROR",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            },
        )

        return ErrorResponse.create(
            status_code=error_info["status_code"],
            error_code=error_info["code"],
            message=error_info["message"],
            request_id=request_id,
            suggestion=EnhancedErrorHandler.ERROR_SUGGESTIONS.get("trading_error"),
        )


def register_enhanced_error_handlers(app):
    """Register enhanced error handlers with FastAPI app"""
    app.add_exception_handler(
        RequestValidationError, EnhancedErrorHandler.validation_error_handler
    )
    app.add_exception_handler(
        HTTPException, EnhancedErrorHandler.http_exception_handler
    )
    app.add_exception_handler(
        StarletteHTTPException, EnhancedErrorHandler.http_exception_handler
    )
    app.add_exception_handler(
        SQLAlchemyError, EnhancedErrorHandler.database_exception_handler
    )
    app.add_exception_handler(Exception, EnhancedErrorHandler.generic_exception_handler)

    logger.info("[OK] Enhanced error handlers configured")
