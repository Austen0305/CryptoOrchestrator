import logging
import time
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket
from pydantic import BaseModel

from .ws import get_current_user_ws

# Import OrderBook model
try:
    from ..models.market import OrderBook
except ImportError:
    # Define OrderBook if model doesn't exist
    class OrderBook(BaseModel):
        pair: str
        bids: list[dict[str, float]]
        asks: list[dict[str, float]]
        timestamp: int


# Exchange services removed - using blockchain/DEX data sources
# Market data now comes from CoinGecko and DEX aggregators
from sqlalchemy.ext.asyncio import AsyncSession

from server_fastapi.services.coingecko_service import CoinGeckoService
from server_fastapi.services.correlation_service import CorrelationService
from server_fastapi.services.market_analysis_service import MarketAnalysisService
from server_fastapi.services.volatility_analyzer import VolatilityAnalyzer

from ..database import get_db_session
from ..dependencies.auth import get_current_user
from ..middleware.cache_manager import cached
from ..middleware.query_cache import cache_query_result
from ..repositories.candle_repository import CandleRepository
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

# Initialize services
market_analysis_service = MarketAnalysisService()
volatility_analyzer = VolatilityAnalyzer()
correlation_service = CorrelationService()


# Market data service (CoinGecko for price data)
def get_market_data_service() -> CoinGeckoService:
    return CoinGeckoService()


router = APIRouter()


# Pydantic models for requests and responses
class TradingPair(BaseModel):
    """Trading pair model for market listings"""

    symbol: str
    base_asset: str
    quote_asset: str
    current_price: float
    change_24h: float
    volume_24h: float
    high_24h: float | None = None
    low_24h: float | None = None
    market_cap: float | None = None
    is_active: bool = True


class MarketSummary(BaseModel):
    total_pairs: int
    total_volume_24h: float
    top_pairs: list[TradingPair]


class TickerResponse(BaseModel):
    symbol: str
    last_price: float
    change_24h: float
    volume_24h: float
    high_24h: float
    low_24h: float


class OHLCVRequest(BaseModel):
    pair: str
    timeframe: str | None = "1h"
    limit: int | None = 100


class MarketData(BaseModel):
    """Market data point for charts"""

    timestamp: int
    price: float
    volume: float | None = None


class PriceChartResponse(BaseModel):
    pair: str
    timeframe: str
    data: list[MarketData]


class CandleDTO(BaseModel):
    ts: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class CandleHistoryResponse(BaseModel):
    pair: str
    timeframe: str
    candles: list[CandleDTO]


class TradingPairDetails(BaseModel):
    symbol: str
    base_asset: str
    quote_asset: str
    current_price: float
    change_24h: float
    volume_24h: float
    high_24h: float
    low_24h: float
    market_cap: float | None = None
    price_precision: int = 8
    quantity_precision: int = 8
    min_order_size: float = 0.0
    max_order_size: float | None = None
    is_active: bool = True


class RealTimeMarketData(BaseModel):
    symbol: str
    price: float
    change_24h: float
    volume_24h: float
    timestamp: int
    bid_price: float | None = None
    ask_price: float | None = None


class TechnicalIndicator(BaseModel):
    name: str
    value: float
    signal: str
    period: int | None = None


class MarketAnalysisResponse(BaseModel):
    pair: str
    price: float
    indicators: list[TechnicalIndicator]
    trend: str
    strength: float
    recommendation: str
    timestamp: int


# Existing endpoints updated with dependency injection and improved models
@router.get("/", response_model=list[TradingPair])
@cache_query_result(
    ttl=600, key_prefix="markets", include_user=False, include_params=False
)
async def get_markets() -> list[TradingPair]:
    """Get all available trading pairs from CoinGecko"""
    try:
        from ..services.coingecko_service import CoinGeckoService

        coingecko = CoinGeckoService()

        # Get popular cryptocurrencies from CoinGecko
        # In production, you might want to maintain a curated list or fetch from DEX aggregators
        popular_coins = [
            "bitcoin",
            "ethereum",
            "cardano",
            "solana",
            "polkadot",
            "binancecoin",
        ]
        pairs = []

        for coin_id in popular_coins:
            try:
                symbol = coin_id.upper() + "/USD"
                market_data = await coingecko.get_market_data(symbol)
                if market_data:
                    pairs.append(
                        {
                            "symbol": symbol,
                            "base_asset": coin_id,
                            "quote_asset": "USD",
                            "current_price": float(market_data.get("current_price", 0)),
                            "change_24h": float(market_data.get("change_24h", 0)),
                            "volume_24h": float(market_data.get("volume_24h", 0)),
                            "high_24h": float(
                                market_data.get(
                                    "high_24h", market_data.get("current_price", 0)
                                )
                            ),
                            "low_24h": float(
                                market_data.get(
                                    "low_24h", market_data.get("current_price", 0)
                                )
                            ),
                        }
                    )
            except Exception as e:
                logger.warning(f"Failed to fetch market data for {coin_id}: {e}")
                continue

        return pairs
    except Exception as e:
        logger.error(f"Error fetching markets: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch markets")


