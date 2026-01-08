"""
Configuration Validator and Hot-Reload
Validates configuration and supports hot-reloading in development
"""

import json
import logging
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validates and monitors configuration changes"""

    def __init__(self, config_path: str | None = None):
        self.config_path = config_path or os.getenv("CONFIG_PATH")
        self.validators: list[Callable] = []
        self.observer: Observer | None = None

    def register_validator(self, validator: Callable):
        """Register a configuration validator"""
        self.validators.append(validator)

    def validate(self, config: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate configuration"""
        errors = []

        for validator in self.validators:
            try:
                result = validator(config)
                if not result[0]:
                    errors.extend(result[1])
            except Exception as e:
                errors.append(f"Validator error: {e}")

        return len(errors) == 0, errors

    def start_hot_reload(self, callback: Callable):
        """Start hot-reload monitoring (development only)"""
        if os.getenv("NODE_ENV") == "production":
            logger.info("Hot-reload disabled in production")
            return

        if not self.config_path or not Path(self.config_path).exists():
            logger.warning("Config path not found, hot-reload disabled")
            return

        if not WATCHDOG_AVAILABLE:
            logger.warning("watchdog not installed, hot-reload disabled")
            return

        try:

            class ConfigFileHandler(FileSystemEventHandler):
                def __init__(self, validator, callback):
                    self.validator = validator
                    self.callback = callback

                def on_modified(self, event):
                    if event.src_path == self.validator.config_path:
                        logger.info("Configuration file changed, reloading...")
                        try:
                            with open(event.src_path) as f:
                                config = json.load(f)
                            is_valid, errors = self.validator.validate(config)
                            if is_valid:
                                self.callback(config)
                                logger.info("Configuration reloaded successfully")
                            else:
                                logger.error(
                                    f"Configuration validation failed: {errors}"
                                )
                        except Exception as e:
                            logger.error(f"Error reloading configuration: {e}")

            self.observer = Observer()
            self.observer.schedule(
                ConfigFileHandler(self, callback),
                str(Path(self.config_path).parent),
                recursive=False,
            )
            self.observer.start()
            logger.info(f"Hot-reload monitoring started for {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to start hot-reload: {e}")

    def stop_hot_reload(self):
        """Stop hot-reload monitoring"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("Hot-reload monitoring stopped")


# Global config validator
config_validator = ConfigValidator()
