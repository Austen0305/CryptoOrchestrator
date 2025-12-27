"""
Smart Bot Engine - Advanced AI-Powered Trading Intelligence
Provides sophisticated market analysis, risk management, and adaptive strategies.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MarketSignal:
    """Structured market signal with confidence and reasoning"""

    action: str  # 'buy', 'sell', 'hold'
    confidence: float  # 0.0 to 1.0
    strength: float  # Signal strength
    reasoning: List[str]  # Human-readable reasons
    risk_score: float  # 0.0 (low) to 1.0 (high)
    timestamp: datetime


@dataclass
class RiskMetrics:
    """Comprehensive risk assessment"""

    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    var_95: float  # Value at Risk 95%
    correlation_score: float
    liquidity_score: float


@dataclass
class PatternRecognition:
    """Detected chart patterns"""

    pattern_type: str  # 'head_shoulders', 'double_top', 'triangle', etc.
    confidence: float
    target_price: Optional[float]
    invalidation_price: Optional[float]
    timeframe: str


class SmartBotEngine:
    """
    Advanced trading bot engine with:
    - Multi-indicator technical analysis
    - Chart pattern recognition (Head & Shoulders, Triangles, Flags)
    - Market microstructure analysis (Order flow, Volume Profile)
    - Sentiment analysis integration
    - Adaptive risk management
    - Market regime detection
    - Portfolio optimization
    - Correlation analysis
    """

    def __init__(self):
        self.market_regimes = ["bull", "bear", "sideways", "volatile"]
        self.confidence_threshold = 0.65
        self.max_risk_per_trade = 0.02  # 2% max risk

        # Pattern recognition parameters
        self.pattern_lookback = 50  # Candles to analyze for patterns
        self.pattern_confidence_boost = 0.15  # Boost confidence when pattern detected

    async def analyze_market(self, market_data: Dict[str, Any]) -> MarketSignal:
        """
        Comprehensive market analysis combining multiple signals with advanced intelligence

        Args:
            market_data: Dict with keys: 'symbol', 'candles', 'volume', 'orderbook'

        Returns:
            MarketSignal with action, confidence, and reasoning
        """
        try:
            candles = market_data.get("candles", [])
            orderbook = market_data.get("orderbook", {"bids": [], "asks": []})

            if not candles or len(candles) < 50:
                return MarketSignal(
                    action="hold",
                    confidence=0.0,
                    strength=0.0,
                    reasoning=["Insufficient data for analysis"],
                    risk_score=1.0,
                    timestamp=datetime.now(),
                )

            # Extract price data
            closes = np.array([c.get("close", 0) for c in candles])
            highs = np.array([c.get("high", 0) for c in candles])
            lows = np.array([c.get("low", 0) for c in candles])
            volumes = np.array([c.get("volume", 0) for c in candles])

            # ===== TRADITIONAL TECHNICAL ANALYSIS =====
            trend_signal = self._analyze_trend(closes)
            momentum_signal = self._analyze_momentum(closes, volumes)
            volatility_signal = self._analyze_volatility(closes, highs, lows)
            volume_signal = self._analyze_volume(volumes)
            support_resistance = self._find_support_resistance(closes, highs, lows)

            # ===== ADVANCED INTELLIGENCE FEATURES =====

            # Chart pattern recognition
            patterns = self._detect_chart_patterns(candles)
            pattern_signal = self._evaluate_patterns(patterns, closes[-1])

            # Order flow and market microstructure
            order_flow = self._analyze_order_flow(candles, orderbook)

            # Volume profile analysis
            volume_profile = self._calculate_volume_profile(candles)

            # ML-based prediction
            ml_prediction = self._predict_next_move_ml(candles)

            # Combine all signals with weighted scoring
            signals = {
                "trend": trend_signal,
                "momentum": momentum_signal,
                "volatility": volatility_signal,
                "volume": volume_signal,
                "support_resistance": support_resistance,
                "patterns": pattern_signal,
                "order_flow": order_flow,
                "volume_profile": volume_profile,
                "ml_prediction": ml_prediction,
            }

            # Enhanced signal synthesis with all features
            action, confidence, strength, reasoning = self._synthesize_signals_enhanced(
                signals, closes[-1]
            )

            # Advanced risk assessment
            risk_score = self._calculate_risk_score_enhanced(
                closes, volumes, volatility_signal, order_flow
            )

            return MarketSignal(
                action=action,
                confidence=confidence,
                strength=strength,
                reasoning=reasoning,
                risk_score=risk_score,
                timestamp=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Error in market analysis: {e}", exc_info=True)
            return MarketSignal(
                action="hold",
                confidence=0.0,
                strength=0.0,
                reasoning=[f"Analysis error: {str(e)}"],
                risk_score=1.0,
                timestamp=datetime.now(),
            )

    def _analyze_trend(self, closes: np.ndarray) -> Dict[str, Any]:
        """Multi-timeframe trend analysis with EMA crossovers"""
        ema_short = self._ema(closes, 9)
        ema_medium = self._ema(closes, 21)
        ema_long = self._ema(closes, 50)

        # Trend direction
        if ema_short[-1] > ema_medium[-1] > ema_long[-1]:
            trend = "strong_bullish"
            score = 1.0
        elif ema_short[-1] > ema_medium[-1]:
            trend = "bullish"
            score = 0.7
        elif ema_short[-1] < ema_medium[-1] < ema_long[-1]:
            trend = "strong_bearish"
            score = -1.0
        elif ema_short[-1] < ema_medium[-1]:
            trend = "bearish"
            score = -0.7
        else:
            trend = "neutral"
            score = 0.0

        # Trend strength (ADX-like calculation)
        price_changes = np.diff(closes)
        avg_change = np.mean(np.abs(price_changes[-14:]))
        trend_strength = min(avg_change / closes[-1] * 100, 1.0)

        return {
            "trend": trend,
            "score": score,
            "strength": trend_strength,
            "ema_short": ema_short[-1],
            "ema_medium": ema_medium[-1],
            "ema_long": ema_long[-1],
        }

    def _analyze_momentum(
        self, closes: np.ndarray, volumes: np.ndarray
    ) -> Dict[str, Any]:
        """RSI, MACD, and Stochastic momentum indicators"""
        # RSI
        rsi = self._rsi(closes, period=14)
        rsi_signal = "overbought" if rsi > 70 else "oversold" if rsi < 30 else "neutral"

        # MACD
        macd_line, signal_line, histogram = self._macd(closes)
        macd_signal = "bullish" if histogram[-1] > 0 else "bearish"
        macd_crossover = self._detect_crossover(macd_line, signal_line)

        # Stochastic
        stoch_k, stoch_d = self._stochastic(closes)
        stoch_signal = (
            "overbought" if stoch_k > 80 else "oversold" if stoch_k < 20 else "neutral"
        )

        # Volume-weighted momentum
        price_vol_correlation = np.corrcoef(np.diff(closes[-20:]), volumes[-20:-1])[
            0, 1
        ]

        momentum_score = 0.0
        if rsi < 30 and stoch_k < 20:
            momentum_score = 1.0  # Strong buy signal
        elif rsi > 70 and stoch_k > 80:
            momentum_score = -1.0  # Strong sell signal
        elif macd_crossover == "bullish":
            momentum_score = 0.7
        elif macd_crossover == "bearish":
            momentum_score = -0.7

        return {
            "rsi": rsi,
            "rsi_signal": rsi_signal,
            "macd_signal": macd_signal,
            "macd_crossover": macd_crossover,
            "stoch_signal": stoch_signal,
            "momentum_score": momentum_score,
            "price_volume_correlation": price_vol_correlation,
        }

    def _analyze_volatility(
        self, closes: np.ndarray, highs: np.ndarray, lows: np.ndarray
    ) -> Dict[str, Any]:
        """Bollinger Bands, ATR, and volatility metrics"""
        # Bollinger Bands
        sma = np.mean(closes[-20:])
        std = np.std(closes[-20:])
        upper_band = sma + (2 * std)
        lower_band = sma - (2 * std)
        bb_position = (closes[-1] - lower_band) / (upper_band - lower_band)

        # ATR (Average True Range)
        atr = self._atr(highs, lows, closes, period=14)
        atr_percent = (atr / closes[-1]) * 100

        # Volatility state
        if bb_position > 0.9:
            volatility_state = "high_resistance"
        elif bb_position < 0.1:
            volatility_state = "low_support"
        else:
            volatility_state = "normal"

        return {
            "bb_position": bb_position,
            "upper_band": upper_band,
            "lower_band": lower_band,
            "atr": atr,
            "atr_percent": atr_percent,
            "volatility_state": volatility_state,
        }

    def _analyze_volume(self, volumes: np.ndarray) -> Dict[str, Any]:
        """Volume analysis with OBV and volume trend"""
        # On-Balance Volume (OBV)
        obv = np.cumsum(volumes)
        obv_sma = np.mean(obv[-20:])
        obv_trend = "increasing" if obv[-1] > obv_sma else "decreasing"

        # Volume spike detection
        avg_volume = np.mean(volumes[-20:])
        current_volume = volumes[-1]
        volume_spike = current_volume > (avg_volume * 1.5)

        volume_score = 1.0 if (obv_trend == "increasing" and volume_spike) else 0.5

        return {
            "obv_trend": obv_trend,
            "volume_spike": volume_spike,
            "volume_score": volume_score,
            "relative_volume": current_volume / avg_volume if avg_volume > 0 else 1.0,
        }

    def _find_support_resistance(
        self, closes: np.ndarray, highs: np.ndarray, lows: np.ndarray
    ) -> Dict[str, Any]:
        """Identify key support and resistance levels"""
        # Find local maxima and minima
        window = 5
        resistances = []
        supports = []

        for i in range(window, len(highs) - window):
            if highs[i] == max(highs[i - window : i + window + 1]):
                resistances.append(highs[i])
            if lows[i] == min(lows[i - window : i + window + 1]):
                supports.append(lows[i])

        current_price = closes[-1]
        nearest_resistance = (
            min(resistances, key=lambda x: abs(x - current_price))
            if resistances
            else current_price * 1.05
        )
        nearest_support = (
            min(supports, key=lambda x: abs(x - current_price))
            if supports
            else current_price * 0.95
        )

        # Distance to key levels
        resistance_distance = (nearest_resistance - current_price) / current_price
        support_distance = (current_price - nearest_support) / current_price

        return {
            "nearest_resistance": nearest_resistance,
            "nearest_support": nearest_support,
            "resistance_distance": resistance_distance,
            "support_distance": support_distance,
            "position": (
                "near_resistance"
                if resistance_distance < 0.02
                else "near_support" if support_distance < 0.02 else "mid_range"
            ),
        }

    def _synthesize_signals(
        self, signals: Dict[str, Any], current_price: float
    ) -> Tuple[str, float, float, List[str]]:
        """Combine all signals into final trading decision"""
        reasoning = []
        buy_score = 0.0
        sell_score = 0.0

        # Trend analysis
        trend = signals["trend"]
        if trend["score"] > 0.5:
            buy_score += trend["score"] * 0.3
            reasoning.append(f"Bullish trend detected (EMA alignment)")
        elif trend["score"] < -0.5:
            sell_score += abs(trend["score"]) * 0.3
            reasoning.append(f"Bearish trend detected (EMA divergence)")

        # Momentum
        momentum = signals["momentum"]
        if momentum["rsi"] < 30 and momentum["stoch_signal"] == "oversold":
            buy_score += 0.4
            reasoning.append(f"Oversold conditions (RSI: {momentum['rsi']:.1f})")
        elif momentum["rsi"] > 70 and momentum["stoch_signal"] == "overbought":
            sell_score += 0.4
            reasoning.append(f"Overbought conditions (RSI: {momentum['rsi']:.1f})")

        if momentum["macd_crossover"] == "bullish":
            buy_score += 0.2
            reasoning.append("MACD bullish crossover")
        elif momentum["macd_crossover"] == "bearish":
            sell_score += 0.2
            reasoning.append("MACD bearish crossover")

        # Volatility
        volatility = signals["volatility"]
        if (
            volatility["volatility_state"] == "low_support"
            and volatility["bb_position"] < 0.2
        ):
            buy_score += 0.3
            reasoning.append("Price near lower Bollinger Band (potential bounce)")
        elif (
            volatility["volatility_state"] == "high_resistance"
            and volatility["bb_position"] > 0.8
        ):
            sell_score += 0.3
            reasoning.append("Price near upper Bollinger Band (potential reversal)")

        # Volume confirmation
        volume = signals["volume"]
        if volume["volume_spike"] and volume["obv_trend"] == "increasing":
            buy_score *= 1.2  # Amplify buy signals with volume
            reasoning.append("Strong volume confirmation")

        # Support/Resistance
        sr = signals["support_resistance"]
        if sr["position"] == "near_support":
            buy_score += 0.2
            reasoning.append(f"Near support level (${sr['nearest_support']:.2f})")
        elif sr["position"] == "near_resistance":
            sell_score += 0.2
            reasoning.append(f"Near resistance level (${sr['nearest_resistance']:.2f})")

        # Determine action
        net_score = buy_score - sell_score
        if net_score > 0.5:
            action = "buy"
            confidence = min(buy_score / 1.5, 1.0)
            strength = buy_score
        elif net_score < -0.5:
            action = "sell"
            confidence = min(sell_score / 1.5, 1.0)
            strength = sell_score
        else:
            action = "hold"
            confidence = 0.5
            strength = abs(net_score)
            reasoning.append("Mixed signals - awaiting clearer trend")

        return action, confidence, strength, reasoning

    def _evaluate_patterns(
        self, patterns: List[PatternRecognition], current_price: float
    ) -> Dict[str, Any]:
        """Evaluate detected chart patterns and return signal"""
        if not patterns:
            return {
                "pattern_signal": "neutral",
                "pattern_confidence": 0,
                "patterns_detected": [],
            }

        # Take the most confident pattern
        best_pattern = max(patterns, key=lambda p: p.confidence)

        # Determine signal direction
        bullish_patterns = ["double_bottom", "ascending_triangle", "bull_flag"]
        bearish_patterns = [
            "head_and_shoulders",
            "double_top",
            "descending_triangle",
            "bear_flag",
        ]

        if best_pattern.pattern_type in bullish_patterns:
            signal = "bullish"
        elif best_pattern.pattern_type in bearish_patterns:
            signal = "bearish"
        else:
            signal = "neutral"

        return {
            "pattern_signal": signal,
            "pattern_confidence": best_pattern.confidence,
            "patterns_detected": [p.pattern_type for p in patterns],
            "best_pattern": best_pattern.pattern_type,
            "target_price": best_pattern.target_price,
        }

    def _synthesize_signals_enhanced(
        self, signals: Dict[str, Any], current_price: float
    ) -> Tuple[str, float, float, List[str]]:
        """
        Enhanced signal synthesis incorporating advanced features
        """
        buy_score = 0.0
        sell_score = 0.0
        reasoning = []

        # ===== TRADITIONAL SIGNALS (70% weight) =====

        # Trend (25%)
        trend = signals["trend"]
        if trend["trend_direction"] == "bullish" and trend["trend_strength"] > 0.6:
            buy_score += 0.25 * trend["trend_strength"]
            reasoning.append(
                f"Strong bullish trend (strength: {trend['trend_strength']:.2f})"
            )
        elif trend["trend_direction"] == "bearish" and trend["trend_strength"] > 0.6:
            sell_score += 0.25 * trend["trend_strength"]
            reasoning.append(
                f"Strong bearish trend (strength: {trend['trend_strength']:.2f})"
            )

        # Momentum (25%)
        momentum = signals["momentum"]
        if momentum["momentum_score"] > 0.5:
            buy_score += 0.25
            reasoning.append(f"Positive momentum (RSI: {momentum['rsi']:.1f})")
        elif momentum["momentum_score"] < -0.5:
            sell_score += 0.25
            reasoning.append(f"Negative momentum (RSI: {momentum['rsi']:.1f})")

        # Volatility (10%)
        volatility = signals["volatility"]
        if volatility["bb_position"] < 0.2:
            buy_score += 0.1
            reasoning.append("Price at lower Bollinger Band")
        elif volatility["bb_position"] > 0.8:
            sell_score += 0.1
            reasoning.append("Price at upper Bollinger Band")

        # Volume (10%)
        volume = signals["volume"]
        if volume["volume_spike"] and volume["obv_trend"] == "increasing":
            buy_score *= 1.15
            reasoning.append("Volume surge confirms momentum")

        # ===== ADVANCED SIGNALS (30% weight) =====

        # Chart Patterns (15%)
        patterns = signals["patterns"]
        if patterns["pattern_signal"] == "bullish":
            buy_score += 0.15 * patterns["pattern_confidence"]
            reasoning.append(f"Bullish pattern: {patterns['best_pattern']} detected")
        elif patterns["pattern_signal"] == "bearish":
            sell_score += 0.15 * patterns["pattern_confidence"]
            reasoning.append(f"Bearish pattern: {patterns['best_pattern']} detected")

        # Order Flow (10%)
        order_flow = signals["order_flow"]
        if order_flow["order_flow_signal"] == "bullish":
            buy_score += 0.1
            reasoning.append(
                f"Bullish order flow (buy pressure: {order_flow['buy_pressure']:.2%})"
            )
        elif order_flow["order_flow_signal"] == "bearish":
            sell_score += 0.1
            reasoning.append(
                f"Bearish order flow (buy pressure: {order_flow['buy_pressure']:.2%})"
            )

        # Volume Profile (5%)
        vp = signals["volume_profile"]
        if vp["poc"] and vp["current_price_position"]:
            if (
                vp["current_price_position"] == "below_value"
                and current_price < vp["poc"]
            ):
                buy_score += 0.05
                reasoning.append(
                    f"Price below POC (${vp['poc']:.2f}) - potential reversion"
                )
            elif (
                vp["current_price_position"] == "above_value"
                and current_price > vp["poc"]
            ):
                sell_score += 0.05
                reasoning.append(
                    f"Price above POC (${vp['poc']:.2f}) - potential reversion"
                )

        # ML Prediction (bonus)
        ml_pred = signals["ml_prediction"]
        if ml_pred["prediction"] == "bullish" and ml_pred["confidence"] > 0.6:
            buy_score *= 1.1
            reasoning.append(
                f"ML prediction: {ml_pred['prediction']} ({ml_pred['confidence']:.2%})"
            )
        elif ml_pred["prediction"] == "bearish" and ml_pred["confidence"] > 0.6:
            sell_score *= 1.1
            reasoning.append(
                f"ML prediction: {ml_pred['prediction']} ({ml_pred['confidence']:.2%})"
            )

        # Determine action
        net_score = buy_score - sell_score
        if net_score > 0.6:
            action = "buy"
            confidence = min(buy_score / 1.2, 1.0)
            strength = buy_score
        elif net_score < -0.6:
            action = "sell"
            confidence = min(sell_score / 1.2, 1.0)
            strength = sell_score
        else:
            action = "hold"
            confidence = 0.5
            strength = abs(net_score)
            if not reasoning:
                reasoning.append("Mixed signals - awaiting clearer confirmation")

        return action, confidence, strength, reasoning

    def _calculate_risk_score_enhanced(
        self,
        closes: np.ndarray,
        volumes: np.ndarray,
        volatility_signal: Dict[str, Any],
        order_flow: Dict[str, Any],
    ) -> float:
        """Enhanced risk score incorporating market microstructure"""
        # Base volatility risk
        returns = np.diff(closes) / closes[:-1]
        volatility = np.std(returns) * np.sqrt(252)
        volatility_risk = min(volatility / 0.5, 1.0)

        # Liquidity risk from order flow
        liquidity_risk = 1.0 - order_flow.get("liquidity_score", 0.5)

        # Drawdown risk
        cumulative_returns = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = abs(np.min(drawdown))
        drawdown_risk = min(max_drawdown / 0.2, 1.0)

        # Volatility state risk multiplier
        if volatility_signal["volatility_state"] == "extreme":
            volatility_multiplier = 1.5
        elif volatility_signal["volatility_state"] == "high":
            volatility_multiplier = 1.2
        else:
            volatility_multiplier = 1.0

        # Combined risk with weights
        combined_risk = (
            volatility_risk * 0.4 * volatility_multiplier
            + liquidity_risk * 0.3
            + drawdown_risk * 0.3
        )

        return min(combined_risk, 1.0)

    def _calculate_risk_score(self, closes: np.ndarray, volumes: np.ndarray) -> float:
        """Calculate comprehensive risk score"""
        # Volatility risk
        returns = np.diff(closes) / closes[:-1]
        volatility = np.std(returns) * np.sqrt(252)  # Annualized
        volatility_risk = min(volatility / 0.5, 1.0)  # Normalize to 50% annual vol

        # Liquidity risk
        avg_volume = np.mean(volumes)
        liquidity_risk = 1.0 if avg_volume < 1000 else 0.3

        # Drawdown risk
        cummax = np.maximum.accumulate(closes)
        drawdown = (cummax - closes) / cummax
        max_drawdown = np.max(drawdown)
        drawdown_risk = min(max_drawdown / 0.2, 1.0)

        # Combined risk score
        risk_score = volatility_risk * 0.4 + liquidity_risk * 0.3 + drawdown_risk * 0.3
        return risk_score

    # Technical indicator helpers
    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Exponential Moving Average"""
        alpha = 2 / (period + 1)
        ema = np.zeros_like(data)
        ema[0] = data[0]
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i - 1]
        return ema

    def _rsi(self, closes: np.ndarray, period: int = 14) -> float:
        """Relative Strength Index"""
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _macd(self, closes: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """MACD indicator"""
        ema_12 = self._ema(closes, 12)
        ema_26 = self._ema(closes, 26)
        macd_line = ema_12 - ema_26
        signal_line = self._ema(macd_line, 9)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    def _stochastic(self, closes: np.ndarray, period: int = 14) -> Tuple[float, float]:
        """Stochastic Oscillator"""
        recent = closes[-period:]
        low = np.min(recent)
        high = np.max(recent)
        current = closes[-1]

        if high == low:
            k = 50.0
        else:
            k = 100 * (current - low) / (high - low)

        # Simplified %D (3-period SMA of %K)
        d = k  # In practice, would smooth over multiple %K values
        return k, d

    def _atr(
        self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14
    ) -> float:
        """Average True Range"""
        tr = np.maximum(
            highs[1:] - lows[1:],
            np.maximum(np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1])),
        )
        atr = np.mean(tr[-period:])
        return atr

    def _detect_crossover(self, line1: np.ndarray, line2: np.ndarray) -> str:
        """Detect bullish or bearish crossover"""
        if len(line1) < 2 or len(line2) < 2:
            return "none"

        if line1[-2] <= line2[-2] and line1[-1] > line2[-1]:
            return "bullish"
        elif line1[-2] >= line2[-2] and line1[-1] < line2[-1]:
            return "bearish"
        return "none"

    async def calculate_position_size(
        self,
        account_balance: float,
        risk_per_trade: float,
        entry_price: float,
        stop_loss_price: float,
    ) -> Dict[str, Any]:
        """Calculate optimal position size based on risk management"""
        risk_amount = account_balance * risk_per_trade
        price_risk = abs(entry_price - stop_loss_price)

        if price_risk == 0:
            return {
                "position_size": 0,
                "risk_amount": 0,
                "reasoning": "Invalid stop loss price",
            }

        position_size = risk_amount / price_risk
        max_position = account_balance * 0.1  # Never more than 10% of account

        if position_size * entry_price > max_position:
            position_size = max_position / entry_price

        return {
            "position_size": position_size,
            "position_value": position_size * entry_price,
            "risk_amount": risk_amount,
            "risk_reward_ratio": price_risk / risk_amount if risk_amount > 0 else 0,
            "percentage_of_account": (position_size * entry_price / account_balance)
            * 100,
        }

    async def get_adaptive_parameters(self, market_condition: str) -> Dict[str, Any]:
        """Adjust bot parameters based on market regime"""
        if market_condition == "bull":
            return {
                "position_size_multiplier": 1.2,
                "stop_loss_distance": 0.02,
                "take_profit_distance": 0.06,
                "confidence_threshold": 0.6,
            }
        elif market_condition == "bear":
            return {
                "position_size_multiplier": 0.8,
                "stop_loss_distance": 0.015,
                "take_profit_distance": 0.04,
                "confidence_threshold": 0.75,
            }
        elif market_condition == "volatile":
            return {
                "position_size_multiplier": 0.5,
                "stop_loss_distance": 0.03,
                "take_profit_distance": 0.08,
                "confidence_threshold": 0.8,
            }
        else:  # sideways
            return {
                "position_size_multiplier": 1.0,
                "stop_loss_distance": 0.02,
                "take_profit_distance": 0.05,
                "confidence_threshold": 0.7,
            }

    # ============= ADVANCED INTELLIGENCE FEATURES =============

    def _detect_chart_patterns(
        self, candles: List[Dict[str, Any]]
    ) -> List[PatternRecognition]:
        """
        Detect chart patterns using advanced pattern recognition
        Returns list of detected patterns with confidence scores
        """
        patterns = []

        if len(candles) < self.pattern_lookback:
            return patterns

        highs = np.array([c["high"] for c in candles[-self.pattern_lookback :]])
        lows = np.array([c["low"] for c in candles[-self.pattern_lookback :]])
        closes = np.array([c["close"] for c in candles[-self.pattern_lookback :]])

        # Head and Shoulders detection
        hs_pattern = self._detect_head_and_shoulders(highs, lows, closes)
        if hs_pattern:
            patterns.append(hs_pattern)

        # Double Top/Bottom detection
        double_pattern = self._detect_double_top_bottom(highs, lows, closes)
        if double_pattern:
            patterns.append(double_pattern)

        # Triangle patterns (ascending, descending, symmetrical)
        triangle_pattern = self._detect_triangle(highs, lows)
        if triangle_pattern:
            patterns.append(triangle_pattern)

        # Flag and Pennant patterns
        flag_pattern = self._detect_flag_pennant(highs, lows, closes)
        if flag_pattern:
            patterns.append(flag_pattern)

        return patterns

    def _detect_head_and_shoulders(
        self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray
    ) -> Optional[PatternRecognition]:
        """Detect Head and Shoulders pattern (bearish reversal)"""
        try:
            # Find peaks using local maxima
            from scipy.signal import find_peaks

            peaks, _ = find_peaks(highs, distance=5, prominence=np.std(highs) * 0.5)

            if len(peaks) >= 3:
                # Check if middle peak is highest (head)
                last_three_peaks = peaks[-3:]
                peak_heights = highs[last_three_peaks]

                if (
                    peak_heights[1] > peak_heights[0]
                    and peak_heights[1] > peak_heights[2]
                ):
                    # Check symmetry of shoulders
                    left_shoulder = peak_heights[0]
                    head = peak_heights[1]
                    right_shoulder = peak_heights[2]

                    shoulder_diff = abs(left_shoulder - right_shoulder) / head

                    if shoulder_diff < 0.05:  # Shoulders within 5% of each other
                        # Calculate neckline and target
                        neckline = np.min(
                            lows[last_three_peaks[0] : last_three_peaks[2]]
                        )
                        head_height = head - neckline
                        target = neckline - head_height

                        confidence = 0.8 - (
                            shoulder_diff * 2
                        )  # Reduce confidence if shoulders uneven

                        return PatternRecognition(
                            pattern_type="head_and_shoulders",
                            confidence=confidence,
                            target_price=target,
                            invalidation_price=head * 1.02,
                            timeframe=f"{len(highs)}m",
                        )
        except ImportError:
            # Fallback if scipy not available - simple peak detection
            window = 5
            for i in range(window, len(highs) - window):
                if highs[i] == np.max(highs[i - window : i + window + 1]):
                    # Simple head detection logic
                    pass
        except Exception as e:
            logger.debug(f"Head and shoulders detection error: {e}")

        return None

    def _detect_double_top_bottom(
        self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray
    ) -> Optional[PatternRecognition]:
        """Detect Double Top (bearish) or Double Bottom (bullish) patterns"""
        try:
            # Double Top detection
            recent_highs = highs[-20:]
            max_indices = np.argsort(recent_highs)[-2:]  # Two highest points

            if len(max_indices) == 2:
                high1, high2 = (
                    recent_highs[max_indices[0]],
                    recent_highs[max_indices[1]],
                )
                price_diff = abs(high1 - high2) / high1

                if price_diff < 0.02:  # Tops within 2% of each other
                    neckline = np.min(lows[max_indices[0] : max_indices[1]])
                    target = neckline - (high1 - neckline)

                    return PatternRecognition(
                        pattern_type="double_top",
                        confidence=0.75,
                        target_price=target,
                        invalidation_price=high1 * 1.03,
                        timeframe=f"{len(closes)}m",
                    )

            # Double Bottom detection
            recent_lows = lows[-20:]
            min_indices = np.argsort(recent_lows)[:2]  # Two lowest points

            if len(min_indices) == 2:
                low1, low2 = recent_lows[min_indices[0]], recent_lows[min_indices[1]]
                price_diff = abs(low1 - low2) / low1

                if price_diff < 0.02:  # Bottoms within 2% of each other
                    neckline = np.max(highs[min_indices[0] : min_indices[1]])
                    target = neckline + (neckline - low1)

                    return PatternRecognition(
                        pattern_type="double_bottom",
                        confidence=0.75,
                        target_price=target,
                        invalidation_price=low1 * 0.97,
                        timeframe=f"{len(closes)}m",
                    )
        except Exception as e:
            logger.debug(f"Double top/bottom detection error: {e}")

        return None

    def _detect_triangle(
        self, highs: np.ndarray, lows: np.ndarray
    ) -> Optional[PatternRecognition]:
        """Detect triangle patterns (ascending, descending, symmetrical)"""
        try:
            if len(highs) < 20:
                return None

            # Calculate trendlines using linear regression
            x = np.arange(len(highs[-20:]))

            # Upper trendline
            high_slope = np.polyfit(x, highs[-20:], 1)[0]

            # Lower trendline
            low_slope = np.polyfit(x, lows[-20:], 1)[0]

            # Ascending triangle: flat top, rising bottom
            if abs(high_slope) < 0.001 and low_slope > 0.002:
                return PatternRecognition(
                    pattern_type="ascending_triangle",
                    confidence=0.70,
                    target_price=highs[-1] * 1.05,  # Bullish breakout target
                    invalidation_price=lows[-1] * 0.97,
                    timeframe=f"{len(highs)}m",
                )

            # Descending triangle: flat bottom, falling top
            elif abs(low_slope) < 0.001 and high_slope < -0.002:
                return PatternRecognition(
                    pattern_type="descending_triangle",
                    confidence=0.70,
                    target_price=lows[-1] * 0.95,  # Bearish breakdown target
                    invalidation_price=highs[-1] * 1.03,
                    timeframe=f"{len(highs)}m",
                )

            # Symmetrical triangle: converging trendlines
            elif high_slope < -0.001 and low_slope > 0.001:
                return PatternRecognition(
                    pattern_type="symmetrical_triangle",
                    confidence=0.65,
                    target_price=None,  # Direction uncertain until breakout
                    invalidation_price=None,
                    timeframe=f"{len(highs)}m",
                )
        except Exception as e:
            logger.debug(f"Triangle detection error: {e}")

        return None

    def _detect_flag_pennant(
        self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray
    ) -> Optional[PatternRecognition]:
        """Detect Flag and Pennant continuation patterns"""
        try:
            if len(closes) < 30:
                return None

            # Look for strong initial move (pole)
            pole_start = closes[-30]
            pole_end = closes[-15]
            pole_move = (pole_end - pole_start) / pole_start

            # Flag requires 5%+ initial move
            if abs(pole_move) > 0.05:
                # Check for consolidation (flag)
                consolidation = closes[-15:]
                consolidation_range = (
                    np.max(consolidation) - np.min(consolidation)
                ) / np.mean(consolidation)

                # Flag: consolidation range < 3%
                if consolidation_range < 0.03:
                    is_bullish = pole_move > 0

                    return PatternRecognition(
                        pattern_type="bull_flag" if is_bullish else "bear_flag",
                        confidence=0.75,
                        target_price=(
                            closes[-1] * (1 + pole_move)
                            if is_bullish
                            else closes[-1] * (1 - abs(pole_move))
                        ),
                        invalidation_price=(
                            np.min(consolidation) * 0.98
                            if is_bullish
                            else np.max(consolidation) * 1.02
                        ),
                        timeframe=f"{len(closes)}m",
                    )
        except Exception as e:
            logger.debug(f"Flag/pennant detection error: {e}")

        return None

    def _analyze_order_flow(
        self, candles: List[Dict[str, Any]], orderbook: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze order flow and market microstructure
        Returns buying/selling pressure and liquidity metrics
        """
        try:
            # Volume analysis - buying vs selling pressure
            recent_candles = candles[-20:]
            buying_volume = sum(
                [c["volume"] for c in recent_candles if c["close"] > c["open"]]
            )
            selling_volume = sum(
                [c["volume"] for c in recent_candles if c["close"] <= c["open"]]
            )
            total_volume = buying_volume + selling_volume

            buy_pressure = buying_volume / total_volume if total_volume > 0 else 0.5

            # Orderbook imbalance
            bids = orderbook.get("bids", [])
            asks = orderbook.get("asks", [])

            bid_volume = sum([float(bid[1]) for bid in bids[:10]]) if bids else 0
            ask_volume = sum([float(ask[1]) for ask in asks[:10]]) if asks else 0
            total_ob_volume = bid_volume + ask_volume

            bid_ask_ratio = bid_volume / ask_volume if ask_volume > 0 else 1.0

            # Spread analysis
            if bids and asks:
                best_bid = float(bids[0][0])
                best_ask = float(asks[0][0])
                spread = (best_ask - best_bid) / best_bid
            else:
                spread = 0.001  # Default 0.1%

            # Liquidity score (lower spread = better liquidity)
            liquidity_score = 1.0 - min(spread * 100, 1.0)  # Scale to 0-1

            return {
                "buy_pressure": buy_pressure,
                "bid_ask_ratio": bid_ask_ratio,
                "spread_pct": spread * 100,
                "liquidity_score": liquidity_score,
                "order_flow_signal": (
                    "bullish"
                    if buy_pressure > 0.6 and bid_ask_ratio > 1.2
                    else (
                        "bearish"
                        if buy_pressure < 0.4 and bid_ask_ratio < 0.8
                        else "neutral"
                    )
                ),
            }
        except Exception as e:
            logger.error(f"Order flow analysis error: {e}")
            return {
                "buy_pressure": 0.5,
                "bid_ask_ratio": 1.0,
                "spread_pct": 0.1,
                "liquidity_score": 0.5,
                "order_flow_signal": "neutral",
            }

    def _calculate_volume_profile(
        self, candles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate volume profile to identify high-volume price levels
        Returns point of control (POC) and value area
        """
        try:
            if len(candles) < 50:
                return {"poc": None, "value_area_high": None, "value_area_low": None}

            # Create price-volume histogram
            recent = candles[-50:]
            prices = []
            volumes = []

            for candle in recent:
                # Approximate OHLC distribution
                mid_price = (candle["high"] + candle["low"]) / 2
                prices.append(mid_price)
                volumes.append(candle["volume"])

            # Bin prices and sum volumes
            price_bins = np.linspace(min(prices), max(prices), 20)
            volume_hist, _ = np.histogram(prices, bins=price_bins, weights=volumes)

            # Point of Control (POC) - price level with highest volume
            poc_index = np.argmax(volume_hist)
            poc_price = (price_bins[poc_index] + price_bins[poc_index + 1]) / 2

            # Value Area (70% of volume)
            total_volume = np.sum(volume_hist)
            target_volume = total_volume * 0.7

            # Find value area by expanding from POC
            value_area_indices = {poc_index}
            current_volume = volume_hist[poc_index]

            while current_volume < target_volume and len(value_area_indices) < len(
                volume_hist
            ):
                # Expand to higher or lower volume bar
                candidates = []
                min_idx, max_idx = min(value_area_indices), max(value_area_indices)

                if min_idx > 0:
                    candidates.append((min_idx - 1, volume_hist[min_idx - 1]))
                if max_idx < len(volume_hist) - 1:
                    candidates.append((max_idx + 1, volume_hist[max_idx + 1]))

                if candidates:
                    next_idx = max(candidates, key=lambda x: x[1])[0]
                    value_area_indices.add(next_idx)
                    current_volume += volume_hist[next_idx]
                else:
                    break

            value_area_low = price_bins[min(value_area_indices)]
            value_area_high = price_bins[max(value_area_indices) + 1]

            return {
                "poc": poc_price,
                "value_area_high": value_area_high,
                "value_area_low": value_area_low,
                "current_price_position": (
                    "above_value"
                    if candles[-1]["close"] > value_area_high
                    else (
                        "below_value"
                        if candles[-1]["close"] < value_area_low
                        else "in_value"
                    )
                ),
            }
        except Exception as e:
            logger.error(f"Volume profile calculation error: {e}")
            return {"poc": None, "value_area_high": None, "value_area_low": None}

    def _predict_next_move_ml(self, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Simple ML-based price prediction using recent patterns
        Uses basic time series features and pattern matching
        """
        try:
            if len(candles) < 20:
                return {"prediction": "neutral", "confidence": 0.5}

            closes = np.array([c["close"] for c in candles[-20:]])
            volumes = np.array([c["volume"] for c in candles[-20:]])

            # Feature extraction
            returns = np.diff(closes) / closes[:-1]

            # Recent trend
            recent_return = (closes[-1] - closes[-5]) / closes[-5]

            # Momentum
            momentum = (closes[-1] - closes[-10]) / closes[-10]

            # Volume trend
            volume_ratio = np.mean(volumes[-5:]) / np.mean(volumes[-10:-5])

            # Simple scoring system (can be replaced with actual ML model)
            score = 0
            confidence_factors = []

            if recent_return > 0.02:
                score += 1
                confidence_factors.append("positive_short_trend")
            elif recent_return < -0.02:
                score -= 1
                confidence_factors.append("negative_short_trend")

            if momentum > 0.05:
                score += 1
                confidence_factors.append("positive_momentum")
            elif momentum < -0.05:
                score -= 1
                confidence_factors.append("negative_momentum")

            if volume_ratio > 1.2:
                score += 0.5
                confidence_factors.append("increasing_volume")
            elif volume_ratio < 0.8:
                score -= 0.5
                confidence_factors.append("decreasing_volume")

            # Volatility check
            volatility = np.std(returns)
            if volatility > 0.03:
                confidence_multiplier = 0.8  # Lower confidence in volatile markets
            else:
                confidence_multiplier = 1.0

            # Final prediction
            if score > 1:
                prediction = "bullish"
                confidence = min(0.7 * confidence_multiplier, 1.0)
            elif score < -1:
                prediction = "bearish"
                confidence = min(0.7 * confidence_multiplier, 1.0)
            else:
                prediction = "neutral"
                confidence = 0.5

            return {
                "prediction": prediction,
                "confidence": confidence,
                "factors": confidence_factors,
                "volatility": float(volatility),
            }
        except Exception as e:
            logger.error(f"ML prediction error: {e}")
            return {"prediction": "neutral", "confidence": 0.5}
