"""
Comprehensive Logging Configuration
Structured logging with proper formatting and handlers
"""

import logging
import logging.handlers
import os
import json
from pathlib import Path
from typing import Optional
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "ip_address"):
            log_data["ip_address"] = record.ip_address

        return json.dumps(log_data, default=str)


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "text",
    log_dir: str = "./logs",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 14,
) -> None:
    """
    Setup comprehensive logging configuration

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ('text' or 'json')
        log_dir: Directory for log files
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
    """
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatters
    if log_format == "json":
        formatter = StructuredFormatter()
        text_formatter = None
    else:
        text_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        formatter = None

    # Console handler (always text for readability)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        text_formatter
        or logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root_logger.addHandler(console_handler)

    # File handlers with rotation
    # Application log
    app_log_file = log_path / "app.log"
    app_handler = logging.handlers.RotatingFileHandler(
        app_log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8", delay=True
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(formatter or text_formatter)
    root_logger.addHandler(app_handler)

    # Error log
    error_log_file = log_path / "error.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8", delay=True
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter or text_formatter)
    root_logger.addHandler(error_handler)

    # Audit log
    audit_log_file = log_path / "audit.log"
    audit_handler = logging.handlers.RotatingFileHandler(
        audit_log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8", delay=True
    )
    audit_handler.setLevel(logging.INFO)
    audit_handler.setFormatter(formatter or text_formatter)

    audit_logger = logging.getLogger("audit")
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False

    # Security log
    security_log_file = log_path / "security.log"
    security_handler = logging.handlers.RotatingFileHandler(
        security_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
        delay=True,
    )
    security_handler.setLevel(logging.WARNING)
    security_handler.setFormatter(formatter or text_formatter)

    security_logger = logging.getLogger("security")
    security_logger.addHandler(security_handler)
    security_logger.setLevel(logging.WARNING)
    security_logger.propagate = False

    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    logging.info("Logging configuration initialized")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with proper configuration"""
    return logging.getLogger(name)
