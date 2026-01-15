"""
Free Market Data Service - Multi-Provider (CoinCap & CoinLore)
Provides real-time cryptocurrency data using free, public APIs.
Primary Provider: CoinCap (https://api.coincap.io/v2) - 200 req/min free
Secondary Provider: CoinLore (https://www.coinlore.com/cryptocurrency-data-api) - fallback
"""

import asyncio
import logging
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from typing import Any

import httpx
import polars as pl

logger = logging.getLogger(__name__)


class MarketDataService:
    """Free service for fetching cryptocurrency market data from multiple public APIs"""

    COINCAP_URL = "https://api.coincap.io/v2"
    COINLORE_URL = "https://api.coinlore.net/api"

    CACHE_TTL = 60  # Cache prices for 60 seconds

    def __init__(self):
        self.price_cache: dict[str, dict[str, Any]] = {}
        self.cache_timestamps: dict[str, float] = {}
        # Mapping for symbols to provider-specific IDs
        self._symbol_to_coincap_id: dict[str, str] = {}
        self._symbol_to_coinlore_id: dict[str, int] = {}
        self._last_request_time = 0
        self.is_streaming = False
        # Simple in-memory candle cache per symbol: list of (ts, open, high, low, close, volume)
        self.candles: dict[str, list[list[float]]] = {}

    def _get_symbol_from_pair(self, symbol: str) -> str:
        """Extract base symbol from trading pair (e.g., 'BTC/USD' -> 'BTC')"""
        return symbol.split("/")[0].upper()

    async def _coincap_get_id(self, symbol: str) -> str | None:
        """Get CoinCap ID for a symbol (e.g., 'bitcoin' for 'BTC')"""
        base_symbol = self._get_symbol_from_pair(symbol)

        if base_symbol in self._symbol_to_coincap_id:
            return self._symbol_to_coincap_id[base_symbol]

        try:
            url = f"{self.COINCAP_URL}/assets"
            params = {"search": base_symbol}
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                for asset in data.get("data", []):
                    if asset.get("symbol", "").upper() == base_symbol:
                        asset_id = asset.get("id")
                        if asset_id:
                            self._symbol_to_coincap_id[base_symbol] = asset_id
                            return asset_id
                return None
        except Exception as e:
            logger.debug(f"CoinCap ID lookup error for {symbol}: {e}")
            return None

    async def _coinlore_get_id(self, symbol: str) -> int | None:
        """Get CoinLore ID for a symbol"""
        base_symbol = self._get_symbol_from_pair(symbol)
        if base_symbol in self._symbol_to_coinlore_id:
            return self._symbol_to_coinlore_id[base_symbol]

        try:
            url = f"{self.COINLORE_URL}/tickers/"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                for coin in data.get("data", []):
                    if coin.get("symbol", "").upper() == base_symbol:
                        coin_id = coin.get("id")
                        if coin_id:
                            self._symbol_to_coinlore_id[base_symbol] = int(coin_id)
                            return int(coin_id)
                return None
        except Exception as e:
            logger.debug(f"CoinLore ID lookup error for {symbol}: {e}")
            return None

    async def get_price(self, symbol: str) -> float | None:
        """Get current USD price with multi-provider fallback"""
        cache_key = symbol.upper()
        now = datetime.now().timestamp()

        # Check cache
        if cache_key in self.price_cache:
            if (now - self.cache_timestamps.get(cache_key, 0)) < self.CACHE_TTL:
                return self.price_cache[cache_key].get("price")

        # Try CoinCap (Primary)
        price = await self._fetch_coincap_price(symbol)
        if price is not None:
            self._update_cache(cache_key, price)
            return price

        # Try CoinLore (Secondary)
        price = await self._fetch_coinlore_price(symbol)
        if price is not None:
            self._update_cache(cache_key, price)
            return price

        logger.warning(f"Could not fetch price for {symbol} from any provider")
        return None

    async def _fetch_coincap_price(self, symbol: str) -> float | None:
        try:
            asset_id = await self._coincap_get_id(symbol)
            if not asset_id:
                return None

            url = f"{self.COINCAP_URL}/assets/{asset_id}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                price = data.get("data", {}).get("priceUsd")
                return float(price) if price else None
        except Exception as e:
            logger.error(f"CoinCap price fetch error for {symbol}: {e}")
            return None

    async def _fetch_coinlore_price(self, symbol: str) -> float | None:
        try:
            coin_id = await self._coinlore_get_id(symbol)
            if not coin_id:
                return None

            url = f"{self.COINLORE_URL}/ticker/"
            params = {"id": coin_id}
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                if data and len(data) > 0:
                    price = data[0].get("price_usd")
                    return float(price) if price else None
            return None
        except Exception as e:
            logger.error(f"CoinLore price fetch error for {symbol}: {e}")
            return None

    def _update_cache(self, key: str, price: float):
        self.price_cache[key] = {"price": price}
        self.cache_timestamps[key] = datetime.now().timestamp()

    async def get_prices_batch(self, symbols: list[str]) -> dict[str, float | None]:
        """Get prices for multiple symbols (sequential due to free tier limits)"""
        results = {}
        for s in symbols:
            results[s] = await self.get_price(s)
        return results

    async def get_market_data(self, symbol: str) -> dict[str, Any] | None:
        """Alias for standard market data structure expected by bots"""
        price = await self.get_price(symbol)
        if price is None:
            return None
        return {
            "price": price,
            "timestamp": datetime.now().timestamp(),
            "provider": "free-market-data-service",
        }

    async def get_historical_prices(
        self, symbol: str, days: int = 7
    ) -> pl.DataFrame | None:
        """Get historical price data as Polars DataFrame"""
        try:
            asset_id = await self._coincap_get_id(symbol)
            if not asset_id:
                return None

            # Determine interval based on duration
            interval = "d1"
            if days <= 1:
                interval = "h1"
            elif days <= 7:
                interval = "h6"

            url = f"{self.COINCAP_URL}/assets/{asset_id}/history"
            # CoinCap history uses start/end timestamps in ms
            end = int(datetime.now().timestamp() * 1000)
            start = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

            params = {"interval": interval, "start": start, "end": end}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                # Optimized Polars creation
                points = [
                    {
                        "timestamp": point.get("time"),
                        "price": float(point.get("priceUsd")),
                    }
                    for point in data.get("data", [])
                ]

                if not points:
                    return pl.DataFrame(
                        schema={"timestamp": pl.Int64, "price": pl.Float64}
                    )

                return pl.DataFrame(points)

        except Exception as e:
            logger.error(f"Error fetching history for {symbol}: {e}")
            # Fallback to single point if history fails
            price = await self.get_price(symbol)
            if price:
                return pl.DataFrame(
                    {
                        "timestamp": [int(datetime.now().timestamp() * 1000)],
                        "price": [price],
                    }
                )
            return None

    async def get_ticker(self, symbol: str) -> dict[str, Any] | None:
        """Get comprehensive ticker data including 24h change"""
        # ... existing implementation (unchanged logic, just context) ...
        try:
            # Try CoinCap for detailed data
            asset_id = await self._coincap_get_id(symbol)
            if asset_id:
                url = f"{self.COINCAP_URL}/assets/{asset_id}"
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        data = response.json().get("data", {})
                        return {
                            "price": float(data.get("priceUsd", 0)),
                            "price_change_percentage_24h": float(
                                data.get("changePercent24Hr", 0)
                            ),
                            "market_cap": float(data.get("marketCapUsd", 0)),
                            "volume_24h": float(data.get("volumeUsd24Hr", 0)),
                            "timestamp": datetime.now().timestamp(),
                            "provider": "coincap",
                        }

            # Fallback to basic price
            price = await self.get_price(symbol)
            if price:
                return {
                    "price": price,
                    "price_change_percentage_24h": 0.0,
                    "timestamp": datetime.now().timestamp(),
                    "provider": "fallback",
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return None

    async def get_trending(self) -> pl.DataFrame | None:
        """Get trending assets (Top gainers/active) as Polars DataFrame"""
        try:
            url = f"{self.COINCAP_URL}/assets"
            params = {"limit": 20}  # Get top 20 to sort
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                coins = []
                for asset in data.get("data", []):
                    coins.append(
                        {
                            "id": asset.get("id"),
                            "symbol": asset.get("symbol"),
                            "name": asset.get("name"),
                            "current_price": float(asset.get("priceUsd", 0)),
                            "price_change_percentage_24h": float(
                                asset.get("changePercent24Hr", 0)
                            ),
                            "market_cap": float(asset.get("marketCapUsd", 0)),
                        }
                    )

                if not coins:
                    return pl.DataFrame()

                return pl.DataFrame(coins)
        except Exception as e:
            logger.error(f"Error fetching trending: {e}")
            return None

    async def stream_market_data(self) -> AsyncGenerator[dict[str, Any], None]:
        """Stream real-time market data updates using multi-provider support"""
        logger.info("Starting market data stream with real data")

        symbols = ["BTC/USD", "ETH/USD", "ADA/USD", "SOL/USD", "DOT/USD"]
        self.is_streaming = True

        # Track previous prices for change calculation
        previous_prices: dict[str, float] = {}

        try:
            while self.is_streaming:
                import time

                # Get real prices from providers
                for symbol in symbols:
                    try:
                        # Get current price using cached/multi-provider logic
                        current_price = await self.get_price(symbol)
                        if not current_price:
                            continue

                        # Calculate change from previous price
                        prev_price = previous_prices.get(symbol)
                        if prev_price:
                            price_change = (current_price - prev_price) / prev_price
                        else:
                            # Try to get 24h change from ticker if available
                            ticker = await self.get_ticker(symbol)
                            price_change = (
                                ticker.get("price_change_percentage_24h", 0) / 100.0
                                if ticker
                                else 0.0
                            )

                        # Update previous price
                        previous_prices[symbol] = current_price

                        update = {
                            "type": "market_data",
                            "symbol": symbol,
                            "price": round(current_price, 4),
                            "change": round(price_change * 100, 2),  # percentage
                            "volume": 0.0,  # Provider volume is usually 24h, hard to estimate per update accurately
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
                        else:
                            # open new candle
                            bucket.append(
                                [
                                    ts_minute,  # 0 timestamp ms
                                    update["price"],  # 1 open
                                    update["price"],  # 2 high
                                    update["price"],  # 3 low
                                    update["price"],  # 4 close
                                    0.0,  # 5 volume
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

                # Rate limit safety
                await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Error in market data stream: {e}")
            raise
        finally:
            logger.info("Market data stream ended")

    def stop_streaming(self):
        """Stop the market data stream"""
        self.is_streaming = False
        logger.info("Market data streaming stopped")

    def get_candles(self, symbol: str, since_ms: int = 0) -> list[list[float]]:
        """Get candle data for a symbol"""
        candles = self.candles.get(symbol, [])
        return [c for c in candles if c[0] >= since_ms]


# Singleton instance
_market_data_service: MarketDataService | None = None


def get_market_data_service() -> MarketDataService:
    global _market_data_service
    if _market_data_service is None:
        _market_data_service = MarketDataService()
    return _market_data_service
