from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel
import logging
import numpy as np
import asyncio
from datetime import datetime
import math
import os

try:
    import tensorflow as tf
    from tensorflow.keras import layers, models, optimizers
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logging.warning("TensorFlow not available, using mock implementations")

logger = logging.getLogger(__name__)

class NeuralNetworkConfig(BaseModel):
    input_size: int = 50  # Lookback period for technical indicators
    hidden_layers: List[int] = [128, 64, 32]
    output_size: int = 3  # buy, sell, hold
    learning_rate: float = 0.001
    epochs: int = 100
    batch_size: int = 32

class MarketData(BaseModel):
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float

class NeuralNetworkEngine:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = NeuralNetworkConfig(**(config or {}))
        self.model: Optional[tf.keras.Model] = None
        self.is_trained: bool = False
        self.recent_predictions: List[Dict[str, str]] = []
        self.max_recent_predictions: int = 100
        self.validation_history: List[Dict[str, float]] = []

        self.initialize_model()

    def get_recent_accuracy(self) -> float:
        """Get recent prediction accuracy"""
        if len(self.recent_predictions) == 0:
            return 0.5  # Default to neutral weight
        correct = sum(1 for p in self.recent_predictions if p['predicted'] == p['actual'])
        return correct / len(self.recent_predictions)

    def record_prediction_result(self, predicted: str, actual: str) -> None:
        """Record a prediction result for accuracy tracking"""
        self.recent_predictions.append({'predicted': predicted, 'actual': actual})
        if len(self.recent_predictions) > self.max_recent_predictions:
            self.recent_predictions.pop(0)

    def initialize_model(self) -> None:
        """Initialize the neural network model"""
        if not TENSORFLOW_AVAILABLE:
            logger.warning('TensorFlow not available, using mock model')
            self.model = None
            return

        try:
            self.model = models.Sequential()

            # Input layer
            self.model.add(layers.Dense(
                self.config.hidden_layers[0],
                input_shape=(self.config.input_size,),
                activation='relu',
                kernel_initializer='glorot_uniform'
            ))

            # Hidden layers
            for i in range(1, len(self.config.hidden_layers)):
                self.model.add(layers.Dense(
                    self.config.hidden_layers[i],
                    activation='relu',
                    kernel_initializer='glorot_uniform'
                ))
                self.model.add(layers.Dropout(0.2))

            # Output layer
            self.model.add(layers.Dense(
                self.config.output_size,
                activation='softmax',
                kernel_initializer='glorot_uniform'
            ))

            self.model.compile(
                optimizer=optimizers.Adam(self.config.learning_rate),
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )

            logger.info('Neural network model initialized successfully')
        except Exception as error:
            logger.error(f'Failed to initialize neural network model: {error}')
            raise error

    def preprocess_data(self, market_data: List[MarketData]) -> Tuple[np.ndarray, np.ndarray]:
        """Preprocess market data for training"""
        inputs: List[List[float]] = []
        labels: List[List[float]] = []

        for i in range(self.config.input_size, len(market_data) - 1):
            # Create input features from technical indicators
            input_features = self.extract_features(market_data, i)
            inputs.append(input_features)

            # Create labels based on future price movement
            current_price = market_data[i].close
            future_price = market_data[i + 1].close
            price_change = (future_price - current_price) / current_price

            # Label: 0=buy, 1=sell, 2=hold
            label = [0, 0, 1]  # Default to hold
            if price_change > 0.002:
                label = [1, 0, 0]  # Buy signal
            elif price_change < -0.002:
                label = [0, 1, 0]  # Sell signal

            labels.append(label)

        return np.array(inputs), np.array(labels)

    def extract_features(self, market_data: List[MarketData], index: int) -> List[float]:
        """Extract feature vector from market data at given index"""
        features: List[float] = []
        lookback = min(self.config.input_size, index)

        # Price data (normalized)
        for i in range(index - lookback, index):
            data = market_data[i]
            base_price = market_data[index - lookback].close
            features.extend([
                (data.open - base_price) / base_price,
                (data.high - base_price) / base_price,
                (data.low - base_price) / base_price,
                (data.close - base_price) / base_price,
                data.volume / 1000000  # Normalize volume
            ])

        # Fill remaining features with zeros if not enough data
        while len(features) < self.config.input_size:
            features.append(0.0)

        return features[:self.config.input_size]

    async def train(self, market_data: List[MarketData]) -> None:
        """Train the neural network model"""
        if len(market_data) < self.config.input_size + 10:
            raise ValueError('Insufficient data for training')

        if not TENSORFLOW_AVAILABLE or not self.model:
            logger.warning('TensorFlow not available, skipping actual training')
            await asyncio.sleep(1)  # Simulate training time
            logger.info('Mock training completed')
            return

        try:
            inputs, labels = self.preprocess_data(market_data)

            if len(inputs) == 0:
                raise ValueError('Insufficient processed data for training')

            history = self.model.fit(
                inputs,
                labels,
                epochs=self.config.epochs,
                batch_size=self.config.batch_size,
                validation_split=0.2,
                shuffle=True,
                verbose=1,
                callbacks=[
                    tf.keras.callbacks.EarlyStopping(
                        monitor='val_loss',
                        patience=10,
                        restore_best_weights=True
                    )
                ]
            )

            self.is_trained = True
            logger.info(f'Neural network training completed. '
                       f'Final accuracy: {history.history["accuracy"][-1]:.4f}, '
                       f'Final loss: {history.history["loss"][-1]:.4f}')

        except Exception as error:
            logger.error(f'Error training neural network: {error}')
            raise error

    async def predict(self, market_data: List[MarketData]) -> Dict[str, Any]:
        """Generate prediction from market data"""
        try:
            if not TENSORFLOW_AVAILABLE or not self.model or not self.is_trained:
                return {"action": "hold", "confidence": 0.0}

            if len(market_data) < self.config.input_size:
                raise ValueError(f'Insufficient data for prediction. Need at least {self.config.input_size} data points')

            features = self.extract_features(market_data, len(market_data) - 1)
            input_tensor = tf.convert_to_tensor([features])

            prediction = self.model.predict(input_tensor, verbose=0)
            prediction_array = prediction.numpy()[0]

            actions = ['buy', 'sell', 'hold']
            max_index = np.argmax(prediction_array)

            return {
                "action": actions[max_index],
                "confidence": float(prediction_array[max_index])
            }

        except Exception as e:
            logger.error(f'Error generating neural network prediction: {e}')
            return {"action": "hold", "confidence": 0.0}

    async def save_model(self, bot_id: str) -> None:
        """Save the trained model to disk"""
        if not self.model:
            raise ValueError('No model to save')

        try:
            model_path = f'./models/{bot_id}'
            os.makedirs(model_path, exist_ok=True)
            self.model.save(model_path)
            logger.info(f'Neural network model saved successfully for bot {bot_id} at {model_path}')
        except Exception as error:
            logger.error(f'Failed to save neural network model: {error}')
            raise error

    async def load_model(self, bot_id: str) -> bool:
        """Load a trained model from disk"""
        try:
            model_path = f'./models/{bot_id}'
            if os.path.exists(model_path):
                self.model = tf.keras.models.load_model(model_path)
                self.is_trained = True
                logger.info(f'Neural network model loaded successfully for bot {bot_id}')
                return True
            else:
                logger.warning(f'Model path does not exist: {model_path}')
                return False
        except Exception as error:
            logger.warning(f'Failed to load neural network model for bot {bot_id}: {error}')
            # Reinitialize with new model if loading fails
            self.initialize_model()
            return False

    def dispose(self) -> None:
        """Clean up resources"""
        if self.model:
            # Clear the model from memory
            del self.model
            self.model = None

            # Force garbage collection
            import gc
            gc.collect()

            # Clear TensorFlow session if available
            if TENSORFLOW_AVAILABLE:
                tf.keras.backend.clear_session()

# Global instance
neural_network_engine = NeuralNetworkEngine()
