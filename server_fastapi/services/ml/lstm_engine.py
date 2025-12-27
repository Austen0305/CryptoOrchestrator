"""
LSTM Engine - Long Short-Term Memory neural network for time-series prediction
"""

from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel
import logging
import numpy as np
from datetime import datetime
import os

try:
    if os.getenv("DISABLE_TENSORFLOW", "0") == "1":
        raise ImportError("TensorFlow disabled by environment")
    import tensorflow as tf
    from tensorflow.keras import layers, models, optimizers, callbacks

    TENSORFLOW_AVAILABLE = True
except Exception:
    TENSORFLOW_AVAILABLE = False
    logging.warning("TensorFlow unavailable; LSTM engine will use mock model.")

logger = logging.getLogger(__name__)


class LSTMConfig(BaseModel):
    """LSTM model configuration"""

    sequence_length: int = 60  # Number of time steps to look back
    lstm_units: int = 128  # Number of LSTM units
    num_layers: int = 2  # Number of LSTM layers
    dropout: float = 0.2  # Dropout rate
    recurrent_dropout: float = 0.2  # Recurrent dropout rate
    dense_units: int = 64  # Dense layer units
    learning_rate: float = 0.001
    epochs: int = 100
    batch_size: int = 32
    validation_split: float = 0.2
    early_stopping_patience: int = 10


