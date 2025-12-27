from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
import numpy as np
import asyncio
from datetime import datetime
import math

try:
    import os

    # Allow disabling heavy TF load via env for test speed
    if os.getenv("DISABLE_TENSORFLOW", "0") == "1":
        raise ImportError("TensorFlow disabled by environment")
    import tensorflow as tf
    from tensorflow.keras import layers, models, optimizers

    TENSORFLOW_AVAILABLE = True
except Exception:
    TENSORFLOW_AVAILABLE = False
    logging.warning("TensorFlow unavailable or disabled; using lightweight mock model.")

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
        """Initialize the neural network model"""
        if not TENSORFLOW_AVAILABLE:
            # Provide minimal mock interface for predict to keep tests fast
            class MockModel:
                def predict(self, arr):
                    import numpy as _np

                    # Return uniform probabilities for buy/sell/hold
                    batch = arr.shape[0]
                    return _np.full((batch, 3), 1 / 3.0)

            self.model = MockModel()
            logger.warning("Using MockModel for ML predictions")
            return

        try:
            self.model = models.Sequential(
                [
                    # Input layer
                    layers.Dense(
                        128,
                        input_shape=(self.lookback_period * self.feature_count,),
                        activation="relu",
                        kernel_initializer="he_normal",
                    ),
                    layers.Dropout(0.3),
                    # Hidden layers with batch normalization
                    layers.Dense(
                        256, activation="relu", kernel_initializer="he_normal"
                    ),
                    layers.BatchNormalization(),
                    layers.Dropout(0.3),
                    layers.Dense(
                        128, activation="relu", kernel_initializer="he_normal"
                    ),
                    layers.BatchNormalization(),
                    layers.Dropout(0.2),
                    layers.Dense(64, activation="relu", kernel_initializer="he_normal"),
                    layers.Dropout(0.2),
                    # Output layer - 3 classes (buy, sell, hold)
                    layers.Dense(3, activation="softmax"),
                ]
            )

            self.model.compile(
                optimizer=optimizers.Adam(0.001),
                loss="categorical_crossentropy",
                metrics=["accuracy"],
            )

            logger.info("Enhanced ML model initialized successfully")
        except Exception as error:
            logger.error(f"Failed to initialize ML model: {error}")
            raise error

    def calculate_technical_indicators(
        self, data: List[MarketData], index: int
    ) -> TechnicalIndicators:
        """Calculate comprehensive technical indicators"""
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
            obv=obv,
        )

    def calculate_rsi(
        self, data: List[MarketData], index: int, period: int = 14
    ) -> float:
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
        return 100 - (100 / (1 + rs))

    def calculate_macd(
        self,
        data: List[MarketData],
        index: int,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> Dict[str, float]:
        if index < slow_period:
            return {"value": 0.0, "signal": 0.0, "histogram": 0.0}

        fast_ema = self.calculate_ema_value(data, index, fast_period)
        slow_ema = self.calculate_ema_value(data, index, slow_period)
        macd_value = fast_ema - slow_ema

        # Simplified signal calculation
        signal = macd_value * 0.2
        histogram = macd_value - signal

        return {"value": macd_value, "signal": signal, "histogram": histogram}

    def calculate_ema_value(
        self, data: List[MarketData], index: int, period: int
    ) -> float:
        if index < period:
            return data[index].close

        multiplier = 2 / (period + 1)
        ema = data[index - period].close

        for i in range(index - period + 1, index + 1):
            ema = (data[i].close - ema) * multiplier + ema

        return ema

    def calculate_bollinger_bands(
        self, data: List[MarketData], index: int, period: int = 20, std_dev: float = 2
    ) -> Dict[str, float]:
        if index < period:
            current = data[index].close
            return {"upper": current, "middle": current, "lower": current}

        prices = [d.close for d in data[index - period + 1 : index + 1]]
        middle = sum(prices) / period

        variance = sum((p - middle) ** 2 for p in prices) / period
        std = math.sqrt(variance)

        return {
            "upper": middle + std_dev * std,
            "middle": middle,
            "lower": middle - std_dev * std,
        }

    def calculate_ema(self, data: List[MarketData], index: int) -> Dict[str, float]:
        return {
            "fast": self.calculate_ema_value(data, index, 12),
            "slow": self.calculate_ema_value(data, index, 26),
        }

    def calculate_atr(
        self, data: List[MarketData], index: int, period: int = 14
    ) -> float:
        if index < period:
            return 0.0

        tr_sum = 0.0
        for i in range(index - period + 1, index + 1):
            high = data[i].high
            low = data[i].low
            prev_close = data[i - 1].close if i > 0 else data[i].close

            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            tr_sum += tr

        return tr_sum / period

    def calculate_volume_oscillator(self, data: List[MarketData], index: int) -> float:
        if index < 26:
            return 0.0

        short_vol_ema = self.calculate_volume_ema(data, index, 5)
        long_vol_ema = self.calculate_volume_ema(data, index, 10)

        return (
            ((short_vol_ema - long_vol_ema) / long_vol_ema) * 100
            if long_vol_ema != 0
            else 0.0
        )

    def calculate_volume_ema(
        self, data: List[MarketData], index: int, period: int
    ) -> float:
        if index < period:
            return data[index].volume

        multiplier = 2 / (period + 1)
        ema = data[index - period].volume

        for i in range(index - period + 1, index + 1):
            ema = (data[i].volume - ema) * multiplier + ema

        return ema

    def calculate_stochastic(
        self, data: List[MarketData], index: int, period: int = 14
    ) -> Dict[str, float]:
        if index < period:
            return {"k": 50.0, "d": 50.0}

        recent_data = data[index - period + 1 : index + 1]
        high = max(d.high for d in recent_data)
        low = min(d.low for d in recent_data)
        close = data[index].close

        k = ((close - low) / (high - low)) * 100 if (high - low) != 0 else 50.0
        d = k  # Simplified D calculation

        return {"k": k, "d": d}

    def calculate_adx(
        self, data: List[MarketData], index: int, period: int = 14
    ) -> float:
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
                abs(data[i].low - data[i - 1].close),
            )
            tr += true_range

        plus_di = (plus_dm / tr) * 100 if tr != 0 else 0.0
        minus_di = (minus_dm / tr) * 100 if tr != 0 else 0.0
        dx = (
            abs(plus_di - minus_di) / (plus_di + minus_di) * 100
            if (plus_di + minus_di) != 0
            else 0.0
        )

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
        """Extract feature vector from market data"""
        features = []
        indicators = self.calculate_technical_indicators(data, index)

        # Price-based features (normalized)
        current_price = data[index].close
        price_change = (
            (current_price - data[index - 1].close) / data[index - 1].close
            if index > 0
            else 0.0
        )
        features.append(price_change)

        # Volume features
        avg_volume = sum(d.volume for d in data[max(0, index - 20) : index + 1]) / min(
            20, index + 1
        )
        volume_ratio = data[index].volume / avg_volume if avg_volume != 0 else 1.0
        features.append(min(volume_ratio, 5))  # Cap at 5x

        # Technical indicators
        features.append(indicators.rsi / 100)
        features.append(math.tanh(indicators.macd["value"] / current_price))
        features.append(math.tanh(indicators.macd["histogram"] / current_price))
        features.append(
            (current_price - indicators.bollinger_bands["lower"])
            / (
                indicators.bollinger_bands["upper"]
                - indicators.bollinger_bands["lower"]
            )
            if (
                indicators.bollinger_bands["upper"]
                - indicators.bollinger_bands["lower"]
            )
            != 0
            else 0.5
        )
        features.append(
            math.tanh((indicators.ema["fast"] - indicators.ema["slow"]) / current_price)
        )
        features.append(min(indicators.atr / current_price, 0.1) * 10)
        features.append(math.tanh(indicators.volume_oscillator / 100))
        features.append(indicators.stochastic["k"] / 100)
        features.append(indicators.stochastic["d"] / 100)
        features.append(indicators.adx / 100)
        features.append(math.tanh(indicators.obv / 1000000))

        # Price momentum features
        momentum5 = (
            (current_price - data[index - 5].close) / data[index - 5].close
            if index >= 5
            else 0.0
        )
        momentum10 = (
            (current_price - data[index - 10].close) / data[index - 10].close
            if index >= 10
            else 0.0
        )
        momentum20 = (
            (current_price - data[index - 20].close) / data[index - 20].close
            if index >= 20
            else 0.0
        )
        features.extend(
            [
                math.tanh(momentum5 * 10),
                math.tanh(momentum10 * 5),
                math.tanh(momentum20 * 2),
            ]
        )

        # Volatility features
        returns = [
            (d.close - data[max(0, i - 1)].close) / data[max(0, i - 1)].close
            for i, d in enumerate(data[max(0, index - 20) : index + 1])
            if i > 0
        ]
        volatility = (
            math.sqrt(sum(r * r for r in returns) / len(returns)) if returns else 0.0
        )
        features.append(min(volatility * 100, 1))

        # Price position relative to recent high/low
        recent_high = max(d.high for d in data[max(0, index - 20) : index + 1])
        recent_low = min(d.low for d in data[max(0, index - 20) : index + 1])
        price_position = (
            (current_price - recent_low) / (recent_high - recent_low)
            if (recent_high - recent_low) != 0
            else 0.5
        )
        features.append(price_position)

        # Time-based features
        hour_of_day = datetime.fromtimestamp(data[index].timestamp / 1000).hour / 24
        day_of_week = datetime.fromtimestamp(data[index].timestamp / 1000).weekday() / 7
        features.extend([hour_of_day, day_of_week])

        # Trend strength
        sma20 = sum(d.close for d in data[max(0, index - 19) : index + 1]) / min(
            20, index + 1
        )
        trend_strength = (current_price - sma20) / sma20 if sma20 != 0 else 0.0
        features.append(math.tanh(trend_strength * 10))

        # Support/Resistance levels
        support_level = min(d.low for d in data[max(0, index - 50) : index + 1])
        resistance_level = max(d.high for d in data[max(0, index - 50) : index + 1])
        distance_to_support = (
            (current_price - support_level) / current_price
            if current_price != 0
            else 0.0
        )
        distance_to_resistance = (
            (resistance_level - current_price) / current_price
            if current_price != 0
            else 0.0
        )
        features.extend(
            [
                min(distance_to_support * 10, 1),
                min(distance_to_resistance * 10, 1),
            ]
        )

        return features

    async def predict(self, data: List[MarketData]) -> MLPrediction:
        """Generate trading prediction from market data"""
        try:
            if not TENSORFLOW_AVAILABLE or not self.model:
                # Fallback to technical indicator-based prediction
                return self._predict_with_technical_indicators(data)

            if len(data) < self.lookback_period:
                raise ValueError(
                    f"Insufficient data for prediction. Need at least {self.lookback_period} data points"
                )

            # Extract features for lookback period
            features = []
            for i in range(len(data) - self.lookback_period, len(data)):
                period_features = self.extract_features(data, i)
                features.extend(period_features)

            input_tensor = tf.convert_to_tensor([features])
            prediction = self.model.predict(input_tensor, verbose=0)
            prediction_array = prediction.numpy()[0]

            # Convert to action
            actions = ["buy", "sell", "hold"]
            buy_prob, sell_prob, hold_prob = prediction_array

            if buy_prob > sell_prob and buy_prob > hold_prob:
                action = "buy"
                confidence = float(buy_prob)
            elif sell_prob > hold_prob and sell_prob > buy_prob:
                action = "sell"
                confidence = float(sell_prob)
            else:
                action = "hold"
                confidence = float(hold_prob)

            # Get technical indicators for reasoning
            indicators = self.calculate_technical_indicators(data, len(data) - 1)
            reasoning = self.generate_reasoning(action, indicators, confidence)

            return MLPrediction(
                action=action,
                confidence=confidence,
                strength=max(buy_prob, sell_prob) - hold_prob,
                indicators=indicators,
                reasoning=reasoning,
            )

        except Exception as e:
            logger.error(f"Error generating prediction: {e}")
            raise e

    def _predict_with_technical_indicators(
        self, data: List[MarketData]
    ) -> MLPrediction:
        """Fallback prediction using technical indicators only"""
        try:
            if len(data) < 2:
                return MLPrediction(
                    action="hold",
                    confidence=0.5,
                    strength=0.0,
                    indicators=TechnicalIndicators(
                        rsi=50.0,
                        macd={"value": 0.0, "signal": 0.0, "histogram": 0.0},
                        bollinger_bands={"upper": 0.0, "middle": 0.0, "lower": 0.0},
                        ema={"fast": 0.0, "slow": 0.0},
                        atr=0.0,
                        volume_oscillator=0.0,
                        stochastic={"k": 50.0, "d": 50.0},
                        adx=25.0,
                        obv=0.0,
                    ),
                    reasoning=["Technical indicator analysis - insufficient data"],
                )

            # Simple technical indicator-based prediction
            indicators = self.calculate_technical_indicators(data, len(data) - 1)

            # Decision logic based on indicators
            score = 0.0

            # RSI signals
            if indicators.rsi < 30:
                score += 1  # Oversold
            elif indicators.rsi > 70:
                score -= 1  # Overbought

            # MACD signals
            if indicators.macd["histogram"] > 0:
                score += 0.5  # Bullish momentum

            # EMA signals
            if indicators.ema["fast"] > indicators.ema["slow"]:
                score += 0.3  # Bullish trend

            # Stochastic signals
            if indicators.stochastic["k"] < 20:
                score += 0.4  # Oversold

            # Determine action
            if score > 0.8:
                action = "buy"
                confidence = min(0.8, 0.5 + score * 0.3)
            elif score < -0.8:
                action = "sell"
                confidence = min(0.8, 0.5 + abs(score) * 0.3)
            else:
                action = "hold"
                confidence = 0.6

            reasoning = self.generate_reasoning(action, indicators, confidence)

            return MLPrediction(
                action=action,
                confidence=confidence,
                strength=abs(score) * 0.5,
                indicators=indicators,
                reasoning=reasoning,
            )

        except Exception as e:
            logger.error(f"Error in technical indicator prediction: {e}")
            raise e

    def generate_reasoning(
        self, action: str, indicators: TechnicalIndicators, confidence: float
    ) -> List[str]:
        reasoning = []

        # RSI analysis
        if indicators.rsi < 30:
            reasoning.append("RSI indicates oversold conditions")
        elif indicators.rsi > 70:
            reasoning.append("RSI indicates overbought conditions")

        # MACD analysis
        if indicators.macd["histogram"] > 0:
            reasoning.append("MACD histogram shows bullish momentum")
        elif indicators.macd["histogram"] < 0:
            reasoning.append("MACD histogram shows bearish momentum")

        # Action-specific reasoning
        reasoning.append(
            f"{action.upper()} signal with {confidence * 100:.1f}% confidence"
        )

        return reasoning

    def prepare_training_data(self, data: List[MarketData]) -> tuple:
        """Prepare training data from market data"""
        inputs = []
        labels = []

        for i in range(self.lookback_period, len(data) - 1):
            features = []
            # Collect features for lookback period
            for j in range(self.lookback_period):
                period_features = self.extract_features(
                    data, i - self.lookback_period + j
                )
                features.extend(period_features)

            inputs.append(features)

            # Label based on future price movement
            future_price = data[i + 1].close
            current_price = data[i].close
            price_change = (future_price - current_price) / current_price

            # Classify: buy (0), hold (1), sell (2)
            if price_change > 0.005:
                label = [1, 0, 0]  # Buy
            elif price_change < -0.005:
                label = [0, 0, 1]  # Sell
            else:
                label = [0, 1, 0]  # Hold

            labels.append(label)

        return np.array(inputs), np.array(labels)

    async def train(self, data: List[MarketData], epochs: int = 50) -> None:
        """Train the neural network model"""
        if self.is_training:
            logger.warning("Training already in progress")
            return

        try:
            self.is_training = True
            logger.info(
                f"Starting ML model training with {len(data)} data points, {epochs} epochs"
            )

            if not TENSORFLOW_AVAILABLE or not self.model:
                logger.warning("TensorFlow not available, skipping actual training")
                await asyncio.sleep(1)  # Simulate training time
                logger.info("Mock training completed")
                return

            inputs, labels = self.prepare_training_data(data)

            if len(inputs) == 0:
                raise ValueError("Insufficient data for training")

            history = self.model.fit(
                inputs,
                labels,
                epochs=epochs,
                batch_size=32,
                validation_split=0.2,
                shuffle=True,
                verbose=1,
                callbacks=[
                    tf.keras.callbacks.EarlyStopping(
                        monitor="val_loss", patience=10, restore_best_weights=True
                    )
                ],
            )

            logger.info(
                f'ML model training completed. Final accuracy: {history.history["accuracy"][-1]:.4f}, '
                f'Final loss: {history.history["loss"][-1]:.4f}'
            )

        except Exception as error:
            logger.error(f"Error training ML model: {error}")
            raise error
        finally:
            self.is_training = False

    def record_prediction_result(self, predicted: str, actual: str) -> None:
        self.prediction_history.append(
            {
                "predicted": predicted,
                "actual": actual,
                "timestamp": datetime.now().timestamp() * 1000,
            }
        )

        if len(self.prediction_history) > self.max_history:
            self.prediction_history.pop(0)

    def get_accuracy(self) -> float:
        if not self.prediction_history:
            return 0.0

        correct = sum(
            1 for p in self.prediction_history if p["predicted"] == p["actual"]
        )
        return correct / len(self.prediction_history)

    async def save_model(self, bot_id: str) -> None:
        """Save the trained model to disk"""
        try:
            if not self.model:
                raise ValueError("No model to save")

            model_path = f"./models/{bot_id}"
            self.model.save(model_path)
            logger.info(f"ML model saved successfully for bot {bot_id} at {model_path}")
        except Exception as error:
            logger.error(f"Failed to save ML model: {error}")
            raise error

    async def load_model(self, bot_id: str) -> bool:
        """Load a trained model from disk"""
        try:
            model_path = f"./models/{bot_id}"
            self.model = tf.keras.models.load_model(model_path)
            logger.info(f"ML model loaded successfully for bot {bot_id}")
            return True
        except Exception as error:
            logger.warning(f"Failed to load ML model for bot {bot_id}: {error}")
            # Reinitialize with new model if loading fails
            self.initialize_model()
            return False

    def dispose(self) -> None:
        """Dispose of the model and free memory"""
        if self.model:
            # Clear the model from memory
            del self.model
            self.model = None
            # Force garbage collection
            import gc

            gc.collect()
            # Clear TensorFlow session
            tf.keras.backend.clear_session()


# Global instance
enhanced_ml_engine = EnhancedMLEngine()
