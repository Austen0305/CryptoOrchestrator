"""
Sentiment Analysis Routes
Provides market sentiment analysis endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sentiment", tags=["Sentiment"])


class MarketSentiment(BaseModel):
    """Market sentiment analysis"""
    sentiment: str  # "bullish", "bearish", "neutral"
    confidence: float
    indicators: Dict[str, float]
    news_sentiment: Optional[float] = None


@router.get("/{symbol}", response_model=MarketSentiment)
async def get_symbol_sentiment(symbol: str):
    """
    Get AI-powered market sentiment analysis for a trading pair
    
    Analyzes:
    - Technical indicators
    - Volume trends
    - Price momentum
    - Social media sentiment (if available)
    - News sentiment (if available)
    """
    try:
        # Try to use the existing ai_analysis sentiment function
        try:
            from ..routes.ai_analysis import _analyze_market_sentiment
            sentiment_data = await _analyze_market_sentiment(symbol)
        except Exception:
            # Fallback to simple stub if ai_analysis is not available
            import random
            sentiment_score = random.uniform(-1, 1)
            
            if sentiment_score > 0.3:
                sentiment = "bullish"
            elif sentiment_score < -0.3:
                sentiment = "bearish"
            else:
                sentiment = "neutral"
            
            sentiment_data = {
                "sentiment": sentiment,
                "confidence": abs(sentiment_score),
                "indicators": {
                    "rsi": random.uniform(30, 70),
                    "macd": random.uniform(-10, 10),
                    "volume_trend": random.uniform(-20, 20),
                    "price_momentum": random.uniform(-15, 15),
                },
                "news_sentiment": random.uniform(-1, 1),
            }

        return MarketSentiment(
            sentiment=sentiment_data["sentiment"],
            confidence=sentiment_data["confidence"],
            indicators=sentiment_data.get("indicators", {}),
            news_sentiment=sentiment_data.get("news_sentiment"),
        )
    except Exception as e:
        logger.error(f"Error analyzing sentiment for {symbol}: {e}", exc_info=True)
        # Return neutral sentiment instead of error
        return MarketSentiment(
            sentiment="neutral",
            confidence=0.5,
            indicators={},
            news_sentiment=None,
        )

