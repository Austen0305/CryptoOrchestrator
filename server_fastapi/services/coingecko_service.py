"""
DEPRECATED: This service has been replaced by crypto_price_service.py
Using CoinLore API (completely free, no API key required)
This file is kept for backward compatibility - all methods delegate to the new service
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Import the new free service
from .crypto_price_service import get_crypto_price_service


class CoinGeckoService:
    """
    DEPRECATED: Wrapper around CryptoPriceService for backward compatibility
    All methods delegate to the new free CoinLore-based service
    """

    def __init__(self):
        # Use the new free service internally
        self._service = get_crypto_price_service()

    async def get_price(self, symbol: str) -> float | None:
        """Get current price - delegates to free crypto price service"""
        return await self._service.get_price(symbol)

    async def get_prices_batch(self, symbols: list[str]) -> dict[str, float | None]:
        """Get batch prices - delegates to free crypto price service"""
        return await self._service.get_prices_batch(symbols)

    async def get_market_data(self, symbol: str) -> dict[str, Any] | None:
        """Get market data - delegates to free crypto price service"""
        return await self._service.get_market_data(symbol)

    async def get_historical_prices(
        self, symbol: str, days: int = 7
    ) -> list[dict[str, Any]] | None:
        """Get historical prices - delegates to free crypto price service"""
        return await self._service.get_historical_prices(symbol, days)

    async def get_ticker(self, symbol: str) -> dict[str, Any] | None:
        """Get ticker data - delegates to free crypto price service"""
        return await self._service.get_ticker(symbol)

    async def get_trending(self) -> list[dict[str, Any]] | None:
        """Get trending coins - delegates to free crypto price service"""
        return await self._service.get_trending()


# Singleton instance
_coingecko_service: CoinGeckoService | None = None


def get_coingecko_service() -> CoinGeckoService:
    """Get singleton CoinGecko service instance (backward compatibility)"""
    global _coingecko_service
    if _coingecko_service is None:
        _coingecko_service = CoinGeckoService()
    return _coingecko_service
