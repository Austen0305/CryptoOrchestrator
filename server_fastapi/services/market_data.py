import asyncio
import random
from typing import AsyncGenerator, Dict, Any, List, Optional
import time
import logging

logger = logging.getLogger(__name__)


class MarketDataService:
    def __init__(self):
        self.subscribed_symbols = set()
        self.is_streaming = False
        # Simple in-memory candle cache per symbol: list of (ts, open, high, low, close, volume)
        self.candles: Dict[str, List[List[float]]] = {}
        # CoinGecko service for fallback price data
        self._coingecko_service: Optional[Any] = None

    def _get_coingecko_service(self):
        """Lazy load CoinGecko service"""
        if self._coingecko_service is None:
            try:
                from .coingecko_service import get_coingecko_service

                self._coingecko_service = get_coingecko_service()
            except ImportError:
                logger.warning("CoinGecko service not available")
                self._coingecko_service = None
        return self._coingecko_service

    async def get_price_with_fallback(self, symbol: str) -> Optional[float]:
        """
        Get price with fallback to CoinGecko if exchange API fails

        Args:
            symbol: Trading pair (e.g., "BTC/USD")

        Returns:
            Current price or None
        """
        # Try CoinGecko first (free tier, no API keys needed)
        coingecko = self._get_coingecko_service()
        if coingecko:
            try:
                price = await coingecko.get_price(symbol)
                if price:
                    logger.debug(f"Got price from CoinGecko for {symbol}: {price}")
                    return price
            except Exception as e:
                logger.debug(f"CoinGecko price fetch failed for {symbol}: {e}")

        # No fallback to mock data - return None if all sources fail
        logger.warning(f"Unable to get price for {symbol} from any source")
        return None

    async def stream_market_data(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream real-time market data updates using CoinGecko"""
        logger.info("Starting market data stream with real data")

        symbols = ["BTC/USD", "ETH/USD", "ADA/USD", "SOL/USD", "DOT/USD"]
        self.is_streaming = True

        # Get CoinGecko service
        coingecko = self._get_coingecko_service()
        if not coingecko:
            logger.error("CoinGecko service not available for market data streaming")
            return

        # Track previous prices for change calculation
        previous_prices: Dict[str, float] = {}

        try:
            while self.is_streaming:
                # Get real prices from CoinGecko
                for symbol in symbols:
                    try:
                        # Get current price
                        current_price = await coingecko.get_price(symbol)
                        if not current_price:
                            continue

                        # Calculate change from previous price
                        prev_price = previous_prices.get(symbol)
                        if prev_price:
                            price_change = (current_price - prev_price) / prev_price
                        else:
                            price_change = 0.0

                        # Get market data for volume
                        market_data = await coingecko.get_market_data(symbol)
                        volume_24h = (
                            market_data.get("volume_24h", 0) if market_data else 0
                        )

                        # Update previous price
                        previous_prices[symbol] = current_price

                        update = {
                            "type": "market_data",
                            "symbol": symbol,
                            "price": round(current_price, 4),
                            "change": round(price_change * 100, 2),  # percentage
                            "volume": (
                                round(volume_24h / 24.0 / 3600.0, 2)
                                if volume_24h > 0
                                else 0
                            ),  # Estimate per-second volume
                            "timestamp": int(time.time() * 1000),
                        }

                        # Update simple 1m candle aggregation
                        ts_minute = update["timestamp"] - (update["timestamp"] % 60_000)
                        bucket = self.candles.setdefault(symbol, [])
                        if bucket and bucket[-1][0] == ts_minute:
                            # mutate existing candle
                            candle = bucket[-1]
                            candle[2] = max(candle[2], update["price"])  # high
                            candle[3] = min(candle[3], update["price"])  # low
                            candle[4] = update["price"]  # close
                            candle[5] += update["volume"]
                        else:
                            # open new candle
                            bucket.append(
                                [
                                    ts_minute,  # 0 timestamp ms
                                    update["price"],  # 1 open
                                    update["price"],  # 2 high
                                    update["price"],  # 3 low
                                    update["price"],  # 4 close
                                    update["volume"],  # 5 volume
                                ]
                            )
                            # Keep only last 500 candles
                            if len(bucket) > 500:
                                del bucket[0 : len(bucket) - 500]

                        yield update
                    except Exception as symbol_error:
                        logger.warning(
                            f"Error getting data for {symbol}: {symbol_error}"
                        )
                        continue

                # Rate limit: CoinGecko free tier is 10-50 calls/minute
                # Update every 5 seconds to stay within limits
                await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Error in market data stream: {e}")
            raise
        finally:
            logger.info("Market data stream ended")

    def _get_base_price(self, symbol: str) -> float:
        """Get base price for a symbol (mock implementation)"""
        base_prices = {
            "BTC/USD": 45000,
            "ETH/USD": 2800,
            "ADA/USD": 0.45,
            "SOL/USD": 120,
            "DOT/USD": 8.50,
        }
        return base_prices.get(symbol, 100.0)

    def stop_streaming(self):
        """Stop the market data stream"""
        self.is_streaming = False
        logger.info("Market data streaming stopped")

    async def get_backfill(self, symbol: str, since_ms: int) -> List[List[float]]:
        """Return candles for a symbol since given millisecond timestamp."""
        candles = self.candles.get(symbol, [])
        return [c for c in candles if c[0] >= since_ms]
