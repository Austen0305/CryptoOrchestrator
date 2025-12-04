from fastapi import APIRouter, HTTPException, Query, Depends, WebSocket
from .ws import get_current_user_ws
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import time

from server_fastapi.services.exchange_service import (
    ExchangeService,
    default_exchange,
    TradingPair,
    MarketData,
    OrderBook,
)
from server_fastapi.services.exchange.enhanced_kraken_service import (
    enhanced_kraken_service,
)
from server_fastapi.services.market_analysis_service import MarketAnalysisService
from server_fastapi.services.volatility_analyzer import VolatilityAnalyzer
from ..dependencies.auth import get_current_user
from ..database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from ..repositories.candle_repository import CandleRepository
from ..models.candle import Candle
from ..middleware.query_cache import cache_query_result

logger = logging.getLogger(__name__)

# Initialize services
market_analysis_service = MarketAnalysisService()
volatility_analyzer = VolatilityAnalyzer()


# Dependency injection for exchange service
def get_exchange_service() -> ExchangeService:
    return default_exchange


# Dependency injection for enhanced Kraken service
def get_enhanced_kraken_service():
    return enhanced_kraken_service


router = APIRouter()


# Pydantic models for requests and responses
class MarketSummary(BaseModel):
    total_pairs: int
    total_volume_24h: float
    top_pairs: List[TradingPair]


class TickerResponse(BaseModel):
    symbol: str
    last_price: float
    change_24h: float
    volume_24h: float
    high_24h: float
    low_24h: float


class OHLCVRequest(BaseModel):
    pair: str
    timeframe: Optional[str] = "1h"
    limit: Optional[int] = 100


class PriceChartResponse(BaseModel):
    pair: str
    timeframe: str
    data: List[MarketData]


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
    candles: List[CandleDTO]


class TradingPairDetails(BaseModel):
    symbol: str
    base_asset: str
    quote_asset: str
    current_price: float
    change_24h: float
    volume_24h: float
    high_24h: float
    low_24h: float
    market_cap: Optional[float] = None
    price_precision: int = 8
    quantity_precision: int = 8
    min_order_size: float = 0.0
    max_order_size: Optional[float] = None
    is_active: bool = True


class RealTimeMarketData(BaseModel):
    symbol: str
    price: float
    change_24h: float
    volume_24h: float
    timestamp: int
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None


class TechnicalIndicator(BaseModel):
    name: str
    value: float
    signal: str
    period: Optional[int] = None


class MarketAnalysisResponse(BaseModel):
    pair: str
    price: float
    indicators: List[TechnicalIndicator]
    trend: str
    strength: float
    recommendation: str
    timestamp: int


# Existing endpoints updated with dependency injection and improved models
@router.get("/", response_model=List[TradingPair])
@cache_query_result(
    ttl=600, key_prefix="markets", include_user=False, include_params=False
)
async def get_markets(
    exchange: ExchangeService = Depends(get_exchange_service),
) -> List[TradingPair]:
    """Get all available trading pairs"""
    try:
        pairs = await exchange.get_all_trading_pairs()
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
    exchange: ExchangeService = Depends(get_exchange_service),
) -> PriceChartResponse:
    """Get OHLCV data for a trading pair"""
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

        # Get historical data and convert to MarketData objects
        historical_data = await exchange.get_historical_data(pair, timeframe, limit)

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
    timeframe: str = Query("1m", description="Timeframe for stored candles"),
    limit: int = Query(500, ge=1, le=5000),
    db: AsyncSession = Depends(get_db_session),
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
async def get_order_book(
    pair: str, exchange: ExchangeService = Depends(get_exchange_service)
) -> OrderBook:
    """Get order book for a trading pair"""
    try:
        if "/" not in pair:
            raise HTTPException(
                status_code=400, detail="Invalid pair format. Use format: BASE/QUOTE"
            )

        order_book = await exchange.get_order_book(pair)
        return order_book
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
async def get_price(
    pair: str, exchange: ExchangeService = Depends(get_exchange_service)
) -> dict:
    """Get current price for a trading pair"""
    try:
        if "/" not in pair:
            raise HTTPException(
                status_code=400, detail="Invalid pair format. Use format: BASE/QUOTE"
            )

        price = await exchange.get_market_price(pair)
        if price is None:
            raise HTTPException(status_code=404, detail=f"Price not found for {pair}")
        return {"pair": pair, "price": price}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching price for {pair}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch price for {pair}")


