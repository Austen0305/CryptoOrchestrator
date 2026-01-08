"""
Route helper utilities for FastAPI routes.
Centralizes common route operations to reduce code duplication.
"""

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from fastapi import HTTPException

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _get_user_id(current_user: dict) -> str:
    """
    Helper function to safely extract user_id from current_user dict.
    Supports multiple key formats for backward compatibility.

    Args:
        current_user: Dictionary containing user information from JWT token

    Returns:
        User ID as string

    Raises:
        HTTPException: If user ID cannot be extracted (401 Unauthorized)

    Example:
        >>> current_user = {"id": "123", "email": "user@example.com"}
        >>> _get_user_id(current_user)
        '123'

        >>> current_user = {"user_id": "456", "email": "user@example.com"}
        >>> _get_user_id(current_user)
        '456'
    """
    user_id = (
        current_user.get("id") or current_user.get("user_id") or current_user.get("sub")
    )
    if not user_id:
        logger.warning(f"User ID not found in current_user: {current_user}")
        raise HTTPException(status_code=401, detail="User not authenticated")
    return str(user_id)


def handle_route_errors(
    operation_name: str,
    user_id: str | None = None,
    error_message: str | None = None,
    status_code: int = 500,
    extra_context: dict | None = None,
) -> Callable:
    """
    Decorator for standardized error handling in routes.

    This decorator wraps route functions to provide consistent error handling:
    - HTTPExceptions are re-raised (let them propagate)
    - Other exceptions are logged with context and converted to HTTPException

    Args:
        operation_name: Name of the operation (e.g., "get portfolio", "create bot")
        user_id: Optional user ID for logging context
        error_message: Custom error message (default: "Failed to {operation_name}")
        status_code: HTTP status code for errors (default: 500)
        extra_context: Additional context for logging

    Returns:
        Decorator function

    Example:
        @router.get("/bots")
        @handle_route_errors("get bots", user_id=user_id)
        async def get_bots(...):
            # Route logic here
            pass
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # Let HTTPExceptions propagate (they're already properly formatted)
                raise
            except Exception as e:
                # Log error with context
                log_context = {
                    "operation": operation_name,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
                if user_id:
                    log_context["user_id"] = user_id
                if extra_context:
                    log_context.update(extra_context)

                logger.error(
                    f"Failed to {operation_name}: {e}", exc_info=True, extra=log_context
                )

                # Raise standardized HTTPException
                message = error_message or f"Failed to {operation_name}"
                raise HTTPException(status_code=status_code, detail=message)

        return wrapper

    return decorator


def standard_error_handler(
    operation_name: str,
    user_id: str | None = None,
    error_message: str | None = None,
    status_code: int = 500,
    extra_context: dict | None = None,
):
    """
    Context manager for standardized error handling in routes.

    Use this in try/except blocks for consistent error handling:

    Example:
        try:
            with standard_error_handler("get portfolio", user_id=user_id):
                # Route logic here
                return result
        except HTTPException:
            raise
        except Exception as e:
            # This will be handled by the context manager
            pass

    Note: This is less preferred than the decorator. Use @handle_route_errors instead.
    """

    class ErrorHandler:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is None:
                return False

            # Let HTTPExceptions propagate
            if issubclass(exc_type, HTTPException):
                return False

            # Log and convert other exceptions
            log_context = {
                "operation": operation_name,
                "error": str(exc_val),
                "error_type": exc_type.__name__,
            }
            if user_id:
                log_context["user_id"] = user_id
            if extra_context:
                log_context.update(extra_context)

            logger.error(
                f"Failed to {operation_name}: {exc_val}",
                exc_info=True,
                extra=log_context,
            )

            # Raise standardized HTTPException
            message = error_message or f"Failed to {operation_name}"
            raise HTTPException(status_code=status_code, detail=message) from exc_val

    return ErrorHandler()


def handle_route_error(
    error: Exception,
    operation_name: str,
    user_id: str | None = None,
    error_message: str | None = None,
    status_code: int = 500,
    extra_context: dict | None = None,
) -> HTTPException:
    """
    Standardized error handler for route exceptions.

    This function provides consistent error handling across all routes.
    Use this in except blocks for standardized error logging and responses.

    Standard pattern for routes:
        try:
            # Route logic here
            return result
        except HTTPException:
            raise  # Let HTTPExceptions propagate
        except Exception as e:
            raise handle_route_error(
                e,
                operation_name="get bots",
                user_id=user_id,
                error_message="Failed to retrieve bots"
            )

    Args:
        error: The exception that occurred
        operation_name: Name of the operation (e.g., "get bots", "create trade")
        user_id: Optional user ID for logging context
        error_message: Custom error message (default: "Failed to {operation_name}")
        status_code: HTTP status code for errors (default: 500)
        extra_context: Additional context for logging (e.g., {"bot_id": "123"})

    Returns:
        HTTPException with standardized format

    Example:
        try:
            bot = await service.get_bot(bot_id, user_id)
            return bot
        except HTTPException:
            raise
        except Exception as e:
            raise handle_route_error(
                e,
                operation_name="get bot",
                user_id=user_id,
                error_message="Failed to retrieve bot",
                extra_context={"bot_id": bot_id}
            )
    """
    # Build logging context
    log_context = {
        "operation": operation_name,
        "error": str(error),
        "error_type": type(error).__name__,
    }
    if user_id:
        log_context["user_id"] = user_id
    if extra_context:
        log_context.update(extra_context)

    # Log error with full context
    logger.error(
        f"Failed to {operation_name}: {error}", exc_info=True, extra=log_context
    )

    # Return standardized HTTPException
    message = error_message or f"Failed to {operation_name}"
    return HTTPException(status_code=status_code, detail=message)
