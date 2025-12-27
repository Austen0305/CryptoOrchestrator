"""
Advanced Configuration Management
Provides hierarchical configuration, validation, and hot-reload
"""

import os
import logging
import json
from typing import Dict, Any, Optional, List, Type
from pathlib import Path
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
import yaml

logger = logging.getLogger(__name__)


class DatabaseConfig(BaseModel):
    """Database configuration"""
    url: str = Field(..., description="Database URL")
    pool_size: int = Field(20, ge=1, le=100, description="Connection pool size")
    max_overflow: int = Field(10, ge=0, le=50, description="Max overflow connections")
    pool_timeout: int = Field(30, ge=1, le=300, description="Pool timeout in seconds")
    pool_recycle: int = Field(3600, ge=60, le=86400, description="Pool recycle time")


class RedisConfig(BaseModel):
    """Redis configuration"""
    url: str = Field("redis://localhost:6379/0", description="Redis URL")
    enabled: bool = Field(True, description="Enable Redis")
    pool_size: int = Field(10, ge=1, le=100, description="Redis pool size")


class SecurityConfig(BaseModel):
    """Security configuration"""
    jwt_secret: str = Field(..., min_length=32, description="JWT secret key")
    jwt_algorithm: str = Field("HS256", description="JWT algorithm")
    jwt_expiration_minutes: int = Field(15, ge=1, le=1440, description="JWT expiration")
    cors_origins: List[str] = Field(default_factory=list, description="CORS origins")
    enable_csrf: bool = Field(False, description="Enable CSRF protection")


class PerformanceConfig(BaseModel):
    """Performance configuration"""
    workers: int = Field(4, ge=1, le=32, description="Number of workers")
    max_connections: int = Field(1000, ge=10, le=10000, description="Max connections")
    cache_ttl: int = Field(300, ge=1, le=86400, description="Cache TTL in seconds")
    enable_compression: bool = Field(True, description="Enable response compression")


class MonitoringConfig(BaseModel):
    """Monitoring configuration"""
    enable_prometheus: bool = Field(True, description="Enable Prometheus")
    enable_sentry: bool = Field(False, description="Enable Sentry")
    sentry_dsn: Optional[str] = Field(None, description="Sentry DSN")
    log_level: str = Field("INFO", description="Log level")


class AdvancedSettings(BaseSettings):
    """Advanced application settings with validation"""

    # Database
    database: DatabaseConfig

    # Redis
    redis: RedisConfig

    # Security
    security: SecurityConfig

    # Performance
    performance: PerformanceConfig

    # Monitoring
    monitoring: MonitoringConfig

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        case_sensitive = False

    @classmethod
    def from_files(cls, *file_paths: Path) -> "AdvancedSettings":
        """Load settings from multiple files"""
        config_dict: Dict[str, Any] = {}

        for file_path in file_paths:
            if not file_path.exists():
                logger.warning(f"Config file not found: {file_path}")
                continue

            with open(file_path) as f:
                if file_path.suffix in [".yaml", ".yml"]:
                    file_config = yaml.safe_load(f)
                elif file_path.suffix == ".json":
                    file_config = json.load(f)
                else:
                    logger.warning(f"Unsupported config file format: {file_path.suffix}")
                    continue

                # Merge configs (later files override earlier ones)
                config_dict = {**config_dict, **file_config}

        # Override with environment variables
        env_config = cls._load_from_env()
        config_dict = {**config_dict, **env_config}

        return cls(**config_dict)

    @classmethod
    def _load_from_env(cls) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        config = {}

        # Database
        if os.getenv("DATABASE_URL"):
            config["database"] = {
                "url": os.getenv("DATABASE_URL"),
                "pool_size": int(os.getenv("PERF_DB_POOL_SIZE", "20")),
                "max_overflow": int(os.getenv("PERF_DB_MAX_OVERFLOW", "10")),
                "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
                "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
            }

        # Redis
        config["redis"] = {
            "url": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            "enabled": os.getenv("REDIS_ENABLED", "true").lower() == "true",
            "pool_size": int(os.getenv("REDIS_POOL_SIZE", "10")),
        }

        # Security
        config["security"] = {
            "jwt_secret": os.getenv("JWT_SECRET", ""),
            "jwt_algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
            "jwt_expiration_minutes": int(os.getenv("JWT_EXPIRATION_MINUTES", "15")),
            "cors_origins": os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else [],
            "enable_csrf": os.getenv("ENABLE_CSRF_PROTECTION", "false").lower() == "true",
        }

        # Performance
        config["performance"] = {
            "workers": int(os.getenv("PERF_WORKERS", "4")),
            "max_connections": int(os.getenv("PERF_MAX_CONNECTIONS", "1000")),
            "cache_ttl": int(os.getenv("PERF_CACHE_TTL", "300")),
            "enable_compression": os.getenv("ENABLE_COMPRESSION", "true").lower() == "true",
        }

        # Monitoring
        config["monitoring"] = {
            "enable_prometheus": os.getenv("ENABLE_PROMETHEUS", "true").lower() == "true",
            "enable_sentry": os.getenv("ENABLE_SENTRY", "false").lower() == "true",
            "sentry_dsn": os.getenv("SENTRY_DSN"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
        }

        return config

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []

        # Validate database URL
        if not self.database.url:
            errors.append("Database URL is required")

        # Validate JWT secret
        if len(self.security.jwt_secret) < 32:
            errors.append("JWT secret must be at least 32 characters")

        # Validate CORS origins
        if not self.security.cors_origins:
            logger.warning("No CORS origins configured")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary"""
        return {
            "database": self.database.dict(),
            "redis": self.redis.dict(),
            "security": {**self.security.dict(), "jwt_secret": "***"},  # Hide secret
            "performance": self.performance.dict(),
            "monitoring": self.monitoring.dict(),
        }


# Global settings instance
_settings: Optional[AdvancedSettings] = None


def get_settings() -> AdvancedSettings:
    """Get or create global settings"""
    global _settings

    if _settings is None:
        # Try to load from config files
        config_paths = [
            Path("config.yaml"),
            Path("config.yml"),
            Path("config.json"),
        ]

        try:
            _settings = AdvancedSettings.from_files(*config_paths)
        except Exception as e:
            logger.warning(f"Failed to load config files: {e}, using environment variables")
            _settings = AdvancedSettings.from_files()

        # Validate
        errors = _settings.validate()
        if errors:
            logger.error(f"Configuration validation errors: {errors}")

    return _settings

