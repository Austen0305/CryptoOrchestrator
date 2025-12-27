"""
Comprehensive Logging Aggregation
Provides centralized logging aggregation and analysis
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum

logger = logging.getLogger(__name__)


class LogLevel(str, Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogAggregator:
    """
    Log aggregation system
    
    Features:
    - Centralized log collection
    - Log analysis
    - Error pattern detection
    - Log statistics
    - Search and filtering
    - Export capabilities
    """

    def __init__(self, max_logs: int = 100000):
        self.logs: deque = deque(maxlen=max_logs)
        self.log_stats: Dict[str, Any] = defaultdict(int)
        self.error_patterns: Dict[str, int] = defaultdict(int)
        self.log_by_level: Dict[LogLevel, deque] = {
            level: deque(maxlen=10000) for level in LogLevel
        }

    def add_log(
        self,
        level: LogLevel,
        message: str,
        source: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Add a log entry"""
        log_entry = {
            "level": level.value,
            "message": message,
            "source": source,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

        self.logs.append(log_entry)
        self.log_by_level[level].append(log_entry)
        self.log_stats[level.value] += 1

        # Detect error patterns
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            pattern = self._extract_error_pattern(message)
            if pattern:
                self.error_patterns[pattern] += 1

    def _extract_error_pattern(self, message: str) -> Optional[str]:
        """Extract error pattern from message"""
        # Extract common error patterns
        patterns = [
            r"(\w+Error):",
            r"(\w+Exception):",
            r"HTTP (\d{3})",
            r"Connection (?:refused|timeout|error)",
        ]

        import re
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(0)

        return None

    def get_logs(
        self,
        level: Optional[LogLevel] = None,
        source: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Get logs with filtering"""
        logs = list(self.logs)

        if level:
            logs = [log for log in logs if log["level"] == level.value]

        if source:
            logs = [log for log in logs if log["source"] == source]

        if start_time:
            logs = [
                log
                for log in logs
                if datetime.fromisoformat(log["timestamp"]) >= start_time
            ]

        if end_time:
            logs = [
                log
                for log in logs
                if datetime.fromisoformat(log["timestamp"]) <= end_time
            ]

        logs.sort(key=lambda x: x["timestamp"], reverse=True)
        return logs[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get logging statistics"""
        total_logs = len(self.logs)
        recent_logs = [
            log
            for log in self.logs
            if datetime.fromisoformat(log["timestamp"])
            > datetime.utcnow() - timedelta(hours=1)
        ]

        return {
            "total_logs": total_logs,
            "recent_logs_1h": len(recent_logs),
            "by_level": dict(self.log_stats),
            "error_patterns": dict(self.error_patterns),
            "top_errors": sorted(
                self.error_patterns.items(), key=lambda x: x[1], reverse=True
            )[:10],
        }

    def search_logs(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Search logs by query"""
        results = []
        query_lower = query.lower()

        for log in self.logs:
            if (
                query_lower in log["message"].lower()
                or query_lower in log.get("source", "").lower()
            ):
                results.append(log)
                if len(results) >= limit:
                    break

        return results

    def export_logs(
        self,
        format: str = "json",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> str:
        """Export logs"""
        logs = self.get_logs(start_time=start_time, end_time=end_time, limit=100000)

        if format == "json":
            return json.dumps(logs, indent=2)
        elif format == "csv":
            import csv
            import io

            output = io.StringIO()
            writer = csv.DictWriter(
                output, fieldnames=["timestamp", "level", "source", "message"]
            )
            writer.writeheader()
            for log in logs:
                writer.writerow({
                    "timestamp": log["timestamp"],
                    "level": log["level"],
                    "source": log["source"],
                    "message": log["message"],
                })
            return output.getvalue()
        else:
            # Plain text
            lines = []
            for log in logs:
                lines.append(
                    f"[{log['timestamp']}] {log['level']} {log['source']}: {log['message']}"
                )
            return "\n".join(lines)


# Custom logging handler
class AggregatingHandler(logging.Handler):
    """Logging handler that aggregates logs"""

    def __init__(self, aggregator: LogAggregator):
        super().__init__()
        self.aggregator = aggregator

    def emit(self, record):
        """Emit log record to aggregator"""
        try:
            level_map = {
                logging.DEBUG: LogLevel.DEBUG,
                logging.INFO: LogLevel.INFO,
                logging.WARNING: LogLevel.WARNING,
                logging.ERROR: LogLevel.ERROR,
                logging.CRITICAL: LogLevel.CRITICAL,
            }

            level = level_map.get(record.levelno, LogLevel.INFO)
            self.aggregator.add_log(
                level=level,
                message=record.getMessage(),
                source=record.name,
                metadata={
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno,
                },
            )
        except Exception:
            pass  # Don't break logging if aggregation fails


# Global log aggregator
log_aggregator = LogAggregator()

# Add handler to root logger
root_logger = logging.getLogger()
aggregating_handler = AggregatingHandler(log_aggregator)
aggregating_handler.setLevel(logging.INFO)
root_logger.addHandler(aggregating_handler)

