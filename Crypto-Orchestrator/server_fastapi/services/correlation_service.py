"""
Correlation Service
Calculates price correlations and generates correlation matrices for trading pairs
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class CorrelationService:
    """Service for calculating price correlations between trading pairs"""

    def __init__(self):
        self._coingecko_service: Optional[Any] = None

    def _get_coingecko_service(self):
        """Lazy load CoinGecko service"""
        if self._coingecko_service is None:
            try:
                from .coingecko_service import CoinGeckoService
                self._coingecko_service = CoinGeckoService()
            except ImportError:
                logger.warning("CoinGecko service not available")
                self._coingecko_service = None
        return self._coingecko_service

    async def get_historical_prices(
        self, symbols: List[str], days: int = 30
    ) -> Dict[str, List[float]]:
        """
        Get historical price data for multiple symbols
        
        Args:
            symbols: List of trading pair symbols (e.g., ["BTC/USD", "ETH/USD"])
            days: Number of days of historical data to fetch
            
        Returns:
            Dict mapping symbols to lists of closing prices
        """
        coingecko = self._get_coingecko_service()
        if not coingecko:
            return {}

        historical_data: Dict[str, List[float]] = {}
        
        # Fetch historical data for each symbol
        for symbol in symbols:
            try:
                # Get historical prices from CoinGecko
                prices = await coingecko.get_historical_prices(symbol, days=days)
                if prices and len(prices) > 0:
                    # Extract closing prices
                    historical_data[symbol] = [p.get("close", 0.0) for p in prices if p.get("close")]
                else:
                    logger.warning(f"No historical data for {symbol}")
                    historical_data[symbol] = []
            except Exception as e:
                logger.error(f"Error fetching historical data for {symbol}: {e}")
                historical_data[symbol] = []

        return historical_data

    def calculate_returns(self, prices: List[float]) -> List[float]:
        """
        Calculate percentage returns from price series
        
        Args:
            prices: List of closing prices
            
        Returns:
            List of percentage returns
        """
        if len(prices) < 2:
            return []
        
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] > 0:
                ret = (prices[i] - prices[i-1]) / prices[i-1] * 100
                returns.append(ret)
            else:
                returns.append(0.0)
        
        return returns

    def calculate_correlation(
        self, prices1: List[float], prices2: List[float]
    ) -> float:
        """
        Calculate Pearson correlation coefficient between two price series
        
        Args:
            prices1: First price series
            prices2: Second price series
            
        Returns:
            Correlation coefficient (-1 to 1)
        """
        if len(prices1) != len(prices2) or len(prices1) < 2:
            return 0.0

        # Calculate returns
        returns1 = self.calculate_returns(prices1)
        returns2 = self.calculate_returns(prices2)

        if len(returns1) != len(returns2) or len(returns1) < 2:
            return 0.0

        # Calculate correlation using numpy
        try:
            correlation = np.corrcoef(returns1, returns2)[0, 1]
            # Handle NaN
            if np.isnan(correlation):
                return 0.0
            return float(correlation)
        except Exception as e:
            logger.error(f"Error calculating correlation: {e}")
            return 0.0

    async def calculate_correlation_matrix(
        self, symbols: List[str], days: int = 30
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate correlation matrix for multiple trading pairs
        
        Args:
            symbols: List of trading pair symbols
            days: Number of days of historical data to use
            
        Returns:
            Nested dict: {symbol1: {symbol2: correlation, ...}, ...}
        """
        # Get historical prices for all symbols
        historical_prices = await self.get_historical_prices(symbols, days)
        
        # Filter out symbols with insufficient data
        valid_symbols = [
            s for s in symbols 
            if s in historical_prices and len(historical_prices[s]) >= 2
        ]
        
        if len(valid_symbols) < 2:
            logger.warning("Insufficient data for correlation calculation")
            return {}

        # Align price series to same length (use minimum length)
        min_length = min(len(historical_prices[s]) for s in valid_symbols)
        aligned_prices: Dict[str, List[float]] = {}
        
        for symbol in valid_symbols:
            # Take the last min_length prices to align
            aligned_prices[symbol] = historical_prices[symbol][-min_length:]

        # Calculate correlation matrix
        correlation_matrix: Dict[str, Dict[str, float]] = {}
        
        for i, symbol1 in enumerate(valid_symbols):
            correlation_matrix[symbol1] = {}
            for symbol2 in valid_symbols:
                if symbol1 == symbol2:
                    correlation_matrix[symbol1][symbol2] = 1.0
                elif symbol2 in correlation_matrix and symbol1 in correlation_matrix[symbol2]:
                    # Use symmetric property
                    correlation_matrix[symbol1][symbol2] = correlation_matrix[symbol2][symbol1]
                else:
                    corr = self.calculate_correlation(
                        aligned_prices[symbol1],
                        aligned_prices[symbol2]
                    )
                    correlation_matrix[symbol1][symbol2] = corr

        return correlation_matrix

    async def get_heatmap_data(
        self, symbols: List[str], metric: str = "change_24h", days: int = 30
    ) -> Dict[str, Dict[str, float]]:
        """
        Get heatmap data for multiple symbols
        
        Args:
            symbols: List of trading pair symbols
            metric: Metric to display ("change_24h", "volume_24h", "correlation")
            days: Number of days for correlation calculation (if metric is "correlation")
            
        Returns:
            Dict with symbol data for heatmap visualization
        """
        coingecko = self._get_coingecko_service()
        if not coingecko:
            return {}

        if metric == "correlation":
            # Return correlation matrix
            return await self.calculate_correlation_matrix(symbols, days)
        elif metric == "change_24h":
            # Get 24h price changes
            heatmap_data: Dict[str, Dict[str, float]] = {}
            for symbol in symbols:
                try:
                    market_data = await coingecko.get_market_data(symbol)
                    if market_data:
                        heatmap_data[symbol] = {
                            "change_24h": market_data.get("change_24h", 0.0),
                            "volume_24h": market_data.get("volume_24h", 0.0),
                            "price": market_data.get("price", 0.0),
                        }
                except Exception as e:
                    logger.error(f"Error fetching market data for {symbol}: {e}")
            return heatmap_data
        elif metric == "volume_24h":
            # Get 24h volumes
            heatmap_data: Dict[str, Dict[str, float]] = {}
            for symbol in symbols:
                try:
                    market_data = await coingecko.get_market_data(symbol)
                    if market_data:
                        volume = market_data.get("volume_24h", 0.0)
                        heatmap_data[symbol] = {
                            "volume_24h": volume,
                            "change_24h": market_data.get("change_24h", 0.0),
                            "price": market_data.get("price", 0.0),
                        }
                except Exception as e:
                    logger.error(f"Error fetching market data for {symbol}: {e}")
            return heatmap_data
        else:
            logger.warning(f"Unknown metric: {metric}")
            return {}
