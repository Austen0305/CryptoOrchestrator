"""
Database models for the application.
"""

from .base import Base, BaseModel, TimestampMixin, SoftDeleteMixin, User
from .bot import Bot
from .risk_alert import RiskAlert
from .risk_limit import RiskLimit
from .portfolio import Portfolio
from .trade import Trade
from .follow import Follow, CopiedTrade
from .order import Order, OrderType, OrderStatus
from .wallet import Wallet, WalletTransaction, WalletType, TransactionType, TransactionStatus
from .idempotency import IdempotencyKey

# New competitive bot models
try:
    from .grid_bot import GridBot
except Exception:
    GridBot = None  # noqa: N816

try:
    from .dca_bot import DCABot
except Exception:
    DCABot = None  # noqa: N816

try:
    from .infinity_grid import InfinityGrid
except Exception:
    InfinityGrid = None  # noqa: N816

try:
    from .trailing_bot import TrailingBot
except Exception:
    TrailingBot = None  # noqa: N816

try:
    from .futures_position import FuturesPosition
except Exception:
    FuturesPosition = None  # noqa: N816

# Optional strategy model import
try:
    from .strategy import Strategy, StrategyVersion  # type: ignore
except Exception:
    Strategy = None  # noqa: N816
    StrategyVersion = None  # noqa: N816

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
    'ExchangeAPIKey',
    'Follow',
    'CopiedTrade',
    'Order',
    'OrderType',
    'OrderStatus',
    'Wallet',
    'WalletTransaction',
    'WalletType',
    'TransactionType',
    'TransactionStatus',
    'IdempotencyKey',
    'Strategy',
    'StrategyVersion',
    # New competitive bot models
    'GridBot',
    'DCABot',
    'InfinityGrid',
    'TrailingBot',
    'FuturesPosition'
]