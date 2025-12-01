"""
CoinGecko API Service - Free Crypto Market Data

This service integrates with CoinGecko's free public API to provide:
- Real-time cryptocurrency prices
- Historical price data
- Market cap rankings
- Trending coins

Free tier limits: 30 calls/minute (public API, no key required)
Documentation: https://www.coingecko.com/en/api/documentation
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import httpx
from functools import lru_cache

logger = logging.getLogger(__name__)

# CoinGecko API base URL (configurable via environment)
COINGECKO_API_URL = os.getenv("COINGECKO_API_URL", "https://api.coingecko.com/api/v3")
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")  # Optional demo key


class CoinGeckoService:
    """
    CoinGecko API client for free crypto market data.
    
    Rate limits (public API):
    - 30 calls/minute
    - No API key required for basic usage
    
    Optional demo API key provides slightly higher limits.
    """
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or COINGECKO_API_URL
        self.api_key = api_key or COINGECKO_API_KEY
        self._client: Optional[httpx.AsyncClient] = None
        
        # Simple in-memory cache for rate limit management
        self._cache: Dict[str, tuple] = {}  # key -> (data, timestamp)
        self._cache_ttl = 60  # Cache TTL in seconds
        
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            headers = {"accept": "application/json"}
            if self.api_key:
                headers["x-cg-demo-api-key"] = self.api_key
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=30.0
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached data if not expired."""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if datetime.now().timestamp() - timestamp < self._cache_ttl:
                return data
            del self._cache[key]
        return None
    
    def _set_cache(self, key: str, data: Any):
        """Cache data with timestamp."""
        self._cache[key] = (data, datetime.now().timestamp())
    
    async def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API request with error handling."""
        cache_key = f"{endpoint}:{str(params)}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
            
        try:
            client = await self._get_client()
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            self._set_cache(cache_key, data)
            return data
        except httpx.HTTPStatusError as e:
            logger.error(f"CoinGecko API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"CoinGecko request failed: {e}")
            raise
    
    # =========================================================================
    # Simple API Methods (Free Tier)
    # =========================================================================
    
    async def ping(self) -> Dict[str, Any]:
        """Check API status. Returns {'gecko_says': '(V3) To the Moon!'}"""
        return await self._request("/ping")
    
    async def get_price(
        self,
        coin_ids: List[str],
        vs_currencies: List[str] = ["usd"],
        include_24hr_change: bool = True,
        include_market_cap: bool = False
    ) -> Dict[str, Any]:
        """
        Get current prices for coins.
        
        Args:
            coin_ids: List of coin IDs (e.g., ['bitcoin', 'ethereum'])
            vs_currencies: Target currencies (e.g., ['usd', 'eur'])
            include_24hr_change: Include 24h price change percentage
            include_market_cap: Include market cap
            
        Returns:
            Price data for each coin
            
        Example:
            {'bitcoin': {'usd': 45000, 'usd_24h_change': 2.5}}
        """
        params = {
            "ids": ",".join(coin_ids),
            "vs_currencies": ",".join(vs_currencies),
            "include_24hr_change": str(include_24hr_change).lower(),
            "include_market_cap": str(include_market_cap).lower()
        }
        return await self._request("/simple/price", params)
    
    async def get_supported_currencies(self) -> List[str]:
        """Get list of supported vs_currencies."""
        return await self._request("/simple/supported_vs_currencies")
    
    async def get_coins_list(self) -> List[Dict[str, str]]:
        """
        Get list of all supported coins with id, symbol, and name.
        
        Returns:
            List of coin objects: [{'id': 'bitcoin', 'symbol': 'btc', 'name': 'Bitcoin'}, ...]
        """
        return await self._request("/coins/list")
    
    async def get_coins_markets(
        self,
        vs_currency: str = "usd",
        coin_ids: Optional[List[str]] = None,
        order: str = "market_cap_desc",
        per_page: int = 100,
        page: int = 1,
        sparkline: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get coin market data (price, market cap, volume).
        
        Args:
            vs_currency: Target currency
            coin_ids: Optional filter by coin IDs
            order: Sort order (market_cap_desc, volume_desc, etc.)
            per_page: Results per page (max 250)
            page: Page number
            sparkline: Include 7-day sparkline
            
        Returns:
            List of market data for each coin
        """
        params = {
            "vs_currency": vs_currency,
            "order": order,
            "per_page": min(per_page, 250),
            "page": page,
            "sparkline": str(sparkline).lower()
        }
        if coin_ids:
            params["ids"] = ",".join(coin_ids)
        return await self._request("/coins/markets", params)
    
    async def get_coin_data(self, coin_id: str) -> Dict[str, Any]:
        """
        Get detailed data for a specific coin.
        
        Args:
            coin_id: Coin ID (e.g., 'bitcoin')
            
        Returns:
            Detailed coin data including description, links, market data
        """
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false"
        }
        return await self._request(f"/coins/{coin_id}", params)
    
    async def get_coin_market_chart(
        self,
        coin_id: str,
        vs_currency: str = "usd",
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get historical market data (price, market cap, volume).
        
        Args:
            coin_id: Coin ID (e.g., 'bitcoin')
            vs_currency: Target currency
            days: Number of days (1, 7, 14, 30, 90, 180, 365, max)
            
        Returns:
            {'prices': [[timestamp, price], ...], 'market_caps': [...], 'total_volumes': [...]}
        """
        params = {
            "vs_currency": vs_currency,
            "days": str(days)
        }
        return await self._request(f"/coins/{coin_id}/market_chart", params)
    
    async def get_trending(self) -> Dict[str, Any]:
        """
        Get trending coins (top 7 by search popularity).
        
        Returns:
            {'coins': [{'item': {'id': 'bitcoin', ...}}, ...]}
        """
        return await self._request("/search/trending")
    
    async def get_global(self) -> Dict[str, Any]:
        """
        Get global cryptocurrency statistics.
        
        Returns:
            Total market cap, volume, BTC dominance, etc.
        """
        return await self._request("/global")
    
    # =========================================================================
    # Convenience Methods
    # =========================================================================
    
    async def get_btc_price(self) -> float:
        """Get current Bitcoin price in USD."""
        data = await self.get_price(["bitcoin"])
        return data.get("bitcoin", {}).get("usd", 0)
    
    async def get_eth_price(self) -> float:
        """Get current Ethereum price in USD."""
        data = await self.get_price(["ethereum"])
        return data.get("ethereum", {}).get("usd", 0)
    
    async def get_top_coins(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top coins by market cap."""
        return await self.get_coins_markets(per_page=limit)
    
    async def get_coin_id_from_symbol(self, symbol: str) -> Optional[str]:
        """
        Look up coin ID from symbol (e.g., 'BTC' -> 'bitcoin').
        
        Note: This fetches the full coin list, so cache the result.
        """
        coins = await self.get_coins_list()
        symbol_lower = symbol.lower()
        for coin in coins:
            if coin.get("symbol") == symbol_lower:
                return coin.get("id")
        return None


# Global service instance (singleton pattern)
_coingecko_service: Optional[CoinGeckoService] = None


def get_coingecko_service() -> CoinGeckoService:
    """Get or create the CoinGecko service instance."""
    global _coingecko_service
    if _coingecko_service is None:
        _coingecko_service = CoinGeckoService()
    return _coingecko_service


async def cleanup_coingecko_service():
    """Cleanup the CoinGecko service on shutdown."""
    global _coingecko_service
    if _coingecko_service:
        await _coingecko_service.close()
        _coingecko_service = None
