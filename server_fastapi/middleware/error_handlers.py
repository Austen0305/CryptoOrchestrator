"""
Comprehensive error handling middleware for FastAPI application.

This module provides centralized error handling for common exceptions,
ensuring consistent error responses across all endpoints.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import Union, Dict, Any
import logging
import traceback

logger = logging.getLogger(__name__)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors with detailed field information.
    
    Args:
        request: The FastAPI request object
        exc: The validation exception
        
    Returns:
        JSON response with validation error details
    """
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(f"Validation error on {request.url.path}: {errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors,
            "path": str(request.url.path)
        }
    )


async def database_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """
    Handle database-related errors.
    
    Args:
        request: The FastAPI request object
        exc: The SQLAlchemy exception
        
    Returns:
        JSON response with appropriate error message
    """
    logger.error(f"Database error on {request.url.path}: {str(exc)}")
    logger.debug(traceback.format_exc())
    
    # Check for specific database errors
    if isinstance(exc, IntegrityError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "Database integrity constraint violated. The resource may already exist.",
                "type": "integrity_error",
                "path": str(request.url.path)
            }
        )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "A database error occurred. Please try again later.",
            "type": "database_error",
            "path": str(request.url.path)
        }
    )


async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Handle all unhandled exceptions with proper logging.
    
    Args:
        request: The FastAPI request object
        exc: The exception
        
    Returns:
        JSON response with generic error message
    """
    logger.error(f"Unhandled exception on {request.url.path}: {str(exc)}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred. Our team has been notified.",
            "type": "internal_error",
            "path": str(request.url.path)
        }
    )


def format_error_response(
    message: str,
    error_type: str = "error",
    details: Dict[str, Any] = None,
    status_code: int = 400
) -> Dict[str, Any]:
    """
    Format a consistent error response.
    
    Args:
        message: The error message
        error_type: Type of error
        details: Additional error details
        status_code: HTTP status code
        
    Returns:
        Formatted error response dictionary
    """
    response = {
        "detail": message,
        "type": error_type,
        "status_code": status_code
    }
    
    if details:
        response["details"] = details
        
    return response


class ErrorContext:
    """Context manager for handling errors in route handlers."""
    
    def __init__(self, operation: str, logger_instance: logging.Logger = None):
        """
        Initialize error context.
        
        Args:
            operation: Description of the operation being performed
            logger_instance: Logger to use (defaults to module logger)
        """
        self.operation = operation
        self.logger = logger_instance or logger
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.error(f"Error during {self.operation}: {str(exc_val)}")
            self.logger.debug(traceback.format_exc())
            return False  # Re-raise the exception
        return True


def handle_trading_error(exc: Exception) -> Dict[str, Any]:
    """
    Handle trading-specific errors with appropriate messages.
    
    Args:
        exc: The exception
        
    Returns:
        Error response dictionary
    """
    error_mapping = {
        "InsufficientBalanceError": {
            "message": str(exc),
            "type": "insufficient_balance",
            "status_code": status.HTTP_400_BAD_REQUEST
        },
        "InvalidSymbolError": {
            "message": str(exc),
            "type": "invalid_symbol",
            "status_code": status.HTTP_400_BAD_REQUEST
        },
        "OrderExecutionError": {
            "message": str(exc),
            "type": "order_execution_failed",
            "status_code": status.HTTP_502_BAD_GATEWAY
        },
        "ExchangeConnectionError": {
            "message": "Unable to connect to exchange. Please try again later.",
            "type": "exchange_connection_error",
            "status_code": status.HTTP_503_SERVICE_UNAVAILABLE
        }
    }
    
    error_name = exc.__class__.__name__
    error_info = error_mapping.get(
        error_name,
        {
            "message": str(exc) if str(exc) else "An error occurred during trading operation",
            "type": "trading_error",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
    )
    
    return format_error_response(
        message=error_info["message"],
        error_type=error_info["type"],
        status_code=error_info["status_code"]
    )
