"""
Enhanced Logging Configuration
Implements structured logging with context (user_id, request_id, trace_id),
log aggregation support, and log sampling.
"""

import logging
import json
import sys
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import os
from contextvars import ContextVar

# Log directory
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Context variables for request-scoped logging
REQUEST_ID_CTX: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
TRACE_ID_CTX: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add context from extra
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        # Prefer explicit record attributes, otherwise read from contextvars
        if hasattr(record, "request_id") and record.request_id:
            log_data["request_id"] = record.request_id
        else:
            ctx_rid = REQUEST_ID_CTX.get()
            if ctx_rid:
                log_data["request_id"] = ctx_rid

        if hasattr(record, "trace_id") and record.trace_id:
            log_data["trace_id"] = record.trace_id
        else:
            ctx_tid = TRACE_ID_CTX.get()
            if ctx_tid:
                log_data["trace_id"] = ctx_tid
        if hasattr(record, "span_id"):
            log_data["span_id"] = record.span_id

        # Add any other extra fields
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        # Add exception info if present
        if record.exc_info:
            is_production = os.getenv("NODE_ENV") == "production"
            exception_info = self.formatException(record.exc_info)

            if is_production:
                # In production, sanitize stack traces (remove file paths, line numbers)
                import re

                # Remove absolute file paths
                exception_info = re.sub(
                    r'File "[^"]*[/\\]([^/\\]+\.py)"', r'File "\1"', exception_info
                )
                # Remove line numbers from traceback
                exception_info = re.sub(r", line \d+", "", exception_info)

            log_data["exception"] = exception_info
            log_data["exception_type"] = (
                record.exc_info[0].__name__ if record.exc_info[0] else None
            )
            log_data["exception_message"] = (
                str(record.exc_info[1]) if record.exc_info[1] else None
            )

        return json.dumps(log_data)


class ContextFilter(logging.Filter):
    """Filter to add context to log records"""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record"""
        # Context will be set by middleware/request handlers
        # This filter ensures it's available for formatting
        return True


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",  # "json" or "text"
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True,
    log_sampling_rate: float = 1.0,  # 1.0 = 100%, 0.1 = 10%
    enable_sampling: bool = False,  # Enable log sampling filter
) -> None:
    """
    Setup enhanced logging configuration

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format ("json" for structured, "text" for human-readable)
        log_file: Optional log file path (default: logs/app.log)
        enable_console: Enable console logging
        enable_file: Enable file logging
        log_sampling_rate: Sampling rate for high-volume logs (0.0-1.0)
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers properly (close them first to avoid file locks)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass
    
    # Also clear handlers from the crypto_orchestrator logger (logger_service.py)
    crypto_logger = logging.getLogger("crypto_orchestrator")
    for handler in crypto_logger.handlers[:]:
        crypto_logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass

    # Create formatters
    if log_format == "json":
        formatter = StructuredFormatter()
        text_formatter = None
    else:
        text_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        formatter = None

    # Add log sampling filter if enabled
    if enable_sampling and log_sampling_rate < 1.0:
        try:
            from .logging.log_sampling import LogSamplingFilter, get_sampling_config

            sampling_config = get_sampling_config()
            sampling_filter = LogSamplingFilter(
                sampling_rate=log_sampling_rate,
                endpoint_sampling_rates=sampling_config.get(
                    "high_volume_endpoints", {}
                ),
            )
        except ImportError:
            logging.warning("Log sampling not available, skipping sampling filter")
            sampling_filter = None
    else:
        sampling_filter = None

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        if text_formatter:
            console_handler.setFormatter(text_formatter)
        else:
            console_handler.setFormatter(formatter)
        console_handler.addFilter(ContextFilter())
        if sampling_filter:
            console_handler.addFilter(sampling_filter)
        root_logger.addHandler(console_handler)

    # File handler with rotation (only if file logging is enabled)
    if enable_file:
        try:
            if not log_file:
                log_file = LOG_DIR / "app.log"

            # Use RotatingFileHandler with delay=True for Windows compatibility
            # delay=True prevents file locking issues on Windows by delaying file opening
            from logging.handlers import RotatingFileHandler
            
            file_handler = RotatingFileHandler(
                str(log_file),
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                delay=True,  # Delay file opening to avoid Windows file lock issues
            )
            file_handler.setLevel(logging.DEBUG)
            if text_formatter:
                file_handler.setFormatter(text_formatter)
            else:
                file_handler.setFormatter(formatter)
            file_handler.addFilter(ContextFilter())
            if sampling_filter:
                file_handler.addFilter(sampling_filter)
            root_logger.addHandler(file_handler)
        except PermissionError as e:
            # File is locked (e.g., by another process), skip file logging
            logging.warning(f"Log file is locked by another process, skipping file logging: {e}")
        except Exception as e:
            logging.warning(f"Could not setup file logging: {e}")

    # Error file handler (separate file for errors) - only if file logging is enabled
    if enable_file:
        try:
            error_log_file = LOG_DIR / "errors.log"
            # Use RotatingFileHandler with delay=True for Windows compatibility
            from logging.handlers import RotatingFileHandler
            
            error_handler = RotatingFileHandler(
                str(error_log_file),
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                delay=True,  # Delay file opening to avoid Windows file lock issues
            )
            error_handler.setLevel(logging.ERROR)
            if text_formatter:
                error_handler.setFormatter(text_formatter)
            else:
                error_handler.setFormatter(formatter)
            error_handler.addFilter(ContextFilter())
            root_logger.addHandler(error_handler)
        except PermissionError as e:
            # File is locked, skip error file logging
            logging.warning(f"Error log file is locked, skipping: {e}")
        except Exception as e:
            logging.warning(f"Could not setup error log file: {e}")

    # Set up log rotation (only if file logging is enabled)
    # NOTE: We use a single RotatingFileHandler instead of separate FileHandler + RotatingFileHandler
    # to avoid conflicts. The RotatingFileHandler handles both writing and rotation.
    # This is already set up above, so we don't need to add another handler here.
    # If we need rotation, we should replace the FileHandler with RotatingFileHandler above.


def get_logger_with_context(
    name: str,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> logging.Logger:
    """
    Get logger with context for structured logging

    Usage:
        logger = get_logger_with_context(__name__, user_id="123", request_id="req-456")
        logger.info("User action", extra={"action": "create_bot"})
    """
    logger = logging.getLogger(name)

    # Add context adapter
    class ContextAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            kwargs.setdefault("extra", {})
            if self.extra.get("user_id"):
                kwargs["extra"]["user_id"] = self.extra["user_id"]
            if self.extra.get("request_id"):
                kwargs["extra"]["request_id"] = self.extra["request_id"]
            if self.extra.get("trace_id"):
                kwargs["extra"]["trace_id"] = self.extra["trace_id"]
            return msg, kwargs

    context = {}
    if user_id:
        context["user_id"] = user_id
    if request_id:
        context["request_id"] = request_id
    if trace_id:
        context["trace_id"] = trace_id

    return ContextAdapter(logger, context)


# Initialize logging on import
_log_level = os.getenv("LOG_LEVEL", "INFO")
_log_format = os.getenv("LOG_FORMAT", "json")
setup_logging(
    log_level=_log_level, log_format=_log_format, enable_console=True, enable_file=True
)
