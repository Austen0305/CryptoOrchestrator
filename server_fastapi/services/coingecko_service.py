"""
CoinGecko API Integration Service
Provides real-time cryptocurrency price data as a fallback to exchange APIs
Free tier: 10-50 calls/minute (no API key required)
"""

import httpx
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class CoinGeckoService:
    """Service for fetching cryptocurrency data from CoinGecko API"""

    BASE_URL = "https://api.coingecko.com/api/v3"
    RATE_LIMIT_DELAY = 1.2  # Seconds between requests (50 calls/min = 1.2s delay)
    CACHE_TTL = 60  # Cache prices for 60 seconds

    def __init__(self):
        self.api_key = os.getenv(
            "COINGECKO_API_KEY"
        )  # Optional, free tier doesn't require
        self.last_request_time = 0
        self.price_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_timestamps: Dict[str, float] = {}

    async def _rate_limit(self):
        """Enforce rate limiting"""
        now = asyncio.get_event_loop().time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.RATE_LIMIT_DELAY:
            await asyncio.sleep(self.RATE_LIMIT_DELAY - time_since_last)
        self.last_request_time = asyncio.get_event_loop().time()

    def _get_cache_key(self, symbol: str) -> str:
        """Convert exchange symbol to CoinGecko ID"""
        # Map common symbols to CoinGecko IDs
        symbol_map = {
            "BTC/USD": "bitcoin",
            "ETH/USD": "ethereum",
            "ADA/USD": "cardano",
            "SOL/USD": "solana",
            "DOT/USD": "polkadot",
            "BNB/USD": "binancecoin",
            "XRP/USD": "ripple",
            "DOGE/USD": "dogecoin",
            "MATIC/USD": "matic-network",
            "AVAX/USD": "avalanche-2",
        }
        # Extract base currency
        base = symbol.split("/")[0].upper()
        return symbol_map.get(symbol, base.lower())

    async def get_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a symbol

        Args:
            symbol: Trading pair (e.g., "BTC/USD")

        Returns:
            Current price or None if unavailable
        """
        cache_key = self._get_cache_key(symbol)

        # Check cache
        if cache_key in self.price_cache:
            cache_time = self.cache_timestamps.get(cache_key, 0)
            if (datetime.now().timestamp() - cache_time) < self.CACHE_TTL:
                return self.price_cache[cache_key].get("price")

        try:
            await self._rate_limit()

            coin_id = cache_key
            url = f"{self.BASE_URL}/simple/price"
            params = {
                "ids": coin_id,
                "vs_currencies": "usd",
            }

            headers = {}
            if self.api_key:
                headers["x-cg-demo-api-key"] = self.api_key

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()

                if coin_id in data and "usd" in data[coin_id]:
                    price = data[coin_id]["usd"]
                    # Update cache
                    self.price_cache[cache_key] = {"price": price}
                    self.cache_timestamps[cache_key] = datetime.now().timestamp()
                    return price

            logger.warning(f"Price not found for {symbol} (CoinGecko ID: {coin_id})")
            return None

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning(
                    "CoinGecko rate limit exceeded, using cached data if available"
                )
            else:
                logger.error(f"CoinGecko API error for {symbol}: {e}")
            # Return cached price if available
            if cache_key in self.price_cache:
                return self.price_cache[cache_key].get("price")
            return None
        except Exception as e:
            logger.error(f"Error fetching price from CoinGecko for {symbol}: {e}")
            # Return cached price if available
            if cache_key in self.price_cache:
                return self.price_cache[cache_key].get("price")
            return None

    async def get_prices_batch(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """
        Get current prices for multiple symbols in a single API call (batch fetch).
        More efficient than calling get_price() multiple times.

        Args:
            symbols: List of trading pairs (e.g., ["BTC/USD", "ETH/USD"])

        Returns:
            Dict mapping symbols to prices (None if unavailable)
        """
        if not symbols:
            return {}

        # Separate cached and uncached symbols
        cached_prices: Dict[str, Optional[float]] = {}
        uncached_symbols: List[str] = []
        coin_id_to_symbol: Dict[str, str] = {}

        for symbol in symbols:
            cache_key = self._get_cache_key(symbol)
            coin_id_to_symbol[cache_key] = symbol

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

        # Batch fetch uncached symbols
        try:
            await self._rate_limit()

            # Convert symbols to CoinGecko IDs
            coin_ids = [self._get_cache_key(symbol) for symbol in uncached_symbols]

            # CoinGecko API supports up to 50 IDs per request
            # Split into chunks if needed
            chunk_size = 50
            all_prices: Dict[str, Optional[float]] = cached_prices.copy()

            for i in range(0, len(coin_ids), chunk_size):
                chunk_ids = coin_ids[i : i + chunk_size]
                chunk_symbols = uncached_symbols[i : i + chunk_size]

                url = f"{self.BASE_URL}/simple/price"
                params = {
                    "ids": ",".join(chunk_ids),
                    "vs_currencies": "usd",
                }

                headers = {}
                if self.api_key:
                    headers["x-cg-demo-api-key"] = self.api_key

                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url, params=params, headers=headers)
                    response.raise_for_status()
                    data = response.json()

                    # Map results back to symbols
                    for coin_id, symbol in zip(chunk_ids, chunk_symbols):
                        if coin_id in data and "usd" in data[coin_id]:
                            price = data[coin_id]["usd"]
                            all_prices[symbol] = price

                            # Update cache
                            cache_key = coin_id
                            self.price_cache[cache_key] = {"price": price}
                            self.cache_timestamps[cache_key] = (
                                datetime.now().timestamp()
                            )
                        else:
                            all_prices[symbol] = None
                            logger.warning(
                                f"Price not found for {symbol} (CoinGecko ID: {coin_id})"
                            )

            logger.debug(f"Batch fetched prices for {len(uncached_symbols)} symbols")
            return all_prices

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning(
                    "CoinGecko rate limit exceeded, using cached data if available"
                )
            else:
                logger.error(f"CoinGecko API error for batch fetch: {e}")

            # Return cached prices for uncached symbols if available
            for symbol in uncached_symbols:
                if symbol not in all_prices:
                    cache_key = self._get_cache_key(symbol)
                    if cache_key in self.price_cache:
                        all_prices[symbol] = self.price_cache[cache_key].get("price")
                    else:
                        all_prices[symbol] = None

            return all_prices
        except Exception as e:
            logger.error(f"Error batch fetching prices from CoinGecko: {e}")

            # Return cached prices for uncached symbols if available
            for symbol in uncached_symbols:
                if symbol not in all_prices:
                    cache_key = self._get_cache_key(symbol)
                    if cache_key in self.price_cache:
                        all_prices[symbol] = self.price_cache[cache_key].get("price")
                    else:
                        all_prices[symbol] = None

            return all_prices

    async def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive market data for a symbol

        Returns:
            Dict with price, change_24h, volume_24h, high_24h, low_24h
        """
        cache_key = self._get_cache_key(symbol)

        # Check cache
        if cache_key in self.price_cache:
            cache_time = self.cache_timestamps.get(cache_key, 0)
            if (datetime.now().timestamp() - cache_time) < self.CACHE_TTL:
                return self.price_cache[cache_key]

        try:
            await self._rate_limit()

            coin_id = cache_key
            url = f"{self.BASE_URL}/coins/{coin_id}"
            params = {
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "false",
                "developer_data": "false",
                "sparkline": "false",
            }

            headers = {}
            if self.api_key:
                headers["x-cg-demo-api-key"] = self.api_key

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()

                market_data = data.get("market_data", {})
                price = market_data.get("current_price", {}).get("usd", 0)
                change_24h = market_data.get("price_change_percentage_24h", 0)
                volume_24h = market_data.get("total_volume", {}).get("usd", 0)
                high_24h = market_data.get("high_24h", {}).get("usd", 0)
                low_24h = market_data.get("low_24h", {}).get("usd", 0)
                market_cap = market_data.get("market_cap", {}).get("usd", 0)

                result = {
                    "price": price,
                    "change_24h": change_24h,
                    "volume_24h": volume_24h,
                    "high_24h": high_24h,
                    "low_24h": low_24h,
                    "market_cap": market_cap,
                    "timestamp": datetime.now().timestamp(),
                }

                # Update cache
                self.price_cache[cache_key] = result
                self.cache_timestamps[cache_key] = datetime.now().timestamp()

                return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("CoinGecko rate limit exceeded")
            else:
                logger.error(f"CoinGecko API error for {symbol}: {e}")
            # Return cached data if available
            if cache_key in self.price_cache:
                return self.price_cache[cache_key]
            return None
        except Exception as e:
            logger.error(f"Error fetching market data from CoinGecko for {symbol}: {e}")
            # Return cached data if available
            if cache_key in self.price_cache:
                return self.price_cache[cache_key]
            return None

    async def get_historical_prices(
        self, symbol: str, days: int = 7
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get historical price data

        Args:
            symbol: Trading pair
            days: Number of days of history (1, 7, 14, 30, 90, 180, 365, max)

        Returns:
            List of price data points
        """
        try:
            await self._rate_limit()

            coin_id = self._get_cache_key(symbol)
            url = f"{self.BASE_URL}/coins/{coin_id}/market_chart"
            params = {
                "vs_currency": "usd",
                "days": days,
                "interval": "daily" if days > 90 else "hourly",
            }

            headers = {}
            if self.api_key:
                headers["x-cg-demo-api-key"] = self.api_key

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()

                prices = data.get("prices", [])
                return [
                    {
                        "timestamp": point[0],
                        "price": point[1],
                    }
                    for point in prices
                ]

        except Exception as e:
            logger.error(
                f"Error fetching historical data from CoinGecko for {symbol}: {e}"
            )
            return None


# Singleton instance
_coingecko_service: Optional[CoinGeckoService] = None


def get_coingecko_service() -> CoinGeckoService:
    """Get singleton CoinGecko service instance"""
    global _coingecko_service
    if _coingecko_service is None:
        _coingecko_service = CoinGeckoService()
    return _coingecko_service