@router.get("/{pair:path}/ohlcv", response_model=PriceChartResponse)
async def get_ohlcv(
    pair: str,
    timeframe: str = Query(
        "1h", description="Timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d, etc.)"
    ),
    limit: int = Query(100, description="Number of candles to return", ge=1, le=1000),
) -> PriceChartResponse:
    """Get OHLCV data for a trading pair from CoinGecko"""
    try:
        from ..services.coingecko_service import CoinGeckoService

        coingecko = CoinGeckoService()

        # Convert pair to CoinGecko ID
        coin_id = pair.split("/")[0].lower()

        # Get historical price data (CoinGecko provides price history, not full OHLCV in free tier)
        # For full OHLCV, you'd need CoinGecko Pro API or use DEX aggregator APIs
        historical_data = await coingecko.get_historical_prices(pair, days=limit)

        if not historical_data:
            raise HTTPException(status_code=404, detail=f"No data available for {pair}")

        # Convert price history to OHLCV format (simplified - in production, use proper OHLCV endpoint)
        candles = []
        for i, point in enumerate(historical_data):
            price = point.get("price", 0)
            # For free tier, we only have price, so estimate OHLCV
            candles.append(
                {
                    "ts": int(point.get("timestamp", 0)),
                    "open": price,
                    "high": price * 1.01,  # Estimate
                    "low": price * 0.99,  # Estimate
                    "close": price,
                    "volume": 0.0,  # Not available in free tier
                }
            )

        return PriceChartResponse(
            pair=pair,
            timeframe=timeframe,
            data=[MarketData(**candle) for candle in candles],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching OHLCV for {pair}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch OHLCV data")
    try:
        # Validate pair format
        if "/" not in pair:
            raise HTTPException(
                status_code=400, detail="Invalid pair format. Use format: BASE/QUOTE"
            )

        # Validate timeframe
        valid_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
        if timeframe not in valid_timeframes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}",
            )

        # Get historical data from CoinGecko
        coingecko = CoinGeckoService()
        # Convert timeframe to days for CoinGecko
        days_map = {"1h": 1, "4h": 7, "1d": 30, "1w": 90, "1m": 365}
        days = days_map.get(timeframe, 30)
        historical_data_points = await coingecko.get_historical_prices(pair, days=days)

        # Convert to MarketData format
        historical_data = []
        for point in historical_data_points[:limit]:
            price = point.get("price", 0)
            if price > 0:
                historical_data.append(
                    {
                        "timestamp": point.get("timestamp", 0),
                        "open": price,
                        "high": price * 1.01,
                        "low": price * 0.99,
                        "close": price,
                        "volume": 0.0,
                    }
                )

        return PriceChartResponse(pair=pair, timeframe=timeframe, data=historical_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching OHLCV for {pair}: {e}", exc_info=True)
        # Return empty data instead of 500 error for better UX during development
        logger.warning(f"Returning empty OHLCV data due to error: {e}")
        return PriceChartResponse(pair=pair, timeframe=timeframe, data=[])


@router.get("/{pair:path}/history", response_model=CandleHistoryResponse)
async def get_candle_history(
    pair: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    timeframe: str = Query("1m", description="Timeframe for stored candles"),
    limit: int = Query(500, ge=1, le=5000),
) -> CandleHistoryResponse:
    """Return stored candle history from the DB for a symbol/timeframe."""
    try:
        if "/" not in pair:
            raise HTTPException(
                status_code=400, detail="Invalid pair format. Use format: BASE/QUOTE"
            )
        repo = CandleRepository(db)
        rows = await repo.get_history(pair, timeframe, limit)
        candles = [
            CandleDTO(
                ts=r.ts,
                open=r.open,
                high=r.high,
                low=r.low,
                close=r.close,
                volume=r.volume or 0,
            )
            for r in rows
        ]
        return CandleHistoryResponse(pair=pair, timeframe=timeframe, candles=candles)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching candle history for {pair}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch candle history for {pair}"
        )


