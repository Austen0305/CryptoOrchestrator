from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class VolumeProfile:
    buyVolume: float
    sellVolume: float
    volumeRatio: float
    largeOrders: int

@dataclass
class MarketMetrics:
    volatility: float
    riskScore: float
    trend: float
    volume: float
    mer: float
    volumeProfile: VolumeProfile

class MarketAnalysisResult(BaseModel):
    summary: Dict[str, Any]
    details: Dict[str, Any]

class MarketAnalysisService:
    def __init__(self):
        pass

    def calculateTrendStrength(self, data: List[Dict[str, Any]]) -> float:
        if len(data) < 2:
            return 0.0

        # Calculate directional movement
        dmPlus = []
        dmMinus = []

        for i in range(1, len(data)):
            high = data[i]['high']
            low = data[i]['low']
            prevHigh = data[i - 1]['high']
            prevLow = data[i - 1]['low']

            upMove = high - prevHigh
            downMove = prevLow - low

            if upMove > downMove and upMove > 0:
                dmPlus.append(upMove)
                dmMinus.append(0.0)
            elif downMove > upMove and downMove > 0:
                dmPlus.append(0.0)
                dmMinus.append(downMove)
            else:
                dmPlus.append(0.0)
                dmMinus.append(0.0)

        # Calculate ADX
        smoothedDmPlus = self._smoothSeries(dmPlus, 14)
        smoothedDmMinus = self._smoothSeries(dmMinus, 14)
        adx = (smoothedDmPlus - smoothedDmMinus) / (smoothedDmPlus + smoothedDmMinus) if (smoothedDmPlus + smoothedDmMinus) != 0 else 0

        return abs(adx)

    def analyzeVolumeProfile(self, data: List[Dict[str, Any]]) -> VolumeProfile:
        buyVolume = 0.0
        sellVolume = 0.0
        largeOrders = 0
        averageVolume = sum(d['volume'] for d in data) / len(data)

        for candle in data:
            isUp = candle['close'] > candle['open']
            if isUp:
                buyVolume += candle['volume']
            else:
                sellVolume += candle['volume']

            if candle['volume'] > averageVolume * 2:
                largeOrders += 1

        return VolumeProfile(
            buyVolume=buyVolume,
            sellVolume=sellVolume,
            volumeRatio=buyVolume / (sellVolume or 1),
            largeOrders=largeOrders
        )

    def calculateMarketEfficiencyRatio(self, data: List[Dict[str, Any]]) -> float:
        if len(data) < 2:
            return 0.0

        directionalMove = 0.0
        totalMove = 0.0

        for i in range(1, len(data)):
            directional = abs(data[i]['close'] - data[i-1]['close'])
            total = abs(data[i]['high'] - data[i]['low'])

            directionalMove += directional
            totalMove += total

        return directionalMove / (totalMove or 1)

    def calculateOverallScore(self, metrics: MarketMetrics) -> float:
        weights = {
            'volatility': 0.2,
            'riskScore': 0.2,
            'trend': 0.2,
            'volume': 0.15,
            'mer': 0.15,
            'volumeProfile': 0.1
        }

        # Normalize metrics to 0-100 scale
        normalizedVolatility = 100 - (metrics.volatility * 100)  # Lower volatility is better
        normalizedRiskScore = 100 - metrics.riskScore  # Lower risk is better
        normalizedTrend = metrics.trend * 100
        normalizedVolume = min(100, (metrics.volume / 1000000))  # Cap at 1M volume
        normalizedMER = metrics.mer * 100
        normalizedVolumeProfile = (
            (100 if metrics.volumeProfile.volumeRatio > 1 else 50) +
            (metrics.volumeProfile.largeOrders * 10)
        ) / 2

        return (
            normalizedVolatility * weights['volatility'] +
            normalizedRiskScore * weights['riskScore'] +
            normalizedTrend * weights['trend'] +
            normalizedVolume * weights['volume'] +
            normalizedMER * weights['mer'] +
            normalizedVolumeProfile * weights['volumeProfile']
        )

    def _smoothSeries(self, data: List[float], period: int) -> float:
        if len(data) < period:
            return sum(data) / len(data) if data else 0.0
        return sum(data[-period:]) / period

    def analyze(self, data: List[Dict[str, Any]], volatility_analyzer: Optional[Any] = None) -> MarketAnalysisResult:
        try:
            # Calculate metrics
            trend = self.calculateTrendStrength(data)
            volumeProfile = self.analyzeVolumeProfile(data)
            mer = self.calculateMarketEfficiencyRatio(data)

            # Get volatility metrics if analyzer provided
            if volatility_analyzer:
                volatility = volatility_analyzer.calculateVolatilityIndex(data)
                riskScore = volatility_analyzer.calculateRiskScore(data)
            else:
                volatility = 0.0
                riskScore = 0.0

            volume = sum(d['volume'] for d in data) / len(data) if data else 0.0

            metrics = MarketMetrics(
                volatility=volatility,
                riskScore=riskScore,
                trend=trend,
                volume=volume,
                mer=mer,
                volumeProfile=volumeProfile
            )

            overallScore = self.calculateOverallScore(metrics)

            summary = {
                "overallScore": overallScore,
                "trendStrength": trend,
                "marketEfficiency": mer,
                "volumeRatio": volumeProfile.volumeRatio,
                "largeOrders": volumeProfile.largeOrders
            }

            details = {
                "metrics": {
                    "volatility": volatility,
                    "riskScore": riskScore,
                    "trend": trend,
                    "volume": volume,
                    "mer": mer
                },
                "volumeProfile": {
                    "buyVolume": volumeProfile.buyVolume,
                    "sellVolume": volumeProfile.sellVolume,
                    "volumeRatio": volumeProfile.volumeRatio,
                    "largeOrders": volumeProfile.largeOrders
                }
            }

            return MarketAnalysisResult(summary=summary, details=details)

        except Exception as e:
            logger.error(f"Error in market analysis: {e}")
            return MarketAnalysisResult(summary={"error": str(e)}, details={})
