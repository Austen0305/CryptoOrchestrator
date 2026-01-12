"""
Free Market Data Service - Multi-Provider (CoinCap & CoinLore)
Provides real-time cryptocurrency data using free, public APIs.
Primary Provider: CoinCap (https://api.coincap.io/v2) - 200 req/min free
Secondary Provider: CoinLore (https://www.coinlore.com/cryptocurrency-data-api) - fallback
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

import httpx

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
    ) -> list[dict[str, Any]] | None:
        """Get historical price data"""
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

                history = []
                for point in data.get("data", []):
                    history.append(
                        {
                            "timestamp": point.get("time"),
                            "price": float(point.get("priceUsd")),
                        }
                    )
                return history

        except Exception as e:
            logger.error(f"Error fetching history for {symbol}: {e}")
            # Fallback to single point if history fails
            price = await self.get_price(symbol)
            if price:
                return [
                    {"timestamp": datetime.now().timestamp() * 1000, "price": price}
                ]
            return None

    async def get_ticker(self, symbol: str) -> dict[str, Any] | None:
        """Get comprehensive ticker data including 24h change"""
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

    async def get_trending(self) -> dict[str, list[dict[str, Any]]] | None:
        """Get trending assets (Top gainers/active)"""
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

                return {"coins": coins}
        except Exception as e:
            logger.error(f"Error fetching trending: {e}")
            return None


# Singleton instance
_market_data_service: MarketDataService | None = None


def get_market_data_service() -> MarketDataService:
    global _market_data_service
    if _market_data_service is None:
        _market_data_service = MarketDataService()
    return _market_data_service
