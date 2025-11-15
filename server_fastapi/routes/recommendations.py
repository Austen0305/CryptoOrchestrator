from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
from datetime import datetime
import random
import jwt
import os

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Environment variables
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

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
    reasoning: List[str]

class OptimalRiskSettings(BaseModel):
    conservative: Dict[str, float]
    moderate: Dict[str, float]
    aggressive: Dict[str, float]

class TradingRecommendations(BaseModel):
    topPairs: List[PairAnalysis]
    optimalRiskSettings: OptimalRiskSettings
    marketSentiment: str
    lastUpdated: int

@router.get("/", response_model=TradingRecommendations)
async def get_trading_recommendations(current_user: dict = Depends(get_current_user)):
    """Get AI-powered trading pair recommendations and optimal risk settings"""
    try:
        # Mock data for demonstration - in production, this would come from ML models
        # analyzing real market data

        mock_pairs = [
            {
                "symbol": "BTC/USDT",
                "baseAsset": "BTC",
                "quoteAsset": "USDT",
                "currentPrice": 65000.0,
                "volatility": 0.15,
                "volumeScore": 9.2,
                "momentumScore": 2.5,
                "profitabilityScore": 8.7,
                "recommendedRiskPerTrade": 1.0,
                "recommendedStopLoss": 2.0,
                "recommendedTakeProfit": 4.0,
                "confidence": 0.85,
                "reasoning": [
                    "Strong upward momentum in BTC price action",
                    "High volume confirming bullish trend",
                    "Low volatility compared to altcoins",
                    "Historical profitability shows 68% win rate"
                ]
            },
            {
                "symbol": "ETH/USDT",
                "baseAsset": "ETH",
                "quoteAsset": "USDT",
                "currentPrice": 3200.0,
                "volatility": 0.20,
                "volumeScore": 8.5,
                "momentumScore": 1.8,
                "profitabilityScore": 7.9,
                "recommendedRiskPerTrade": 1.2,
                "recommendedStopLoss": 2.5,
                "recommendedTakeProfit": 5.0,
                "confidence": 0.78,
                "reasoning": [
                    "ETH showing positive momentum with BTC correlation",
                    "Growing DeFi ecosystem adoption",
                    "Recent network upgrades improving fundamentals",
                    "Volume increasing as institutional interest rises"
                ]
            },
            {
                "symbol": "SOL/USDT",
                "baseAsset": "SOL",
                "quoteAsset": "USDT",
                "currentPrice": 180.0,
                "volatility": 0.35,
                "volumeScore": 7.8,
                "momentumScore": 3.2,
                "profitabilityScore": 8.1,
                "recommendedRiskPerTrade": 1.5,
                "recommendedStopLoss": 3.0,
                "recommendedTakeProfit": 6.0,
                "confidence": 0.72,
                "reasoning": [
                    "Strong momentum in Solana ecosystem growth",
                    "High volatility signals opportunity for scalping",
                    "Increasing developer activity and TVL",
                    "Positive correlation with overall market sentiment"
                ]
            },
            {
                "symbol": "ADA/USDT",
                "baseAsset": "ADA",
                "quoteAsset": "USDT",
                "currentPrice": 0.45,
                "volatility": 0.25,
                "volumeScore": 6.9,
                "momentumScore": -1.2,
                "profitabilityScore": 6.5,
                "recommendedRiskPerTrade": 0.8,
                "recommendedStopLoss": 1.5,
                "recommendedTakeProfit": 3.0,
                "confidence": 0.65,
                "reasoning": [
                    "Cardano showing consolidation after recent pullback",
                    "Smart contract platform with strong fundamentals",
                    "Lower risk entry point with solid support levels",
                    "Long-term potential despite short-term weakness"
                ]
            },
            {
                "symbol": "DOT/USDT",
                "baseAsset": "DOT",
                "quoteAsset": "USDT",
                "currentPrice": 6.80,
                "volatility": 0.28,
                "volumeScore": 7.2,
                "momentumScore": 0.9,
                "profitabilityScore": 7.3,
                "recommendedRiskPerTrade": 1.0,
                "recommendedStopLoss": 2.0,
                "recommendedTakeProfit": 4.0,
                "confidence": 0.70,
                "reasoning": [
                    "Polkadot parachain auctions driving interest",
                    "Interoperability features gaining traction",
                    "Balanced risk-reward profile",
                    "Growing ecosystem adoption"
                ]
            }
        ]

        # Add some randomization to make data more realistic
        for pair in mock_pairs:
            # Slight price variations
            pair["currentPrice"] *= (1 + random.uniform(-0.02, 0.02))
            # Slight score variations
            pair["confidence"] += random.uniform(-0.05, 0.05)
            pair["confidence"] = max(0.5, min(0.95, pair["confidence"]))

        # Determine market sentiment based on average momentum
        avg_momentum = sum(p["momentumScore"] for p in mock_pairs) / len(mock_pairs)
        if avg_momentum > 1.5:
            market_sentiment = "bullish"
        elif avg_momentum < -1.5:
            market_sentiment = "bearish"
        else:
            market_sentiment = "neutral"

        # Optimal risk settings based on market conditions
        if market_sentiment == "bullish":
            optimal_risk = {
                "conservative": {"riskPerTrade": 0.5, "stopLoss": 1.0, "takeProfit": 2.0},
                "moderate": {"riskPerTrade": 1.0, "stopLoss": 2.0, "takeProfit": 4.0},
                "aggressive": {"riskPerTrade": 2.0, "stopLoss": 3.0, "takeProfit": 6.0}
            }
        elif market_sentiment == "bearish":
            optimal_risk = {
                "conservative": {"riskPerTrade": 0.3, "stopLoss": 0.5, "takeProfit": 1.0},
                "moderate": {"riskPerTrade": 0.7, "stopLoss": 1.5, "takeProfit": 3.0},
                "aggressive": {"riskPerTrade": 1.5, "stopLoss": 2.5, "takeProfit": 5.0}
            }
        else:
            optimal_risk = {
                "conservative": {"riskPerTrade": 0.5, "stopLoss": 1.0, "takeProfit": 2.0},
                "moderate": {"riskPerTrade": 1.0, "stopLoss": 2.0, "takeProfit": 4.0},
                "aggressive": {"riskPerTrade": 1.5, "stopLoss": 2.5, "takeProfit": 5.0}
            }

        response = TradingRecommendations(
            topPairs=[PairAnalysis(**pair) for pair in mock_pairs],
            optimalRiskSettings=OptimalRiskSettings(**optimal_risk),
            marketSentiment=market_sentiment,
            lastUpdated=int(datetime.now().timestamp() * 1000)  # milliseconds
        )

        return response

    except Exception as e:
        logger.error(f"Error generating trading recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate trading recommendations")