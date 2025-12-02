import tensorflow as tf
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class TechnicalIndicators(BaseModel):
    rsi: float
    macd: Dict[str, float]
    bollinger_bands: Dict[str, float]
    ema: Dict[str, float]
    atr: float
    volume_oscillator: float
    stochastic: Dict[str, float]
    adx: float
    obv: float

class MLPrediction(BaseModel):
    action: str  # 'buy', 'sell', 'hold'
    confidence: float
    strength: float
    indicators: TechnicalIndicators
    reasoning: List[str]

class MarketData(BaseModel):
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float

class EnhancedMLEngine:
    def __init__(self):
        self.model: Optional[tf.keras.Model] = None
        self.is_training: bool = False
        self.prediction_history: List[Dict[str, Any]] = []
        self.max_history: int = 1000
        self.lookback_period: int = 50
        self.feature_count: int = 25
        self.initialize_model()

    def initialize_model(self) -> None:
        try:
            self.model = tf.keras.Sequential([
                # Input layer
                tf.keras.layers.Dense(
                    128,
                    activation='relu',
                    kernel_initializer='he_normal',
                    input_shape=(self.lookback_period * self.feature_count,)
                ),
                tf.keras.layers.Dropout(0.3),

                # Hidden layers with batch normalization
                tf.keras.layers.Dense(256, activation='relu', kernel_initializer='he_normal'),
                tf.keras.layers.BatchNormalization(),
                tf.keras.layers.Dropout(0.3),

                tf.keras.layers.Dense(128, activation='relu', kernel_initializer='he_normal'),
                tf.keras.layers.BatchNormalization(),
                tf.keras.layers.Dropout(0.2),

                tf.keras.layers.Dense(64, activation='relu', kernel_initializer='he_normal'),
                tf.keras.layers.Dropout(0.2),

                # Output layer - 3 classes (buy, sell, hold)
                tf.keras.layers.Dense(3, activation='softmax')
            ])

            self.model.compile(
                optimizer=tf.keras.optimizers.Adam(0.001),
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )

            logger.info('Enhanced ML model initialized successfully')
        except Exception as error:
            logger.error(f'Failed to initialize ML model: {error}')
            raise error

    def calculate_technical_indicators(self, data: List[MarketData], index: int) -> TechnicalIndicators:
        rsi = self.calculate_rsi(data, index)
        macd = self.calculate_macd(data, index)
        bollinger_bands = self.calculate_bollinger_bands(data, index)
        ema = self.calculate_ema(data, index)
        atr = self.calculate_atr(data, index)
        volume_oscillator = self.calculate_volume_oscillator(data, index)
        stochastic = self.calculate_stochastic(data, index)
        adx = self.calculate_adx(data, index)
        obv = self.calculate_obv(data, index)

        return TechnicalIndicators(
            rsi=rsi,
            macd=macd,
            bollinger_bands=bollinger_bands,
            ema=ema,
            atr=atr,
            volume_oscillator=volume_oscillator,
            stochastic=stochastic,
            adx=adx,
            obv=obv
        )

    def calculate_rsi(self, data: List[MarketData], index: int, period: int = 14) -> float:
        if index < period:
            return 50.0

        gains = 0.0
        losses = 0.0

        for i in range(index - period + 1, index + 1):
            change = data[i].close - data[i - 1].close
            if change > 0:
                gains += change
            else:
                losses += abs(change)

        avg_gain = gains / period
        avg_loss = losses / period
        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        return 100.0 - 100.0 / (1.0 + rs)

    def calculate_macd(self, data: List[MarketData], index: int,
                       fast_period: int = 12, slow_period: int = 26,
                       signal_period: int = 9) -> Dict[str, float]:
        if index < slow_period:
            return {"value": 0.0, "signal": 0.0, "histogram": 0.0}

        fast_ema = self.calculate_ema_value(data, index, fast_period)
        slow_ema = self.calculate_ema_value(data, index, slow_period)
        macd_value = fast_ema - slow_ema

        # Simplified signal calculation
        signal = macd_value * 0.2
        histogram = macd_value - signal

        return {
            "value": macd_value,
            "signal": signal,
            "histogram": histogram
        }

    def calculate_ema_value(self, data: List[MarketData], index: int, period: int) -> float:
        if index < period:
            return data[index].close

        multiplier = 2.0 / (period + 1)
        ema = data[index - period].close

        for i in range(index - period + 1, index + 1):
            ema = (data[i].close - ema) * multiplier + ema

        return ema

    def calculate_bollinger_bands(self, data: List[MarketData], index: int,
                                  period: int = 20, std_dev: float = 2.0) -> Dict[str, float]:
        if index < period:
            current = data[index].close
            return {"upper": current, "middle": current, "lower": current}

        prices = [d.close for d in data[index - period + 1:index + 1]]
        middle = sum(prices) / period

        variance = sum((p - middle) ** 2 for p in prices) / period
        std = variance ** 0.5

        return {
            "upper": middle + std_dev * std,
            "middle": middle,
            "lower": middle - std_dev * std
        }

    def calculate_ema(self, data: List[MarketData], index: int) -> Dict[str, float]:
        return {
            "fast": self.calculate_ema_value(data, index, 12),
            "slow": self.calculate_ema_value(data, index, 26)
        }

    def calculate_atr(self, data: List[MarketData], index: int, period: int = 14) -> float:
        if index < period:
            return 0.0

        tr_sum = 0.0
        for i in range(index - period + 1, index + 1):
            high = data[i].high
            low = data[i].low
            prev_close = data[i - 1].close if i > 0 else data[i].close

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            tr_sum += tr

        return tr_sum / period

    def calculate_volume_oscillator(self, data: List[MarketData], index: int) -> float:
        if index < 26:
            return 0.0

        short_vol_ema = self.calculate_volume_ema(data, index, 5)
        long_vol_ema = self.calculate_volume_ema(data, index, 10)

        return ((short_vol_ema - long_vol_ema) / long_vol_ema) * 100 if long_vol_ema != 0 else 0.0

    def calculate_volume_ema(self, data: List[MarketData], index: int, period: int) -> float:
        if index < period:
            return data[index].volume

        multiplier = 2.0 / (period + 1)
        ema = data[index - period].volume

        for i in range(index - period + 1, index + 1):
            ema = (data[i].volume - ema) * multiplier + ema

        return ema

    def calculate_stochastic(self, data: List[MarketData], index: int, period: int = 14) -> Dict[str, float]:
        if index < period:
            return {"k": 50.0, "d": 50.0}

        recent_data = data[index - period + 1:index + 1]
        high = max(d.high for d in recent_data)
        low = min(d.low for d in recent_data)
        close = data[index].close

        k = ((close - low) / (high - low)) * 100 if high != low else 50.0
        d = k  # Simplified D calculation

        return {"k": k, "d": d}

    def calculate_adx(self, data: List[MarketData], index: int, period: int = 14) -> float:
        if index < period + 1:
            return 25.0  # Neutral value

        plus_dm = 0.0
        minus_dm = 0.0
        tr = 0.0

        for i in range(index - period + 1, index + 1):
            high_diff = data[i].high - data[i - 1].high
            low_diff = data[i - 1].low - data[i].low

            plus_dm += high_diff if high_diff > low_diff and high_diff > 0 else 0.0
            minus_dm += low_diff if low_diff > high_diff and low_diff > 0 else 0.0

            true_range = max(
                data[i].high - data[i].low,
                abs(data[i].high - data[i - 1].close),
                abs(data[i].low - data[i - 1].close)
            )
            tr += true_range

        plus_di = (plus_dm / tr) * 100 if tr != 0 else 0.0
        minus_di = (minus_dm / tr) * 100 if tr != 0 else 0.0
        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if (plus_di + minus_di) != 0 else 0.0

        return dx

    def calculate_obv(self, data: List[MarketData], index: int) -> float:
        if index == 0:
            return data[0].volume

        obv = 0.0
        for i in range(1, index + 1):
            if data[i].close > data[i - 1].close:
                obv += data[i].volume
            elif data[i].close < data[i - 1].close:
                obv -= data[i].volume

        return obv

    def extract_features(self, data: List[MarketData], index: int) -> List[float]:
        features = []
        indicators = self.calculate_technical_indicators(data, index)

        # Price-based features (normalized)
        current_price = data[index].close
        price_change = (current_price - data[index - 1].close) / data[index - 1].close if index > 0 else 0.0
        features.append(price_change)

        # Volume features
        start_idx = max(0, index - 20)
        avg_volume = sum(d.volume for d in data[start_idx:index + 1]) / (index - start_idx + 1)
        volume_ratio = data[index].volume / avg_volume if avg_volume != 0 else 1.0
        features.append(min(volume_ratio, 5.0))  # Cap at 5x

        # Technical indicators
        features.append(indicators.rsi / 100.0)
        features.append(np.tanh(indicators.macd["value"] / current_price))
        features.append(np.tanh(indicators.macd["histogram"] / current_price))
        bb_range = indicators.bollinger_bands["upper"] - indicators.bollinger_bands["lower"]
        bb_position = (current_price - indicators.bollinger_bands["lower"]) / bb_range if bb_range != 0 else 0.5
        features.append(bb_position)
        features.append(np.tanh((indicators.ema["fast"] - indicators.ema["slow"]) / current_price))
        features.append(min(indicators.atr / current_price, 0.1) * 10)
        features.append(np.tanh(indicators.volume_oscillator / 100.0))
        features.append(indicators.stochastic["k"] / 100.0)
        features.append(indicators.stochastic["d"] / 100.0)
        features.append(indicators.adx / 100.0)
        features.append(np.tanh(indicators.obv / 1000000.0))

        # Price momentum features
        momentum5 = (current_price - data[index - 5].close) / data[index - 5].close if index >= 5 else 0.0
        momentum10 = (current_price - data[index - 10].close) / data[index - 10].close if index >= 10 else 0.0
        momentum20 = (current_price - data[index - 20].close) / data[index - 20].close if index >= 20 else 0.0
        features.append(np.tanh(momentum5 * 10))
        features.append(np.tanh(momentum10 * 5))
        features.append(np.tanh(momentum20 * 2))

        # Volatility features
        start_idx_vol = max(0, index - 20)
        returns = []
        for i in range(start_idx_vol + 1, index + 1):
            ret = (data[i].close - data[i - 1].close) / data[i - 1].close
            returns.append(ret)
        volatility = np.sqrt(sum(r ** 2 for r in returns) / len(returns)) if returns else 0.0
        features.append(min(volatility * 100, 1.0))

        # Price position relative to recent high/low
        start_idx_hl = max(0, index - 20)
        recent_high = max(d.high for d in data[start_idx_hl:index + 1])
        recent_low = min(d.low for d in data[start_idx_hl:index + 1])
        price_position = (current_price - recent_low) / (recent_high - recent_low) if recent_high != recent_low else 0.5
        features.append(price_position)

        # Time-based features
        dt = datetime.fromtimestamp(data[index].timestamp / 1000)
        hour_of_day = dt.hour / 24.0
        day_of_week = dt.weekday() / 7.0
        features.append(hour_of_day)
        features.append(day_of_week)

        # Trend strength
        start_idx_trend = max(0, index - 19)
        sma20 = sum(d.close for d in data[start_idx_trend:index + 1]) / (index - start_idx_trend + 1)
        trend_strength = (current_price - sma20) / sma20 if sma20 != 0 else 0.0
        features.append(np.tanh(trend_strength * 10))

        # Support/Resistance levels
        start_idx_sr = max(0, index - 50)
        support_level = min(d.low for d in data[start_idx_sr:index + 1])
        resistance_level = max(d.high for d in data[start_idx_sr:index + 1])
        distance_to_support = (current_price - support_level) / current_price if current_price != 0 else 0.0
        distance_to_resistance = (resistance_level - current_price) / current_price if current_price != 0 else 0.0
        features.append(min(distance_to_support * 10, 1.0))
        features.append(min(distance_to_resistance * 10, 1.0))

        return features

    def prepare_training_data(self, data: List[MarketData]) -> Tuple[np.ndarray, np.ndarray]:
        inputs = []
        labels = []

        for i in range(self.lookback_period, len(data) - 1):
            features = []

            # Collect features for lookback period
            for j in range(self.lookback_period):
                period_features = self.extract_features(data, i - self.lookback_period + j)
                features.extend(period_features)

            inputs.append(features)

            # Label based on future price movement
            future_price = data[i + 1].close
            current_price = data[i].close
            price_change = (future_price - current_price) / current_price

            # Classify: buy (0), hold (1), sell (2)
            if price_change > 0.005:
                labels.append([1, 0, 0])  # Buy
            elif price_change < -0.005:
                labels.append([0, 0, 1])  # Sell
            else:
                labels.append([0, 1, 0])  # Hold

        return np.array(inputs), np.array(labels)

    async def train(self, data: List[MarketData], epochs: int = 50) -> None:
        if self.is_training:
            logger.warning('Training already in progress')
            return

        try:
            self.is_training = True
            logger.info(f'Starting ML model training with {len(data)} data points, {epochs} epochs')

            inputs, labels = self.prepare_training_data(data)

            if len(inputs) == 0:
                raise ValueError('Insufficient data for training')

            history = self.model.fit(
                inputs, labels,
                epochs=epochs,
                batch_size=32,
                validation_split=0.2,
                shuffle=True,
                verbose=1
            )

            logger.info('ML model training completed', extra={
                'final_accuracy': history.history.get('accuracy', [-1])[-1],
                'final_loss': history.history.get('loss', [-1])[-1]
            })
        except Exception as error:
            logger.error(f'Error training ML model: {error}')
            raise error
        finally:
            self.is_training = False

    async def predict(self, data: List[MarketData]) -> MLPrediction:
        if self.model is None:
            raise ValueError('Model not initialized')

        if len(data) < self.lookback_period:
            raise ValueError(f'Insufficient data for prediction. Need at least {self.lookback_period} data points')

        try:
            features = []

            # Collect features for lookback period
            for i in range(len(data) - self.lookback_period, len(data)):
                period_features = self.extract_features(data, i)
                features.extend(period_features)

            input_tensor = np.array([features])
            prediction = self.model.predict(input_tensor, verbose=0)
            prediction_array = prediction[0]

            # Convert to action
            buy_prob = prediction_array[0]
            hold_prob = prediction_array[1]
            sell_prob = prediction_array[2]

            if buy_prob > hold_prob and buy_prob > sell_prob:
                action = 'buy'
                confidence = float(buy_prob)
            elif sell_prob > hold_prob and sell_prob > buy_prob:
                action = 'sell'
                confidence = float(sell_prob)
            else:
                action = 'hold'
                confidence = float(hold_prob)

            # Get technical indicators for reasoning
            indicators = self.calculate_technical_indicators(data, len(data) - 1)
            reasoning = self.generate_reasoning(action, indicators, confidence)

            return MLPrediction(
                action=action,
                confidence=confidence,
                strength=float(max(buy_prob, sell_prob) - hold_prob),
                indicators=indicators,
                reasoning=reasoning
            )
        except Exception as error:
            logger.error(f'Error making prediction: {error}')
            raise error

    def generate_reasoning(self, action: str, indicators: TechnicalIndicators, confidence: float) -> List[str]:
        reasoning = []

        # RSI analysis
        if indicators.rsi < 30:
            reasoning.append('RSI indicates oversold conditions')
        elif indicators.rsi > 70:
            reasoning.append('RSI indicates overbought conditions')

        # MACD analysis
        if indicators.macd["histogram"] > 0:
            reasoning.append('MACD histogram shows bullish momentum')
        elif indicators.macd["histogram"] < 0:
            reasoning.append('MACD histogram shows bearish momentum')

        # Bollinger Bands analysis
        current_price = indicators.bollinger_bands["middle"]  # Approximation
        lower_dist = current_price - indicators.bollinger_bands["lower"]
        upper_dist = indicators.bollinger_bands["upper"] - current_price

        if lower_dist < upper_dist * 0.5:
            reasoning.append('Price near lower Bollinger Band (potential bounce)')
        elif upper_dist < lower_dist * 0.5:
            reasoning.append('Price near upper Bollinger Band (potential reversal)')

        # EMA analysis
        if indicators.ema["fast"] > indicators.ema["slow"]:
            reasoning.append('Fast EMA above slow EMA (bullish signal)')
        else:
            reasoning.append('Fast EMA below slow EMA (bearish signal)')

        # Stochastic analysis
        if indicators.stochastic["k"] < 20:
            reasoning.append('Stochastic indicates oversold')
        elif indicators.stochastic["k"] > 80:
            reasoning.append('Stochastic indicates overbought')

        # ADX analysis
        if indicators.adx > 25:
            reasoning.append('Strong trend detected (ADX > 25)')
        else:
            reasoning.append('Weak trend or ranging market (ADX < 25)')

        # Action-specific reasoning
        reasoning.append(f'{action.upper()} signal with {confidence * 100:.1f}% confidence')

        return reasoning

    def record_prediction_result(self, predicted: str, actual: str) -> None:
        self.prediction_history.append({
            'predicted': predicted,
            'actual': actual,
            'timestamp': datetime.now().timestamp() * 1000
        })

        if len(self.prediction_history) > self.max_history:
            self.prediction_history.pop(0)

    def get_accuracy(self) -> float:
        if not self.prediction_history:
            return 0.0

        correct = sum(1 for p in self.prediction_history if p['predicted'] == p['actual'])
        return correct / len(self.prediction_history)

    async def save_model(self, bot_id: str) -> None:
        try:
            model_dir = f'./models/{bot_id}'
            os.makedirs(model_dir, exist_ok=True)
            self.model.save(model_dir)
            logger.info(f'ML model saved successfully for bot {bot_id}')
        except Exception as error:
            logger.error(f'Failed to save ML model for bot {bot_id}: {error}')
            raise error

    async def load_model(self, bot_id: str) -> bool:
        try:
            model_path = f'./models/{bot_id}'
            self.model = tf.keras.models.load_model(model_path)
            logger.info(f'ML model loaded successfully for bot {bot_id}')
            return True
        except Exception as error:
            logger.warning(f'Failed to load ML model for bot {bot_id}, using new model: {error}')
            return False

    def dispose(self) -> None:
        if self.model:
            # Clear Keras session to free memory
            tf.keras.backend.clear_session()

# Global instance
enhanced_ml_engine = EnhancedMLEngine()
