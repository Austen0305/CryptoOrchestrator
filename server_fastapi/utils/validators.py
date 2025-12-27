"""
Enhanced input validation utilities
Provides comprehensive validation for trading inputs
"""

import re
from typing import Optional, List
from pydantic import field_validator, ValidationError
from decimal import Decimal, InvalidOperation


class TradingValidators:
    """Collection of trading-specific validators"""

    # Supported trading symbols pattern
    SYMBOL_PATTERN = re.compile(r"^[A-Z]{2,10}/[A-Z]{2,10}$")

    # Common valid symbols for suggestions
    COMMON_SYMBOLS = [
        "BTC/USDT",
        "ETH/USDT",
        "BNB/USDT",
        "SOL/USDT",
        "ADA/USDT",
        "XRP/USDT",
        "DOT/USDT",
        "AVAX/USDT",
        "MATIC/USDT",
        "LINK/USDT",
        "BTC/USD",
        "ETH/USD",
        "BNB/USD",
    ]

    @staticmethod
    def validate_symbol(symbol: str) -> str:
        """
        Validate trading symbol format.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')

        Returns:
            Normalized symbol in uppercase

        Raises:
            ValueError: If symbol format is invalid
        """
        if not symbol:
            raise ValueError("Symbol cannot be empty")

        # Normalize to uppercase
        symbol = symbol.upper().strip()

        # Check format
        if not TradingValidators.SYMBOL_PATTERN.match(symbol):
            # Try to suggest a similar symbol
            suggestion = TradingValidators._suggest_symbol(symbol)
            if suggestion:
                raise ValueError(
                    f"Invalid symbol format '{symbol}'. Did you mean '{suggestion}'? "
                    f"Format should be BASE/QUOTE (e.g., BTC/USDT)"
                )
            else:
                raise ValueError(
                    f"Invalid symbol format '{symbol}'. "
                    f"Format should be BASE/QUOTE (e.g., BTC/USDT)"
                )

        return symbol

    @staticmethod
    def _suggest_symbol(invalid_symbol: str) -> Optional[str]:
        """Suggest a similar valid symbol"""
        invalid_upper = invalid_symbol.upper().replace("/", "")

        # Look for similar symbols
        for valid in TradingValidators.COMMON_SYMBOLS:
            valid_clean = valid.replace("/", "")
            if invalid_upper in valid_clean or valid_clean in invalid_upper:
                return valid

        return None

    @staticmethod
    def validate_amount(
        amount: float,
        min_amount: float = 0.0,
        max_amount: Optional[float] = None,
        field_name: str = "Amount",
    ) -> float:
        """
        Validate trading amount.

        Args:
            amount: Amount to validate
            min_amount: Minimum allowed amount
            max_amount: Maximum allowed amount (if any)
            field_name: Name of field for error messages

        Returns:
            Validated amount

        Raises:
            ValueError: If amount is invalid
        """
        if amount is None:
            raise ValueError(f"{field_name} cannot be None")

        if amount <= min_amount:
            raise ValueError(f"{field_name} must be greater than {min_amount}")

        if max_amount and amount > max_amount:
            raise ValueError(f"{field_name} cannot exceed {max_amount}")

        # Check for reasonable precision (max 8 decimal places)
        try:
            decimal_amount = Decimal(str(amount))
            if abs(decimal_amount.as_tuple().exponent) > 8:
                raise ValueError(f"{field_name} has too many decimal places (max 8)")
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f"{field_name} is not a valid number: {e}")

        return amount

    @staticmethod
    def validate_percentage(percentage: float, field_name: str = "Percentage") -> float:
        """
        Validate percentage value (0-100).

        Args:
            percentage: Percentage to validate
            field_name: Name of field for error messages

        Returns:
            Validated percentage

        Raises:
            ValueError: If percentage is invalid
        """
        if percentage < 0:
            raise ValueError(f"{field_name} cannot be negative")

        if percentage > 100:
            raise ValueError(f"{field_name} cannot exceed 100%")

        return percentage

    @staticmethod
    def validate_price(
        price: float, min_price: float = 0.0, field_name: str = "Price"
    ) -> float:
        """
        Validate price value.

        Args:
            price: Price to validate
            min_price: Minimum allowed price
            field_name: Name of field for error messages

        Returns:
            Validated price

        Raises:
            ValueError: If price is invalid
        """
        if price <= min_price:
            raise ValueError(f"{field_name} must be greater than {min_price}")

        return price

    @staticmethod
    def validate_balance_sufficient(
        current_balance: float, required_amount: float
    ) -> None:
        """
        Validate that balance is sufficient for operation.

        Args:
            current_balance: Current available balance
            required_amount: Amount required for operation

        Raises:
            ValueError: If balance is insufficient
        """
        if current_balance < required_amount:
            raise ValueError(
                f"Insufficient balance: You have ${current_balance:.2f}, "
                f"need ${required_amount:.2f} "
                f"(${required_amount - current_balance:.2f} short)"
            )

    @staticmethod
    def validate_order_type(order_type: str) -> str:
        """
        Validate order type.

        Args:
            order_type: Type of order

        Returns:
            Normalized order type

        Raises:
            ValueError: If order type is invalid
        """
        valid_types = ["market", "limit", "stop", "stop_limit"]
        order_type = order_type.lower().strip()

        if order_type not in valid_types:
            raise ValueError(
                f"Invalid order type '{order_type}'. "
                f"Must be one of: {', '.join(valid_types)}"
            )

        return order_type

    @staticmethod
    def validate_side(side: str) -> str:
        """
        Validate trading side.

        Args:
            side: Trading side

        Returns:
            Normalized side

        Raises:
            ValueError: If side is invalid
        """
        valid_sides = ["buy", "sell"]
        side = side.lower().strip()

        if side not in valid_sides:
            raise ValueError(f"Invalid side '{side}'. Must be 'buy' or 'sell'")

        return side

    @staticmethod
    def validate_timeframe(timeframe: str) -> str:
        """
        Validate chart timeframe.

        Args:
            timeframe: Timeframe string

        Returns:
            Validated timeframe

        Raises:
            ValueError: If timeframe is invalid
        """
        valid_timeframes = [
            "1m",
            "3m",
            "5m",
            "15m",
            "30m",
            "1h",
            "2h",
            "4h",
            "6h",
            "8h",
            "12h",
            "1d",
            "3d",
            "1w",
            "1M",
        ]

        if timeframe not in valid_timeframes:
            raise ValueError(
                f"Invalid timeframe '{timeframe}'. "
                f"Must be one of: {', '.join(valid_timeframes)}"
            )

        return timeframe

    @staticmethod
    def validate_confidence(confidence: float) -> float:
        """
        Validate confidence score (0-1).

        Args:
            confidence: Confidence score

        Returns:
            Validated confidence

        Raises:
            ValueError: If confidence is invalid
        """
        if not 0 <= confidence <= 1:
            raise ValueError(f"Confidence must be between 0 and 1, got {confidence}")

        return confidence


# Convenience functions for common validations
def validate_trade_params(
    symbol: str, amount: float, price: Optional[float] = None
) -> tuple:
    """
    Validate common trading parameters.

    Returns:
        Tuple of (validated_symbol, validated_amount, validated_price)
    """
    validated_symbol = TradingValidators.validate_symbol(symbol)
    validated_amount = TradingValidators.validate_amount(
        amount, min_amount=0.0, field_name="Trade amount"
    )
    validated_price = (
        TradingValidators.validate_price(price, field_name="Price") if price else None
    )

    return validated_symbol, validated_amount, validated_price


def validate_bot_config(name: str, symbol: str, amount: float) -> dict:
    """
    Validate bot configuration parameters.

    Returns:
        Dict with validated parameters
    """
    if not name or len(name.strip()) == 0:
        raise ValueError("Bot name cannot be empty")

    if len(name) > 100:
        raise ValueError("Bot name cannot exceed 100 characters")

    validated_symbol = TradingValidators.validate_symbol(symbol)
    validated_amount = TradingValidators.validate_amount(
        amount, min_amount=1.0, field_name="Bot amount"
    )

    return {
        "name": name.strip(),
        "symbol": validated_symbol,
        "amount": validated_amount,
    }
