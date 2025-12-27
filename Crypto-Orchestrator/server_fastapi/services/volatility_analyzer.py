from typing import List, Dict, Any, Literal
from pydantic import BaseModel
import logging
import math

logger = logging.getLogger(__name__)


class VolatilityAnalysisResult(BaseModel):
    volatility: float
    details: Dict[str, Any]


class VolatilityAnalyzer:
    def __init__(self):
        pass

    def calculateATR(self, data: List[Dict[str, Any]], period: int = 14) -> float:
        if len(data) < period:
            return 0.0

        trueRanges = []
        for i in range(1, len(data)):
            high = data[i]["high"]
            low = data[i]["low"]
            prevClose = data[i - 1]["close"]

            tr1 = high - low
            tr2 = abs(high - prevClose)
            tr3 = abs(low - prevClose)

            trueRanges.append(max(tr1, tr2, tr3))

        # Calculate ATR using Wilder's smoothing
        atr = sum(trueRanges[:period]) / period
        for i in range(period, len(trueRanges)):
            atr = ((atr * (period - 1)) + trueRanges[i]) / period

        return atr

    def calculateVolatilityIndex(
        self, data: List[Dict[str, Any]], period: int = 20
    ) -> float:
        if len(data) < period:
            return 0.0

        returns = []
        for i in range(1, len(data)):
            returns.append(
                (data[i]["close"] - data[i - 1]["close"]) / data[i - 1]["close"]
            )

        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)

        return math.sqrt(variance * 252)  # Annualized volatility

    def calculateVolatilityAdjustedSize(
        self,
        baseSize: float,
        currentVolatility: float,
        averageVolatility: float,
        maxVolatilityIncrease: float = 2.0,
    ) -> float:
        volatilityRatio = (
            averageVolatility / currentVolatility if currentVolatility != 0 else 1.0
        )
        adjustmentFactor = min(
            max(volatilityRatio, 1 / maxVolatilityIncrease), maxVolatilityIncrease
        )

        return baseSize * adjustmentFactor

    def analyzeMarketRegime(
        self, data: List[Dict[str, Any]]
    ) -> Literal["low_volatility", "normal", "high_volatility"]:
        volatility = self.calculateVolatilityIndex(data)

        if volatility < 0.15:
            return "low_volatility"
        elif volatility > 0.35:
            return "high_volatility"
        else:
            return "normal"

    def calculateRiskScore(self, data: List[Dict[str, Any]]) -> float:
        volatility = self.calculateVolatilityIndex(data)
        atr = self.calculateATR(data)
        regime = self.analyzeMarketRegime(data)

        # Normalize volatility to 0-100 scale
        volatilityScore = min(100, (volatility * 100) / 0.5)

        # Adjust based on market regime
        regimeMultiplier = (
            1.2
            if regime == "high_volatility"
            else 0.8 if regime == "low_volatility" else 1.0
        )

        return min(100, volatilityScore * regimeMultiplier)

    def analyze(self, data: List[Dict[str, Any]]) -> VolatilityAnalysisResult:
        try:
            volatility = self.calculateVolatilityIndex(data)
            atr = self.calculateATR(data)
            regime = self.analyzeMarketRegime(data)
            riskScore = self.calculateRiskScore(data)

            details = {
                "atr": atr,
                "regime": regime,
                "riskScore": riskScore,
                "annualizedVolatility": volatility,
            }

            return VolatilityAnalysisResult(volatility=volatility, details=details)

        except Exception as e:
            logger.error(f"Error in volatility analysis: {e}")
            return VolatilityAnalysisResult(volatility=0.0, details={"error": str(e)})
