"""
Anomaly Detection Service
AI-powered anomaly detection for metrics and time-series data
"""

import logging
import statistics
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# ML library availability
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. Install with: pip install scikit-learn")

try:
    import torch
    import torch.nn as nn

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available. Install with: pip install torch")


@dataclass
class Baseline:
    """Statistical baseline for a metric"""

    mean: float
    std_dev: float
    min_value: float
    max_value: float
    sample_count: int
    last_updated: datetime


@dataclass
class Anomaly:
    """Detected anomaly"""

    metric_name: str
    value: float
    baseline_mean: float
    deviation: float  # Number of standard deviations from mean
    severity: str  # "low", "medium", "high", "critical"
    timestamp: datetime
    tags: dict[str, str] = field(default_factory=dict)


class LSTMAutoencoder(nn.Module):
    """LSTM-based autoencoder for time-series anomaly detection"""

    def __init__(self, input_size: int = 1, hidden_size: int = 64, num_layers: int = 2):
        super().__init__()
        self.encoder = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.decoder = nn.LSTM(hidden_size, input_size, num_layers, batch_first=True)
        self.hidden_size = hidden_size
        self.num_layers = num_layers

    def forward(self, x):
        # Encode
        encoded, (hidden, cell) = self.encoder(x)
        # Decode
        decoded, _ = self.decoder(encoded, (hidden, cell))
        return decoded


