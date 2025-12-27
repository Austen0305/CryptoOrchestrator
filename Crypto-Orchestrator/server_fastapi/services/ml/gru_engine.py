"""
GRU Engine - Gated Recurrent Unit neural network for time-series prediction
GRU is similar to LSTM but simpler and often faster to train
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
    logging.warning("TensorFlow unavailable; GRU engine will use mock model.")

logger = logging.getLogger(__name__)


class GRUConfig(BaseModel):
    """GRU model configuration"""

    sequence_length: int = 60  # Number of time steps to look back
    gru_units: int = 128  # Number of GRU units
    num_layers: int = 2  # Number of GRU layers
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


class GRUEngine:
    """GRU neural network engine for time-series prediction"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = GRUConfig(**(config or {}))
        self.model: Optional[tf.keras.Model] = None
        self.is_training: bool = False
        self.feature_count: int = 5  # OHLCV
        self.scaler = None  # For feature normalization

        if TENSORFLOW_AVAILABLE:
            self.initialize_model()
        else:
            logger.warning("GRU engine initialized with mock model")
            self._initialize_mock_model()

    def _initialize_mock_model(self):
        """Initialize mock model for testing when TensorFlow is unavailable"""

        class MockModel:
            def predict(self, data):
                batch_size = data.shape[0] if len(data.shape) > 1 else 1
                return np.full((batch_size, 3), 1 / 3.0)

            def fit(self, *args, **kwargs):
                return None

            def save(self, *args, **kwargs):
                pass

            def compile(self, *args, **kwargs):
                pass

        self.model = MockModel()

    def initialize_model(self) -> None:
        """Initialize the GRU model"""
        if not TENSORFLOW_AVAILABLE:
            self._initialize_mock_model()
            return

        try:
            model = models.Sequential()

            # Input layer
            model.add(
                layers.Input(shape=(self.config.sequence_length, self.feature_count))
            )

            # GRU layers with return_sequences=True (except last layer)
            for i in range(self.config.num_layers - 1):
                model.add(
                    layers.GRU(
                        self.config.gru_units,
                        return_sequences=True,
                        dropout=self.config.dropout,
                        recurrent_dropout=self.config.recurrent_dropout,
                        kernel_initializer="glorot_uniform",
                        recurrent_initializer="orthogonal",
                    )
                )
                model.add(layers.BatchNormalization())

            # Final GRU layer (return_sequences=False)
            model.add(
                layers.GRU(
                    self.config.gru_units,
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
                f"GRU model initialized: {self.config.num_layers} layers, "
                f"{self.config.gru_units} units each"
            )

        except Exception as error:
            logger.error(f"Failed to initialize GRU model: {error}")
            raise error

    def create_sequences(
        self, data: np.ndarray, labels: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Create sequences from time-series data"""
        X, y = [], []

        for i in range(len(data) - self.config.sequence_length):
            X.append(data[i : i + self.config.sequence_length])
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
        """Preprocess market data for GRU input"""
        if not market_data:
            raise ValueError("Market data is empty")

        # Convert to numpy array [samples, features]
        data_array = np.array(
            [[d.open, d.high, d.low, d.close, d.volume] for d in market_data]
        )

        # Normalize features
        from sklearn.preprocessing import MinMaxScaler

        if self.scaler is None:
            self.scaler = MinMaxScaler()
            data_array = self.scaler.fit_transform(data_array)
        else:
            data_array = self.scaler.transform(data_array)

        X, _ = self.create_sequences(data_array)
        return X, None

    def predict(self, market_data: List[MarketData]) -> Dict[str, Any]:
        """Make prediction using GRU model"""
        try:
            X, _ = self.preprocess_data(market_data)

            if len(X) == 0:
                return {
                    "action": "hold",
                    "confidence": 0.33,
                    "probabilities": {"buy": 0.33, "sell": 0.33, "hold": 0.33},
                }

            predictions = self.model.predict(X[-1:], verbose=0)
            probs = predictions[0]

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
            logger.error(f"GRU prediction error: {error}")
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
        """Train the GRU model"""
        if not TENSORFLOW_AVAILABLE:
            logger.warning("TensorFlow not available, cannot train GRU model")
            return {"status": "skipped", "reason": "TensorFlow not available"}

        try:
            self.is_training = True

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
                    filepath="models/gru_best.h5",
                    monitor="val_loss" if X_val is not None else "loss",
                    save_best_only=True,
                    verbose=0,
                ),
            ]

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
            logger.error(f"GRU training error: {error}")
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
            logger.info(f"GRU model saved to {filepath}")
            return True

        except Exception as error:
            logger.error(f"Failed to save GRU model: {error}")
            return False

    def load_model(self, filepath: str) -> bool:
        """Load the model from file"""
        try:
            if not TENSORFLOW_AVAILABLE:
                return False

            if not os.path.exists(filepath):
                logger.warning(f"GRU model file not found: {filepath}")
                return False

            self.model = models.load_model(filepath)
            logger.info(f"GRU model loaded from {filepath}")
            return True

        except Exception as error:
            logger.error(f"Failed to load GRU model: {error}")
            return False
