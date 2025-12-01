"""
Binance Exchange Service - Enhanced integration with specific features
"""
import ccxt
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from dataclasses import dataclass
import logging
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class BinanceFee:
    """Binance fee structure"""
    maker: float
    taker: float
    bnb_discount: bool = False  # BNB discount if enabled


class BinanceService:
    """Enhanced Binance exchange service with specific features"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, testnet: bool = False, use_mock: Optional[bool] = None):
        self.name = 'binance'
        # Check production mode - mock data disabled in production
        from ...config.settings import get_settings
        settings = get_settings()
        production_mode = settings.production_mode or settings.is_production
        
        # Determine mock mode: explicit override > production check > env var > default False
        if use_mock is not None:
            self.use_mock = use_mock
        elif production_mode:
            self.use_mock = False  # Force real mode in production
            logger.info("Production mode detected - disabling mock data for Binance")
        else:
            # Only allow mock in development if explicitly enabled
            self.use_mock = os.getenv("ENABLE_MOCK_DATA", "false").lower() == "true" or os.getenv("USE_MOCK_BINANCE", "false").lower() == "true"
        
        self.connected = False
        self.exchange = None
        self.testnet = testnet
        
        if not self.use_mock:
            try:
                exchange_config = {
                    'apiKey': api_key or os.getenv('BINANCE_API_KEY'),
                    'secret': api_secret or os.getenv('BINANCE_API_SECRET'),
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'spot',  # 'spot', 'margin', 'future', 'delivery'
                    }
                }
                
                if testnet:
                    exchange_config['options']['testnet'] = True
                    # Binance testnet URL
                    exchange_config['urls'] = {
                        'api': {
                            'public': 'https://testnet.binance.vision/api',
                            'private': 'https://testnet.binance.vision/api',
                        }
                    }
                
                self.exchange = ccxt.binance(exchange_config)
            except Exception as err:
                logger.error(f"Failed to construct Binance client: {err}")
                self.exchange = None
        else:
            logger.info("BinanceService: running in MOCK mode")
    
    async def connect(self) -> None:
        """Connect to Binance API"""
        try:
            if self.use_mock:
                self.connected = True
                return
            
            if not self.exchange:
                logger.error("No exchange client available for Binance")
                self.connected = False
                return
            
            await self.exchange.load_markets()
            self.connected = True
            logger.info("Connected to Binance API")
        except Exception as error:
            logger.error(f"Failed to connect to Binance: {error}")
            self.connected = False
    
    def is_connected(self) -> bool:
        """Check if connected to Binance"""
        return self.connected
    
    async def get_historical_data(self, symbol: str, timeframe: str = '1h', limit: int = 168) -> List[Dict[str, Any]]:
        """Get historical OHLCV data from Binance"""
        if not self.connected:
            await self.connect()
        
        try:
            if self.use_mock:
                now = int(datetime.now().timestamp() * 1000)
                data = []
                for i in range(min(limit, 24)):
                    timestamp = now - i * 60 * 60 * 1000
                    close = 50000 + i if symbol.startswith('BTC') else 3500 + i if symbol.startswith('ETH') else 1 + i
                    data.append({
                        'timestamp': timestamp,
                        'open': close - 5,
                        'high': close + 10,
                        'low': close - 10,
                        'close': close,
                        'volume': 1000 + i * 10
                    })
                return data
            
            if not self.exchange:
                return []
            
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            return [
                {
                    'timestamp': candle[0],
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5]
                }
                for candle in ohlcv
            ]
        except Exception as error:
            logger.error(f"Error fetching historical data from Binance: {error}")
            return []
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker data for a symbol"""
        if not self.connected:
            await self.connect()
        
        try:
            if self.use_mock:
                return {
                    'symbol': symbol,
                    'last': 50000.0 if symbol.startswith('BTC') else 3500.0 if symbol.startswith('ETH') else 1.0,
                    'bid': 49990.0,
                    'ask': 50010.0,
                    'volume': 1000.0,
                    'timestamp': int(datetime.now().timestamp() * 1000)
                }
            
            if not self.exchange:
                return {}
            
            ticker = await self.exchange.fetch_ticker(symbol)
            return {
                'symbol': ticker['symbol'],
                'last': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'volume': ticker['quoteVolume'] if 'quoteVolume' in ticker else ticker['volume'],
                'timestamp': ticker['timestamp']
            }
        except Exception as error:
            logger.error(f"Error fetching ticker from Binance: {error}")
            return {}
    
    async def get_order_book(self, pair: str, depth: int = 20) -> Dict[str, List[List[float]]]:
        """Get order book with depth"""
        if not self.connected:
            await self.connect()
        
        try:
            if self.use_mock:
                return {
                    'bids': [[49990.0, 1.0], [49985.0, 2.0]],
                    'asks': [[50010.0, 1.0], [50015.0, 2.0]]
                }
            
            if not self.exchange:
                return {'bids': [], 'asks': []}
            
            orderbook = await self.exchange.fetch_order_book(pair, depth)
            return {
                'bids': orderbook['bids'][:depth],
                'asks': orderbook['asks'][:depth]
            }
        except Exception as error:
            logger.error(f"Error fetching order book from Binance: {error}")
            return {'bids': [], 'asks': []}
    
    async def place_order(
        self,
        pair: str,
        side: str,
        type_: str,
        amount: float,
        price: Optional[float] = None,
        time_in_force: str = 'GTC'  # GTC, IOC, FOK
    ) -> Dict[str, Any]:
        """Place order on Binance with time-in-force options"""
        try:
            if self.use_mock:
                return {
                    'id': f'mock-{int(datetime.now().timestamp() * 1000)}',
                    'pair': pair,
                    'side': side,
                    'type': type_,
                    'amount': amount,
                    'price': price,
                    'status': 'closed',
                    'timestamp': int(datetime.now().timestamp() * 1000)
                }
            
            if not self.exchange:
                raise ValueError('Exchange client not initialized')
            
            order_params = {
                'symbol': pair,
                'side': side.upper(),
                'type': type_.upper(),
                'amount': amount,
            }
            
            if type_ == 'limit':
                if not price:
                    raise ValueError('Price required for limit orders')
                order_params['price'] = price
                order_params['timeInForce'] = time_in_force
            
            # Binance-specific order types
            if type_ == 'stop_loss' or type_ == 'stop_loss_limit':
                order_params['stopPrice'] = price  # Stop price for stop-loss orders
            
            order = await self.exchange.create_order(**order_params)
            return order
        except Exception as error:
            logger.error(f"Error placing order on Binance: {error}")
            raise error
    
    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel order on Binance"""
        try:
            if self.use_mock:
                return {'id': order_id, 'status': 'cancelled'}
            
            if not self.exchange:
                raise ValueError('Exchange client not initialized')
            
            result = await self.exchange.cancel_order(order_id, symbol)
            return result
        except Exception as error:
            logger.error(f"Error cancelling order on Binance: {error}")
            raise error
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get open orders (optionally for a specific symbol)"""
        try:
            if self.use_mock:
                return []
            
            if not self.exchange:
                return []
            
            orders = await self.exchange.fetch_open_orders(symbol)
            return [order for order in orders]
        except Exception as error:
            logger.error(f"Error fetching open orders from Binance: {error}")
            return []
    
    async def get_balance(self) -> Dict[str, float]:
        """Get account balance"""
        try:
            if self.use_mock:
                return {'USDT': 100000, 'BTC': 1.2, 'ETH': 10}
            
            if not self.exchange:
                return {}
            
            balance = await self.exchange.fetch_balance()
            return balance.get('total', {})
        except Exception as error:
            logger.error(f"Error fetching balance from Binance: {error}")
            return {}
    
    async def get_fees(self) -> BinanceFee:
        """Get Binance fee structure"""
        try:
            if self.use_mock:
                return BinanceFee(maker=0.001, taker=0.001, bnb_discount=False)
            
            if not self.exchange:
                return BinanceFee(maker=0.001, taker=0.001)
            
            # Binance standard fees: 0.1% maker and taker
            # Can be reduced with BNB discount or VIP levels
            account = await self.exchange.fetch_balance()
            
            # Check if BNB discount is enabled (would need additional API call)
            bnb_discount = False  # Placeholder
            
            return BinanceFee(
                maker=0.001,  # 0.1%
                taker=0.001,  # 0.1%
                bnb_discount=bnb_discount
            )
        except Exception as error:
            logger.error(f"Error fetching fees from Binance: {error}")
            return BinanceFee(maker=0.001, taker=0.001)
    
    async def get_server_time(self) -> int:
        """Get Binance server time"""
        try:
            if self.use_mock:
                return int(datetime.now().timestamp() * 1000)
            
            if not self.exchange:
                return int(datetime.now().timestamp() * 1000)
            
            # Binance provides server time endpoint
            server_time = await self.exchange.fetch_time()
            return server_time
        except Exception as error:
            logger.error(f"Error fetching server time from Binance: {error}")
            return int(datetime.now().timestamp() * 1000)
    
    async def get_trading_pairs(self, quote_currency: str = 'USDT') -> List[Dict[str, Any]]:
        """Get trading pairs available on Binance"""
        try:
            if not self.connected:
                await self.connect()
            
            if self.use_mock:
                return [
                    {'symbol': 'BTC/USDT', 'base': 'BTC', 'quote': 'USDT'},
                    {'symbol': 'ETH/USDT', 'base': 'ETH', 'quote': 'USDT'},
                ]
            
            if not self.exchange:
                return []
            
            markets = self.exchange.markets
            pairs = []
            
            for symbol, market in markets.items():
                if market['quote'] == quote_currency and market['active']:
                    pairs.append({
                        'symbol': symbol,
                        'base': market['base'],
                        'quote': market['quote'],
                        'active': market.get('active', True),
                        'precision': market.get('precision', {})
                    })
            
            return pairs
        except Exception as error:
            logger.error(f"Error fetching trading pairs from Binance: {error}")
            return []
    
    async def get_24h_ticker_stats(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get 24-hour ticker statistics (all symbols or specific)"""
        try:
            if not self.connected:
                await self.connect()
            
            if self.use_mock:
                return {
                    'priceChange': 100.0,
                    'priceChangePercent': 2.0,
                    'volume': 1000.0,
                    'high': 51000.0,
                    'low': 49000.0
                }
            
            if not self.exchange:
                return {}
            
            if symbol:
                ticker = await self.exchange.fetch_ticker(symbol)
            else:
                tickers = await self.exchange.fetch_tickers()
                return {symbol: {
                    'priceChange': ticker.get('change', 0),
                    'priceChangePercent': ticker.get('percentage', 0),
                    'volume': ticker.get('quoteVolume', ticker.get('volume', 0)),
                    'high': ticker.get('high', 0),
                    'low': ticker.get('low', 0)
                } for symbol, ticker in tickers.items()}
            
            return {
                'priceChange': ticker.get('change', 0),
                'priceChangePercent': ticker.get('percentage', 0),
                'volume': ticker.get('quoteVolume', ticker.get('volume', 0)),
                'high': ticker.get('high', 0),
                'low': ticker.get('low', 0)
            }
        except Exception as error:
            logger.error(f"Error fetching 24h stats from Binance: {error}")
            return {}


# Global service instance (can be initialized with credentials)
binance_service = BinanceService()
