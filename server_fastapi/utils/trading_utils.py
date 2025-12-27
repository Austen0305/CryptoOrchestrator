"""
Trading utility functions.
Centralizes common trading-related operations.
"""


def normalize_trading_mode(mode: str) -> str:
    """
    Normalize trading mode: 'live' -> 'real' for backend compatibility.

    The frontend may use 'live' as a user-friendly term, but the backend
    uses 'real' to represent live trading mode.

    Args:
        mode: Trading mode string ('paper', 'real', or 'live')

    Returns:
        Normalized trading mode ('paper' or 'real')

    Example:
        >>> normalize_trading_mode("live")
        'real'

        >>> normalize_trading_mode("real")
        'real'

        >>> normalize_trading_mode("paper")
        'paper'
    """
    return "real" if mode == "live" else mode
