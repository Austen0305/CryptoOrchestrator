"""
ML Pipeline - Data loader, windowing, normalization, and trainer service
"""

from typing import List, Dict, Any, Optional, Tuple, Literal
from pydantic import BaseModel
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

try:
    from sklearn.preprocessing import MinMaxScaler, StandardScaler, RobustScaler
    from sklearn.model_selection import train_test_split, TimeSeriesSplit

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn unavailable; ML pipeline preprocessing may fail.")

logger = logging.getLogger(__name__)


class PipelineConfig(BaseModel):
    """ML Pipeline configuration"""

    sequence_length: int = 60  # Lookback window
    prediction_horizon: int = 1  # Steps ahead to predict
    train_split: float = 0.8  # Training set fraction
    val_split: float = 0.1  # Validation set fraction
    test_split: float = 0.1  # Test set fraction
    normalization: Literal["minmax", "standard", "robust", "none"] = "minmax"
    shuffle: bool = False  # Don't shuffle time-series data
    create_labels: bool = True  # Create labels from future prices


class MarketData(BaseModel):
    """Market data point"""

    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class MLPipeline:
    """Machine Learning Pipeline for data processing and training"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = PipelineConfig(**(config or {}))
        self.scaler = None
        self.feature_names: List[str] = ["open", "high", "low", "close", "volume"]

    def load_data(self, market_data: List[MarketData]) -> pd.DataFrame:
        """Load market data into pandas DataFrame"""
        data = {
            "timestamp": [d.timestamp for d in market_data],
            "open": [d.open for d in market_data],
            "high": [d.high for d in market_data],
            "low": [d.low for d in market_data],
            "close": [d.close for d in market_data],
            "volume": [d.volume for d in market_data],
        }

        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", errors="coerce")
        df = df.sort_values("timestamp").reset_index(drop=True)

        return df

    def create_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to the dataframe"""
        # Moving averages
        df["sma_5"] = df["close"].rolling(window=5).mean()
        df["sma_10"] = df["close"].rolling(window=10).mean()
        df["sma_20"] = df["close"].rolling(window=20).mean()
        df["ema_12"] = df["close"].ewm(span=12, adjust=False).mean()
        df["ema_26"] = df["close"].ewm(span=26, adjust=False).mean()

        # MACD
        df["macd"] = df["ema_12"] - df["ema_26"]
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        # RSI
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))

        # Bollinger Bands
        df["bb_middle"] = df["close"].rolling(window=20).mean()
        bb_std = df["close"].rolling(window=20).std()
        df["bb_upper"] = df["bb_middle"] + (bb_std * 2)
        df["bb_lower"] = df["bb_middle"] - (bb_std * 2)
        df["bb_width"] = df["bb_upper"] - df["bb_lower"]

        # ATR
        high_low = df["high"] - df["low"]
        high_close = np.abs(df["high"] - df["close"].shift())
        low_close = np.abs(df["low"] - df["close"].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df["atr"] = tr.rolling(window=14).mean()

        # Volume indicators
        df["volume_sma"] = df["volume"].rolling(window=20).mean()
        df["volume_ratio"] = df["volume"] / df["volume_sma"]

        # Price changes
        df["price_change"] = df["close"].pct_change()
        df["price_change_5"] = df["close"].pct_change(5)
        df["price_change_20"] = df["close"].pct_change(20)

        # Volatility
        df["volatility"] = df["price_change"].rolling(window=20).std()

        # Fill NaN values
        df = df.bfill().fillna(0)

        return df

    def normalize_features(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """Normalize features in the dataframe"""
        if self.config.normalization == "none":
            return df

        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available, skipping normalization")
            return df

        # Select numeric columns to normalize
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        numeric_cols = [col for col in numeric_cols if col != "timestamp"]

        if len(numeric_cols) == 0:
            return df

        # Initialize scaler if needed
        if self.scaler is None or fit:
            if self.config.normalization == "minmax":
                self.scaler = MinMaxScaler()
            elif self.config.normalization == "standard":
                self.scaler = StandardScaler()
            elif self.config.normalization == "robust":
                self.scaler = RobustScaler()

            if fit:
                df[numeric_cols] = self.scaler.fit_transform(df[numeric_cols])
        else:
            df[numeric_cols] = self.scaler.transform(df[numeric_cols])

        return df

    def create_sequences(
        self,
        df: pd.DataFrame,
        feature_cols: Optional[List[str]] = None,
        label_col: Optional[str] = None,
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Create sequences from time-series data"""
        if feature_cols is None:
            # Use all numeric columns except timestamp
            feature_cols = [col for col in df.columns if col != "timestamp"]

        features = df[feature_cols].values

        X, y = [], []

        for i in range(
            len(features)
            - self.config.sequence_length
            - self.config.prediction_horizon
            + 1
        ):
            # Extract sequence
            X.append(features[i : i + self.config.sequence_length])

            # Extract label (future price movement)
            if label_col and self.config.create_labels:
                future_idx = (
                    i + self.config.sequence_length + self.config.prediction_horizon - 1
                )
                if future_idx < len(df):
                    current_price = df.iloc[i + self.config.sequence_length - 1][
                        "close"
                    ]
                    future_price = df.iloc[future_idx]["close"]

                    # Create label: buy (1), sell (2), hold (0)
                    if current_price != 0:
                        price_change = (future_price - current_price) / current_price
                        if price_change > 0.01:  # > 1% increase
                            label = 1  # buy
                        elif price_change < -0.01:  # < -1% decrease
                            label = 2  # sell
                        else:
                            label = 0  # hold
                    else:
                        label = 0  # hold as default

                    y.append(label)
                else:
                    y.append(0)  # hold as default

        X = np.array(X)
        if y:
            y = np.array(y)
            return X, y
        return X, None

    def split_data(
        self,
        X: np.ndarray,
        y: Optional[np.ndarray] = None,
        method: Literal["sequential", "random", "timeseries"] = "sequential",
    ) -> Tuple[
        np.ndarray,
        Optional[np.ndarray],
        np.ndarray,
        Optional[np.ndarray],
        np.ndarray,
        Optional[np.ndarray],
    ]:
        """Split data into train/validation/test sets"""
        n_samples = len(X)

        if method == "sequential" or method == "timeseries":
            # Sequential split for time-series
            train_size = int(n_samples * self.config.train_split)
            val_size = int(n_samples * self.config.val_split)

            X_train = X[:train_size]
            X_val = X[train_size : train_size + val_size]
            X_test = X[train_size + val_size :]

            if y is not None:
                y_train = y[:train_size]
                y_val = y[train_size : train_size + val_size]
                y_test = y[train_size + val_size :]
            else:
                y_train = y_val = y_test = None

        elif method == "random" and SKLEARN_AVAILABLE:
            # Random split
            X_train, X_temp, y_train, y_temp = train_test_split(
                X,
                y,
                test_size=(1 - self.config.train_split),
                shuffle=self.config.shuffle,
                random_state=42,
            )

            val_size_adj = self.config.val_split / (1 - self.config.train_split)
            X_val, X_test, y_val, y_test = train_test_split(
                X_temp,
                y_temp,
                test_size=(1 - val_size_adj),
                shuffle=self.config.shuffle,
                random_state=42,
            )

        else:
            raise ValueError(f"Unsupported split method: {method}")

        return X_train, y_train, X_val, y_val, X_test, y_test

    def process_data(
        self, market_data: List[MarketData], create_labels: bool = True
    ) -> Dict[str, Any]:
        """Complete data processing pipeline"""
        # Load data
        df = self.load_data(market_data)

        # Create technical indicators
        df = self.create_technical_indicators(df)

        # Normalize features
        df = self.normalize_features(df, fit=True)

        # Create sequences
        X, y = self.create_sequences(df, label_col="close" if create_labels else None)

        # Split data
        X_train, y_train, X_val, y_val, X_test, y_test = self.split_data(X, y)

        return {
            "X_train": X_train,
            "y_train": y_train,
            "X_val": X_val,
            "y_val": y_val,
            "X_test": X_test,
            "y_test": y_test,
            "feature_names": [col for col in df.columns if col != "timestamp"],
            "scaler": self.scaler,
        }

    def get_feature_count(self) -> int:
        """Get the number of features after adding technical indicators"""
        # Base features + technical indicators
        return 5 + 20  # OHLCV + technical indicators (approximate)
