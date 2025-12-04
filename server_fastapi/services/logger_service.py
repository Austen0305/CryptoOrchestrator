import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
import json

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.getcwd(), "logs")
os.makedirs(logs_dir, exist_ok=True)

# Configure logging with Winston-like functionality
logger = logging.getLogger("crypto_orchestrator")
logger.setLevel(logging.INFO)

# Create formatters
json_formatter = logging.Formatter(
    json.dumps(
        {
            "timestamp": "%(asctime)s",
            "level": "%(levelname)s",
            "message": "%(message)s",
            "module": "%(name)s",
        },
        default=str,
    )
)

# Error log file - rotates daily, keep 14 days
error_handler = RotatingFileHandler(
    os.path.join(logs_dir, "error.log"),
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=14,
    delay=True,  # Delay file opening to avoid Windows file lock issues
)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(json_formatter)

# Combined log file - rotates daily, keep 14 days
combined_handler = RotatingFileHandler(
    os.path.join(logs_dir, "combined.log"),
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=14,
    delay=True,  # Delay file opening to avoid Windows file lock issues
)
combined_handler.setLevel(logging.INFO)
combined_handler.setFormatter(json_formatter)

# Add handlers to logger
logger.addHandler(error_handler)
logger.addHandler(combined_handler)

# Prevent duplicate logs
logger.propagate = False


class LoggerService:
    """Logger service with Winston-like functionality for FastAPI"""

    def __init__(self):
        self.logger = logger

    def info(self, message: str, extra: dict = None):
        """Log info level message"""
        self.logger.info(message, extra=extra)

    def warn(self, message: str, extra: dict = None):
        """Log warning level message"""
        self.logger.warning(message, extra=extra)

    def error(self, message: str, extra: dict = None):
        """Log error level message"""
        self.logger.error(message, extra=extra)

    def debug(self, message: str, extra: dict = None):
        """Log debug level message"""
        self.logger.debug(message, extra=extra)

    def log(self, level: str, message: str, extra: dict = None):
        """Generic log method"""
        if level.lower() == "info":
            self.info(message, extra)
        elif level.lower() == "warn" or level.lower() == "warning":
            self.warn(message, extra)
        elif level.lower() == "error":
            self.error(message, extra)
        elif level.lower() == "debug":
            self.debug(message, extra)
        else:
            self.info(message, extra)


# Export singleton instance
logger_service = LoggerService()
