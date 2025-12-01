"""
Coinbase Exchange Service - Enhanced integration with advanced features
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
class CoinbaseFee:
    """Coinbase fee structure"""
    maker: float
    taker: float
    tier: str = "basic"  # basic, advanced, pro


class CoinbaseService:
    """Enhanced Coinbase exchange service with advanced features"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, passphrase: Optional[str] = None, sandbox: bool = False, use_mock: Optional[bool] = None):
        self.name = 'coinbasepro'  # CCXT uses 'coinbasepro' for Coinbase Pro/Advanced Trade
        # Check production mode - mock data disabled in production
        from ...config.settings import get_settings
        settings = get_settings()
        production_mode = settings.production_mode or settings.is_production
        
        # Determine mock mode: explicit override > production check > env var > default False
        if use_mock is not None:
            self.use_mock = use_mock
        elif production_mode:
            self.use_mock = False  # Force real mode in production
            logger.info("Production mode detected - disabling mock data for Coinbase")
        else:
            # Only allow mock in development if explicitly enabled
            self.use_mock = os.getenv("ENABLE_MOCK_DATA", "false").lower() == "true" or os.getenv("USE_MOCK_COINBASE", "false").lower() == "true"
        
        self.connected = False
        self.exchange = None
        self.sandbox = sandbox
        
        if not self.use_mock:
            try:
                exchange_config = {
                    'apiKey': api_key or os.getenv('COINBASE_API_KEY'),
                    'secret': api_secret or os.getenv('COINBASE_API_SECRET'),
                    'password': passphrase or os.getenv('COINBASE_PASSPHRASE'),
                    'enableRateLimit': True,
                }
                
                if sandbox:
                    # Coinbase Pro sandbox
                    exchange_config['urls'] = {
                        'api': {
                            'public': 'https://public.sandbox.pro.coinbase.com',
                            'private': 'https://public.sandbox.pro.coinbase.com',
                        }
                    }
                
                self.exchange = ccxt.coinbasepro(exchange_config)
            except Exception as err:
                logger.error(f"Failed to construct Coinbase client: {err}")
                self.exchange = None
        else:
            logger.info("CoinbaseService: running in MOCK mode")
    
    async def connect(self) -> None:
        """Connect to Coinbase API"""
        try:
            if self.use_mock:
                self.connected = True
                return
            
            if not self.exchange:
                logger.error("No exchange client available for Coinbase")
                self.connected = False
                return
            
            await self.exchange.load_markets()
            self.connected = True
            logger.info("Connected to Coinbase API")
        except Exception as error:
            logger.error(f"Failed to connect to Coinbase: {error}")
            self.connected = False
    
    def is_connected(self) -> bool:
        """Check if connected to Coinbase"""
        return self.connected
    
    async def get_historical_data(self, symbol: str, timeframe: str = '1h', limit: int = 168) -> List[Dict[str, Any]]:
        """Get historical OHLCV data from Coinbase"""
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
            logger.error(f"Error fetching historical data from Coinbase: {error}")
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
            logger.error(f"Error fetching ticker from Coinbase: {error}")
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
            logger.error(f"Error fetching order book from Coinbase: {error}")
            return {'bids': [], 'asks': []}
    
    async def place_order(
        self,
        pair: str,
        side: str,
        type_: str,
        amount: float,
        price: Optional[float] = None,
        stop: Optional[float] = None  # Stop price for stop orders
    ) -> Dict[str, Any]:
        """Place order on Coinbase"""
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
            
            if type_ == 'market':
                if side == 'buy':
                    order = await self.exchange.create_market_buy_order(pair, amount)
                else:
                    order = await self.exchange.create_market_sell_order(pair, amount)
            elif type_ == 'limit' and price:
                if side == 'buy':
                    order = await self.exchange.create_limit_buy_order(pair, amount, price)
                else:
                    order = await self.exchange.create_limit_sell_order(pair, amount, price)
            elif type_ == 'stop' and stop:
                # Stop order (stop-loss or stop-limit)
                order_params = {
                    'symbol': pair,
                    'side': side.upper(),
                    'amount': amount,
                    'stopPrice': stop
                }
                if price:
                    order_params['price'] = price
                order = await self.exchange.create_order(**order_params)
            else:
                raise ValueError('Invalid order type or missing required parameters')
            
            return order
        except Exception as error:
            logger.error(f"Error placing order on Coinbase: {error}")
            raise error
    
    async def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Cancel order on Coinbase"""
        try:
            if self.use_mock:
                return {'id': order_id, 'status': 'cancelled'}
            
            if not self.exchange:
                raise ValueError('Exchange client not initialized')
            
            # Coinbase requires symbol for cancel order
            if not symbol:
                raise ValueError('Symbol required for cancelling Coinbase orders')
            
            result = await self.exchange.cancel_order(order_id, symbol)
            return result
        except Exception as error:
            logger.error(f"Error cancelling order on Coinbase: {error}")
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
            logger.error(f"Error fetching open orders from Coinbase: {error}")
            return []
    
    async def get_balance(self) -> Dict[str, float]:
        """Get account balance"""
        try:
            if self.use_mock:
                return {'USD': 100000, 'BTC': 1.2, 'ETH': 10}
            
            if not self.exchange:
                return {}
            
            balance = await self.exchange.fetch_balance()
            return balance.get('total', {})
        except Exception as error:
            logger.error(f"Error fetching balance from Coinbase: {error}")
            return {}
    
    async def get_fees(self) -> CoinbaseFee:
        """Get Coinbase fee structure"""
        try:
            if self.use_mock:
                return CoinbaseFee(maker=0.005, taker=0.005, tier="basic")
            
            if not self.exchange:
                return CoinbaseFee(maker=0.005, taker=0.005)
            
            # Coinbase Pro fees (variable based on 30-day volume)
            # Basic tier: 0.5% maker, 0.5% taker
            # Would need to fetch account info to determine actual tier
            return CoinbaseFee(
                maker=0.005,  # 0.5%
                taker=0.005,  # 0.5%
                tier="basic"
            )
        except Exception as error:
            logger.error(f"Error fetching fees from Coinbase: {error}")
            return CoinbaseFee(maker=0.005, taker=0.005)
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get Coinbase account information"""
        try:
            if self.use_mock:
                return {
                    'tier': 'basic',
                    'trading_enabled': True,
                    'fiat_currency': 'USD'
                }
            
            if not self.exchange:
                return {}
            
            # Coinbase-specific account info endpoint
            account = await self.exchange.fetch_balance()
            return {
                'tier': account.get('info', {}).get('tier', 'basic'),
                'trading_enabled': account.get('info', {}).get('trading_enabled', True),
                'fiat_currency': account.get('info', {}).get('fiat_currency', 'USD')
            }
        except Exception as error:
            logger.error(f"Error fetching account info from Coinbase: {error}")
            return {}


# Global service instance
coinbase_service = CoinbaseService()
