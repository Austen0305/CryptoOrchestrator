"""
Log Aggregation Service
Prepares logs for centralized aggregation systems (ELK stack, CloudWatch, etc.).
Supports multiple output formats and transport mechanisms.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class LogAggregator:
    """
    Service for aggregating and forwarding logs to centralized systems
    """

    def __init__(
        self,
        aggregation_enabled: bool = False,
        aggregation_type: str = "file",  # "file", "stdout", "http", "kafka"
        aggregation_endpoint: str | None = None,
    ):
        """
        Initialize log aggregator

        Args:
            aggregation_enabled: Enable log aggregation
            aggregation_type: Type of aggregation ("file", "stdout", "http", "kafka")
            aggregation_endpoint: Endpoint URL for HTTP/Kafka aggregation
        """
        self.aggregation_enabled = aggregation_enabled
        self.aggregation_type = aggregation_type
        self.aggregation_endpoint = aggregation_endpoint

        # Buffer for batch aggregation
        self.log_buffer: list[dict[str, Any]] = []
        self.buffer_size = int(os.getenv("LOG_AGGREGATION_BUFFER_SIZE", "100"))
        self.buffer_timeout = float(os.getenv("LOG_AGGREGATION_BUFFER_TIMEOUT", "5.0"))

    def aggregate_log(
        self, log_entry: dict[str, Any], flush_immediately: bool = False
    ) -> bool:
        """
        Aggregate a log entry for centralized logging

        Args:
            log_entry: Structured log entry dictionary
            flush_immediately: Force immediate flush (for errors)

        Returns:
            True if log was aggregated successfully
        """
        if not self.aggregation_enabled:
            return False

        try:
            # Add metadata for aggregation
            enriched_entry = self._enrich_log_entry(log_entry)

            # Add to buffer
            self.log_buffer.append(enriched_entry)

            # Flush if buffer is full or immediate flush requested
            if len(self.log_buffer) >= self.buffer_size or flush_immediately:
                return self._flush_buffer()

            return True

        except Exception as e:
            logger.error(f"Error aggregating log: {e}", exc_info=True)
            return False

    def _enrich_log_entry(self, log_entry: dict[str, Any]) -> dict[str, Any]:
        """Enrich log entry with aggregation metadata"""
        enriched = log_entry.copy()

        # Add service metadata
        enriched["service"] = {
            "name": os.getenv("SERVICE_NAME", "cryptoorchestrator"),
            "version": os.getenv("SERVICE_VERSION", "1.0.0"),
            "environment": os.getenv("NODE_ENV", "development"),
            "host": os.getenv("HOSTNAME", "unknown"),
            "instance_id": os.getenv("INSTANCE_ID", "unknown"),
        }

        # Add aggregation metadata
        enriched["@timestamp"] = datetime.utcnow().isoformat() + "Z"
        enriched["aggregation_type"] = self.aggregation_type

        return enriched

    def _flush_buffer(self) -> bool:
        """Flush log buffer to aggregation system"""
        if not self.log_buffer:
            return True

        try:
            if self.aggregation_type == "file":
                return self._flush_to_file()
            elif self.aggregation_type == "stdout":
                return self._flush_to_stdout()
            elif self.aggregation_type == "http":
                return self._flush_to_http()
            elif self.aggregation_type == "kafka":
                return self._flush_to_kafka()
            else:
                logger.warning(f"Unknown aggregation type: {self.aggregation_type}")
                return False

        except Exception as e:
            logger.error(f"Error flushing log buffer: {e}", exc_info=True)
            return False

        finally:
            self.log_buffer.clear()

    def _flush_to_file(self) -> bool:
        """Flush logs to file (for filebeat or similar)"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        aggregation_file = log_dir / "aggregation.log"

        try:
            with open(aggregation_file, "a", encoding="utf-8") as f:
                for entry in self.log_buffer:
                    f.write(json.dumps(entry) + "\n")
            return True
        except Exception as e:
            logger.error(f"Error writing to aggregation file: {e}")
            return False

    def _flush_to_stdout(self) -> bool:
        """Flush logs to stdout (for Docker/Kubernetes log collection)"""
        try:
            import sys

            for entry in self.log_buffer:
                print(json.dumps(entry), file=sys.stdout, flush=True)
            return True
        except Exception as e:
            logger.error(f"Error writing to stdout: {e}")
            return False

    def _flush_to_http(self) -> bool:
        """Flush logs to HTTP endpoint (ELK HTTP input, CloudWatch, etc.)"""
        if not self.aggregation_endpoint:
            logger.warning("HTTP aggregation endpoint not configured")
            return False

        try:
            import httpx

            # Send logs in batches
            with httpx.Client(timeout=5.0) as client:
                response = client.post(
                    self.aggregation_endpoint,
                    json={"logs": self.log_buffer},
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error sending logs to HTTP endpoint: {e}")
            return False

    def _flush_to_kafka(self) -> bool:
        """Flush logs to Kafka (for high-volume log streaming)"""
        if not self.aggregation_endpoint:
            logger.warning("Kafka endpoint not configured")
            return False

        try:
            # Kafka integration would require kafka-python or confluent-kafka
            # This is a placeholder for future implementation
            logger.warning("Kafka aggregation not yet implemented")
            return False
        except Exception as e:
            logger.error(f"Error sending logs to Kafka: {e}")
            return False

    def flush(self) -> bool:
        """Manually flush the log buffer"""
        return self._flush_buffer()


def get_log_aggregator() -> LogAggregator:
    """Get singleton log aggregator instance"""
    if not hasattr(get_log_aggregator, "_instance"):
        aggregation_enabled = (
            os.getenv("LOG_AGGREGATION_ENABLED", "false").lower() == "true"
        )
        aggregation_type = os.getenv("LOG_AGGREGATION_TYPE", "file")
        aggregation_endpoint = os.getenv("LOG_AGGREGATION_ENDPOINT")

        get_log_aggregator._instance = LogAggregator(
            aggregation_enabled=aggregation_enabled,
            aggregation_type=aggregation_type,
            aggregation_endpoint=aggregation_endpoint,
        )
    return get_log_aggregator._instance
