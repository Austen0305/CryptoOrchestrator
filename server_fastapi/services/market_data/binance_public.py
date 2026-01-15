"""
Binance Public Market Data Service
Provides keyless access to Binance Public API for real-time prices and OHLCV history
"""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class BinancePublicService:
    """Service for fetching data from Binance Public API (Keyless)"""

    BASE_URL = "https://api.binance.com/api/v3"

    async def get_price(self, symbol: str) -> float | None:
        """Get current price for a symbol (e.g., BTCUSDT)"""
        try:
            # Normalize symbol for Binance (remove slash, uppercase)
            binance_symbol = symbol.replace("/", "").upper()
            if "USD" in binance_symbol and "USDT" not in binance_symbol:
                binance_symbol = binance_symbol.replace("USD", "USDT")

            url = f"{self.BASE_URL}/ticker/price"
            params = {"symbol": binance_symbol}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                return float(data.get("price", 0))
        except Exception as e:
            logger.error(f"Error fetching Binance price for {symbol}: {e}")
            return None

    async def get_ohlcv(
        self, symbol: str, interval: str = "1d", limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Get historical OHLCV data
        Intervals: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
        """
        try:
            binance_symbol = symbol.replace("/", "").upper()
            if "USD" in binance_symbol and "USDT" not in binance_symbol:
                binance_symbol = binance_symbol.replace("USD", "USDT")

            url = f"{self.BASE_URL}/klines"
            params = {"symbol": binance_symbol, "interval": interval, "limit": limit}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                ohlcv = []
                for entry in data:
                    ohlcv.append(
                        {
                            "timestamp": int(entry[0]),
                            "open": float(entry[1]),
                            "high": float(entry[2]),
                            "low": float(entry[3]),
                            "close": float(entry[4]),
                            "volume": float(entry[5]),
                        }
                    )
                return ohlcv
        except Exception as e:
            logger.error(f"Error fetching Binance OHLCV for {symbol}: {e}")
            return []

    async def get_returns(self, symbol: str, limit: int = 100) -> list[float]:
        """Get historical returns for VaR calculation"""
        ohlcv = await self.get_ohlcv(symbol, limit=limit + 1)
        if len(ohlcv) < 2:
            return []

        returns = []
        for i in range(1, len(ohlcv)):
            prev_close = ohlcv[i - 1]["close"]
            curr_close = ohlcv[i]["close"]
            returns.append((curr_close - prev_close) / prev_close)

        return returns


# Global instance
binance_public_service = BinancePublicService()