@router.get("/{pair:path}/orderbook", response_model=OrderBook)
async def get_order_book(pair: str) -> OrderBook:
    """Get order book for a trading pair"""
    try:
        if "/" not in pair:
            raise HTTPException(
                status_code=400, detail="Invalid pair format. Use format: BASE/QUOTE"
            )

        # CoinGecko doesn't provide orderbook data, return empty orderbook
        # In production, integrate with DEX aggregator APIs for real orderbook data
        logger.info(
            f"Orderbook requested for {pair} - returning empty (CoinGecko doesn't provide orderbook)"
        )
        return OrderBook(
            pair=pair,
            bids=[],
            asks=[],
            timestamp=int(time.time() * 1000),
        )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order book for {pair}: {e}", exc_info=True)
        # Return empty orderbook instead of 500 error for better UX during development
        logger.warning(f"Returning empty orderbook for {pair} due to error: {e}")
        return OrderBook(
            pair=pair,
            bids=[],
            asks=[],
            timestamp=int(time.time() * 1000),
        )


@router.get("/price/{pair}")
@cached(ttl=30, prefix="markets")  # 30s TTL for price data
async def get_price(pair: str) -> dict:
    """Get current price for a trading pair"""
    try:
        if "/" not in pair:
            raise HTTPException(
                status_code=400, detail="Invalid pair format. Use format: BASE/QUOTE"
            )

        coingecko = CoinGeckoService()
        price = await coingecko.get_price(pair)
        if price is None:
            raise HTTPException(status_code=404, detail=f"Price not found for {pair}")
        return {"pair": pair, "price": price}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching price for {pair}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch price for {pair}")


# New market data endpoints
@router.get("/tickers", response_model=list[TickerResponse])
@cached(ttl=60, prefix="markets")  # 60s TTL for ticker data
async def get_tickers(
    limit: int = Query(50, description="Number of tickers to return", ge=1, le=500),
) -> list[TickerResponse]:
    """Get ticker data for multiple trading pairs"""
    try:
        coingecko = CoinGeckoService()
        # Get popular pairs from CoinGecko
        pairs = await get_markets()  # Reuse the get_markets function

        # Sort by volume and limit results
        sorted_pairs = sorted(pairs, key=lambda x: x.volume_24h, reverse=True)[:limit]

        tickers = []
        for pair in sorted_pairs:
            tickers.append(
                TickerResponse(
                    symbol=pair.symbol,
                    last_price=pair.current_price,
                    change_24h=pair.change_24h,
                    volume_24h=pair.volume_24h,
                    high_24h=pair.high_24h,
                    low_24h=pair.low_24h,
                )
            )

        return tickers
    except Exception as e:
        logger.error(f"Error fetching tickers: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch tickers")


@router.get("/summary", response_model=MarketSummary)
@cached(ttl=60, prefix="markets")  # 60s TTL for market summary
async def get_market_summary(
    top_count: int = Query(
        10, description="Number of top pairs to include", ge=1, le=50
    ),
) -> MarketSummary:
    """Get market summary with total statistics and top pairs"""
    try:
        pairs = await get_markets()  # Reuse the get_markets function

        if not pairs:
            return MarketSummary(total_pairs=0, total_volume_24h=0.0, top_pairs=[])

        # Calculate total volume
        total_volume = sum(pair.volume_24h for pair in pairs)

        # Get top pairs by volume
        top_pairs = sorted(pairs, key=lambda x: x.volume_24h, reverse=True)[:top_count]

        return MarketSummary(
            total_pairs=len(pairs), total_volume_24h=total_volume, top_pairs=top_pairs
        )
    except Exception as e:
        logger.error(f"Error fetching market summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch market summary")


