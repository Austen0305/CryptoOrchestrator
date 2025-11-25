"""
Database models for the application.
"""

from .base import Base, BaseModel, TimestampMixin, SoftDeleteMixin, User
from .bot import Bot
from .risk_alert import RiskAlert
from .risk_limit import RiskLimit
from .portfolio import Portfolio
from .trade import Trade

# Optional candle model import guarded (created in this patch)
try:
    from .candle import Candle  # type: ignore
except Exception:
    Candle = None  # noqa: N816

# Optional exchange_api_key model import guarded
try:
    from .exchange_api_key import ExchangeAPIKey  # type: ignore
except Exception:
    ExchangeAPIKey = None  # noqa: N816

__all__ = [
    'Base',
    'BaseModel',
    'TimestampMixin',
    'SoftDeleteMixin',
    'User',
    'Bot',
    'RiskAlert',
    'RiskLimit',
    'Portfolio',
    'Trade',
    'Candle',
    'ExchangeAPIKey'
]