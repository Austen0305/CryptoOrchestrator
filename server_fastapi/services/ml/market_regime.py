"""
Market Regime Detection Service - Identify market conditions
"""
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import logging
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)


class MarketRegime(str, Enum):
    """Market regime types"""
    BULL = "bull"  # Bull market - uptrend
    BEAR = "bear"  # Bear market - downtrend
    SIDEWAYS = "sideways"  # Range-bound, sideways
    VOLATILE = "volatile"  # High volatility, choppy
    TRENDING = "trending"  # Strong trend (up or down)
    CONSOLIDATION = "consolidation"  # Consolidation phase


class RegimeMetrics(BaseModel):
    """Market regime metrics"""
    regime: MarketRegime
    confidence: float  # 0 to 1
    trend_strength: float  # -1 to 1 (negative = downtrend, positive = uptrend)
    volatility: float  # 0 to 1
    volume_trend: float  # -1 to 1
    rsi: float  # RSI indicator value
    macd_signal: float  # MACD signal strength
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MarketRegimeService:
    """Service for detecting market regimes"""
    
    def __init__(self):
        logger.info("Market Regime Detection Service initialized")
    
    def detect_regime(
        self,
        prices: List[float],
        volumes: List[float],
        lookback_period: int = 20
    ) -> RegimeMetrics:
        """Detect current market regime from price and volume data"""
        try:
            if len(prices) < lookback_period:
                # Not enough data
                return RegimeMetrics(
                    regime=MarketRegime.SIDEWAYS,
                    confidence=0.0,
                    trend_strength=0.0,
                    volatility=0.0,
                    volume_trend=0.0,
                    rsi=50.0,
                    macd_signal=0.0
                )
            
            # Get recent data
            recent_prices = prices[-lookback_period:]
            recent_volumes = volumes[-lookback_period:] if volumes else [1.0] * lookback_period
            
            # Calculate technical indicators
            rsi = self._calculate_rsi(recent_prices, period=14)
            macd_signal = self._calculate_macd_signal(recent_prices)
            volatility = self._calculate_volatility(recent_prices)
            trend_strength = self._calculate_trend_strength(recent_prices)
            volume_trend = self._calculate_volume_trend(recent_volumes)
            
            # Determine regime
            regime, confidence = self._classify_regime(
                trend_strength,
                volatility,
                volume_trend,
                rsi,
                macd_signal
            )
            
            return RegimeMetrics(
                regime=regime,
                confidence=confidence,
                trend_strength=trend_strength,
                volatility=volatility,
                volume_trend=volume_trend,
                rsi=rsi,
                macd_signal=macd_signal
            )
        
        except Exception as e:
            logger.error(f"Regime detection failed: {e}")
            return RegimeMetrics(
                regime=MarketRegime.SIDEWAYS,
                confidence=0.0,
                trend_strength=0.0,
                volatility=0.0,
                volume_trend=0.0,
                rsi=50.0,
                macd_signal=0.0
            )
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index)"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi)
    
    def _calculate_macd_signal(self, prices: List[float]) -> float:
        """Calculate MACD signal strength"""
        if len(prices) < 26:
            return 0.0
        
        prices_array = np.array(prices)
        
        # Calculate EMAs
        ema_12 = self._calculate_ema(prices_array, 12)
        ema_26 = self._calculate_ema(prices_array, 26)
        
        # MACD line
        macd_line = ema_12 - ema_26
        
        # Signal line (9-period EMA of MACD)
        if len(macd_line) < 9:
            return 0.0
        
        signal_line = self._calculate_ema(macd_line, 9)
        
        # MACD histogram (MACD - Signal)
        if len(macd_line) == len(signal_line):
            histogram = macd_line[-1] - signal_line[-1]
            # Normalize to -1 to 1 range
            signal_strength = np.tanh(histogram / prices_array[-1]) if prices_array[-1] != 0 else 0.0
            return float(signal_strength)
        
        return 0.0
    
    def _calculate_ema(self, values: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average"""
        if len(values) < period:
            return np.array([])
        
        ema = np.zeros(len(values))
        ema[period - 1] = np.mean(values[:period])
        
        multiplier = 2.0 / (period + 1)
        
        for i in range(period, len(values)):
            ema[i] = (values[i] * multiplier) + (ema[i - 1] * (1 - multiplier))
        
        return ema[period - 1:]
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calculate normalized volatility (0 to 1)"""
        if len(prices) < 2:
            return 0.0
        
        returns = np.diff(prices) / prices[:-1]
        volatility = np.std(returns)
        
        # Normalize to 0-1 range (assuming max volatility around 0.1 or 10%)
        normalized_volatility = min(volatility / 0.1, 1.0)
        
        return float(normalized_volatility)
    
    def _calculate_trend_strength(self, prices: List[float]) -> float:
        """Calculate trend strength (-1 to 1)"""
        if len(prices) < 2:
            return 0.0
        
        prices_array = np.array(prices)
        
        # Linear regression to determine trend
        x = np.arange(len(prices_array))
        slope = np.polyfit(x, prices_array, 1)[0]
        
        # Normalize slope to -1 to 1 range
        max_slope = prices_array[-1] * 0.1  # 10% change over period
        trend_strength = np.tanh(slope / max_slope) if max_slope != 0 else 0.0
        
        return float(trend_strength)
    
    def _calculate_volume_trend(self, volumes: List[float]) -> float:
        """Calculate volume trend (-1 to 1)"""
        if len(volumes) < 2:
            return 0.0
        
        volumes_array = np.array(volumes)
        
        # Compare recent volume to average
        recent_avg = np.mean(volumes_array[-5:])
        overall_avg = np.mean(volumes_array)
        
        if overall_avg == 0:
            return 0.0
        
        volume_ratio = (recent_avg - overall_avg) / overall_avg
        volume_trend = np.tanh(volume_ratio)
        
        return float(volume_trend)
    
    def _classify_regime(
        self,
        trend_strength: float,
        volatility: float,
        volume_trend: float,
        rsi: float,
        macd_signal: float
    ) -> Tuple[MarketRegime, float]:
        """Classify market regime from metrics"""
        # High volatility -> volatile regime
        if volatility > 0.7:
            confidence = volatility
            return MarketRegime.VOLATILE, confidence
        
        # Strong uptrend with low volatility -> bull market
        if trend_strength > 0.6 and volatility < 0.4:
            confidence = abs(trend_strength) * (1 - volatility)
            return MarketRegime.BULL, confidence
        
        # Strong downtrend with low volatility -> bear market
        if trend_strength < -0.6 and volatility < 0.4:
            confidence = abs(trend_strength) * (1 - volatility)
            return MarketRegime.BEAR, confidence
        
        # Moderate trend -> trending regime
        if abs(trend_strength) > 0.3:
            confidence = abs(trend_strength)
            return MarketRegime.TRENDING, confidence
        
        # Low volatility, neutral trend -> consolidation
        if volatility < 0.3 and abs(trend_strength) < 0.2:
            confidence = (1 - volatility) * (1 - abs(trend_strength))
            return MarketRegime.CONSOLIDATION, confidence
        
        # Default: sideways
        confidence = 0.5
        return MarketRegime.SIDEWAYS, confidence
    
    def get_regime_aware_strategy(
        self,
        regime: MarketRegime,
        base_strategy: str
    ) -> Dict[str, Any]:
        """Get regime-aware strategy recommendations"""
        strategy_mappings = {
            MarketRegime.BULL: {
                'strategy_type': 'trend_following',
                'risk_level': 'medium',
                'position_sizing': 'aggressive',
                'stop_loss_pct': 2.0,
                'take_profit_pct': 10.0,
                'recommended_indicators': ['MA', 'MACD', 'RSI']
            },
            MarketRegime.BEAR: {
                'strategy_type': 'defensive',
                'risk_level': 'low',
                'position_sizing': 'conservative',
                'stop_loss_pct': 1.0,
                'take_profit_pct': 3.0,
                'recommended_indicators': ['RSI', 'Bollinger Bands']
            },
            MarketRegime.SIDEWAYS: {
                'strategy_type': 'mean_reversion',
                'risk_level': 'medium',
                'position_sizing': 'moderate',
                'stop_loss_pct': 1.5,
                'take_profit_pct': 5.0,
                'recommended_indicators': ['RSI', 'Bollinger Bands', 'Stochastic']
            },
            MarketRegime.VOLATILE: {
                'strategy_type': 'scalping',
                'risk_level': 'high',
                'position_sizing': 'small',
                'stop_loss_pct': 0.5,
                'take_profit_pct': 1.0,
                'recommended_indicators': ['ATR', 'VWAP']
            },
            MarketRegime.TRENDING: {
                'strategy_type': 'trend_following',
                'risk_level': 'medium',
                'position_sizing': 'moderate',
                'stop_loss_pct': 2.0,
                'take_profit_pct': 8.0,
                'recommended_indicators': ['MA', 'MACD', 'ADX']
            },
            MarketRegime.CONSOLIDATION: {
                'strategy_type': 'range_trading',
                'risk_level': 'low',
                'position_sizing': 'moderate',
                'stop_loss_pct': 1.0,
                'take_profit_pct': 3.0,
                'recommended_indicators': ['RSI', 'Support/Resistance']
            }
        }
        
        return strategy_mappings.get(regime, {
            'strategy_type': base_strategy,
            'risk_level': 'medium',
            'position_sizing': 'moderate',
            'stop_loss_pct': 2.0,
            'take_profit_pct': 5.0,
            'recommended_indicators': []
        })


# Global service instance
market_regime_service = MarketRegimeService()
