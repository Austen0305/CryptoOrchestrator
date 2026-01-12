import asyncio
import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

logger = logging.getLogger(__name__)


class MarketDataService:
    def __init__(self):
        self.subscribed_symbols = set()
        self.is_streaming = False
        # Simple in-memory candle cache per symbol: list of (ts, open, high, low, close, volume)
        self.candles: dict[str, list[list[float]]] = {}
        # Free Market Data Service
        self._market_service: Any | None = None

    def _get_market_service(self):
        """Lazy load MarketDataService"""
        if self._market_service is None:
            try:
                from .market_data_service import get_market_data_service

                self._market_service = get_market_data_service()
            except ImportError:
                logger.warning("MarketDataService not available")
                self._market_service = None
        return self._market_service

    async def get_price_with_fallback(self, symbol: str) -> float | None:
        """
        Get price with fallback to free providers if exchange API fails

        Args:
            symbol: Trading pair (e.g., "BTC/USD")

        Returns:
            Current price or None
        """
        # Try Free Market Service first
        market_service = self._get_market_service()
        if market_service:
            try:
                price = await market_service.get_price(symbol)
                if price:
                    logger.debug(f"Got price from MarketService for {symbol}: {price}")
                    return price
            except Exception as e:
                logger.debug(f"MarketService price fetch failed for {symbol}: {e}")

        # No fallback to mock data - return None if all sources fail
        logger.warning(f"Unable to get price for {symbol} from any source")
        return None

    async def stream_market_data(self) -> AsyncGenerator[dict[str, Any], None]:
        """Stream real-time market data updates using Free Market Service"""
        logger.info("Starting market data stream with real data")

        symbols = ["BTC/USD", "ETH/USD", "ADA/USD", "SOL/USD", "DOT/USD"]
        self.is_streaming = True

        # Get Market Service
        market_service = self._get_market_service()
        if not market_service:
            logger.error("MarketDataService not available for market data streaming")
            return

        # Track previous prices for change calculation
        previous_prices: dict[str, float] = {}

        try:
            while self.is_streaming:
                # Get real prices from Market Service
                for symbol in symbols:
                    try:
                        # Get current price
                        current_price = await market_service.get_price(symbol)
                        if not current_price:
                            continue

                        # Calculate change from previous price
                        prev_price = previous_prices.get(symbol)
                        if prev_price:
                            price_change = (current_price - prev_price) / prev_price
                        else:
                            price_change = 0.0

                        # Get market data for volume
                        market_data = await market_service.get_market_data(symbol)
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

                # Rate limit: CoinCap 200/min approx check
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

        candles = self.candles.get(symbol, [])
        return [c for c in candles if c[0] >= since_ms]


# Singleton instance
_market_data_service: MarketDataService | None = None


def get_market_data_service() -> MarketDataService:
    """Get singleton MarketDataService instance"""
    global _market_data_service
    if _market_data_service is None:
        _market_data_service = MarketDataService()
    return _market_data_service
