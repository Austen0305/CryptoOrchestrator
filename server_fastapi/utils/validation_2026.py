"""
Comprehensive Input Validation Utilities (2026 Best Practices)
Provides robust validation for all user inputs with security hardening
"""

import logging
import re
from typing import Any

from fastapi import HTTPException, status

from ..services.risk.risk_manager import risk_manager

logger = logging.getLogger(__name__)

# Security patterns (2026)
ETHEREUM_ADDRESS_PATTERN = re.compile(r"^0x[a-fA-F0-9]{40}$")
HEX_PATTERN = re.compile(r"^0x[a-fA-F0-9]+$")
SQL_INJECTION_PATTERNS = [
    re.compile(
        r"(?i)(union|select|insert|update|delete|drop|create|alter|exec|execute)"
    ),
    re.compile(r"(?i)(--|/\*|\*/|;|'|%)"),
]
XSS_PATTERNS = [
    re.compile(r"<script[^>]*>", re.IGNORECASE),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
]


async def validate_transaction_intent(
    user_id: int,
    signal: dict[str, Any]
) -> None:
    """
    Validate transaction intent against Risk Manager before execution.
    (2026 Best Practice: Intent-based Validation)

    Args:
        user_id: User initiating the transaction
        signal: Transaction signal details

    Raises:
        ValidationError: If risk checks fail
    """
    try:
        current_risk_manager = risk_manager  # Get global instance
        
        # Check if trade is allowed by risk manager
        errors = await current_risk_manager.validate_trade(user_id, signal)
        
        if errors:
            logger.warning(f"Transaction intent blocked for user {user_id}: {errors}")
            raise ValidationError(
                message="Transaction blocked by risk controls",
                details={"risk_errors": errors}
            )
            
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error validating transaction intent: {e}")
        # Fail safe: Block if validation fails
        raise ValidationError(message="Failed to validate transaction risk")

def validate_ethereum_address(address: str) -> str:
    """
    Validate and normalize Ethereum address (2026 best practice)

    Args:
        address: Ethereum address to validate

    Returns:
        Checksummed address (EIP-55)

    Raises:
        ValueError: If address is invalid
    """
    if not address:
        raise ValueError("Ethereum address is required")

    address = address.strip()

    if not ETHEREUM_ADDRESS_PATTERN.match(address):
        raise ValueError(f"Invalid Ethereum address format: {address}")

    # Normalize to checksum (EIP-55)
    try:
        from eth_utils import to_checksum_address

        return to_checksum_address(address)
    except ImportError:
        # Fallback if eth_utils not available
        return address.lower()


def validate_hex_string(
    value: str, min_length: int = 0, max_length: int | None = None
) -> str:
    """
    Validate hex string (2026 best practice)

    Args:
        value: Hex string to validate
        min_length: Minimum length
        max_length: Maximum length

    Returns:
        Validated hex string

    Raises:
        ValueError: If hex string is invalid
    """
    if not value:
        raise ValueError("Hex string is required")

    value = value.strip()

    if not HEX_PATTERN.match(value):
        raise ValueError(f"Invalid hex string format: {value}")

    hex_length = len(value) - 2  # Subtract '0x' prefix
    if min_length and hex_length < min_length:
        raise ValueError(f"Hex string too short (minimum {min_length} characters)")
    if max_length and hex_length > max_length:
        raise ValueError(f"Hex string too long (maximum {max_length} characters)")

    return value.lower()


def sanitize_input(value: str, allow_html: bool = False) -> str:
    """
    Sanitize user input to prevent injection attacks (2026 best practice)

    Args:
        value: Input string to sanitize
        allow_html: Whether to allow HTML (default: False)

    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return str(value)

    # Remove null bytes
    value = value.replace("\x00", "")

    # Check for SQL injection patterns
    for pattern in SQL_INJECTION_PATTERNS:
        if pattern.search(value):
            logger.warning(f"Potential SQL injection detected: {value[:50]}")
            raise ValueError("Invalid input detected")

    # Check for XSS patterns (if HTML not allowed)
    if not allow_html:
        for pattern in XSS_PATTERNS:
            if pattern.search(value):
                logger.warning(f"Potential XSS detected: {value[:50]}")
                raise ValueError("Invalid input detected")

    # Trim whitespace
    value = value.strip()

    return value


def validate_amount(
    amount: float, min_value: float = 0.0, max_value: float | None = None
) -> float:
    """
    Validate amount with bounds checking (2026 best practice)

    Args:
        amount: Amount to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value

    Returns:
        Validated amount

    Raises:
        ValueError: If amount is invalid
    """
    if not isinstance(amount, (int, float)):
        raise ValueError("Amount must be a number")

    if amount < min_value:
        raise ValueError(f"Amount must be at least {min_value}")

    if max_value is not None and amount > max_value:
        raise ValueError(f"Amount must not exceed {max_value}")

    # Check for NaN or Infinity
    if not (amount == amount):  # NaN check
        raise ValueError("Amount cannot be NaN")
    if amount == float("inf") or amount == float("-inf"):
        raise ValueError("Amount cannot be infinite")

    return float(amount)


def validate_slippage(slippage: float, max_slippage: float = 50.0) -> float:
    """
    Validate slippage tolerance (2026 best practice)

    Args:
        slippage: Slippage percentage
        max_slippage: Maximum allowed slippage

    Returns:
        Validated slippage

    Raises:
        ValueError: If slippage is invalid
    """
    slippage = validate_amount(slippage, min_value=0.0, max_value=max_slippage)

    if slippage > max_slippage:
        raise ValueError(f"Slippage tolerance cannot exceed {max_slippage}%")

    return slippage


def validate_symbol(symbol: str) -> str:
    """
    Validate trading symbol (2026 best practice)

    Args:
        symbol: Trading symbol to validate

    Returns:
        Validated symbol

    Raises:
        ValueError: If symbol is invalid
    """
    if not symbol:
        raise ValueError("Symbol is required")

    symbol = sanitize_input(symbol.upper().strip())

    # Validate format (e.g., BTC/USD, ETH/USDT)
    if not re.match(r"^[A-Z0-9]+/[A-Z0-9]+$", symbol):
        raise ValueError(
            f"Invalid symbol format: {symbol}. Expected format: BASE/QUOTE"
        )

    # Check length
    if len(symbol) > 20:
        raise ValueError("Symbol too long (maximum 20 characters)")

    return symbol


class ValidationError(HTTPException):
    """Custom validation error with structured response"""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": message,
                "field": field,
                "details": details or {},
            },
        )


def validate_pagination(
    page: int = 1, per_page: int = 20, max_per_page: int = 100
) -> tuple[int, int]:
    """
    Validate pagination parameters (2026 best practice)

    Args:
        page: Page number (1-indexed)
        per_page: Items per page
        max_per_page: Maximum items per page

    Returns:
        Tuple of (page, per_page)

    Raises:
        ValueError: If pagination parameters are invalid
    """
    if page < 1:
        raise ValueError("Page must be at least 1")

    if per_page < 1:
        raise ValueError("Per page must be at least 1")

    if per_page > max_per_page:
        raise ValueError(f"Per page cannot exceed {max_per_page}")

    return page, per_page