# New market data endpoints
@router.get("/tickers", response_model=List[TickerResponse])
async def get_tickers(
    limit: int = Query(50, description="Number of tickers to return", ge=1, le=500),
    exchange: ExchangeService = Depends(get_exchange_service),
) -> List[TickerResponse]:
    """Get ticker data for multiple trading pairs"""
    try:
        pairs = await exchange.get_all_trading_pairs()

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
async def get_market_summary(
    top_count: int = Query(
        10, description="Number of top pairs to include", ge=1, le=50
    ),
    exchange: ExchangeService = Depends(get_exchange_service),
) -> MarketSummary:
    """Get market summary with total statistics and top pairs"""
    try:
        pairs = await exchange.get_all_trading_pairs()

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
    exchange: ExchangeService = Depends(get_exchange_service),
) -> List[TradingPair]:
    """Search for trading pairs by symbol"""
    try:
        if not query or len(query.strip()) < 1:
            raise HTTPException(
                status_code=400, detail="Search query must be at least 1 character"
            )

        query_lower = query.lower().strip()
        pairs = await exchange.get_all_trading_pairs()

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
async def get_trading_pair_details(
    pair: str, exchange: ExchangeService = Depends(get_exchange_service)
) -> TradingPairDetails:
    """Get detailed information about a specific trading pair"""
    try:
        if "/" not in pair:
            raise HTTPException(
                status_code=400, detail="Invalid pair format. Use format: BASE/QUOTE"
            )

        # Get basic pair info
        pairs = await exchange.get_all_trading_pairs()
        pair_info = next((p for p in pairs if p.symbol == pair), None)

        if not pair_info:
            raise HTTPException(
                status_code=404, detail=f"Trading pair {pair} not found"
            )

        # Get additional details from exchange
        try:
            # In a real implementation, this would fetch market details, precision, limits, etc.
            market_details = {
                "price_precision": 8,
                "quantity_precision": 8,
                "min_order_size": 0.0001 if pair_info.base_asset == "BTC" else 0.01,
                "max_order_size": None,
                "is_active": True,
            }
        except:
            market_details = {
                "price_precision": 8,
                "quantity_precision": 8,
                "min_order_size": 0.0,
                "max_order_size": None,
                "is_active": True,
            }

        return TradingPairDetails(
            symbol=pair_info.symbol,
            base_asset=pair_info.base_asset,
            quote_asset=pair_info.quote_asset,
            current_price=pair_info.current_price,
            change_24h=pair_info.change_24h,
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
@router.get("/favorites", response_model=List[TradingPair])
async def get_favorite_pairs(
    current_user: dict = Depends(get_current_user),
    exchange: ExchangeService = Depends(get_exchange_service),
) -> List[TradingPair]:
    """Get user's favorite trading pairs (requires authentication)"""
    try:
        # In a real implementation, this would fetch from user's preferences
        # For now, return popular pairs as favorites
        pairs = await exchange.get_all_trading_pairs()
        favorites = sorted(pairs, key=lambda x: x.volume_24h, reverse=True)[:5]
        return favorites
    except Exception as e:
        logger.error(
            f"Error fetching favorite pairs for user {current_user['id']}: {e}"
        )
        raise HTTPException(status_code=500, detail="Failed to fetch favorite pairs")


@router.get("/watchlist", response_model=List[TradingPair])
async def get_watchlist(
    current_user: dict = Depends(get_current_user),
    exchange: ExchangeService = Depends(get_exchange_service),
) -> List[TradingPair]:
    """Get user's watchlist (requires authentication)"""
    try:
        # In a real implementation, this would fetch from user's watchlist
        # For now, return some pairs as watchlist
        pairs = await exchange.get_all_trading_pairs()
        watchlist = pairs[:10]  # First 10 pairs as mock watchlist
        return watchlist
    except Exception as e:
        logger.error(f"Error fetching watchlist for user {current_user['id']}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch watchlist")


# Rate-limited endpoints with enhanced validation and authentication
@router.get("/advanced/{pair}/analysis", response_model=MarketAnalysisResponse)
async def get_advanced_market_analysis(
    pair: str,
    indicators: List[str] = Query(
        ["rsi", "macd", "bollinger"], description="Technical indicators to calculate"
    ),
    period: int = Query(14, description="Period for indicators", ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    exchange: ExchangeService = Depends(get_exchange_service),
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

        # Get historical data for analysis
        historical_data = await exchange.get_historical_data(pair, "1h", 200)

        if not historical_data:
            raise HTTPException(
                status_code=404, detail=f"No market data available for {pair}"
            )

        # Convert MarketData to dict format for analysis
        ohlcv_data = [
            {
                "timestamp": data.timestamp,
                "open": data.open,
                "high": data.high,
                "low": data.low,
                "close": data.close,
                "volume": data.volume,
            }
            for data in historical_data
        ]

        # Perform market analysis using the analysis service
        analysis_result = market_analysis_service.analyze(
            ohlcv_data, volatility_analyzer
        )

        # Get current price
        current_price = await exchange.get_market_price(pair)
        if not current_price and historical_data:
            current_price = historical_data[-1].close

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
                    else "bearish" if rsi_value > 70 else "neutral"
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
            else "bearish" if trend_strength < 0.4 else "sideways"
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
        logger.error(f"Error getting advanced analysis for {pair}: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform market analysis")


@router.get("/realtime/{pair}/price-stream", response_model=RealTimeMarketData)
async def get_realtime_price_stream(
    pair: str,
    current_user: dict = Depends(get_current_user),
    exchange: ExchangeService = Depends(get_exchange_service),
) -> RealTimeMarketData:
    """Get realtime price stream info (requires authentication)"""
    try:
        if "/" not in pair:
            raise HTTPException(
                status_code=400, detail="Invalid pair format. Use format: BASE/QUOTE"
            )

        # Get current price
        price = await exchange.get_market_price(pair)
        if price is None:
            raise HTTPException(status_code=404, detail=f"Price not found for {pair}")

        # Get order book for bid/ask prices
        order_book = await exchange.get_order_book(pair)
        bid_price = order_book.bids[0][0] if order_book.bids else None
        ask_price = order_book.asks[0][0] if order_book.asks else None

        # Get recent trading pair data for 24h change and volume
        pairs = await exchange.get_all_trading_pairs()
        pair_data = next((p for p in pairs if p.symbol == pair), None)

        return RealTimeMarketData(
            symbol=pair,
            price=price,
            change_24h=pair_data.change_24h if pair_data else 0.0,
            volume_24h=pair_data.volume_24h if pair_data else 0.0,
            timestamp=int(__import__("time").time() * 1000),
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

        # Send initial data
        exchange = get_exchange_service()
        await exchange.connect()

        # Send initial market data
        price = await exchange.get_market_price(pair)
        order_book = await exchange.get_order_book(pair)

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
                except asyncio.TimeoutError:
                    pass  # No message received, continue with updates

                # Send periodic updates (every 5 seconds in mock mode)
                await asyncio.sleep(5)

                # Get fresh data
                current_price = await exchange.get_market_price(pair)
                current_order_book = await exchange.get_order_book(pair)

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
