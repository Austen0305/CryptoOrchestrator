"""
Free Cryptocurrency Price Service - CoinLore API Integration
Provides real-time cryptocurrency price data - completely free, no API key required
CoinLore API: https://www.coinlore.com/cryptocurrency-data-api
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class CryptoPriceService:
    """Free service for fetching cryptocurrency data from CoinLore API"""

    BASE_URL = "https://api.coinlore.net/api"
    RATE_LIMIT_DELAY = 1.0  # Seconds between requests (1 request/second recommended)
    CACHE_TTL = 60  # Cache prices for 60 seconds

    def __init__(self):
        self.last_request_time = 0
        self.price_cache: dict[str, dict[str, Any]] = {}
        self.cache_timestamps: dict[str, float] = {}
        # CoinLore uses numeric IDs, we'll map symbols to IDs
        self._symbol_to_id_cache: dict[str, int] = {}

    async def _rate_limit(self):
        """Enforce rate limiting"""
        now = asyncio.get_event_loop().time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.RATE_LIMIT_DELAY:
            await asyncio.sleep(self.RATE_LIMIT_DELAY - time_since_last)
        self.last_request_time = asyncio.get_event_loop().time()

    def _get_symbol_from_pair(self, symbol: str) -> str:
        """Extract base symbol from trading pair (e.g., 'BTC/USD' -> 'BTC')"""
        return symbol.split("/")[0].upper()

    async def _get_coin_id(self, symbol: str) -> int | None:
        """Get CoinLore coin ID for a symbol"""
        base_symbol = self._get_symbol_from_pair(symbol)

        # Check cache first
        if base_symbol in self._symbol_to_id_cache:
            return self._symbol_to_id_cache[base_symbol]

        try:
            await self._rate_limit()

            # Get ticker list and find the coin
            url = f"{self.BASE_URL}/tickers/"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                # Find coin by symbol
                for coin in data.get("data", []):
                    if coin.get("symbol", "").upper() == base_symbol:
                        coin_id = coin.get("id")
                        if coin_id:
                            self._symbol_to_id_cache[base_symbol] = coin_id
                            return coin_id

                logger.warning(f"Coin ID not found for symbol {base_symbol}")
                return None

        except Exception as e:
            logger.error(f"Error fetching coin ID for {symbol}: {e}")
            return None

    async def get_price(self, symbol: str) -> float | None:
        """
        Get current price for a symbol

        Args:
            symbol: Trading pair (e.g., "BTC/USD")

        Returns:
            Current price in USD or None if unavailable
        """
        cache_key = symbol.upper()

        # Check cache
        if cache_key in self.price_cache:
            cache_time = self.cache_timestamps.get(cache_key, 0)
            if (datetime.now().timestamp() - cache_time) < self.CACHE_TTL:
                return self.price_cache[cache_key].get("price")

        try:
            await self._rate_limit()

            coin_id = await self._get_coin_id(symbol)
            if not coin_id:
                return None

            url = f"{self.BASE_URL}/ticker/"
            params = {"id": coin_id}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                if data and len(data) > 0:
                    coin_data = data[0]
                    price = coin_data.get("price_usd")
                    if price:
                        try:
                            price_float = float(price)
                            # Update cache
                            self.price_cache[cache_key] = {"price": price_float}
                            self.cache_timestamps[cache_key] = (
                                datetime.now().timestamp()
                            )
                            return price_float
                        except (ValueError, TypeError):
                            logger.warning(
                                f"Invalid price format for {symbol}: {price}"
                            )
                            return None

            logger.warning(f"Price not found for {symbol}")
            return None

        except httpx.HTTPStatusError as e:
            logger.error(f"CoinLore API error for {symbol}: {e}")
            # Return cached price if available
            if cache_key in self.price_cache:
                return self.price_cache[cache_key].get("price")
            return None
        except Exception as e:
            logger.error(f"Error fetching price from CoinLore for {symbol}: {e}")
            # Return cached price if available
            if cache_key in self.price_cache:
                return self.price_cache[cache_key].get("price")
            return None

    async def get_prices_batch(self, symbols: list[str]) -> dict[str, float | None]:
        """
        Get current prices for multiple symbols

        Args:
            symbols: List of trading pairs (e.g., ["BTC/USD", "ETH/USD"])

        Returns:
            Dict mapping symbols to prices (None if unavailable)
        """
        if not symbols:
            return {}

        # Separate cached and uncached symbols
        cached_prices: dict[str, float | None] = {}
        uncached_symbols: list[str] = []

        for symbol in symbols:
            cache_key = symbol.upper()

            # Check cache
            if cache_key in self.price_cache:
                cache_time = self.cache_timestamps.get(cache_key, 0)
                if (datetime.now().timestamp() - cache_time) < self.CACHE_TTL:
                    cached_prices[symbol] = self.price_cache[cache_key].get("price")
                    continue

            uncached_symbols.append(symbol)

        # If all symbols are cached, return immediately
        if not uncached_symbols:
            return cached_prices

        # Fetch uncached symbols (CoinLore doesn't support batch, so we fetch individually)
        all_prices: dict[str, float | None] = cached_prices.copy()

        for symbol in uncached_symbols:
            price = await self.get_price(symbol)
            all_prices[symbol] = price

        return all_prices

    async def get_market_data(self, symbol: str) -> dict[str, Any] | None:
        """
        Get comprehensive market data for a symbol

        Returns:
            Dict with price, change_24h, volume_24h, high_24h, low_24h, market_cap
        """
        cache_key = symbol.upper()

        # Check cache
        if cache_key in self.price_cache:
            cache_time = self.cache_timestamps.get(cache_key, 0)
            if (datetime.now().timestamp() - cache_time) < self.CACHE_TTL:
                cached_data = self.price_cache[cache_key]
                # If cache has full market data, return it
                if "change_24h" in cached_data:
                    return cached_data

        try:
            await self._rate_limit()

            coin_id = await self._get_coin_id(symbol)
            if not coin_id:
                return None

            url = f"{self.BASE_URL}/ticker/"
            params = {"id": coin_id}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                if data and len(data) > 0:
                    coin_data = data[0]

                    try:
                        result = {
                            "price": float(coin_data.get("price_usd", 0)),
                            "change_24h": float(coin_data.get("percent_change_24h", 0)),
                            "volume_24h": float(coin_data.get("volume24", 0)),
                            "high_24h": float(coin_data.get("high24h", 0)),
                            "low_24h": float(coin_data.get("low24h", 0)),
                            "market_cap": float(coin_data.get("market_cap_usd", 0)),
                            "timestamp": datetime.now().timestamp(),
                        }

                        # Update cache
                        self.price_cache[cache_key] = result
                        self.cache_timestamps[cache_key] = datetime.now().timestamp()

                        return result
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error parsing market data for {symbol}: {e}")
                        return None

            logger.warning(f"Market data not found for {symbol}")
            return None

        except httpx.HTTPStatusError as e:
            logger.error(f"CoinLore API error for {symbol}: {e}")
            # Return cached data if available
            if cache_key in self.price_cache:
                return self.price_cache[cache_key]
            return None
        except Exception as e:
            logger.error(f"Error fetching market data from CoinLore for {symbol}: {e}")
            # Return cached data if available
            if cache_key in self.price_cache:
                return self.price_cache[cache_key]
            return None

    async def get_historical_prices(
        self, symbol: str, days: int = 7
    ) -> list[dict[str, Any]] | None:
        """
        Get historical price data
        Note: CoinLore doesn't provide historical data in free tier,
        so we return current price as a single data point

        Args:
            symbol: Trading pair
            days: Number of days (not used, kept for compatibility)

        Returns:
            List of price data points (single point with current price)
        """
        try:
            price = await self.get_price(symbol)
            if price:
                return [
                    {
                        "timestamp": datetime.now().timestamp() * 1000,  # milliseconds
                        "price": price,
                    }
                ]
            return None
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None

    async def get_ticker(self, symbol: str) -> dict[str, Any] | None:
        """
        Get ticker data for a symbol (alias for get_market_data for compatibility)
        """
        return await self.get_market_data(symbol)

    async def get_trending(self) -> list[dict[str, Any]] | None:
        """
        Get trending cryptocurrencies
        Returns top coins by market cap
        """
        try:
            await self._rate_limit()

            url = f"{self.BASE_URL}/tickers/"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                # Get top 10 by market cap
                coins = data.get("data", [])[:10]
                return [
                    {
                        "symbol": coin.get("symbol", ""),
                        "name": coin.get("name", ""),
                        "price": float(coin.get("price_usd", 0)),
                        "change_24h": float(coin.get("percent_change_24h", 0)),
                        "market_cap": float(coin.get("market_cap_usd", 0)),
                    }
                    for coin in coins
                ]
        except Exception as e:
            logger.error(f"Error fetching trending coins: {e}")
            return None


# Singleton instance
_crypto_price_service: CryptoPriceService | None = None


def get_crypto_price_service() -> CryptoPriceService:
    """Get singleton crypto price service instance"""
    global _crypto_price_service
    if _crypto_price_service is None:
        _crypto_price_service = CryptoPriceService()
    return _crypto_price_service
