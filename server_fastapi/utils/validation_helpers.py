"""
Validation Helpers
Common validation utilities for routes and services
"""

import re
import logging
from typing import Optional, List, Any
from fastapi import HTTPException, status
from pydantic import BaseModel, validator

logger = logging.getLogger(__name__)


class ValidationError(HTTPException):
    """Custom validation error"""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation_error", "message": message, "field": field},
        )


def validate_ethereum_address(address: str) -> str:
    """
    Validate Ethereum address format.

    Args:
        address: Ethereum address to validate

    Returns:
        Normalized address (checksummed)

    Raises:
        ValidationError: If address is invalid
    """
    if not address:
        raise ValidationError("Address is required", "address")

    # Basic format check
    if not re.match(r"^0x[a-fA-F0-9]{40}$", address):
        raise ValidationError("Invalid Ethereum address format", "address")

    return address


def validate_amount(amount: float, min_amount: Optional[float] = None, max_amount: Optional[float] = None) -> float:
    """
    Validate amount value.

    Args:
        amount: Amount to validate
        min_amount: Minimum allowed amount
        max_amount: Maximum allowed amount

    Returns:
        Validated amount

    Raises:
        ValidationError: If amount is invalid
    """
    if amount is None:
        raise ValidationError("Amount is required", "amount")

    if not isinstance(amount, (int, float)):
        raise ValidationError("Amount must be a number", "amount")

    if amount <= 0:
        raise ValidationError("Amount must be positive", "amount")

    if min_amount is not None and amount < min_amount:
        raise ValidationError(f"Amount must be at least {min_amount}", "amount")

    if max_amount is not None and amount > max_amount:
        raise ValidationError(f"Amount must be at most {max_amount}", "amount")

    return amount


def validate_symbol(symbol: str) -> str:
    """
    Validate trading symbol format.

    Args:
        symbol: Trading symbol to validate

    Returns:
        Normalized symbol

    Raises:
        ValidationError: If symbol is invalid
    """
    if not symbol:
        raise ValidationError("Symbol is required", "symbol")

    # Basic format check (uppercase, alphanumeric, dash, underscore)
    if not re.match(r"^[A-Z0-9_-]+$", symbol.upper()):
        raise ValidationError("Invalid symbol format", "symbol")

    return symbol.upper()


def sanitize_input(input_str: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input string.

    Args:
        input_str: Input string to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string

    Raises:
        ValidationError: If input is invalid
    """
    if not isinstance(input_str, str):
        raise ValidationError("Input must be a string", "input")

    # Remove leading/trailing whitespace
    sanitized = input_str.strip()

    if max_length and len(sanitized) > max_length:
        raise ValidationError(f"Input exceeds maximum length of {max_length}", "input")

    return sanitized


def validate_pagination(page: int, page_size: int, max_page_size: int = 100) -> tuple[int, int]:
    """
    Validate pagination parameters.

    Args:
        page: Page number (1-indexed)
        page_size: Items per page
        max_page_size: Maximum allowed page size

    Returns:
        Tuple of (validated_page, validated_page_size)

    Raises:
        ValidationError: If pagination parameters are invalid
    """
    if page < 1:
        raise ValidationError("Page must be at least 1", "page")

    if page_size < 1:
        raise ValidationError("Page size must be at least 1", "page_size")

    if page_size > max_page_size:
        raise ValidationError(f"Page size cannot exceed {max_page_size}", "page_size")

    return page, page_size


def validate_email(email: str) -> str:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        Normalized email

    Raises:
        ValidationError: If email is invalid
    """
    if not email:
        raise ValidationError("Email is required", "email")

    # Basic email format check
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        raise ValidationError("Invalid email format", "email")

    return email.lower().strip()


def validate_url(url: str) -> str:
    """
    Validate URL format.

    Args:
        url: URL to validate

    Returns:
        Normalized URL

    Raises:
        ValidationError: If URL is invalid
    """
    if not url:
        raise ValidationError("URL is required", "url")

    # Basic URL format check
    url_pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    if not re.match(url_pattern, url):
        raise ValidationError("Invalid URL format", "url")

    return url.strip()

