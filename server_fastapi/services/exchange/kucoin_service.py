"""
KuCoin Exchange Service - Full integration with complete feature set
"""
import ccxt
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from dataclasses import dataclass
import logging
from datetime import datetime
import asyncio
import base64
import hmac
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class KuCoinFee:
    """KuCoin fee structure"""
    maker: float
    taker: float
    vip_level: int = 0  # VIP level (0-12)


class KuCoinService:
    """Full KuCoin exchange service with complete feature set"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, passphrase: Optional[str] = None, sandbox: bool = False, use_mock: Optional[bool] = None):
        self.name = 'kucoin'
        # Check production mode - mock data disabled in production
        from ...config.settings import get_settings
        settings = get_settings()
        production_mode = settings.production_mode or settings.is_production
        
        # Determine mock mode: explicit override > production check > env var > default False
        if use_mock is not None:
            self.use_mock = use_mock
        elif production_mode:
            self.use_mock = False  # Force real mode in production
            logger.info("Production mode detected - disabling mock data for KuCoin")
        else:
            # Only allow mock in development if explicitly enabled
            self.use_mock = os.getenv("ENABLE_MOCK_DATA", "false").lower() == "true" or os.getenv("USE_MOCK_KUCOIN", "false").lower() == "true"
        
        self.connected = False
        self.exchange = None
        self.sandbox = sandbox
        
        if not self.use_mock:
            try:
                exchange_config = {
                    'apiKey': api_key or os.getenv('KUCOIN_API_KEY'),
                    'secret': api_secret or os.getenv('KUCOIN_SECRET_KEY'),
                    'password': passphrase or os.getenv('KUCOIN_PASSPHRASE'),
                    'enableRateLimit': True,
                }
                
                if sandbox:
                    # KuCoin sandbox
                    exchange_config['urls'] = {
                        'api': {
                            'public': 'https://openapi-sandbox.kucoin.com',
                            'private': 'https://openapi-sandbox.kucoin.com',
                        }
                    }
                
                self.exchange = ccxt.kucoin(exchange_config)
            except Exception as err:
                logger.error(f"Failed to construct KuCoin client: {err}")
                self.exchange = None
        else:
            logger.info("KuCoinService: running in MOCK mode")
    
    async def connect(self) -> None:
        """Connect to KuCoin API"""
        try:
            if self.use_mock:
                self.connected = True
                return
            
            if not self.exchange:
                logger.error("No exchange client available for KuCoin")
                self.connected = False
                return
            
            await self.exchange.load_markets()
            self.connected = True
            logger.info("Connected to KuCoin API")
        except Exception as error:
            logger.error(f"Failed to connect to KuCoin: {error}")
            self.connected = False
    
    def is_connected(self) -> bool:
        """Check if connected to KuCoin"""
        return self.connected
    
    async def get_historical_data(self, symbol: str, timeframe: str = '1h', limit: int = 168) -> List[Dict[str, Any]]:
        """Get historical OHLCV data from KuCoin"""
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
            logger.error(f"Error fetching historical data from KuCoin: {error}")
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
            logger.error(f"Error fetching ticker from KuCoin: {error}")
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
            logger.error(f"Error fetching order book from KuCoin: {error}")
            return {'bids': [], 'asks': []}
    
    async def place_order(
        self,
        pair: str,
        side: str,
        type_: str,
        amount: float,
        price: Optional[float] = None,
        client_oid: Optional[str] = None  # KuCoin client order ID
    ) -> Dict[str, Any]:
        """Place order on KuCoin"""
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
            
            if price:
                order_params['price'] = price
            
            if client_oid:
                order_params['clientOrderId'] = client_oid
            
            order = await self.exchange.create_order(**order_params)
            return order
        except Exception as error:
            logger.error(f"Error placing order on KuCoin: {error}")
            raise error
    
    async def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Cancel order on KuCoin"""
        try:
            if self.use_mock:
                return {'id': order_id, 'status': 'cancelled'}
            
            if not self.exchange:
                raise ValueError('Exchange client not initialized')
            
            result = await self.exchange.cancel_order(order_id, symbol)
            return result
        except Exception as error:
            logger.error(f"Error cancelling order on KuCoin: {error}")
            raise error
    
    async def cancel_all_orders(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Cancel all open orders (KuCoin specific feature)"""
        try:
            if self.use_mock:
                return {'cancelled': 0}
            
            if not self.exchange:
                raise ValueError('Exchange client not initialized')
            
            result = await self.exchange.cancel_all_orders(symbol)
            return result
        except Exception as error:
            logger.error(f"Error cancelling all orders on KuCoin: {error}")
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
            logger.error(f"Error fetching open orders from KuCoin: {error}")
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
            logger.error(f"Error fetching balance from KuCoin: {error}")
            return {}
    
    async def get_fees(self) -> KuCoinFee:
        """Get KuCoin fee structure with VIP level"""
        try:
            if self.use_mock:
                return KuCoinFee(maker=0.001, taker=0.001, vip_level=0)
            
            if not self.exchange:
                return KuCoinFee(maker=0.001, taker=0.001)
            
            # KuCoin fees vary by VIP level
            # Default: 0.1% maker, 0.1% taker
            # VIP levels 1-12 reduce fees progressively
            account = await self.exchange.fetch_balance()
            vip_level = account.get('info', {}).get('vipLevel', 0)
            
            # Fee calculation based on VIP level (simplified)
            base_maker = 0.001
            base_taker = 0.001
            maker_fee = max(0.0001, base_maker * (1 - vip_level * 0.05))  # 5% reduction per VIP level
            taker_fee = max(0.0001, base_taker * (1 - vip_level * 0.05))
            
            return KuCoinFee(
                maker=maker_fee,
                taker=taker_fee,
                vip_level=vip_level
            )
        except Exception as error:
            logger.error(f"Error fetching fees from KuCoin: {error}")
            return KuCoinFee(maker=0.001, taker=0.001)
    
    async def get_server_time(self) -> int:
        """Get KuCoin server time"""
        try:
            if self.use_mock:
                return int(datetime.now().timestamp() * 1000)
            
            if not self.exchange:
                return int(datetime.now().timestamp() * 1000)
            
            server_time = await self.exchange.fetch_time()
            return server_time
        except Exception as error:
            logger.error(f"Error fetching server time from KuCoin: {error}")
            return int(datetime.now().timestamp() * 1000)
    
    async def get_symbols_list(self, quote_currency: str = 'USDT') -> List[str]:
        """Get list of trading symbols on KuCoin"""
        try:
            if not self.connected:
                await self.connect()
            
            if self.use_mock:
                return ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
            
            if not self.exchange:
                return []
            
            markets = self.exchange.markets
            symbols = []
            
            for symbol, market in markets.items():
                if market['quote'] == quote_currency and market['active']:
                    symbols.append(symbol)
            
            return symbols
        except Exception as error:
            logger.error(f"Error fetching symbols from KuCoin: {error}")
            return []


# Global service instance
kucoin_service = KuCoinService()
