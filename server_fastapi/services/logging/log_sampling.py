"""
Log Sampling Service
Implements intelligent log sampling for high-volume endpoints to reduce log volume
while preserving important events (errors, security events, etc.).
"""

import logging
import os
import random
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class LogSamplingFilter(logging.Filter):
    """
    Filter that samples logs based on configuration.
    Always logs errors, warnings, and security events.
    Samples INFO and DEBUG logs based on sampling rate.
    """

    def __init__(
        self,
        sampling_rate: float = 1.0,
        always_log_levels: set[str] | None = None,
        endpoint_sampling_rates: dict[str, float] | None = None,
    ):
        """
        Initialize log sampling filter

        Args:
            sampling_rate: Base sampling rate (0.0-1.0), 1.0 = 100%
            always_log_levels: Log levels to always log (default: ERROR, WARNING, CRITICAL)
            endpoint_sampling_rates: Per-endpoint sampling rates override
        """
        super().__init__()
        self.sampling_rate = max(0.0, min(1.0, sampling_rate))
        self.always_log_levels = always_log_levels or {"ERROR", "WARNING", "CRITICAL"}
        self.endpoint_sampling_rates = endpoint_sampling_rates or {}

        # Track sampling decisions for monitoring
        self.sampled_count = 0
        self.total_count = 0

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Determine if log record should be logged based on sampling rules

        Returns:
            True if log should be recorded, False if it should be sampled out
        """
        self.total_count += 1

        # Always log errors, warnings, and critical events
        if record.levelname in self.always_log_levels:
            return True

        # Always log security events
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            if record.extra_data.get("event_type") == "security_event":
                return True

        # Check for endpoint-specific sampling rate
        endpoint = getattr(record, "endpoint", None)
        if endpoint and endpoint in self.endpoint_sampling_rates:
            sampling_rate = self.endpoint_sampling_rates[endpoint]
        else:
            sampling_rate = self.sampling_rate

        # Sample based on rate
        if random.random() < sampling_rate:
            return True

        # Log was sampled out
        self.sampled_count += 1
        return False

    def get_sampling_stats(self) -> dict[str, any]:
        """Get sampling statistics"""
        if self.total_count == 0:
            return {"sampled": 0, "total": 0, "rate": 0.0}

        return {
            "sampled": self.sampled_count,
            "total": self.total_count,
            "rate": self.sampled_count / self.total_count,
            "sampling_rate": self.sampling_rate,
        }


class AdaptiveLogSampler:
    """
    Adaptive log sampler that adjusts sampling rates based on log volume
    """

    def __init__(
        self,
        base_sampling_rate: float = 1.0,
        high_volume_threshold: int = 1000,  # logs per minute
        low_sampling_rate: float = 0.1,  # When volume is high
    ):
        self.base_sampling_rate = base_sampling_rate
        self.high_volume_threshold = high_volume_threshold
        self.low_sampling_rate = low_sampling_rate

        # Track log volume per endpoint
        self.endpoint_counts: dict[str, list] = defaultdict(list)
        self.current_sampling_rates: dict[str, float] = {}

    def should_sample(
        self, endpoint: str | None = None, log_level: str = "INFO"
    ) -> bool:
        """
        Determine if log should be sampled based on adaptive rules

        Args:
            endpoint: API endpoint path
            log_level: Log level (ERROR, WARNING, INFO, DEBUG)

        Returns:
            True if log should be recorded
        """
        # Always log errors and warnings
        if log_level in {"ERROR", "WARNING", "CRITICAL"}:
            return True

        # Update endpoint volume tracking
        if endpoint:
            now = datetime.utcnow()
            cutoff = now - timedelta(minutes=1)

            # Clean old entries
            self.endpoint_counts[endpoint] = [
                ts for ts in self.endpoint_counts[endpoint] if ts > cutoff
            ]

            # Add current log
            self.endpoint_counts[endpoint].append(now)

            # Calculate volume
            volume = len(self.endpoint_counts[endpoint])

            # Adjust sampling rate based on volume
            if volume > self.high_volume_threshold:
                sampling_rate = self.low_sampling_rate
            else:
                # Linear interpolation between base and low rate
                volume_ratio = volume / self.high_volume_threshold
                sampling_rate = self.base_sampling_rate - (
                    (self.base_sampling_rate - self.low_sampling_rate) * volume_ratio
                )

            self.current_sampling_rates[endpoint] = sampling_rate
        else:
            sampling_rate = self.base_sampling_rate

        # Sample based on rate
        return random.random() < sampling_rate

    def get_sampling_rates(self) -> dict[str, float]:
        """Get current sampling rates for all endpoints"""
        return self.current_sampling_rates.copy()


def get_sampling_config() -> dict[str, any]:
    """
    Get log sampling configuration from environment variables

    Returns:
        Configuration dictionary with sampling settings
    """
    return {
        "base_sampling_rate": float(os.getenv("LOG_SAMPLING_RATE", "1.0")),
        "high_volume_endpoints": {
            "/api/markets/": float(os.getenv("LOG_SAMPLING_RATE_MARKETS", "0.1")),
            "/api/dex/quote": float(os.getenv("LOG_SAMPLING_RATE_DEX_QUOTE", "0.2")),
            "/api/health": float(os.getenv("LOG_SAMPLING_RATE_HEALTH", "0.01")),
        },
        "always_log": {
            "levels": {"ERROR", "WARNING", "CRITICAL"},
            "event_types": {"security_event", "audit_event", "risk_event"},
        },
    }
