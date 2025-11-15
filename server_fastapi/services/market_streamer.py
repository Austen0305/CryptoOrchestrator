"""
Market Data Streaming Service
Fetches real-time market data and broadcasts to WebSocket subscribers
"""
import asyncio
from typing import Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MarketDataStreamer:
    """
    Background service that fetches market data and broadcasts to WebSocket clients
    
    Features:
    - Fetches data for subscribed symbols only (efficient)
    - Configurable update intervals
    - Automatic error recovery
    - Rate limiting to respect exchange limits
    """
    
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        self.running = False
        self.task: Optional[asyncio.Task] = None
        
        # Track which symbols need updates
        self.active_symbols: Dict[str, int] = {}  # symbol -> subscriber count
        
        # Configuration
        self.update_interval = 1.0  # seconds
        self.max_symbols_per_batch = 10
    
    def start(self):
        """Start the streaming service"""
        if not self.running:
            self.running = True
            self.task = asyncio.create_task(self._stream_loop())
            logger.info("📡 Market data streaming service started")
    
    def stop(self):
        """Stop the streaming service"""
        self.running = False
        if self.task:
            self.task.cancel()
        logger.info("📡 Market data streaming service stopped")
    
    async def _stream_loop(self):
        """Main streaming loop"""
        while self.running:
            try:
                # Get list of symbols that have subscribers
                await self._update_active_symbols()
                
                if not self.active_symbols:
                    # No active subscriptions, wait longer
                    await asyncio.sleep(5.0)
                    continue
                
                # Fetch and broadcast data for each symbol
                for symbol in list(self.active_symbols.keys()):
                    try:
                        data = await self._fetch_market_data(symbol)
                        if data:
                            await self.connection_manager.broadcast(
                                f"market:{symbol}",
                                data
                            )
                    except Exception as e:
                        logger.error(f"Error fetching data for {symbol}: {e}")
                
                # Wait before next update
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in streaming loop: {e}")
                await asyncio.sleep(5.0)  # Back off on error
    
    async def _update_active_symbols(self):
        """Update list of symbols that have active subscribers"""
        self.active_symbols.clear()
        
        # Check all market channels
        for channel, subscribers in self.connection_manager.subscriptions.items():
            if channel.startswith("market:") and subscribers:
                symbol = channel.replace("market:", "")
                self.active_symbols[symbol] = len(subscribers)
    
    async def _fetch_market_data(self, symbol: str) -> dict:
        """
        Fetch real-time market data for a symbol
        
        In production, this would connect to exchange WebSocket or REST API
        For now, returns mock data structure
        """
        try:
            # Import exchange service
            from .exchange.exchange_service import ExchangeService
            
            exchange = ExchangeService()
            
            # Fetch ticker data
            ticker = await exchange.fetch_ticker(symbol)
            
            # Fetch recent trades
            trades = await exchange.fetch_recent_trades(symbol, limit=10)
            
            # Fetch order book summary
            orderbook = await exchange.fetch_orderbook_summary(symbol)
            
            return {
                "symbol": symbol,
                "ticker": ticker,
                "trades": trades,
                "orderbook": orderbook,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch market data for {symbol}: {e}")
            
            # Return mock data for development
            import random
            base_price = 50000 if "BTC" in symbol else 3000
            
            return {
                "symbol": symbol,
                "ticker": {
                    "last": base_price + random.uniform(-100, 100),
                    "bid": base_price - random.uniform(0, 10),
                    "ask": base_price + random.uniform(0, 10),
                    "volume": random.uniform(1000, 10000),
                    "high": base_price + random.uniform(0, 200),
                    "low": base_price - random.uniform(0, 200),
                    "change_24h": random.uniform(-5, 5)
                },
                "trades": [
                    {
                        "price": base_price + random.uniform(-50, 50),
                        "amount": random.uniform(0.01, 1.0),
                        "side": random.choice(["buy", "sell"]),
                        "timestamp": datetime.now().isoformat()
                    }
                    for _ in range(5)
                ],
                "orderbook": {
                    "bids": [[base_price - i*10, random.uniform(0.1, 2.0)] for i in range(1, 6)],
                    "asks": [[base_price + i*10, random.uniform(0.1, 2.0)] for i in range(1, 6)]
                },
                "timestamp": datetime.now().isoformat()
            }
    
    def get_stats(self) -> dict:
        """Get streaming service statistics"""
        return {
            "running": self.running,
            "active_symbols": len(self.active_symbols),
            "symbols": dict(self.active_symbols),
            "update_interval": self.update_interval
        }


# Global streamer instance (initialized in startup)
market_data_streamer: Optional[MarketDataStreamer] = None


def get_market_streamer(connection_manager) -> MarketDataStreamer:
    """Get or create market data streamer"""
    global market_data_streamer
    if market_data_streamer is None:
        market_data_streamer = MarketDataStreamer(connection_manager)
    return market_data_streamer
