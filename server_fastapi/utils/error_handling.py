"""
Enhanced error messages and exception handling
Provides user-friendly, actionable error messages
"""

import logging
from typing import Any

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class TradingError(Exception):
    """Base exception for trading-related errors"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class InsufficientBalanceError(TradingError):
    """Raised when user has insufficient balance"""

    def __init__(
        self, current_balance: float, required_amount: float, currency: str = "USD"
    ):
        message = (
            f"Insufficient balance: You have ${current_balance:.2f} {currency}, "
            f"but need ${required_amount:.2f} {currency} "
            f"(${required_amount - current_balance:.2f} short)"
        )
        details = {
            "current_balance": current_balance,
            "required_amount": required_amount,
            "shortfall": required_amount - current_balance,
            "currency": currency,
        }
        super().__init__(message, details)


class InvalidSymbolError(TradingError):
    """Raised when trading symbol is invalid"""

    def __init__(self, symbol: str, suggestion: str | None = None):
        if suggestion:
            message = f"Symbol '{symbol}' not found. Did you mean '{suggestion}'?"
        else:
            message = f"Symbol '{symbol}' is not supported. Please check the symbol and try again."

        details = {"symbol": symbol, "suggestion": suggestion}
        super().__init__(message, details)


class OrderExecutionError(TradingError):
    """Raised when order execution fails"""

    def __init__(self, reason: str, order_details: dict[str, Any] | None = None):
        message = f"Order execution failed: {reason}"
        super().__init__(message, order_details or {})


class BotCreationError(TradingError):
    """Raised when bot creation fails"""

    def __init__(self, reason: str):
        message = f"Failed to create bot: {reason}"
        super().__init__(message)


class ConfigurationError(TradingError):
    """Raised when configuration is invalid"""

    def __init__(self, field: str, reason: str):
        message = f"Invalid configuration for '{field}': {reason}"
        details = {"field": field, "reason": reason}
        super().__init__(message, details)


def create_http_exception(
    status_code: int, message: str, details: dict[str, Any] | None = None
) -> HTTPException:
    """
    Create an HTTPException with enhanced error information.

    Args:
        status_code: HTTP status code
        message: Human-readable error message
        details: Additional error details

    Returns:
        HTTPException with formatted error
    """
    error_detail = {"message": message}
    if details:
        error_detail["details"] = details

    return HTTPException(status_code=status_code, detail=error_detail)


def handle_trading_error(
    error: Exception, default_message: str = "An error occurred"
) -> HTTPException:
    """
    Convert trading errors to appropriate HTTP exceptions.

    Args:
        error: The error that occurred
        default_message: Default message if error type is unknown

    Returns:
        HTTPException with appropriate status code and message
    """
    if isinstance(error, InsufficientBalanceError):
        logger.warning(f"Insufficient balance: {error.message}")
        return create_http_exception(
            status.HTTP_400_BAD_REQUEST, error.message, error.details
        )

    elif isinstance(error, InvalidSymbolError):
        logger.warning(f"Invalid symbol: {error.message}")
        return create_http_exception(
            status.HTTP_400_BAD_REQUEST, error.message, error.details
        )

    elif isinstance(error, OrderExecutionError):
        logger.error(f"Order execution error: {error.message}", exc_info=True)
        return create_http_exception(
            status.HTTP_500_INTERNAL_SERVER_ERROR, error.message, error.details
        )

    elif isinstance(error, BotCreationError):
        logger.error(f"Bot creation error: {error.message}", exc_info=True)
        return create_http_exception(
            status.HTTP_400_BAD_REQUEST, error.message, error.details
        )

    elif isinstance(error, ConfigurationError):
        logger.warning(f"Configuration error: {error.message}")
        return create_http_exception(
            status.HTTP_400_BAD_REQUEST, error.message, error.details
        )

    elif isinstance(error, ValueError):
        logger.warning(f"Validation error: {str(error)}")
        return create_http_exception(status.HTTP_400_BAD_REQUEST, str(error))

    else:
        # Unknown error - log and return generic message
        logger.error(f"Unexpected error: {str(error)}", exc_info=True)
        return create_http_exception(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            default_message,
            {"error_type": type(error).__name__},
        )


# Error message templates
ERROR_MESSAGES = {
    "insufficient_balance": "Insufficient balance: You have ${current:.2f}, need ${required:.2f}",
    "invalid_symbol": "Symbol '{symbol}' not found. Valid format: BASE/QUOTE (e.g., BTC/USDT)",
    "invalid_amount": "Amount must be between ${min:.2f} and ${max:.2f}",
    "invalid_price": "Price must be greater than 0",
    "order_failed": "Order execution failed: {reason}",
    "bot_limit_reached": "You've reached the maximum number of bots ({limit}) for your plan. Upgrade to create more bots.",
    "exchange_error": "Exchange API error: {error}. Please try again.",
    "network_error": "Network error: Unable to connect to exchange. Please check your connection.",
    "permission_denied": "Permission denied: This action requires {required_permission} permission.",
    "rate_limit": "Rate limit exceeded. Please wait {wait_seconds} seconds before trying again.",
    "invalid_timeframe": "Timeframe '{timeframe}' is not supported. Use: 1m, 5m, 15m, 1h, 4h, 1d, 1w",
    "invalid_strategy": "Strategy '{strategy}' not found. Available strategies: {available}",
}


def format_error_message(template_key: str, **kwargs) -> str:
    """
    Format an error message using a template.

    Args:
        template_key: Key of the error template
        **kwargs: Values to interpolate into template

    Returns:
        Formatted error message
    """
    template = ERROR_MESSAGES.get(template_key, "An error occurred")
    try:
        return template.format(**kwargs)
    except KeyError as e:
        logger.warning(f"Missing parameter for error template '{template_key}': {e}")
        return template
