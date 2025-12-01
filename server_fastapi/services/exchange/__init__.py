"""
Exchange Services Module
"""
try:
    from .kraken_service import KrakenService
    kraken_service = KrakenService()
except Exception:
    kraken_service = None

from .binance_service import BinanceService, BinanceFee, binance_service
from .coinbase_service import CoinbaseService, CoinbaseFee, coinbase_service
from .kucoin_service import KuCoinService, KuCoinFee, kucoin_service
from .smart_routing import (
    SmartRoutingService,
    RoutingStrategy,
    OrderQuote,
    RoutingResult,
    Exchange,
    smart_routing_service
)

__all__ = [
    "KrakenService",
    "kraken_service",
    "BinanceService",
    "BinanceFee",
    "binance_service",
    "CoinbaseService",
    "CoinbaseFee",
    "coinbase_service",
    "KuCoinService",
    "KuCoinFee",
    "kucoin_service",
    "SmartRoutingService",
    "RoutingStrategy",
    "OrderQuote",
    "RoutingResult",
    "Exchange",
    "smart_routing_service",
]