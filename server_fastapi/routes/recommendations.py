import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..dependencies.auth import get_current_user
from ..middleware.cache_manager import cached
from ..services.market_data_service import MarketDataService, get_market_data_service
from ..services.ml.enhanced_ml_engine import EnhancedMLEngine
from ..services.ml.enhanced_ml_engine import MarketData as MLMarketData
from ..services.ml.ensemble_engine import EnsembleEngine
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter()


class PairAnalysis(BaseModel):
    symbol: str
    baseAsset: str
    quoteAsset: str
    currentPrice: float
    volatility: float
    volumeScore: float
    momentumScore: float
    profitabilityScore: float
    recommendedRiskPerTrade: float
    recommendedStopLoss: float
    recommendedTakeProfit: float
    confidence: float
    reasoning: list[str]


class OptimalRiskSettings(BaseModel):
    conservative: dict[str, float]
    moderate: dict[str, float]
    aggressive: dict[str, float]


class TradingRecommendations(BaseModel):
    topPairs: list[PairAnalysis]
    optimalRiskSettings: OptimalRiskSettings
    marketSentiment: str
    lastUpdated: int


@router.get("/", response_model=TradingRecommendations)
@cached(
    ttl=300, prefix="trading_recommendations"
)  # 5min TTL for recommendations (ML-generated)
async def get_trading_recommendations(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get AI-powered trading pair recommendations and optimal risk settings"""
    try:
        # Initialize services
        market_data = get_market_data_service()
        ml_engine = EnhancedMLEngine()
        ensemble_engine = EnsembleEngine()

        # Top trading pairs to analyze
        trading_pairs = [
            {"symbol": "BTC/USD", "baseAsset": "BTC", "quoteAsset": "USD"},
            {"symbol": "ETH/USD", "baseAsset": "ETH", "quoteAsset": "USD"},
            {"symbol": "SOL/USD", "baseAsset": "SOL", "quoteAsset": "USD"},
            {"symbol": "ADA/USD", "baseAsset": "ADA", "quoteAsset": "USD"},
            {"symbol": "DOT/USD", "baseAsset": "DOT", "quoteAsset": "USD"},
        ]

        analyzed_pairs = []

        for pair_info in trading_pairs:
            symbol = pair_info["symbol"]
            try:
                # Get real market data
                market_data_dict = await market_data.get_market_data(symbol)
                if not market_data_dict:
                    continue

                current_price = market_data_dict.get("price", 0.0)
                if not current_price or current_price <= 0:
                    continue

                # Get historical prices for ML analysis
                historical_prices = await market_data.get_historical_prices(
                    symbol, days=30
                )
                if not historical_prices or len(historical_prices) < 20:
                    # Fallback: use current price data
                    historical_prices = [{"price": current_price}] * 30

                # Convert to ML MarketData format
                ml_data = []
                for i, price_point in enumerate(
                    historical_prices[-30:]
                ):  # Last 30 days
                    price = price_point.get("price", current_price)
                    # Estimate OHLCV from price (simplified - in production use real OHLCV)
                    high = price * 1.02
                    low = price * 0.98
                    volume = (
                        market_data_dict.get("volume_24h", 0.0) / 30.0
                    )  # Average daily volume
                    ml_data.append(
                        MLMarketData(
                            open=price,
                            high=high,
                            low=low,
                            close=price,
                            volume=volume,
                        )
                    )

                # Get ML prediction
                try:
                    ml_prediction = await ml_engine.predict(ml_data)
                    ensemble_prediction = await ensemble_engine.predict(ml_data)
                except Exception as ml_error:
                    logger.warning(f"ML prediction failed for {symbol}: {ml_error}")
                    # Fallback to technical analysis
                    ml_prediction = None
                    ensemble_prediction = None

                # Calculate metrics from market data
                change_24h = market_data_dict.get("change_24h", 0.0)
                volume_24h = market_data_dict.get("volume_24h", 0.0)
                high_24h = market_data_dict.get("high_24h", current_price)
                low_24h = market_data_dict.get("low_24h", current_price)

                # Calculate volatility (24h range as percentage)
                volatility = (
                    abs((high_24h - low_24h) / current_price)
                    if current_price > 0
                    else 0.0
                )

                # Calculate volume score (0-10, normalized)
                # Use relative volume compared to BTC as baseline
                btc_volume = 20000000000  # Approximate BTC daily volume
                volume_score = (
                    min(10.0, (volume_24h / btc_volume) * 10.0)
                    if volume_24h > 0
                    else 0.0
                )

                # Calculate momentum score (based on 24h change)
                momentum_score = change_24h / 10.0  # Normalize to -5 to +5 range
                momentum_score = max(-5.0, min(5.0, momentum_score))

                # Calculate profitability score (based on ML confidence and momentum)
                if ml_prediction and hasattr(ml_prediction, "confidence"):
                    ml_confidence = ml_prediction.confidence
                elif ensemble_prediction and hasattr(ensemble_prediction, "confidence"):
                    ml_confidence = ensemble_prediction.confidence
                else:
                    ml_confidence = 0.5

                # Profitability score combines ML confidence, momentum, and volume
                profitability_score = (
                    (ml_confidence * 5.0)  # ML confidence component (0-5)
                    + (max(0, momentum_score) * 2.0)  # Positive momentum (0-10)
                    + (volume_score * 0.3)  # Volume component (0-3)
                )
                profitability_score = min(10.0, max(0.0, profitability_score))

                # Calculate recommended risk settings based on volatility
                if volatility < 0.05:
                    # Low volatility - conservative settings
                    recommended_risk = 1.0
                    recommended_stop_loss = 2.0
                    recommended_take_profit = 4.0
                elif volatility < 0.15:
                    # Medium volatility - moderate settings
                    recommended_risk = 1.2
                    recommended_stop_loss = 2.5
                    recommended_take_profit = 5.0
                else:
                    # High volatility - wider stops
                    recommended_risk = 1.5
                    recommended_stop_loss = 3.0
                    recommended_take_profit = 6.0

                # Calculate confidence from ML prediction
                if ml_prediction and hasattr(ml_prediction, "confidence"):
                    confidence = float(ml_prediction.confidence)
                elif ensemble_prediction and hasattr(ensemble_prediction, "confidence"):
                    confidence = float(ensemble_prediction.confidence)
                else:
                    # Fallback confidence based on profitability score
                    confidence = min(0.95, max(0.5, profitability_score / 10.0))

                # Generate reasoning from ML prediction and market data
                reasoning = []
                if ml_prediction and hasattr(ml_prediction, "reasoning"):
                    reasoning.append(ml_prediction.reasoning)
                elif ensemble_prediction and hasattr(ensemble_prediction, "reasoning"):
                    reasoning.append(ensemble_prediction.reasoning)
                else:
                    # Fallback reasoning
                    if momentum_score > 1.0:
                        reasoning.append(
                            f"Strong upward momentum ({change_24h:.2f}% 24h change)"
                        )
                    elif momentum_score < -1.0:
                        reasoning.append(
                            f"Downward momentum ({change_24h:.2f}% 24h change)"
                        )
                    else:
                        reasoning.append("Neutral momentum, consolidation phase")

                if volume_score > 7.0:
                    reasoning.append("High trading volume confirming trend")
                elif volume_score < 3.0:
                    reasoning.append("Low volume, potential reversal risk")

                if volatility < 0.1:
                    reasoning.append("Low volatility, stable price action")
                elif volatility > 0.3:
                    reasoning.append("High volatility, increased risk and opportunity")

                if profitability_score > 7.0:
                    reasoning.append(
                        "Strong profitability potential based on ML analysis"
                    )
                elif profitability_score < 4.0:
                    reasoning.append(
                        "Lower profitability score, consider reduced position size"
                    )

                analyzed_pairs.append(
                    {
                        "symbol": symbol,
                        "baseAsset": pair_info["baseAsset"],
                        "quoteAsset": pair_info["quoteAsset"],
                        "currentPrice": round(current_price, 2),
                        "volatility": round(volatility, 2),
                        "volumeScore": round(volume_score, 1),
                        "momentumScore": round(momentum_score, 2),
                        "profitabilityScore": round(profitability_score, 1),
                        "recommendedRiskPerTrade": round(recommended_risk, 1),
                        "recommendedStopLoss": round(recommended_stop_loss, 1),
                        "recommendedTakeProfit": round(recommended_take_profit, 1),
                        "confidence": round(confidence, 2),
                        "reasoning": reasoning[:4],  # Limit to 4 reasons
                    }
                )

            except Exception as pair_error:
                logger.warning(f"Error analyzing pair {symbol}: {pair_error}")
                continue

        # Sort by profitability score (descending)
        analyzed_pairs.sort(key=lambda x: x["profitabilityScore"], reverse=True)
        top_pairs = analyzed_pairs[:5]  # Top 5 pairs

        # Determine market sentiment based on average momentum
        if top_pairs:
            avg_momentum = sum(p["momentumScore"] for p in top_pairs) / len(top_pairs)
            if avg_momentum > 1.5:
                market_sentiment = "bullish"
            elif avg_momentum < -1.5:
                market_sentiment = "bearish"
            else:
                market_sentiment = "neutral"
        else:
            # Fallback if no pairs analyzed
            market_sentiment = "neutral"

        # Optimal risk settings based on market conditions
        if market_sentiment == "bullish":
            optimal_risk = {
                "conservative": {
                    "riskPerTrade": 0.5,
                    "stopLoss": 1.0,
                    "takeProfit": 2.0,
                },
                "moderate": {"riskPerTrade": 1.0, "stopLoss": 2.0, "takeProfit": 4.0},
                "aggressive": {"riskPerTrade": 2.0, "stopLoss": 3.0, "takeProfit": 6.0},
            }
        elif market_sentiment == "bearish":
            optimal_risk = {
                "conservative": {
                    "riskPerTrade": 0.3,
                    "stopLoss": 0.5,
                    "takeProfit": 1.0,
                },
                "moderate": {"riskPerTrade": 0.7, "stopLoss": 1.5, "takeProfit": 3.0},
                "aggressive": {"riskPerTrade": 1.5, "stopLoss": 2.5, "takeProfit": 5.0},
            }
        else:
            optimal_risk = {
                "conservative": {
                    "riskPerTrade": 0.5,
                    "stopLoss": 1.0,
                    "takeProfit": 2.0,
                },
                "moderate": {"riskPerTrade": 1.0, "stopLoss": 2.0, "takeProfit": 4.0},
                "aggressive": {"riskPerTrade": 1.5, "stopLoss": 2.5, "takeProfit": 5.0},
            }

        # If no pairs were successfully analyzed, return empty with fallback sentiment
        if not top_pairs:
            logger.warning(
                "No trading pairs successfully analyzed, returning empty recommendations"
            )
            return TradingRecommendations(
                topPairs=[],
                optimalRiskSettings=OptimalRiskSettings(**optimal_risk),
                marketSentiment=market_sentiment,
                lastUpdated=int(datetime.now().timestamp() * 1000),
            )

        response = TradingRecommendations(
            topPairs=[PairAnalysis(**pair) for pair in top_pairs],
            optimalRiskSettings=OptimalRiskSettings(**optimal_risk),
            marketSentiment=market_sentiment,
            lastUpdated=int(datetime.now().timestamp() * 1000),  # milliseconds
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        user_id = None
        try:
            user_id = _get_user_id(current_user)
        except HTTPException:
            pass  # User ID not available, log without it
        logger.error(
            f"Failed to get trading recommendations: {e}",
            exc_info=True,
            extra={"user_id": user_id, "operation": "get_trading_recommendations"},
        )
        raise HTTPException(
            status_code=500, detail="Failed to generate trading recommendations"
        )
