"""
Unified Error Handler
Consolidates error_handler.py and enhanced_error_handler.py into a single, comprehensive error handling system
"""

import logging
import os
import re
import traceback
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

# Error rate tracking (in-memory, would use Redis in production)
_error_rate_tracker: dict[str, list] = defaultdict(list)
_error_rate_window = 60  # Track errors per minute


class UnifiedErrorResponse:
    """Unified error response format combining both approaches"""

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
    def create(
        code: str,
        message: str,
        status_code: int,
        details: dict | None = None,
        request_id: str | None = None,
        suggestion: str | None = None,
        classification: str | None = None,
    ) -> dict:
        """
        Create a unified error response

        Args:
            code: Error code (e.g., "VALIDATION_ERROR")
            message: Human-readable error message
            status_code: HTTP status code
            details: Additional error details
            request_id: Request ID for correlation
            suggestion: Helpful suggestion for the user
            classification: Error classification (user_error, system_error, security_error)
        """
        response = {
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "status_code": status_code,
            },
            "timestamp": datetime.now(UTC).isoformat() + "Z",
        }

        if details:
            response["error"]["details"] = details

        if suggestion:
            response["error"]["suggestion"] = suggestion

        if classification:
            response["error"]["classification"] = classification

        if request_id:
            response["request_id"] = request_id

        return response

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

        # Remove API keys, tokens, passwords
        message = re.sub(
            r"(?i)(api[_-]?key|token|password|secret|private[_-]?key)\s*[:=]\s*[\w\-]+",
            r"\1: [REDACTED]",
            message,
        )
        # Remove email addresses
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
            now = datetime.now(UTC)
            key = f"{error_code}:{path}"

            # Clean old entries
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