class MarketData(BaseModel):
    """Market data point"""

    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class LSTMEngine:
    """LSTM neural network engine for time-series prediction"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = LSTMConfig(**(config or {}))
        self.model: Optional[tf.keras.Model] = None
        self.is_training: bool = False
        self.feature_count: int = 5  # OHLCV
        self.scaler = None  # For feature normalization

        if TENSORFLOW_AVAILABLE:
            self.initialize_model()
        else:
            logger.warning("LSTM engine initialized with mock model")
            self._initialize_mock_model()

    def _initialize_mock_model(self):
        """Initialize mock model for testing when TensorFlow is unavailable"""

        class MockModel:
            def predict(self, data):
                batch_size = data.shape[0] if len(data.shape) > 1 else 1
                # Return uniform probabilities for buy/sell/hold
                return np.full((batch_size, 3), 1 / 3.0)

            def fit(self, *args, **kwargs):
                return None

            def save(self, *args, **kwargs):
                pass

            def compile(self, *args, **kwargs):
                pass

        self.model = MockModel()

    def initialize_model(self) -> None:
        """Initialize the LSTM model"""
        if not TENSORFLOW_AVAILABLE:
            self._initialize_mock_model()
            return

        try:
            model = models.Sequential()

            # Input layer
            model.add(
                layers.Input(shape=(self.config.sequence_length, self.feature_count))
            )

            # LSTM layers with return_sequences=True (except last layer)
            for i in range(self.config.num_layers - 1):
                model.add(
                    layers.LSTM(
                        self.config.lstm_units,
                        return_sequences=True,
                        dropout=self.config.dropout,
                        recurrent_dropout=self.config.recurrent_dropout,
                        kernel_initializer="glorot_uniform",
                        recurrent_initializer="orthogonal",
                    )
                )
                model.add(layers.BatchNormalization())

            # Final LSTM layer (return_sequences=False)
            model.add(
                layers.LSTM(
                    self.config.lstm_units,
                    return_sequences=False,
                    dropout=self.config.dropout,
                    recurrent_dropout=self.config.recurrent_dropout,
                    kernel_initializer="glorot_uniform",
                    recurrent_initializer="orthogonal",
                )
            )
            model.add(layers.BatchNormalization())

            # Dense layers
            model.add(
                layers.Dense(
                    self.config.dense_units,
                    activation="relu",
                    kernel_initializer="he_normal",
                )
            )
            model.add(layers.Dropout(self.config.dropout))

            model.add(
                layers.Dense(
                    self.config.dense_units // 2,
                    activation="relu",
                    kernel_initializer="he_normal",
                )
            )
            model.add(layers.Dropout(self.config.dropout / 2))

            # Output layer - 3 classes (buy, sell, hold)
            model.add(layers.Dense(3, activation="softmax"))

            # Compile model
            model.compile(
                optimizer=optimizers.Adam(learning_rate=self.config.learning_rate),
                loss="categorical_crossentropy",
                metrics=["accuracy", "sparse_categorical_accuracy"],
            )

            self.model = model
            logger.info(
                f"LSTM model initialized: {self.config.num_layers} layers, "
                f"{self.config.lstm_units} units each"
            )

        except Exception as error:
            logger.error(f"Failed to initialize LSTM model: {error}")
            raise error

    def create_sequences(
        self, data: np.ndarray, labels: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Create sequences from time-series data"""
        X, y = [], []

        for i in range(len(data) - self.config.sequence_length):
            # Extract sequence
            X.append(data[i : i + self.config.sequence_length])
            # Extract label (if provided)
            if labels is not None:
                y.append(labels[i + self.config.sequence_length])

        X = np.array(X)
        if labels is not None:
            y = np.array(y)
            return X, y
        return X, None

    def preprocess_data(
        self, market_data: List[MarketData]
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Preprocess market data for LSTM input"""
        if not market_data:
            raise ValueError("Market data is empty")

        # Convert to numpy array [samples, features] where features = [open, high, low, close, volume]
        data_array = np.array(
            [[d.open, d.high, d.low, d.close, d.volume] for d in market_data]
        )

        # Normalize features (use MinMaxScaler or StandardScaler)
        from sklearn.preprocessing import MinMaxScaler

        if self.scaler is None:
            self.scaler = MinMaxScaler()
            data_array = self.scaler.fit_transform(data_array)
        else:
            data_array = self.scaler.transform(data_array)

        # For now, return sequences without labels (for prediction)
        # In training, labels would be created separately
        X, _ = self.create_sequences(data_array)
        return X, None

    def predict(self, market_data: List[MarketData]) -> Dict[str, Any]:
        """Make prediction using LSTM model"""
        try:
            # Preprocess data
            X, _ = self.preprocess_data(market_data)

            if len(X) == 0:
                return {
                    "action": "hold",
                    "confidence": 0.33,
                    "probabilities": {"buy": 0.33, "sell": 0.33, "hold": 0.33},
                }

            # Get prediction for last sequence
            predictions = self.model.predict(X[-1:], verbose=0)
            probs = predictions[0]

            # Map to actions
            actions = ["buy", "sell", "hold"]
            action_idx = np.argmax(probs)
            action = actions[action_idx]
            confidence = float(probs[action_idx])

            return {
                "action": action,
                "confidence": confidence,
                "probabilities": {
                    "buy": float(probs[0]),
                    "sell": float(probs[1]),
                    "hold": float(probs[2]),
                },
            }

        except Exception as error:
            logger.error(f"LSTM prediction error: {error}")
            return {
                "action": "hold",
                "confidence": 0.33,
                "probabilities": {"buy": 0.33, "sell": 0.33, "hold": 0.33},
            }

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """Train the LSTM model"""
        if not TENSORFLOW_AVAILABLE:
            logger.warning("TensorFlow not available, cannot train LSTM model")
            return {"status": "skipped", "reason": "TensorFlow not available"}

        try:
            self.is_training = True

            # Callbacks
            callback_list = [
                callbacks.EarlyStopping(
                    monitor="val_loss" if X_val is not None else "loss",
                    patience=self.config.early_stopping_patience,
                    restore_best_weights=True,
                ),
                callbacks.ReduceLROnPlateau(
                    monitor="val_loss" if X_val is not None else "loss",
                    factor=0.5,
                    patience=5,
                    min_lr=1e-7,
                ),
                callbacks.ModelCheckpoint(
                    filepath="models/lstm_best.h5",
                    monitor="val_loss" if X_val is not None else "loss",
                    save_best_only=True,
                    verbose=0,
                ),
            ]

            # Training
            validation_data = (X_val, y_val) if X_val is not None else None

            history = self.model.fit(
                X_train,
                y_train,
                batch_size=self.config.batch_size,
                epochs=self.config.epochs,
                validation_data=validation_data,
                callbacks=callback_list,
                verbose=1,
            )

            self.is_training = False

            return {
                "status": "success",
                "history": {
                    "loss": history.history.get("loss", []),
                    "val_loss": history.history.get("val_loss", []),
                    "accuracy": history.history.get("accuracy", []),
                    "val_accuracy": history.history.get("val_accuracy", []),
                },
            }

        except Exception as error:
            self.is_training = False
            logger.error(f"LSTM training error: {error}")
            return {"status": "error", "error": str(error)}

    def save_model(self, filepath: str) -> bool:
        """Save the model to file"""
        try:
            if not TENSORFLOW_AVAILABLE:
                return False

            os.makedirs(
                os.path.dirname(filepath) if os.path.dirname(filepath) else ".",
                exist_ok=True,
            )
            self.model.save(filepath)
            logger.info(f"LSTM model saved to {filepath}")
            return True

        except Exception as error:
            logger.error(f"Failed to save LSTM model: {error}")
            return False

    def load_model(self, filepath: str) -> bool:
        """Load the model from file"""
        try:
            if not TENSORFLOW_AVAILABLE:
                return False

            if not os.path.exists(filepath):
                logger.warning(f"LSTM model file not found: {filepath}")
                return False

            self.model = models.load_model(filepath)
            logger.info(f"LSTM model loaded from {filepath}")
            return True

        except Exception as error:
            logger.error(f"Failed to load LSTM model: {error}")
            return False
