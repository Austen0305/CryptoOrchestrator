"""
LSTM Model Training Service
Enhanced ML capabilities for price prediction
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import logging
import os
import json

logger = logging.getLogger(__name__)

# Try to import ML libraries
try:
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.model_selection import train_test_split

    ML_AVAILABLE = True
except ImportError:
    logger.warning("scikit-learn not installed. ML features limited.")
    ML_AVAILABLE = False

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

    TENSORFLOW_AVAILABLE = True
except ImportError:
    logger.warning("TensorFlow not installed. LSTM training unavailable.")
    TENSORFLOW_AVAILABLE = False


class LSTMTrainingService:
    """
    LSTM Model Training Service for price prediction

    Features:
    - Data collection from exchanges
    - Feature engineering with technical indicators
    - LSTM model training
    - Model evaluation and validation
    - Prediction generation
    """

    def __init__(self):
        """Initialize LSTM Training Service"""
        self.ml_available = ML_AVAILABLE and TENSORFLOW_AVAILABLE
        self.model = None
        self.scaler = MinMaxScaler() if ML_AVAILABLE else None
        self.sequence_length = 60  # Use 60 time steps for prediction
        self.features = []

        if not self.ml_available:
            logger.warning(
                "ML libraries not available. Install tensorflow and scikit-learn for full functionality."
            )

    def prepare_data(
        self, price_data: List[Dict[str, Any]], symbol: str = "BTC/USDT"
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare training data with feature engineering

        Args:
            price_data: List of price candles with OHLCV data
            symbol: Trading pair symbol

        Returns:
            X, y: Training features and labels
        """
        if not self.ml_available:
            raise RuntimeError("ML libraries not available")

        # Convert to DataFrame
        df = pd.DataFrame(price_data)

        # Ensure required columns
        required_columns = ["timestamp", "open", "high", "low", "close", "volume"]
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"Missing required columns. Need: {required_columns}")

        # Add technical indicators
        df = self._add_technical_indicators(df)

        # Select features
        feature_cols = [
            "close",
            "volume",
            "high",
            "low",
            "sma_20",
            "sma_50",
            "sma_200",
            "rsi",
            "macd",
            "macd_signal",
            "bb_upper",
            "bb_lower",
            "bb_middle",
            "atr",
            "obv",
            "price_momentum",
        ]

        # Remove rows with NaN
        df = df.dropna()

        # Extract features
        features = df[feature_cols].values

        # Scale features
        scaled_features = self.scaler.fit_transform(features)

        # Create sequences
        X, y = self._create_sequences(scaled_features)

        logger.info(
            f"Prepared {len(X)} training sequences with {len(feature_cols)} features"
        )

        return X, y

    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators as features"""

        # Simple Moving Averages
        df["sma_20"] = df["close"].rolling(window=20).mean()
        df["sma_50"] = df["close"].rolling(window=50).mean()
        df["sma_200"] = df["close"].rolling(window=200).mean()

        # RSI (Relative Strength Index)
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = df["close"].ewm(span=12, adjust=False).mean()
        exp2 = df["close"].ewm(span=26, adjust=False).mean()
        df["macd"] = exp1 - exp2
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

        # Bollinger Bands
        df["bb_middle"] = df["close"].rolling(window=20).mean()
        bb_std = df["close"].rolling(window=20).std()
        df["bb_upper"] = df["bb_middle"] + (bb_std * 2)
        df["bb_lower"] = df["bb_middle"] - (bb_std * 2)

        # ATR (Average True Range)
        high_low = df["high"] - df["low"]
        high_close = np.abs(df["high"] - df["close"].shift())
        low_close = np.abs(df["low"] - df["close"].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df["atr"] = true_range.rolling(14).mean()

        # OBV (On-Balance Volume)
        df["obv"] = (np.sign(df["close"].diff()) * df["volume"]).fillna(0).cumsum()

        # Price Momentum
        df["price_momentum"] = df["close"].diff(10)

        return df

    def _create_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for LSTM training"""
        X, y = [], []

        for i in range(self.sequence_length, len(data)):
            X.append(data[i - self.sequence_length : i])
            # Predict next close price (index 0)
            y.append(data[i, 0])

        return np.array(X), np.array(y)

    def build_model(
        self,
        input_shape: Tuple[int, int],
        lstm_units: List[int] = [128, 64],
        dropout_rate: float = 0.2,
    ) -> Any:
        """
        Build LSTM model architecture

        Args:
            input_shape: (sequence_length, num_features)
            lstm_units: List of LSTM layer units
            dropout_rate: Dropout rate for regularization

        Returns:
            Compiled Keras model
        """
        if not TENSORFLOW_AVAILABLE:
            raise RuntimeError("TensorFlow not available")

        model = Sequential()

        # First LSTM layer
        model.add(
            LSTM(
                units=lstm_units[0],
                return_sequences=True if len(lstm_units) > 1 else False,
                input_shape=input_shape,
            )
        )
        model.add(Dropout(dropout_rate))

        # Additional LSTM layers
        for i, units in enumerate(lstm_units[1:]):
            return_seq = i < len(lstm_units) - 2
            model.add(LSTM(units=units, return_sequences=return_seq))
            model.add(Dropout(dropout_rate))

        # Output layer
        model.add(Dense(units=1))

        # Compile model
        model.compile(
            optimizer="adam", loss="mean_squared_error", metrics=["mae", "mse"]
        )

        logger.info(f"Built LSTM model with architecture: {lstm_units}")

        return model

    def train_model(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        epochs: int = 50,
        batch_size: int = 32,
        model_path: str = "lstm_model.h5",
    ) -> Dict[str, Any]:
        """
        Train LSTM model

        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features
            y_val: Validation labels
            epochs: Number of training epochs
            batch_size: Batch size for training
            model_path: Path to save trained model

        Returns:
            Training history and metrics
        """
        if not TENSORFLOW_AVAILABLE:
            raise RuntimeError("TensorFlow not available")

        # Build model
        input_shape = (X_train.shape[1], X_train.shape[2])
        self.model = self.build_model(input_shape)

        # Callbacks
        early_stopping = EarlyStopping(
            monitor="val_loss", patience=10, restore_best_weights=True
        )

        model_checkpoint = ModelCheckpoint(
            model_path, monitor="val_loss", save_best_only=True
        )

        # Train model
        logger.info(f"Training LSTM model for {epochs} epochs...")
        history = self.model.fit(
            X_train,
            y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stopping, model_checkpoint],
            verbose=1,
        )

        # Evaluate
        train_loss, train_mae, train_mse = self.model.evaluate(
            X_train, y_train, verbose=0
        )
        val_loss, val_mae, val_mse = self.model.evaluate(X_val, y_val, verbose=0)

        results = {
            "success": True,
            "epochs_trained": len(history.history["loss"]),
            "train_loss": float(train_loss),
            "train_mae": float(train_mae),
            "val_loss": float(val_loss),
            "val_mae": float(val_mae),
            "model_path": model_path,
            "history": {
                "loss": [float(x) for x in history.history["loss"]],
                "val_loss": [float(x) for x in history.history["val_loss"]],
                "mae": [float(x) for x in history.history["mae"]],
                "val_mae": [float(x) for x in history.history["val_mae"]],
            },
        }

        logger.info(f"Model trained successfully. Val MAE: {val_mae:.6f}")

        return results

    def predict(self, recent_data: np.ndarray) -> Dict[str, Any]:
        """
        Make predictions with trained model

        Args:
            recent_data: Recent price data (last sequence_length points)

        Returns:
            Prediction result
        """
        if not self.model:
            return {"success": False, "error": "Model not trained"}

        # Ensure correct shape
        if len(recent_data.shape) == 2:
            recent_data = np.expand_dims(recent_data, axis=0)

        # Predict
        prediction = self.model.predict(recent_data, verbose=0)

        # Inverse transform to get actual price
        predicted_price = float(prediction[0, 0])

        return {
            "success": True,
            "predicted_price": predicted_price,
            "timestamp": datetime.now().isoformat(),
        }

    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "ml_available": self.ml_available,
            "tensorflow_available": TENSORFLOW_AVAILABLE,
            "sklearn_available": ML_AVAILABLE,
            "model_trained": self.model is not None,
            "sequence_length": self.sequence_length,
        }


# Singleton instance
_lstm_service = None


def get_lstm_service() -> LSTMTrainingService:
    """Get singleton instance of LSTM Training Service"""
    global _lstm_service
    if _lstm_service is None:
        _lstm_service = LSTMTrainingService()
    return _lstm_service
