"""
Kraken exchange service for FastAPI backend
Migrated from TypeScript krakenService.ts
"""

import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import ccxt.async_support as ccxt
from pydantic import BaseModel
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class TradingPair:
    symbol: str
    baseAsset: str
    quoteAsset: str
    currentPrice: float
    change24h: float
    volume24h: float
    high24h: float
    low24h: float


@dataclass
class MarketData:
    pair: str
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class KrakenFee:
    maker: float
    taker: float


class KrakenService:
    """Kraken exchange service"""

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, use_mock: Optional[bool] = None):
        self.name = 'kraken'
        # Check production mode - mock data disabled in production
        from ...config.settings import get_settings
        settings = get_settings()
        production_mode = settings.production_mode or settings.is_production
        
        # Determine mock mode: explicit override > production check > env var > default False
        if use_mock is not None:
            self.use_mock = use_mock
        elif production_mode:
            self.use_mock = False  # Force real mode in production
            logger.info("Production mode detected - disabling mock data for Kraken")
        else:
            # Only allow mock in development if explicitly enabled
            self.use_mock = os.getenv("ENABLE_MOCK_DATA", "false").lower() == "true" or os.getenv("USE_MOCK_KRAKEN", "false").lower() == "true"
        
        self.connected = False
        self.exchange = None

        if not self.use_mock:
            try:
                # Use provided API keys or fall back to environment variables
                exchange_api_key = api_key or os.getenv('KRAKEN_API_KEY')
                exchange_api_secret = api_secret or os.getenv('KRAKEN_SECRET_KEY')
                
                if not exchange_api_key or not exchange_api_secret:
                    logger.warning(f"No API keys provided for Kraken. Exchange will be read-only or unavailable.")
                
                self.exchange = ccxt.kraken({
                    'apiKey': exchange_api_key or '',
                    'secret': exchange_api_secret or '',
                    'enableRateLimit': True,
                })
            except Exception as err:
                logger.error(f"Failed to construct Kraken client: {err}")
                self.exchange = None
        else:
            logger.info("KrakenService: running in MOCK mode")

    async def connect(self) -> None:
        try:
            if self.use_mock:
                self.connected = True
                return

            if not self.exchange:
                logger.warning("No exchange client available for kraken")
                self.connected = False
                return

            await self.exchange.loadMarkets()
            self.connected = True
            logger.info("Connected to Kraken API")
        except Exception as error:
            logger.error(f"Failed to connect to kraken: {error}")
            self.connected = False

    def is_connected(self) -> bool:
        return self.connected

    async def get_historical_data(self, symbol: str, timeframe: str = '1h', limit: int = 168) -> List[MarketData]:
        if not self.connected:
            await self.connect()

        try:
            if self.use_mock:
                import time
                now = int(time.time() * 1000)
                data = []
                for i in range(min(limit, 24)):
                    timestamp = now - i * 60 * 60 * 1000
                    close = 50000 + i if symbol.startswith('BTC') else 3500 + i if symbol.startswith('ETH') else 1 + i
                    data.append(MarketData(
                        pair=symbol,
                        timestamp=timestamp,
                        open=close - 5,
                        high=close + 10,
                        low=close - 10,
                        close=close,
                        volume=0.1 * (i + 1)
                    ))
                return data

            if not self.exchange:
                logger.warning('Exchange client missing or does not support fetchOHLCV')
                return []

            ohlcv = await self.exchange.fetchOHLCV(symbol, timeframe, None, limit)
            return [
                MarketData(
                    pair=symbol,
                    timestamp=timestamp,
                    open=open_,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume
                )
                for timestamp, open_, high, low, close, volume in ohlcv
            ]
        except Exception as error:
            logger.error(f"Failed to fetch historical data for {symbol} on kraken: {error}")
            return []

    async def get_all_trading_pairs(self) -> List[TradingPair]:
        if not self.connected:
            await self.connect()

        try:
            if self.use_mock:
                return [
                    TradingPair(symbol='BTC/USD', baseAsset='BTC', quoteAsset='USD', currentPrice=50000, change24h=1.2, volume24h=1200000, high24h=50500, low24h=49000),
                    TradingPair(symbol='ETH/USD', baseAsset='ETH', quoteAsset='USD', currentPrice=3500, change24h=-0.5, volume24h=600000, high24h=3600, low24h=3400),
                    TradingPair(symbol='XRP/USD', baseAsset='XRP', quoteAsset='USD', currentPrice=0.45, change24h=0.7, volume24h=200000, high24h=0.47, low24h=0.42),
                ]

            if not self.exchange:
                logger.warning('Exchange client missing or does not support fetchTickers')
                return []

            tickers = await self.exchange.fetchTickers()
            pairs = []

            for symbol, ticker in tickers.items():
                base_asset, quote_asset = symbol.split('/')
                pairs.append(TradingPair(
                    symbol=symbol,
                    baseAsset=base_asset,
                    quoteAsset=quote_asset,
                    currentPrice=ticker.get('last', 0),
                    change24h=ticker.get('percentage', 0),
                    volume24h=ticker.get('quoteVolume', 0),
                    high24h=ticker.get('high', 0),
                    low24h=ticker.get('low', 0)
                ))

            return sorted(pairs, key=lambda x: x.volume24h, reverse=True)
        except Exception as error:
            logger.error(f"Error fetching trading pairs from kraken: {error}")
            return []

    async def get_market_price(self, pair: str) -> Optional[float]:
        try:
            if self.use_mock:
                if pair == 'BTC/USD':
                    return 50000
                elif pair == 'ETH/USD':
                    return 3500
                return 1

            if not self.exchange:
                return None
            ticker = await self.exchange.fetchTicker(pair)
            return ticker.get('last')
        except Exception as error:
            logger.error(f"Error fetching price for {pair} on kraken: {error}")
            return None

    async def get_order_book(self, pair: str) -> Dict[str, List[List[float]]]:
        try:
            if self.use_mock:
                return {
                    'bids': [[49990, 0.5], [49980, 1.2], [49950, 0.1]],
                    'asks': [[50010, 0.4], [50020, 2.0], [50050, 0.3]]
                }

            if not self.exchange:
                return {'bids': [], 'asks': []}
            order_book = await self.exchange.fetchOrderBook(pair)
            return {
                'bids': order_book['bids'][:10],
                'asks': order_book['asks'][:10]
            }
        except Exception as error:
            logger.error(f"Error fetching order book for {pair} on kraken: {error}")
            return {'bids': [], 'asks': []}

    async def place_order(self, pair: str, side: str, type_: str, amount: float, price: Optional[float] = None) -> Dict[str, Any]:
        try:
            if self.use_mock:
                return {
                    'id': f'mock-{asyncio.get_event_loop().time() * 1000}',
                    'pair': pair,
                    'side': side,
                    'type': type_,
                    'amount': amount,
                    'price': price,
                    'status': 'closed',
                    'timestamp': int(asyncio.get_event_loop().time() * 1000)
                }

            if not self.exchange:
                raise ValueError('Exchange client not initialized')

            if type_ == 'market':
                if side == 'buy':
                    order = await self.exchange.createMarketBuyOrder(pair, amount)
                else:
                    order = await self.exchange.createMarketSellOrder(pair, amount)
            elif type_ == 'limit' and price:
                if side == 'buy':
                    order = await self.exchange.createLimitBuyOrder(pair, amount, price)
                else:
                    order = await self.exchange.createLimitSellOrder(pair, amount, price)
            else:
                raise ValueError('Invalid order type or missing price for limit order')

            return order
        except Exception as error:
            logger.error(f"Error placing order on kraken: {error}")
            raise error

    async def get_balance(self) -> Dict[str, float]:
        try:
            if self.use_mock:
                return {'USD': 100000, 'BTC': 1.2, 'ETH': 10}
            if not self.exchange:
                return {}
            balance = await self.exchange.fetchBalance()
            return balance.get('total', {})
        except Exception as error:
            logger.error(f"Error fetching balance from kraken: {error}")
            return {}

    async def get_ohlcv(self, pair: str, timeframe: str = '1h', limit: int = 100) -> List[List[float]]:
        try:
            if self.use_mock:
                import time
                now = int(time.time() * 1000)
                close = 50000 if pair.startswith('BTC') else 3500 if pair.startswith('ETH') else 1
                open_ = close - 10
                high = max(close, open_) + 5
                low = min(close, open_) - 5
                volume = 0.1
                return [[now, open_, high, low, close, volume]]

            if not self.connected:
                await self.connect()
            if not self.exchange:
                logger.warning('Exchange OHLCV not supported or client missing')
                return []
            ohlcv = await self.exchange.fetchOHLCV(pair, timeframe, None, limit)
            return ohlcv
        except Exception as error:
            logger.error(f"Error fetching OHLCV for {pair} on kraken: {error}")
            return []

    async def get_api_quota(self) -> Dict[str, Any]:
        try:
            if self.use_mock:
                import time
                return {'remaining': 1000, 'reset': int(time.time() * 1000) + 60 * 1000}
            if not self.exchange:
                return {'remaining': 0, 'reset': 0}
            # Best-effort: some exchanges may not provide headers
            if hasattr(self.exchange, 'rateLimit') and isinstance(self.exchange.rateLimit, (int, float)):
                return {
                    'remaining': max(0, 1000 - int(self.exchange.rateLimit)),
                    'reset': int(asyncio.get_event_loop().time() * 1000) + 60 * 1000
                }
            return {'remaining': 0, 'reset': 0}
        except Exception as error:
            logger.error(f"Error fetching API quota from kraken: {error}")
            return {'remaining': 0, 'reset': 0}

    def get_fees(self, volume_usd: float = 0) -> KrakenFee:
        if volume_usd < 50000:
            return KrakenFee(maker=0.0016, taker=0.0026)
        elif volume_usd < 100000:
            return KrakenFee(maker=0.0014, taker=0.0024)
        elif volume_usd < 250000:
            return KrakenFee(maker=0.0012, taker=0.0022)
        elif volume_usd < 500000:
            return KrakenFee(maker=0.0010, taker=0.0020)
        elif volume_usd < 1000000:
            return KrakenFee(maker=0.0008, taker=0.0018)
        elif volume_usd < 2500000:
            return KrakenFee(maker=0.0006, taker=0.0016)
        elif volume_usd < 5000000:
            return KrakenFee(maker=0.0004, taker=0.0014)
        elif volume_usd < 10000000:
            return KrakenFee(maker=0.0002, taker=0.0012)
        return KrakenFee(maker=0.0000, taker=0.0010)

    def calculate_fee(self, amount: float, price: float, is_maker: bool = False, volume_usd: float = 0) -> float:
        fees = self.get_fees(volume_usd)
        fee_rate = fees.maker if is_maker else fees.taker
        return amount * price * fee_rate

    def calculate_total_with_fee(self, amount: float, price: float, side: str, is_maker: bool = False, volume_usd: float = 0) -> Dict[str, float]:
        subtotal = amount * price
        fee = self.calculate_fee(amount, price, is_maker, volume_usd)
        total = subtotal + fee if side == 'buy' else subtotal - fee
        return {'subtotal': subtotal, 'fee': fee, 'total': total}


# Create singleton instance
kraken_service = KrakenService()