@router.get("/trading-pairs/search")
async def search_trading_pairs(
    query: str = Query(..., description="Search query for pair symbols"),
    limit: int = Query(20, description="Maximum number of results", ge=1, le=100),
) -> list[TradingPair]:
    """Search for trading pairs by symbol"""
    try:
        if not query or len(query.strip()) < 1:
            raise HTTPException(
                status_code=400, detail="Search query must be at least 1 character"
            )

        query_lower = query.lower().strip()
        pairs = await get_markets()  # Reuse the get_markets function

        # Filter pairs that contain the query in their symbol
        matching_pairs = [
            pair
            for pair in pairs
            if query_lower in pair.symbol.lower()
            or query_lower in pair.base_asset.lower()
            or query_lower in pair.quote_asset.lower()
        ]

        # Sort by volume and limit results
        return sorted(matching_pairs, key=lambda x: x.volume_24h, reverse=True)[:limit]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching trading pairs: {e}")
        raise HTTPException(status_code=500, detail="Failed to search trading pairs")


@router.get("/{pair}/details", response_model=TradingPairDetails)
@cached(ttl=60, prefix="markets")  # 60s TTL for pair details
async def get_trading_pair_details(pair: str) -> TradingPairDetails:
    """Get detailed information about a specific trading pair"""
    try:
        if "/" not in pair:
            raise HTTPException(
                status_code=400, detail="Invalid pair format. Use format: BASE/QUOTE"
            )

        # Get market data from CoinGecko
        coingecko = CoinGeckoService()
        market_data = await coingecko.get_market_data(pair)

        if not market_data:
            raise HTTPException(
                status_code=404, detail=f"Trading pair {pair} not found"
            )

        # Parse symbol to get base and quote assets
        base_asset = pair.split("/")[0] if "/" in pair else pair
        quote_asset = pair.split("/")[1] if "/" in pair else "USD"

        # Get additional details (defaults for DEX trading)
        market_details = {
            "price_precision": 8,
            "quantity_precision": 8,
            "min_order_size": 0.0001 if base_asset == "BTC" else 0.01,
            "max_order_size": None,
            "is_active": True,
        }

        return TradingPairDetails(
            symbol=pair,
            base_asset=base_asset,
            quote_asset=quote_asset,
            current_price=market_data.get("price", 0.0),
            change_24h=market_data.get("change_24h", 0.0),
            volume_24h=pair_info.volume_24h,
            high_24h=pair_info.high_24h,
            low_24h=pair_info.low_24h,
            market_cap=None,  # Would need additional data source
            **market_details,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching trading pair details for {pair}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch details for {pair}"
        )


