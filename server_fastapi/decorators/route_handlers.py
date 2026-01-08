"""
Route decorators for comprehensive error handling.

Provides decorators to wrap route handlers with standardized error handling,
logging, and response formatting.
"""

import logging
import traceback
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Any

from fastapi import HTTPException, status

from ..utils.error_handling import (
    BotCreationError,
    ConfigurationError,
    InsufficientBalanceError,
    InvalidSymbolError,
    OrderExecutionError,
)

logger = logging.getLogger(__name__)


def handle_errors(operation_name: str, logger_instance: logging.Logger | None = None):
    """
    Decorator to handle errors in route handlers with consistent logging.

    Args:
        operation_name: Description of the operation for logging
        logger_instance: Custom logger instance (defaults to module logger)

    Usage:
        @router.post("/bots")
        @handle_errors("create bot")
        async def create_bot(request: CreateBotRequest):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            log = logger_instance or logger
            start_time = datetime.utcnow()

            try:
                log.info(f"Starting {operation_name}")
                result = await func(*args, **kwargs)

                duration = (datetime.utcnow() - start_time).total_seconds()
                log.info(f"Completed {operation_name} in {duration:.2f}s")

                return result

            except InsufficientBalanceError as e:
                log.warning(f"{operation_name} failed: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "insufficient_balance",
                        "message": str(e),
                        "operation": operation_name,
                    },
                )

            except InvalidSymbolError as e:
                log.warning(f"{operation_name} failed: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "invalid_symbol",
                        "message": str(e),
                        "operation": operation_name,
                    },
                )

            except OrderExecutionError as e:
                log.error(f"{operation_name} failed: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail={
                        "error": "order_execution_failed",
                        "message": str(e),
                        "operation": operation_name,
                    },
                )

            except BotCreationError as e:
                log.error(f"{operation_name} failed: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "bot_creation_failed",
                        "message": str(e),
                        "operation": operation_name,
                    },
                )

            except ConfigurationError as e:
                log.warning(f"{operation_name} failed: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "configuration_error",
                        "message": str(e),
                        "operation": operation_name,
                    },
                )

            except HTTPException:
                # Re-raise HTTP exceptions as-is
                raise

            except ValueError as e:
                log.warning(f"{operation_name} validation error: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "validation_error",
                        "message": str(e),
                        "operation": operation_name,
                    },
                )

            except Exception as e:
                log.error(f"{operation_name} unexpected error: {str(e)}")
                log.debug(traceback.format_exc())

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error": "internal_error",
                        "message": "An unexpected error occurred. Our team has been notified.",
                        "operation": operation_name,
                    },
                )

        return wrapper

    return decorator


def require_trading_enabled(func: Callable) -> Callable:
    """
    Decorator to ensure trading is enabled before executing operation.

    Usage:
        @router.post("/trade")
        @require_trading_enabled
        async def execute_trade(request: TradeRequest):
            ...
    """

    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        # Import here to avoid circular dependency
        from ..config import settings

        if not getattr(settings, "TRADING_ENABLED", True):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "trading_disabled",
                    "message": "Trading is currently disabled for maintenance",
                },
            )

        return await func(*args, **kwargs)

    return wrapper


def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """
    Decorator for rate limiting endpoints.

    Args:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds

    Usage:
        @router.post("/trade")
        @rate_limit(max_requests=10, window_seconds=60)
        async def execute_trade(request: TradeRequest):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # This is a simplified version - in production, you'd use Redis
            # Rate limiting is handled by middleware (SlowAPIMiddleware, AdvancedRateLimitMiddleware)
            # This decorator is for per-route rate limiting if needed in the future
            # For now, rely on global middleware rate limiting configured in main.py
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def log_performance(slow_threshold_seconds: float = 1.0):
    """
    Decorator to log slow requests for performance monitoring.

    Args:
        slow_threshold_seconds: Threshold in seconds to log warning

    Usage:
        @router.get("/expensive-operation")
        @log_performance(slow_threshold_seconds=2.0)
        async def expensive_operation():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = datetime.utcnow()

            result = await func(*args, **kwargs)

            duration = (datetime.utcnow() - start_time).total_seconds()

            if duration >= slow_threshold_seconds:
                logger.warning(
                    f"Slow request detected: {func.__name__} took {duration:.2f}s "
                    f"(threshold: {slow_threshold_seconds}s)"
                )

            return result

        return wrapper

    return decorator


def validate_request(validator_func: Callable[[Any], tuple[bool, str | None]]):
    """
    Decorator for custom request validation.

    Args:
        validator_func: Function that takes request and returns (is_valid, error_message)

    Usage:
        def validate_amount(request):
            if request.amount <= 0:
                return False, "Amount must be positive"
            return True, None

        @router.post("/trade")
        @validate_request(validate_amount)
        async def execute_trade(request: TradeRequest):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Try to find the request object in args/kwargs
            request_obj = None

            # Check args for Pydantic models
            for arg in args:
                if hasattr(arg, "__fields__"):  # Pydantic model
                    request_obj = arg
                    break

            # Check kwargs
            if not request_obj:
                for value in kwargs.values():
                    if hasattr(value, "__fields__"):
                        request_obj = value
                        break

            if request_obj:
                is_valid, error_message = validator_func(request_obj)
                if not is_valid:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "error": "validation_error",
                            "message": error_message or "Invalid request",
                        },
                    )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