class UnifiedErrorHandler:
    """Unified error handler combining best features from both implementations"""

    @staticmethod
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle validation errors with helpful messages"""
        is_production = os.getenv("NODE_ENV") == "production"
        request_id = getattr(request.state, "request_id", None)

        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error.get("loc", []))
            message = error.get("msg", "Validation error")
            error_type = error.get("type", "validation_error")

            # Sanitize field values in production
            sanitized_message = UnifiedErrorResponse._sanitize_error_message(
                message, is_production
            )

            errors.append(
                {
                    "field": field,
                    "message": sanitized_message,
                    "type": error_type,
                }
            )

        # Track error rate
        UnifiedErrorResponse._track_error_rate("VALIDATION_ERROR", request.url.path)

        logger.warning(
            f"Validation error: {exc.errors()}",
            extra={"request_id": request_id, "path": request.url.path},
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=UnifiedErrorResponse.create(
                code="VALIDATION_ERROR",
                message="Request validation failed",
                status_code=422,
                details={"validation_errors": errors},
                request_id=request_id,
                suggestion=UnifiedErrorResponse.ERROR_SUGGESTIONS.get(
                    "validation_error"
                ),
                classification="user_error",
            ),
            headers={"X-Request-ID": request_id} if request_id else {},
        )

    @staticmethod
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        """Handle HTTP exceptions with helpful messages"""
        status_code = exc.status_code
        detail = exc.detail
        is_production = os.getenv("NODE_ENV") == "production"
        request_id = getattr(request.state, "request_id", None)

        # Determine error type
        if status_code == 401:
            error_code = "AUTHENTICATION_ERROR"
            suggestion = UnifiedErrorResponse.ERROR_SUGGESTIONS.get(
                "authentication_error"
            )
            classification = "security_error"
        elif status_code == 403:
            error_code = "AUTHORIZATION_ERROR"
            suggestion = UnifiedErrorResponse.ERROR_SUGGESTIONS.get(
                "authorization_error"
            )
            classification = "security_error"
        elif status_code == 404:
            error_code = "NOT_FOUND"
            suggestion = UnifiedErrorResponse.ERROR_SUGGESTIONS.get("not_found")
            classification = "user_error"
        elif status_code == 429:
            error_code = "RATE_LIMIT_EXCEEDED"
            suggestion = UnifiedErrorResponse.ERROR_SUGGESTIONS.get(
                "rate_limit_exceeded"
            )
            classification = "security_error"
        else:
            error_code = f"HTTP_{status_code}"
            suggestion = None
            classification = UnifiedErrorResponse._classify_error(exc, status_code)

        # Sanitize error message
        detail_str = detail if isinstance(detail, str) else str(detail)
        sanitized_message = UnifiedErrorResponse._sanitize_error_message(
            detail_str, is_production
        )

        # Track error rate
        UnifiedErrorResponse._track_error_rate(error_code, request.url.path)

        logger.warning(
            f"HTTP exception: {sanitized_message}",
            extra={
                "request_id": request_id,
                "status_code": status_code,
                "path": request.url.path,
            },
        )

        return JSONResponse(
            status_code=status_code,
            content=UnifiedErrorResponse.create(
                code=error_code,
                message=sanitized_message,
                status_code=status_code,
                request_id=request_id,
                suggestion=suggestion,
                classification=classification,
            ),
            headers={"X-Request-ID": request_id} if request_id else {},
        )

    @staticmethod
    async def database_exception_handler(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        """Handle database-related errors"""
        request_id = getattr(request.state, "request_id", None)
        os.getenv("NODE_ENV") == "production"

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
        UnifiedErrorResponse._track_error_rate("DATABASE_ERROR", request.url.path)

        # Check for specific database errors
        if isinstance(exc, IntegrityError):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content=UnifiedErrorResponse.create(
                    code="INTEGRITY_ERROR",
                    message="Database integrity constraint violated. The resource may already exist.",
                    status_code=409,
                    request_id=request_id,
                    suggestion=UnifiedErrorResponse.ERROR_SUGGESTIONS.get(
                        "integrity_error"
                    ),
                    classification="user_error",
                ),
                headers={"X-Request-ID": request_id} if request_id else {},
            )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=UnifiedErrorResponse.create(
                code="DATABASE_ERROR",
                message="A database error occurred. Please try again later.",
                status_code=500,
                request_id=request_id,
                suggestion=UnifiedErrorResponse.ERROR_SUGGESTIONS.get("database_error"),
                classification="system_error",
            ),
            headers={"X-Request-ID": request_id} if request_id else {},
        )

    @staticmethod
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions with helpful messages"""
        is_development = os.getenv("NODE_ENV") == "development"
        is_production = os.getenv("NODE_ENV") == "production"
        request_id = getattr(request.state, "request_id", None)

        # Classify error
        classification = UnifiedErrorResponse._classify_error(exc, 500)

        # Sanitize error message
        error_message = str(exc) if exc else "An unexpected error occurred"
        sanitized_message = UnifiedErrorResponse._sanitize_error_message(
            error_message, is_production
        )

        # Log the error
        logger.error(
            f"Unhandled exception: {exc}",
            exc_info=True,
            extra={
                "path": request.url.path,
                "method": request.method,
                "request_id": request_id,
                "error_classification": classification,
            },
        )

        # Track error rate
        UnifiedErrorResponse._track_error_rate("INTERNAL_ERROR", request.url.path)

        # Prepare error response
        details = None
        if is_development:
            details = {
                "error": str(exc),
                "type": type(exc).__name__,
                "traceback": traceback.format_exc(),
            }

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=UnifiedErrorResponse.create(
                code="INTERNAL_ERROR",
                message=(
                    sanitized_message
                    if not is_production
                    else "An unexpected error occurred"
                ),
                status_code=500,
                details=details,
                request_id=request_id,
                suggestion="Please try again later. If the problem persists, contact support.",
                classification=classification,
            ),
            headers={"X-Request-ID": request_id} if request_id else {},
        )

    @staticmethod
    def handle_trading_error(exc: Exception, request: Request) -> dict[str, Any]:
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

        return UnifiedErrorResponse.create(
            status_code=error_info["status_code"],
            code=error_info["code"],
            message=error_info["message"],
            request_id=request_id,
            suggestion=UnifiedErrorResponse.ERROR_SUGGESTIONS.get("trading_error"),
        )


def register_unified_error_handlers(app):
    """Register unified error handlers with FastAPI app"""
    app.add_exception_handler(
        RequestValidationError, UnifiedErrorHandler.validation_error_handler
    )
    app.add_exception_handler(HTTPException, UnifiedErrorHandler.http_exception_handler)
    app.add_exception_handler(
        StarletteHTTPException, UnifiedErrorHandler.http_exception_handler
    )
    app.add_exception_handler(
        SQLAlchemyError, UnifiedErrorHandler.database_exception_handler
    )
    app.add_exception_handler(Exception, UnifiedErrorHandler.generic_exception_handler)

    logger.info("[OK] Unified error handlers configured")


# Backward compatibility aliases
register_enhanced_error_handlers = register_unified_error_handlers
validation_exception_handler = UnifiedErrorHandler.validation_error_handler
http_exception_handler = UnifiedErrorHandler.http_exception_handler
general_exception_handler = UnifiedErrorHandler.generic_exception_handler