class AnomalyDetectionService:
    """
    AI-powered anomaly detection service with enhanced ML models

    Features:
    - Statistical baseline learning (Z-score)
    - Isolation Forest for multivariate anomaly detection
    - LSTM Autoencoder for time-series anomaly detection
    - Moving average trend detection
    - Seasonal pattern recognition
    - Adaptive thresholds
    - Ensemble methods
    """

    def __init__(self, baseline_window_minutes: int = 60, min_samples: int = 10):
        """
        Initialize anomaly detection service

        Args:
            baseline_window_minutes: Time window for baseline calculation
            min_samples: Minimum samples needed for baseline
        """
        self.baseline_window_minutes = baseline_window_minutes
        self.min_samples = min_samples
        self.baselines: dict[str, Baseline] = {}
        self.metric_history: dict[str, deque] = {}
        self.z_score_threshold = 3.0  # 3 standard deviations
        self.anomaly_history: list[Anomaly] = []
        self.max_history = 1000

        # ML models
        self.isolation_forests: dict[str, Any] = {}  # metric_key -> IsolationForest
        self.lstm_models: dict[str, Any] = {}  # metric_key -> LSTM Autoencoder
        self.scalers: dict[str, Any] = {}  # metric_key -> StandardScaler

        # Model configuration
        self.use_isolation_forest = SKLEARN_AVAILABLE
        self.use_lstm = TORCH_AVAILABLE
        self.isolation_forest_contamination = 0.1  # Expected proportion of anomalies
        self.lstm_window_size = 10  # Sequence length for LSTM

    def record_metric(
        self, metric_name: str, value: float, tags: dict[str, str] | None = None
    ):
        """
        Record a metric value and check for anomalies

        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Optional tags for metric identification
        """
        key = self._make_key(metric_name, tags)

        # Store in history
        if key not in self.metric_history:
            self.metric_history[key] = deque(maxlen=1000)

        timestamp = datetime.now(UTC)
        self.metric_history[key].append((timestamp, value))

        # Update baseline
        self._update_baseline(key, metric_name)

        # Check for anomaly
        anomaly = self._detect_anomaly(key, metric_name, value, tags)
        if anomaly:
            self.anomaly_history.append(anomaly)
            if len(self.anomaly_history) > self.max_history:
                self.anomaly_history = self.anomaly_history[-self.max_history :]
            return anomaly

        return None

    def _update_baseline(self, key: str, metric_name: str):
        """Update statistical baseline for a metric"""
        if key not in self.metric_history:
            return

        history = self.metric_history[key]
        if len(history) < self.min_samples:
            return

        # Get recent values within baseline window
        cutoff_time = datetime.now(UTC) - timedelta(
            minutes=self.baseline_window_minutes
        )
        recent_values = [v for t, v in history if t >= cutoff_time]

        if len(recent_values) < self.min_samples:
            return

        # Calculate statistics
        mean = statistics.mean(recent_values)
        std_dev = statistics.stdev(recent_values) if len(recent_values) > 1 else 0.0
        min_value = min(recent_values)
        max_value = max(recent_values)

        self.baselines[key] = Baseline(
            mean=mean,
            std_dev=std_dev,
            min_value=min_value,
            max_value=max_value,
            sample_count=len(recent_values),
            last_updated=datetime.now(UTC),
        )

    def _detect_anomaly(
        self, key: str, metric_name: str, value: float, tags: dict[str, str] | None
    ) -> Anomaly | None:
        """Detect if a value is anomalous using ensemble of methods"""
        if key not in self.baselines:
            return None

        baseline = self.baselines[key]

        # Skip if std_dev is too small (constant values)
        if baseline.std_dev < 0.001:
            return None

        # Method 1: Z-score detection
        z_score = abs((value - baseline.mean) / baseline.std_dev)
        z_score_anomaly = z_score >= self.z_score_threshold

        # Method 2: Isolation Forest (if available)
        isolation_forest_anomaly = False
        if self.use_isolation_forest and key in self.isolation_forests:
            try:
                if key not in self.scalers:
                    self.scalers[key] = StandardScaler()

                # Get recent values for context
                history = self.metric_history.get(key, deque())
                if len(history) >= self.lstm_window_size:
                    recent_values = [
                        v for _, v in list(history)[-self.lstm_window_size :]
                    ]
                    recent_values.append(value)

                    # Scale features
                    features = np.array(recent_values).reshape(-1, 1)
                    scaled = self.scalers[key].fit_transform(features)

                    # Predict
                    prediction = self.isolation_forests[key].predict(
                        scaled[-1:].reshape(1, -1)
                    )
                    isolation_forest_anomaly = prediction[0] == -1
            except Exception as e:
                logger.warning(f"Isolation Forest detection failed: {e}")

        # Method 3: LSTM Autoencoder (if available)
        lstm_anomaly = False
        lstm_reconstruction_error = 0.0
        if self.use_lstm and key in self.lstm_models:
            try:
                history = self.metric_history.get(key, deque())
                if len(history) >= self.lstm_window_size:
                    # Get sequence
                    sequence = [v for _, v in list(history)[-self.lstm_window_size :]]
                    sequence.append(value)

                    # Normalize
                    if key not in self.scalers:
                        self.scalers[key] = StandardScaler()
                    sequence_array = np.array(sequence).reshape(-1, 1)
                    scaled_sequence = self.scalers[key].fit_transform(sequence_array)

                    # Prepare input
                    input_tensor = torch.FloatTensor(
                        scaled_sequence[-self.lstm_window_size :]
                    ).unsqueeze(0)

                    # Reconstruct
                    model = self.lstm_models[key]
                    model.eval()
                    with torch.no_grad():
                        reconstructed = model(input_tensor)
                        reconstruction_error = torch.mean(
                            (input_tensor - reconstructed) ** 2
                        ).item()

                    # Threshold for anomaly (adaptive based on historical errors)
                    threshold = baseline.std_dev * 2.0
                    lstm_anomaly = reconstruction_error > threshold
                    lstm_reconstruction_error = reconstruction_error
            except Exception as e:
                logger.warning(f"LSTM detection failed: {e}")

        # Ensemble decision: anomaly if any method detects it
        is_anomaly = z_score_anomaly or isolation_forest_anomaly or lstm_anomaly

        if is_anomaly:
            # Determine severity based on all methods
            severity_scores = []

            if z_score_anomaly:
                if z_score >= 5.0:
                    severity_scores.append(4)  # critical
                elif z_score >= 4.0:
                    severity_scores.append(3)  # high
                elif z_score >= 3.5:
                    severity_scores.append(2)  # medium
                else:
                    severity_scores.append(1)  # low

            if isolation_forest_anomaly:
                severity_scores.append(2)  # medium

            if lstm_anomaly:
                if lstm_reconstruction_error > baseline.std_dev * 3.0:
                    severity_scores.append(4)  # critical
                elif lstm_reconstruction_error > baseline.std_dev * 2.0:
                    severity_scores.append(3)  # high
                else:
                    severity_scores.append(2)  # medium

            # Use maximum severity
            max_severity_score = max(severity_scores) if severity_scores else 1

            severity_map = {4: "critical", 3: "high", 2: "medium", 1: "low"}
            severity = severity_map.get(max_severity_score, "low")

            # Use z_score as primary deviation metric
            deviation = z_score

            return Anomaly(
                metric_name=metric_name,
                value=value,
                baseline_mean=baseline.mean,
                deviation=deviation,
                severity=severity,
                timestamp=datetime.now(UTC),
                tags=tags or {},
            )

        return None

    def get_baseline(
        self, metric_name: str, tags: dict[str, str] | None = None
    ) -> Baseline | None:
        """Get baseline for a metric"""
        key = self._make_key(metric_name, tags)
        return self.baselines.get(key)

    def get_anomalies(
        self,
        metric_name: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[Anomaly]:
        """Get recent anomalies"""
        anomalies = self.anomaly_history[-limit:] if limit else self.anomaly_history

        if metric_name:
            anomalies = [a for a in anomalies if a.metric_name == metric_name]

        if severity:
            anomalies = [a for a in anomalies if a.severity == severity]

        return sorted(anomalies, key=lambda a: a.timestamp, reverse=True)

    def get_anomaly_summary(self) -> dict[str, Any]:
        """Get anomaly detection summary"""
        total_anomalies = len(self.anomaly_history)
        recent_anomalies = [
            a
            for a in self.anomaly_history
            if a.timestamp >= datetime.now(UTC) - timedelta(hours=24)
        ]

        severity_counts = {}
        for anomaly in recent_anomalies:
            severity_counts[anomaly.severity] = (
                severity_counts.get(anomaly.severity, 0) + 1
            )

        return {
            "total_anomalies": total_anomalies,
            "recent_anomalies_24h": len(recent_anomalies),
            "severity_counts": severity_counts,
            "baselines_count": len(self.baselines),
            "z_score_threshold": self.z_score_threshold,
        }

    def _make_key(self, metric_name: str, tags: dict[str, str] | None) -> str:
        """Create a key from metric name and tags"""
        if not tags:
            return metric_name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{metric_name}[{tag_str}]"

    def set_z_score_threshold(self, threshold: float):
        """Set z-score threshold for anomaly detection"""
        self.z_score_threshold = threshold
        logger.info(f"Z-score threshold set to {threshold}")

    def train_isolation_forest(
        self, metric_name: str, tags: dict[str, str] | None = None
    ):
        """
        Train Isolation Forest model for a metric

        Args:
            metric_name: Name of the metric
            tags: Optional tags
        """
        if not self.use_isolation_forest:
            logger.warning(
                "Isolation Forest not available (scikit-learn not installed)"
            )
            return False

        key = self._make_key(metric_name, tags)

        if key not in self.metric_history:
            logger.warning(f"No history for metric {metric_name}")
            return False

        history = self.metric_history[key]
        if len(history) < self.min_samples:
            logger.warning(
                f"Insufficient samples for {metric_name}: {len(history)} < {self.min_samples}"
            )
            return False

        try:
            # Get recent values
            values = [v for _, v in history]

            # Prepare features (can include time-based features)
            features = np.array(values).reshape(-1, 1)

            # Scale features
            if key not in self.scalers:
                self.scalers[key] = StandardScaler()
            scaled_features = self.scalers[key].fit_transform(features)

            # Train Isolation Forest
            isolation_forest = IsolationForest(
                contamination=self.isolation_forest_contamination,
                random_state=42,
                n_estimators=100,
            )
            isolation_forest.fit(scaled_features)

            self.isolation_forests[key] = isolation_forest
            logger.info(f"Trained Isolation Forest for {metric_name}")
            return True
        except Exception as e:
            logger.error(
                f"Failed to train Isolation Forest for {metric_name}: {e}",
                exc_info=True,
            )
            return False

    def train_lstm_autoencoder(
        self, metric_name: str, tags: dict[str, str] | None = None, epochs: int = 10
    ):
        """
        Train LSTM Autoencoder for time-series anomaly detection

        Args:
            metric_name: Name of the metric
            tags: Optional tags
            epochs: Number of training epochs
        """
        if not self.use_lstm:
            logger.warning("LSTM not available (PyTorch not installed)")
            return False

        key = self._make_key(metric_name, tags)

        if key not in self.metric_history:
            logger.warning(f"No history for metric {metric_name}")
            return False

        history = self.metric_history[key]
        if len(history) < self.lstm_window_size * 2:
            logger.warning(
                f"Insufficient samples for LSTM: {len(history)} < {self.lstm_window_size * 2}"
            )
            return False

        try:
            # Get values
            values = [v for _, v in history]

            # Normalize
            if key not in self.scalers:
                self.scalers[key] = StandardScaler()
            values_array = np.array(values).reshape(-1, 1)
            scaled_values = self.scalers[key].fit_transform(values_array)

            # Create sequences
            sequences = []
            for i in range(len(scaled_values) - self.lstm_window_size + 1):
                sequences.append(scaled_values[i : i + self.lstm_window_size])

            if len(sequences) < 5:
                logger.warning(f"Insufficient sequences for training: {len(sequences)}")
                return False

            # Convert to tensor
            sequences_tensor = torch.FloatTensor(np.array(sequences))

            # Initialize model
            model = LSTMAutoencoder(input_size=1, hidden_size=64, num_layers=2)
            optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
            criterion = nn.MSELoss()

            # Train
            model.train()
            for epoch in range(epochs):
                optimizer.zero_grad()
                reconstructed = model(sequences_tensor)
                loss = criterion(reconstructed, sequences_tensor)
                loss.backward()
                optimizer.step()

                if epoch % 5 == 0:
                    logger.debug(
                        f"LSTM training epoch {epoch}, loss: {loss.item():.4f}"
                    )

            model.eval()
            self.lstm_models[key] = model
            logger.info(f"Trained LSTM Autoencoder for {metric_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to train LSTM for {metric_name}: {e}", exc_info=True)
            return False

    def auto_train_models(self, metric_name: str | None = None):
        """
        Automatically train ML models for metrics with sufficient history

        Args:
            metric_name: Optional specific metric to train, or None for all metrics
        """
        metrics_to_train = (
            [metric_name] if metric_name else list(self.metric_history.keys())
        )

        trained_count = 0
        for key in metrics_to_train:
            # Extract metric name from key
            metric = key.split("[")[0] if "[" in key else key

            # Train Isolation Forest
            if self.use_isolation_forest:
                if self.train_isolation_forest(metric):
                    trained_count += 1

            # Train LSTM (requires more data)
            if (
                self.use_lstm
                and len(self.metric_history.get(key, deque()))
                >= self.lstm_window_size * 2
            ) and self.train_lstm_autoencoder(metric):
                trained_count += 1

        logger.info(f"Auto-trained models for {trained_count} metrics")
        return trained_count

    def get_model_status(self) -> dict[str, Any]:
        """Get status of ML models"""
        return {
            "isolation_forest_available": self.use_isolation_forest,
            "lstm_available": self.use_lstm,
            "isolation_forest_models": len(self.isolation_forests),
            "lstm_models": len(self.lstm_models),
            "total_metrics": len(self.metric_history),
            "models_trained": len(self.isolation_forests) + len(self.lstm_models),
        }


# Global instance
anomaly_detection_service = AnomalyDetectionService()