# Protected endpoints (require authentication)
@router.get("/favorites", response_model=list[TradingPair])
@cached(ttl=120, prefix="markets_favorites")
async def get_favorite_pairs(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> list[TradingPair]:
    """Get user's favorite trading pairs (requires authentication)"""
    try:
        user_id = _get_user_id(current_user)
        # In a real implementation, this would fetch from user's preferences
        # For now, return popular pairs as favorites
        pairs = await get_markets()  # Reuse the get_markets function
        favorites = sorted(pairs, key=lambda x: x.volume_24h or 0, reverse=True)[:5]
        return favorites
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching favorite pairs for user {user_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to fetch favorite pairs")


@router.get("/watchlist", response_model=list[TradingPair])
@cached(ttl=120, prefix="markets_watchlist")
async def get_watchlist(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> list[TradingPair]:
    """Get user's watchlist (requires authentication)"""
    try:
        user_id = _get_user_id(current_user)
        # In a real implementation, this would fetch from user's watchlist
        # For now, return some pairs as watchlist
        pairs = await get_markets()  # Reuse the get_markets function
        watchlist = pairs[:10]  # First 10 pairs as mock watchlist
        return watchlist
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching watchlist for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch watchlist")


# Rate-limited endpoints with enhanced validation and authentication
@router.get("/advanced/{pair}/analysis", response_model=MarketAnalysisResponse)
@cached(ttl=300, prefix="markets_analysis")
async def get_advanced_market_analysis(
    pair: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    indicators: list[str] = Query(
        ["rsi", "macd", "bollinger"], description="Technical indicators to calculate"
    ),
    period: int = Query(14, description="Period for indicators", ge=1, le=200),
) -> MarketAnalysisResponse:
    """Get advanced market analysis with technical indicators (requires authentication)"""
    try:
        # Enhanced validation
        if "/" not in pair:
            raise HTTPException(
                status_code=400, detail="Invalid pair format. Use format: BASE/QUOTE"
            )

        valid_indicators = ["rsi", "macd", "bollinger", "sma", "ema", "stoch"]
        invalid_indicators = [ind for ind in indicators if ind not in valid_indicators]
        if invalid_indicators:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid indicators: {', '.join(invalid_indicators)}. Valid: {', '.join(valid_indicators)}",
            )

        # Get historical data from CoinGecko
        coingecko = CoinGeckoService()
        historical_data = await coingecko.get_historical_prices(pair, days=30)

        if not historical_data or len(historical_data) < 2:
            raise HTTPException(
                status_code=404, detail=f"No market data available for {pair}"
            )

        # Convert to OHLCV format for analysis (simplified - CoinGecko only provides prices)
        ohlcv_data = []
        for i, point in enumerate(historical_data):
            price = point.get("price", 0)
            if price > 0:
                ohlcv_data.append(
                    {
                        "timestamp": point.get("timestamp", 0),
                        "open": price,
                        "high": price * 1.01,  # Estimate
                        "low": price * 0.99,  # Estimate
                        "close": price,
                        "volume": 0.0,
                    }
                )

        if len(ohlcv_data) < 2:
            raise HTTPException(
                status_code=404, detail=f"Insufficient market data for {pair}"
            )

        # Perform market analysis using the analysis service
        analysis_result = market_analysis_service.analyze(
            ohlcv_data, volatility_analyzer
        )

        # Get current price from CoinGecko
        current_price = await coingecko.get_price(pair)
        if not current_price and ohlcv_data:
            current_price = ohlcv_data[-1]["close"]

        # Calculate technical indicators
        calculated_indicators = []
        closes = [d["close"] for d in ohlcv_data[-period:]]

        for indicator in indicators:
            if indicator == "rsi" and len(closes) >= period:
                # Simple RSI calculation
                gains = []
                losses = []
                for i in range(1, len(closes)):
                    change = closes[i] - closes[i - 1]
                    if change > 0:
                        gains.append(change)
                        losses.append(0)
                    else:
                        gains.append(0)
                        losses.append(abs(change))

                avg_gain = sum(gains) / len(gains) if gains else 0
                avg_loss = sum(losses) / len(losses) if losses else 0
                rs = avg_gain / avg_loss if avg_loss != 0 else 100
                rsi_value = 100 - (100 / (1 + rs))

                signal = (
                    "bullish"
                    if rsi_value < 30
                    else "bearish"
                    if rsi_value > 70
                    else "neutral"
                )
                calculated_indicators.append(
                    TechnicalIndicator(
                        name="rsi",
                        value=round(rsi_value, 2),
                        signal=signal,
                        period=period,
                    )
                )

            elif indicator == "macd" and len(closes) >= 26:
                # Simple MACD calculation
                ema12 = sum(closes[-12:]) / 12
                ema26 = sum(closes[-26:]) / 26
                macd = ema12 - ema26
                signal_line = sum(
                    [ema12 - ema26 for _ in range(min(9, len(closes)))]
                ) / min(9, len(closes))
                histogram = macd - signal_line

                signal = "bullish" if macd > signal_line else "bearish"
                calculated_indicators.append(
                    TechnicalIndicator(
                        name="macd", value=round(macd, 4), signal=signal, period=26
                    )
                )

            elif indicator == "bollinger" and len(closes) >= 20:
                # Bollinger Bands
                sma = sum(closes[-20:]) / 20
                std = (sum((x - sma) ** 2 for x in closes[-20:]) / 20) ** 0.5
                upper = sma + (std * 2)
                lower = sma - (std * 2)

                # Signal based on current price relative to bands
                if current_price:
                    if current_price > upper:
                        signal = "overbought"
                    elif current_price < lower:
                        signal = "oversold"
                    else:
                        signal = "neutral"
                else:
                    signal = "neutral"

                calculated_indicators.append(
                    TechnicalIndicator(
                        name="bollinger",
                        value=round(
                            (
                                (current_price - sma) / (std * 2)
                                if current_price and std != 0
                                else 0
                            ),
                            2,
                        ),
                        signal=signal,
                        period=20,
                    )
                )

        # Determine trend and strength from analysis
        trend_strength = analysis_result.summary.get("trendStrength", 0.0)
        trend = (
            "bullish"
            if trend_strength > 0.6
            else "bearish"
            if trend_strength < 0.4
            else "sideways"
        )

        # Generate recommendation based on analysis
        overall_score = analysis_result.summary.get("overallScore", 50)
        if overall_score > 70:
            recommendation = "strong_buy"
        elif overall_score > 60:
            recommendation = "buy"
        elif overall_score > 40:
            recommendation = "hold"
        elif overall_score > 30:
            recommendation = "sell"
        else:
            recommendation = "strong_sell"

        return MarketAnalysisResponse(
            pair=pair,
            price=current_price or 0.0,
            indicators=calculated_indicators,
            trend=trend,
            strength=round(trend_strength, 2),
            recommendation=recommendation,
            timestamp=int(__import__("time").time() * 1000),
        )

    except HTTPException:
        raise
    except Exception as e:
        user_id = _get_user_id(current_user) if "current_user" in locals() else None
        logger.error(
            f"Error getting advanced analysis for {pair}: {e}",
            exc_info=True,
            extra={"user_id": user_id},
        )
        raise HTTPException(status_code=500, detail="Failed to perform market analysis")


@router.get("/realtime/{pair}/price-stream", response_model=RealTimeMarketData)
async def get_realtime_price_stream(
    pair: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> RealTimeMarketData:
    """Get realtime price stream info (requires authentication)"""
    try:
        if "/" not in pair:
            raise HTTPException(
                status_code=400, detail="Invalid pair format. Use format: BASE/QUOTE"
            )

        # Get current price and market data from CoinGecko
        coingecko = CoinGeckoService()
        price = await coingecko.get_price(pair)
        if price is None:
            raise HTTPException(status_code=404, detail=f"Price not found for {pair}")

        # Get market data for 24h change and volume
        market_data = await coingecko.get_market_data(pair)

        # CoinGecko doesn't provide orderbook, so bid/ask are None
        bid_price = None
        ask_price = None

        return RealTimeMarketData(
            symbol=pair,
            price=price,
            change_24h=market_data.get("change_24h", 0.0) if market_data else 0.0,
            volume_24h=market_data.get("volume_24h", 0.0) if market_data else 0.0,
            timestamp=int(time.time() * 1000),
            bid_price=bid_price,
            ask_price=ask_price,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting realtime price stream for {pair}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get realtime price stream"
        )


class CorrelationMatrixResponse(BaseModel):
    """Response model for correlation matrix"""

    symbols: list[str]
    matrix: dict[str, dict[str, float]]
    calculated_at: str


class HeatmapDataResponse(BaseModel):
    """Response model for heatmap data"""

    data: dict[str, dict[str, float]]
    metric: str
    calculated_at: str


@router.get("/correlation/matrix", response_model=CorrelationMatrixResponse)
@cached(ttl=3600, prefix="correlation")  # Cache for 1 hour
async def get_correlation_matrix(
    symbols: str = Query(
        ..., description="Comma-separated list of trading pairs (e.g., BTC/USD,ETH/USD)"
    ),
    days: int = Query(
        30, ge=7, le=365, description="Number of days of historical data to use"
    ),
    current_user: Annotated[dict, Depends(get_current_user)] | None = None,
) -> CorrelationMatrixResponse:
    """
    Calculate correlation matrix for multiple trading pairs

    Returns correlation coefficients between all pairs of symbols.
    Correlation ranges from -1 (perfect negative) to +1 (perfect positive).
    """
    try:
        # Parse symbols
        symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]

        if len(symbol_list) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 trading pairs required for correlation calculation",
            )

        if len(symbol_list) > 50:
            raise HTTPException(
                status_code=400, detail="Maximum 50 trading pairs allowed"
            )

        # Calculate correlation matrix
        matrix = await correlation_service.calculate_correlation_matrix(
            symbol_list, days
        )

        if not matrix:
            raise HTTPException(
                status_code=500,
                detail="Failed to calculate correlation matrix - insufficient data",
            )

        return CorrelationMatrixResponse(
            symbols=symbol_list,
            matrix=matrix,
            calculated_at=datetime.utcnow().isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating correlation matrix: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to calculate correlation matrix"
        )


@router.get("/heatmap/data", response_model=HeatmapDataResponse)
@cached(ttl=300, prefix="heatmap")  # Cache for 5 minutes
async def get_heatmap_data(
    symbols: str = Query(..., description="Comma-separated list of trading pairs"),
    metric: str = Query(
        "change_24h", description="Metric: change_24h, volume_24h, or correlation"
    ),
    days: int = Query(30, ge=7, le=365, description="Days for correlation calculation"),
    current_user: Annotated[dict, Depends(get_current_user)] | None = None,
) -> HeatmapDataResponse:
    """
    Get heatmap data for multiple trading pairs

    Supports different metrics:
    - change_24h: 24-hour price change percentage
    - volume_24h: 24-hour trading volume
    - correlation: Correlation matrix between pairs
    """
    try:
        # Parse symbols
        symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]

        if len(symbol_list) < 1:
            raise HTTPException(
                status_code=400, detail="At least 1 trading pair required"
            )

        if len(symbol_list) > 100:
            raise HTTPException(
                status_code=400, detail="Maximum 100 trading pairs allowed"
            )

        # Validate metric
        valid_metrics = ["change_24h", "volume_24h", "correlation"]
        if metric not in valid_metrics:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid metric. Must be one of: {', '.join(valid_metrics)}",
            )

        # Get heatmap data
        data = await correlation_service.get_heatmap_data(symbol_list, metric, days)

        if not data:
            raise HTTPException(status_code=500, detail="Failed to fetch heatmap data")

        return HeatmapDataResponse(
            data=data,
            metric=metric,
            calculated_at=datetime.utcnow().isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching heatmap data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch heatmap data")


@router.websocket("/ws/market-stream/{pair}")
async def websocket_market_stream(
    websocket: WebSocket,
    pair: str,
    token: str = Query(..., description="JWT authentication token"),
):
    """WebSocket endpoint for real-time market data streaming"""
    try:
        # Authenticate user
        user = get_current_user_ws(token)
        await websocket.accept()

        logger.info(f"User {user['id']} connected to market stream for {pair}")

        # Send initial data from CoinGecko
        coingecko = CoinGeckoService()
        price = await coingecko.get_price(pair)

        # CoinGecko doesn't provide orderbook, use empty
        from ..models.market import OrderBook

        order_book = OrderBook(
            pair=pair,
            bids=[],
            asks=[],
            timestamp=int(time.time() * 1000),
        )

        if price:
            initial_data = RealTimeMarketData(
                symbol=pair,
                price=price,
                change_24h=0.0,  # Would need to fetch from tickers
                volume_24h=0.0,  # Would need to fetch from tickers
                timestamp=int(__import__("time").time() * 1000),
                bid_price=order_book.bids[0][0] if order_book.bids else None,
                ask_price=order_book.asks[0][0] if order_book.asks else None,
            )
            await websocket.send_json(initial_data.dict())

        # In a real implementation, this would subscribe to exchange websockets
        # and forward updates. For now, we'll simulate periodic updates
        import asyncio

        while True:
            try:
                # Check for client messages (keepalive, unsubscribe, etc.)
                try:
                    data = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)
                    if data.get("action") == "unsubscribe":
                        break
                except TimeoutError:
                    pass  # No message received, continue with updates

                # Send periodic updates (every 5 seconds in mock mode)
                await asyncio.sleep(5)

                # Get fresh data from CoinGecko
                current_price = await coingecko.get_price(pair)
                # CoinGecko doesn't provide orderbook
                current_order_book = order_book  # Reuse empty orderbook

                if current_price:
                    update = RealTimeMarketData(
                        symbol=pair,
                        price=current_price,
                        change_24h=0.0,  # Static in mock
                        volume_24h=0.0,  # Static in mock
                        timestamp=int(__import__("time").time() * 1000),
                        bid_price=(
                            current_order_book.bids[0][0]
                            if current_order_book.bids
                            else None
                        ),
                        ask_price=(
                            current_order_book.asks[0][0]
                            if current_order_book.asks
                            else None
                        ),
                    )
                    await websocket.send_json(update.dict())

            except Exception as e:
                logger.error(f"Error in market stream for {pair}: {e}")
                break

    except Exception as e:
        logger.error(f"Market stream connection failed for {pair}: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
    finally:
        logger.info(f"Market stream closed for {pair}")
