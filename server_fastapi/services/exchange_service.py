import ccxt
import os
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TradingPair(BaseModel):
    symbol: str
    base_asset: str
    quote_asset: str
    current_price: float
    change_24h: float
    volume_24h: float
    high_24h: float
    low_24h: float

class MarketData(BaseModel):
    pair: str
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float

class KrakenFee(BaseModel):
    maker: float
    taker: float

class OrderBook(BaseModel):
    bids: List[List[float]]
    asks: List[List[float]]

class ExchangeService:
    def __init__(self, name: str, use_mock: Optional[bool] = None, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.name = name
        # Check production mode - mock data disabled in production
        from ..config.settings import get_settings
        settings = get_settings()
        production_mode = settings.production_mode or settings.is_production
        
        # Determine mock mode: explicit override > production check > env var > default False
        if use_mock is not None:
            self.use_mock = use_mock
        elif production_mode:
            self.use_mock = False  # Force real mode in production
            logger.info(f"Production mode detected - disabling mock data for {name}")
        else:
            # Only allow mock in development if explicitly enabled
            self.use_mock = os.getenv('ENABLE_MOCK_DATA', 'false').lower() == 'true' or os.getenv(f'USE_MOCK_{name.upper()}', 'false').lower() == 'true'
        
        self.exchange: Optional[Any] = None
        self.connected: bool = False
        self.api_key = api_key
        self.api_secret = api_secret

        if not self.use_mock:
            try:
                exchange_class = getattr(ccxt, name, None)
                if not exchange_class:
                    logger.warning(f"Exchange {name} not found in ccxt; falling back to undefined exchange client")
                    self.exchange = None
                    return

                # Use provided API keys or fall back to environment variables
                exchange_api_key = api_key or os.getenv(f'{name.upper()}_API_KEY') or os.getenv('KRAKEN_API_KEY')
                exchange_api_secret = api_secret or os.getenv(f'{name.upper()}_SECRET_KEY') or os.getenv('KRAKEN_SECRET_KEY')
                
                if not exchange_api_key or not exchange_api_secret:
                    logger.warning(f"No API keys provided for {name}. Exchange will be read-only or unavailable.")
                
                self.exchange = exchange_class({
                    'apiKey': exchange_api_key or '',
                    'secret': exchange_api_secret or '',
                    'enableRateLimit': True,
                })
            except Exception as err:
                logger.error(f"Failed to construct exchange client for {name}: {err}")
                self.exchange = None
        else:
            logger.info(f"ExchangeService({name}): running in MOCK mode")

    async def connect(self) -> None:
        try:
            if self.use_mock:
                self.connected = True
                return

            if not self.exchange:
                logger.error(f"No exchange client available for {self.name}")
                self.connected = False
                return

            await self.exchange.load_markets()
            self.connected = True
            logger.info(f"Connected to {self.name} API")
        except Exception as error:
            logger.error(f"Failed to connect to {self.name}: {error}")
            self.connected = False

    def is_connected(self) -> bool:
        return self.connected

    async def get_historical_data(self, symbol: str, timeframe: str = '1h', limit: int = 168) -> List[MarketData]:
        """Get historical data with circuit breaker protection"""
        if not self.connected:
            await self.connect()

        try:
            # Import circuit breaker
            try:
                from ..middleware.circuit_breaker import exchange_breaker, CircuitBreakerOpenError
            except ImportError:
                exchange_breaker = None
            
            async def _get_historical_data_internal():
                if self.use_mock:
                    now = int(datetime.now().timestamp() * 1000)
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
                            volume=0.1 * (0.5 + 0.5 * (i % 2))  # Random-like volume
                        ))
                    return data

                if not self.exchange or not hasattr(self.exchange, 'fetch_ohlcv'):
                    logger.error("Exchange client missing or does not support fetch_ohlcv")
                    return []

                ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, None, limit)

                return [
                    MarketData(
                        pair=symbol,
                        timestamp=timestamp,
                        open=open_price,
                        high=high,
                        low=low,
                        close=close,
                        volume=volume
                    )
                    for timestamp, open_price, high, low, close, volume in ohlcv
                ]
            
            # Use circuit breaker if available
            if exchange_breaker:
                try:
                    return await exchange_breaker.call(_get_historical_data_internal)
                except CircuitBreakerOpenError as e:
                    logger.error(f"Circuit breaker open for {self.name} historical data: {e}")
                    return []  # Return empty list on circuit breaker open
            else:
                return await _get_historical_data_internal()
        except Exception as error:
            logger.error(f"Failed to fetch historical data for {symbol} on {self.name}: {error}")
            return []

    async def get_all_trading_pairs(self) -> List[TradingPair]:
        if not self.connected:
            await self.connect()

        try:
            if self.use_mock:
                return [
                    TradingPair(
                        symbol='BTC/USD',
                        base_asset='BTC',
                        quote_asset='USD',
                        current_price=50000.0,
                        change_24h=1.2,
                        volume_24h=1200000.0,
                        high_24h=50500.0,
                        low_24h=49000.0
                    ),
                    TradingPair(
                        symbol='ETH/USD',
                        base_asset='ETH',
                        quote_asset='USD',
                        current_price=3500.0,
                        change_24h=-0.5,
                        volume_24h=600000.0,
                        high_24h=3600.0,
                        low_24h=3400.0
                    ),
                    TradingPair(
                        symbol='XRP/USD',
                        base_asset='XRP',
                        quote_asset='USD',
                        current_price=0.45,
                        change_24h=0.7,
                        volume_24h=200000.0,
                        high_24h=0.47,
                        low_24h=0.42
                    ),
                ]

            if not self.exchange or not hasattr(self.exchange, 'fetch_tickers'):
                logger.error("Exchange client missing or does not support fetch_tickers")
                return []

            tickers = await self.exchange.fetch_tickers()
            pairs = []

            for symbol, ticker in tickers.items():
                base_asset, quote_asset = symbol.split('/')
                if not base_asset or not quote_asset:
                    continue

                pairs.append(TradingPair(
                    symbol=symbol,
                    base_asset=base_asset,
                    quote_asset=quote_asset,
                    current_price=ticker.get('last', 0.0),
                    change_24h=ticker.get('percentage', 0.0),
                    volume_24h=ticker.get('quoteVolume', 0.0),
                    high_24h=ticker.get('high', 0.0),
                    low_24h=ticker.get('low', 0.0)
                ))

            return sorted(pairs, key=lambda x: x.volume_24h, reverse=True)
        except Exception as error:
            logger.error(f"Error fetching trading pairs from {self.name}: {error}")
            return []

    async def get_market_price(self, pair: str) -> Optional[float]:
        try:
            if self.use_mock:
                if pair == 'BTC/USD':
                    return 50000.0
                elif pair == 'ETH/USD':
                    return 3500.0
                return 1.0

            if not self.exchange or not hasattr(self.exchange, 'fetch_ticker'):
                return None

            ticker = await self.exchange.fetch_ticker(pair)
            return ticker.get('last')
        except Exception as error:
            logger.error(f"Error fetching price for {pair} on {self.name}: {error}")
            return None

    async def get_order_book(self, pair: str) -> OrderBook:
        """Get order book with circuit breaker protection"""
        try:
            # Import circuit breaker
            try:
                from ..middleware.circuit_breaker import exchange_breaker, CircuitBreakerOpenError
            except ImportError:
                exchange_breaker = None
            
            async def _get_order_book_internal():
                if self.use_mock:
                    return OrderBook(
                        bids=[[49990.0, 0.5], [49980.0, 1.2], [49950.0, 0.1]],
                        asks=[[50010.0, 0.4], [50020.0, 2.0], [50050.0, 0.3]]
                    )

                if not self.exchange or not hasattr(self.exchange, 'fetch_order_book'):
                    return OrderBook(bids=[], asks=[])

                order_book = await self.exchange.fetch_order_book(pair)
                return OrderBook(
                    bids=order_book['bids'][:10],
                    asks=order_book['asks'][:10]
                )
            
            # Use circuit breaker if available
            if exchange_breaker:
                try:
                    return await exchange_breaker.call(_get_order_book_internal)
                except CircuitBreakerOpenError as e:
                    logger.error(f"Circuit breaker open for {self.name} order book: {e}")
                    return OrderBook(bids=[], asks=[])  # Return empty order book
            else:
                return await _get_order_book_internal()
        except Exception as error:
            logger.error(f"Error fetching order book for {pair} on {self.name}: {error}")
            return OrderBook(bids=[], asks=[])

    async def place_order(self, pair: str, side: str, order_type: str, amount: float, price: Optional[float] = None) -> Dict[str, Any]:
        """Place order with circuit breaker protection"""
        try:
            # Import circuit breaker
            try:
                from ..middleware.circuit_breaker import exchange_breaker, CircuitBreakerOpenError
            except ImportError:
                # Fallback if circuit breaker not available
                exchange_breaker = None
            
            async def _place_order_internal():
                if self.use_mock:
                    return {
                        'id': f'mock-{int(datetime.now().timestamp() * 1000)}',
                        'pair': pair,
                        'side': side,
                        'type': order_type,
                        'amount': amount,
                        'price': price,
                        'status': 'closed',
                        'timestamp': int(datetime.now().timestamp() * 1000)
                    }

                if not self.exchange:
                    raise ValueError('Exchange client not initialized')

                if order_type == 'market':
                    if side == 'buy':
                        order = await self.exchange.create_market_buy_order(pair, amount)
                    else:
                        order = await self.exchange.create_market_sell_order(pair, amount)
                elif order_type == 'limit' and price is not None:
                    if side == 'buy':
                        order = await self.exchange.create_limit_buy_order(pair, amount, price)
                    else:
                        order = await self.exchange.create_limit_sell_order(pair, amount, price)
                else:
                    raise ValueError('Invalid order type or missing price for limit order')

                return order
            
            # Use circuit breaker if available
            if exchange_breaker:
                try:
                    return await exchange_breaker.call(_place_order_internal)
                except CircuitBreakerOpenError as e:
                    logger.error(f"Circuit breaker open for {self.name}: {e}")
                    raise RuntimeError(f"Exchange {self.name} is temporarily unavailable. Please try again later.")
            else:
                return await _place_order_internal()
                
        except Exception as error:
            logger.error(f"Error placing order on {self.name}: {error}")
            raise error

    async def get_balance(self) -> Dict[str, float]:
        """Get balance with circuit breaker protection"""
        try:
            # Import circuit breaker
            try:
                from ..middleware.circuit_breaker import exchange_breaker, CircuitBreakerOpenError
            except ImportError:
                exchange_breaker = None
            
            async def _get_balance_internal():
                if self.use_mock:
                    return {'USD': 100000.0, 'BTC': 1.2, 'ETH': 10.0}

                if not self.exchange or not hasattr(self.exchange, 'fetch_balance'):
                    return {}

                balance = await self.exchange.fetch_balance()
                return balance.get('total', {})
            
            # Use circuit breaker if available
            if exchange_breaker:
                try:
                    return await exchange_breaker.call(_get_balance_internal)
                except CircuitBreakerOpenError as e:
                    logger.error(f"Circuit breaker open for {self.name} balance: {e}")
                    return {}  # Return empty balance on circuit breaker open
            else:
                return await _get_balance_internal()
        except Exception as error:
            logger.error(f"Error fetching balance from {self.name}: {error}")
            return {}

    async def get_ohlcv(self, pair: str, timeframe: str = '1h', limit: int = 100) -> List[List[float]]:
        try:
            if self.use_mock:
                now = int(datetime.now().timestamp() * 1000)
                close = 50000.0 if pair.startswith('BTC') else 3500.0 if pair.startswith('ETH') else 1.0
                open_price = close - 10
                high = max(close, open_price) + 5
                low = min(close, open_price) - 5
                volume = 0.1 * (0.5 + 0.5 * (int(now) % 2))
                return [[now, open_price, high, low, close, volume]]

            if not self.connected:
                await self.connect()

            if not self.exchange or not hasattr(self.exchange, 'fetch_ohlcv'):
                logger.error("Exchange OHLCV not supported or client missing")
                return []

            ohlcv = await self.exchange.fetch_ohlcv(pair, timeframe, None, limit)
            return ohlcv
        except Exception as error:
            logger.error(f"Error fetching OHLCV for {pair} on {self.name}: {error}")
            return []

    async def get_api_quota(self) -> Dict[str, Any]:
        try:
            if self.use_mock:
                return {
                    'remaining': 1000,
                    'reset': int(datetime.now().timestamp() * 1000) + 60 * 1000
                }

            if not self.exchange:
                return {'remaining': 0, 'reset': 0}

            # This is a simplified implementation
            # Real implementation would check rate limit headers
            return {'remaining': 0, 'reset': 0}
        except Exception as error:
            logger.error(f"Failed to get API quota for {self.name}: {error}")
            return {'remaining': 0, 'reset': 0}

    def get_fees(self, volume_usd: float = 0.0) -> KrakenFee:
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
        else:
            return KrakenFee(maker=0.0000, taker=0.0010)

    def calculate_fee(self, amount: float, price: float, is_maker: bool = False, volume_usd: float = 0.0) -> float:
        fees = self.get_fees(volume_usd)
        fee_rate = fees.maker if is_maker else fees.taker
        return amount * price * fee_rate

    def calculate_total_with_fee(self, amount: float, price: float, side: str, is_maker: bool = False, volume_usd: float = 0.0) -> Dict[str, float]:
        subtotal = amount * price
        fee = self.calculate_fee(amount, price, is_maker, volume_usd)
        total = subtotal + fee if side == 'buy' else subtotal - fee
        return {
            'subtotal': subtotal,
            'fee': fee,
            'total': total
        }

# Convenience factory for default exchange
default_exchange_name = os.getenv('EXCHANGE_NAME', 'kraken')
default_exchange = ExchangeService(default_exchange_name)
