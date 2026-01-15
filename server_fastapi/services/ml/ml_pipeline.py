"""
ML Pipeline - Data loader, windowing, normalization, and trainer service (Polars Edition 2026)
"""

import hashlib
import logging
from typing import Any, Literal

import numpy as np
import polars as pl
from pydantic import BaseModel

try:
    from sklearn.model_selection import TimeSeriesSplit

    # We handle split manually or use sklearn if absolutely needed for non-pandas ops
    from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler

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
    """Machine Learning Pipeline for data processing and training (Polars Optimized)"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = PipelineConfig(**(config or {}))
        self.scaler = None
        self.feature_names: list[str] = ["open", "high", "low", "close", "volume"]

    def load_data(self, market_data: list[MarketData]) -> pl.DataFrame:
        """Load market data into Polars DataFrame"""
        # Polars reads dicts very fast
        data = [d.model_dump() for d in market_data]
        df = pl.DataFrame(data)

        # Ensure correct types and sort
        df = df.with_columns(
            [
                pl.col("timestamp").cast(pl.Int64),
                pl.col("open").cast(pl.Float64),
                pl.col("high").cast(pl.Float64),
                pl.col("low").cast(pl.Float64),
                pl.col("close").cast(pl.Float64),
                pl.col("volume").cast(pl.Float64),
            ]
        ).sort("timestamp")

        return df

    def create_technical_indicators(self, df: pl.DataFrame) -> pl.DataFrame:
        """Add technical indicators to the dataframe using Polars Expressions"""

        # Moving averages
        df = df.with_columns(
            [
                pl.col("close").rolling_mean(window_size=5).alias("sma_5"),
                pl.col("close").rolling_mean(window_size=10).alias("sma_10"),
                pl.col("close").rolling_mean(window_size=20).alias("sma_20"),
            ]
        )

        # EMAs (Polars ewm_mean is available in recent versions, if not, we use pandas-like approximation or extension plugin)
        # For simplicity and perf in standard Polars, we use ewm_mean if available or skip if complex.
        # Assuming modern Polars:
        df = df.with_columns(
            [
                pl.col("close").ewm_mean(span=12, adjust=False).alias("ema_12"),
                pl.col("close").ewm_mean(span=26, adjust=False).alias("ema_26"),
            ]
        )

        # MACD
        df = df.with_columns([(pl.col("ema_12") - pl.col("ema_26")).alias("macd")])

        df = df.with_columns(
            [pl.col("macd").ewm_mean(span=9, adjust=False).alias("macd_signal")]
        )

        df = df.with_columns(
            [(pl.col("macd") - pl.col("macd_signal")).alias("macd_hist")]
        )

        # RSI (14)
        # RSI calculation in Polars requires a bit of expression chaining
        delta = pl.col("close").diff()
        gain = delta.clip(lower_bound=0)
        loss = delta.clip(upper_bound=0).abs()

        avg_gain = gain.rolling_mean(window_size=14)
        avg_loss = loss.rolling_mean(window_size=14)

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        df = df.with_columns(rsi.alias("rsi"))

        # Bollinger Bands
        # middle = sma_20
        # std = rolling_std_20
        df = df.with_columns(
            [
                pl.col("close").rolling_mean(window_size=20).alias("bb_middle"),
                pl.col("close").rolling_std(window_size=20).alias("bb_std"),
            ]
        )

        df = df.with_columns(
            [
                (pl.col("bb_middle") + (pl.col("bb_std") * 2)).alias("bb_upper"),
                (pl.col("bb_middle") - (pl.col("bb_std") * 2)).alias("bb_lower"),
            ]
        )

        df = df.with_columns(
            [(pl.col("bb_upper") - pl.col("bb_lower")).alias("bb_width")]
        )

        # Volume
        df = df.with_columns(
            [pl.col("volume").rolling_mean(window_size=20).alias("volume_sma")]
        )

        df = df.with_columns(
            [(pl.col("volume") / pl.col("volume_sma")).alias("volume_ratio")]
        )

        # Price Changes
        df = df.with_columns(
            [
                pl.col("close").pct_change(n=1).alias("price_change"),
                pl.col("close").pct_change(n=5).alias("price_change_5"),
                pl.col("close").pct_change(n=20).alias("price_change_20"),
            ]
        )

        # Volatility
        df = df.with_columns(
            [pl.col("price_change").rolling_std(window_size=20).alias("volatility")]
        )

        # Fill Nulls (bfill equivalent in polars is backward fill)
        df = df.fill_null(strategy="backward").fill_null(0)

        return df

    def normalize_features(self, df: pl.DataFrame, fit: bool = True) -> pl.DataFrame:
        """Normalize features. Note: Scikit-learn expects numpy/pandas. We convert back and forth or use Polars ops."""
        if self.config.normalization == "none":
            return df

        # Filter numeric columns excluding timestamp
        numeric_cols = [
            c
            for c in df.columns
            if c not in ["timestamp", "date"]
            and df[c].dtype in [pl.Float64, pl.Float32, pl.Int64]
        ]

        if not numeric_cols:
            return df

        # For simplicity and robustness with Sklearn, we convert selected cols to numpy
        # In a pure Polars pipeline we would do (col - min) / (max - min) manually

        # Manual MinMax for performance (Pure Polars)
        if self.config.normalization == "minmax":
            # We can calculate min/max per column
            # But supporting stateful scaling (fit vs transform) usually requires storing the params
            # Here we fallback to sklearn for "fit/transform" semantics if `self.scaler` is used.
            pass

        # If we rely on sklearn:
        if SKLEARN_AVAILABLE:
            # Polars -> Numpy
            np_data = df.select(numeric_cols).to_numpy()

            if self.scaler is None or fit:
                if self.config.normalization == "minmax":
                    self.scaler = MinMaxScaler()
                elif self.config.normalization == "standard":
                    self.scaler = StandardScaler()
                elif self.config.normalization == "robust":
                    self.scaler = RobustScaler()

                if fit and self.scaler:
                    normalized_data = self.scaler.fit_transform(np_data)
            else:
                normalized_data = self.scaler.transform(np_data)

            # Reconstruct Polars DF
            # This is efficient enough for batch training
            normalized_dict = {}
            for idx, col in enumerate(numeric_cols):
                normalized_dict[col] = normalized_data[:, idx]

            # Replace columns in original DF
            # we drop the old ones and attach new ones, keeping timestamp
            timestamps = df.select("timestamp")

            # Add validated columns back
            # simplest is to create new DF from dict and hstack timestamp
            new_df_main = pl.DataFrame(normalized_dict)
            final_df = pl.concat([timestamps, new_df_main], how="horizontal")
            return final_df

        return df

    def create_sequences(
        self,
        df: pl.DataFrame,
        feature_cols: list[str] | None = None,
        label_col: str | None = None,
    ) -> tuple[np.ndarray, np.ndarray | None]:
        """Create sequences (numpy) from Polars DataFrame"""
        if feature_cols is None:
            feature_cols = [col for col in df.columns if col != "timestamp"]

        # Convert to numpy for slicing
        features = df.select(feature_cols).to_numpy()

        # If label column exists, get it
        if label_col and label_col in df.columns:
            prices = df.select(label_col).to_numpy().flatten()
        else:
            prices = None

        X, y = [], []

        # Vectorization of sliding window is possible but complex for "labels based on future"
        # We stick to the loop for logic parity, but optimize if needed.
        # Ideally: usage of `rolling` in Polars?
        # For sequence generation for Torch/TF, strict ndarray output is needed anyway.

        total_len = len(features)
        seq_len = self.config.sequence_length
        pred_hor = self.config.prediction_horizon

        limit = total_len - seq_len - pred_hor + 1

        for i in range(limit):
            X.append(features[i : i + seq_len])

            if self.config.create_labels and prices is not None:
                future_idx = i + seq_len + pred_hor - 1
                if future_idx < total_len:
                    current_price = prices[i + seq_len - 1]
                    future_price = prices[future_idx]

                    if current_price != 0:
                        change = (future_price - current_price) / current_price
                        if change > 0.01:
                            label = 1
                        elif change < -0.01:
                            label = 2
                        else:
                            label = 0
                    else:
                        label = 0
                    y.append(label)
                else:
                    y.append(0)

        X = np.array(X)
        if y:
            y = np.array(y)
            return X, y
        return X, None

    def split_data(
        self,
        X: np.ndarray,
        y: np.ndarray | None = None,
        method: Literal["sequential", "random", "timeseries"] = "sequential",
    ) -> tuple[
        np.ndarray,
        np.ndarray | None,
        np.ndarray,
        np.ndarray | None,
        np.ndarray,
        np.ndarray | None,
    ]:
        """
        Split Numpy Arrays.
        Since X/y are already numpy from `create_sequences`, logic is identical to previous version.
        """
        n_samples = len(X)

        if method in ["sequential", "timeseries"]:
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
            # Random split using sklearn
            # (See original logic, adapted slightly for clarity)
            # Logic is complex to replicate without sklearn if banned, but SKLEARN_AVAILABLE check handles it.
            # We assume sklearn is permitted for SPLITTING/SCALING only, but DataFrame ops must be Polars.

            # ... (Same logic as before, omitted for brevity as it works on numpy arrays)
            # Re-implementing simplified version:
            indices = np.arange(n_samples)
            np.random.shuffle(indices)

            train_idx = int(n_samples * self.config.train_split)
            val_idx = int(n_samples * (self.config.train_split + self.config.val_split))

            train_indices = indices[:train_idx]
            val_indices = indices[train_idx:val_idx]
            test_indices = indices[val_idx:]

            X_train, X_val, X_test = X[train_indices], X[val_indices], X[test_indices]
            if y is not None:
                y_train, y_val, y_test = (
                    y[train_indices],
                    y[val_indices],
                    y[test_indices],
                )
            else:
                y_train = y_val = y_test = None
        else:
            # Fallback to sequential
            return self.split_data(X, y, "sequential")

        return X_train, y_train, X_val, y_val, X_test, y_test

    def get_dataset_hash(self, X: np.ndarray, y: np.ndarray | None = None) -> str:
        data_to_hash = [X.tobytes()]
        if y is not None:
            data_to_hash.append(y.tobytes())

        m = hashlib.sha256()
        for d in data_to_hash:
            m.update(d)
        return m.hexdigest()

    def process_data(
        self, market_data: list[MarketData], create_labels: bool = True
    ) -> dict[str, Any]:
        """Complete data processing pipeline (Polars-based)"""
        # Load (Polars)
        df = self.load_data(market_data)

        # Indicators (Polars)
        df = self.create_technical_indicators(df)

        # Normalize (Polars -> Numpy -> Polars)
        df = self.normalize_features(df, fit=True)

        # Sequences (Polars -> Numpy)
        X, y = self.create_sequences(df, label_col="close" if create_labels else None)

        # Split (Numpy)
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
        return 5 + 20


import logging
from typing import Any, Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel

try:
    from sklearn.model_selection import TimeSeriesSplit, train_test_split
    from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler

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

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = PipelineConfig(**(config or {}))
        self.scaler = None
        self.feature_names: list[str] = ["open", "high", "low", "close", "volume"]

    def load_data(self, market_data: list[MarketData]) -> pd.DataFrame:
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
        feature_cols: list[str] | None = None,
        label_col: str | None = None,
    ) -> tuple[np.ndarray, np.ndarray | None]:
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
        y: np.ndarray | None = None,
        method: Literal["sequential", "random", "timeseries"] = "sequential",
    ) -> tuple[
        np.ndarray,
        np.ndarray | None,
        np.ndarray,
        np.ndarray | None,
        np.ndarray,
        np.ndarray | None,
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

    def get_dataset_hash(self, X: np.ndarray, y: np.ndarray | None = None) -> str:
        """
        Generate a stable hash for a dataset.
        Useful for auditing what data was used for training/inference.
        """
        data_to_hash = [X.tobytes()]
        if y is not None:
            data_to_hash.append(y.tobytes())

        m = hashlib.sha256()
        for d in data_to_hash:
            m.update(d)
        return m.hexdigest()

    def process_data(
        self, market_data: list[MarketData], create_labels: bool = True
    ) -> dict[str, Any]:
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
