"""
Comprehensive Settings Management
Validates and provides type-safe access to all environment variables
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional, List
import os
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with validation"""

    # Application
    node_env: str = Field(default="development", alias="NODE_ENV")
    api_version: str = Field(default="1.0.0", alias="API_VERSION")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="text", alias="LOG_FORMAT")

    # Server
    port: int = Field(default=8000, alias="PORT")
    host: str = Field(default="0.0.0.0", alias="HOST")
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://localhost:8000",
        alias="ALLOWED_ORIGINS",
    )

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/app.db", alias="DATABASE_URL"
    )
    db_pool_size: int = Field(
        default=50, alias="DB_POOL_SIZE"
    )  # Optimized for 2026: Increased from 30 for better concurrency
    db_max_overflow: int = Field(
        default=30, alias="DB_MAX_OVERFLOW"
    )  # Optimized for 2026: Increased from 20 for peak load handling
    db_pool_timeout: int = Field(
        default=60, alias="DB_POOL_TIMEOUT"
    )  # Increased from 30 to prevent timeouts
    db_pool_recycle: int = Field(default=3600, alias="DB_POOL_RECYCLE")

    # Read Replicas (comma-separated URLs)
    db_read_replica_urls: Optional[str] = Field(
        default=None, alias="DB_READ_REPLICA_URLS"
    )
    enable_read_replicas: bool = Field(default=False, alias="ENABLE_READ_REPLICAS")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_pool_size: int = Field(default=10, alias="REDIS_POOL_SIZE")

    # Security
    jwt_secret: str = Field(
        default="dev-secret-change-me-in-production", alias="JWT_SECRET"
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, alias="JWT_EXPIRATION_HOURS")
    exchange_key_encryption_key: str = Field(
        default="dev-key-32-bytes-long-change-me", alias="EXCHANGE_KEY_ENCRYPTION_KEY"
    )

    # Stripe
    stripe_secret_key: Optional[str] = Field(default=None, alias="STRIPE_SECRET_KEY")
    stripe_publishable_key: Optional[str] = Field(
        default=None, alias="STRIPE_PUBLISHABLE_KEY"
    )
    stripe_webhook_secret: Optional[str] = Field(
        default=None, alias="STRIPE_WEBHOOK_SECRET"
    )

    # Email
    smtp_host: Optional[str] = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, alias="SMTP_USER")
    smtp_password: Optional[str] = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from: Optional[str] = Field(default=None, alias="SMTP_FROM")
    email_enabled: bool = Field(default=False, alias="EMAIL_ENABLED")

    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")
    enable_sentry: bool = Field(default=False, alias="ENABLE_SENTRY")
    enable_prometheus: bool = Field(default=True, alias="ENABLE_PROMETHEUS")

    # Rate Limiting
    enable_distributed_rate_limit: bool = Field(
        default=False, alias="ENABLE_DISTRIBUTED_RATE_LIMIT"
    )
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")
    rate_limit_burst: int = Field(default=100, alias="RATE_LIMIT_BURST")

    # Trading
    default_trading_mode: str = Field(default="paper", alias="DEFAULT_TRADING_MODE")
    exchange_timeout: int = Field(default=30, alias="EXCHANGE_TIMEOUT")
    exchange_retry_attempts: int = Field(default=3, alias="EXCHANGE_RETRY_ATTEMPTS")
    production_mode: bool = Field(default=False, alias="PRODUCTION_MODE")
    enable_mock_data: bool = Field(default=False, alias="ENABLE_MOCK_DATA")

    # Cache
    cache_ttl: int = Field(default=300, alias="CACHE_TTL")
    cache_max_size: int = Field(default=1000, alias="CACHE_MAX_SIZE")

    # WebSocket
    ws_ping_interval: int = Field(default=20, alias="WS_PING_INTERVAL")
    ws_ping_timeout: int = Field(default=10, alias="WS_PING_TIMEOUT")
    ws_max_message_size: int = Field(default=1048576, alias="WS_MAX_MESSAGE_SIZE")

    # Celery
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1", alias="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2", alias="CELERY_RESULT_BACKEND"
    )

    # Cold Storage
    cold_storage_threshold: float = Field(
        default=10000.0, alias="COLD_STORAGE_THRESHOLD"
    )
    cold_storage_processing_hours: int = Field(
        default=24, alias="COLD_STORAGE_PROCESSING_HOURS"
    )

    # Staking
    staking_min_amount: float = Field(default=10.0, alias="STAKING_MIN_AMOUNT")
    staking_reward_distribution_time: str = Field(
        default="00:00", alias="STAKING_REWARD_DISTRIBUTION_TIME"
    )

    # Performance
    workers: int = Field(default_factory=lambda: os.cpu_count() or 4, alias="WORKERS")
    max_connections: int = Field(default=1000, alias="MAX_CONNECTIONS")
    keepalive_timeout: int = Field(default=65, alias="KEEPALIVE_TIMEOUT")
    request_timeout: int = Field(default=30, alias="REQUEST_TIMEOUT")

    # DEX Trading
    zerox_api_key: Optional[str] = Field(default=None, alias="ZEROX_API_KEY")
    okx_api_key: Optional[str] = Field(default=None, alias="OKX_API_KEY")
    okx_secret_key: Optional[str] = Field(default=None, alias="OKX_SECRET_KEY")
    okx_passphrase: Optional[str] = Field(default=None, alias="OKX_PASSPHRASE")
    rubic_api_key: Optional[str] = Field(default=None, alias="RUBIC_API_KEY")
    affiliate_fee_recipient: Optional[str] = Field(
        default=None, alias="AFFILIATE_FEE_RECIPIENT"
    )
    trade_surplus_recipient: Optional[str] = Field(
        default=None, alias="TRADE_SURPLUS_RECIPIENT"
    )
    zerox_affiliate_fee_bps: int = Field(default=0, alias="ZEROX_AFFILIATE_FEE_BPS")
    platform_trading_fee_bps: int = Field(
        default=20, alias="PLATFORM_TRADING_FEE_BPS"
    )  # 0.2% default
    custodial_fee_bps: int = Field(
        default=20, alias="CUSTODIAL_FEE_BPS"
    )  # 0.2% for custodial
    non_custodial_fee_bps: int = Field(
        default=15, alias="NON_CUSTODIAL_FEE_BPS"
    )  # 0.15% for non-custodial

    # Blockchain RPC Providers
    ethereum_rpc_url: Optional[str] = Field(default=None, alias="ETHEREUM_RPC_URL")
    base_rpc_url: Optional[str] = Field(default=None, alias="BASE_RPC_URL")
    arbitrum_rpc_url: Optional[str] = Field(default=None, alias="ARBITRUM_RPC_URL")
    polygon_rpc_url: Optional[str] = Field(default=None, alias="POLYGON_RPC_URL")
    optimism_rpc_url: Optional[str] = Field(default=None, alias="OPTIMISM_RPC_URL")
    avalanche_rpc_url: Optional[str] = Field(default=None, alias="AVALANCHE_RPC_URL")
    bnb_chain_rpc_url: Optional[str] = Field(default=None, alias="BNB_CHAIN_RPC_URL")
    rpc_provider_type: str = Field(
        default="public", alias="RPC_PROVIDER_TYPE"
    )  # alchemy, infura, quicknode, public
    rpc_api_key: Optional[str] = Field(default=None, alias="RPC_API_KEY")
    rpc_timeout: int = Field(default=30, alias="RPC_TIMEOUT")  # Timeout in seconds
    rpc_max_retries: int = Field(default=3, alias="RPC_MAX_RETRIES")

    # Feature Flags
    enable_2fa: bool = Field(default=True, alias="ENABLE_2FA")
    enable_kyc: bool = Field(default=True, alias="ENABLE_KYC")
    enable_cold_storage: bool = Field(default=True, alias="ENABLE_COLD_STORAGE")
    enable_staking: bool = Field(default=True, alias="ENABLE_STAKING")
    enable_copy_trading: bool = Field(default=True, alias="ENABLE_COPY_TRADING")
    enable_dex_trading: bool = Field(default=True, alias="ENABLE_DEX_TRADING")
    enable_withdrawal_whitelist: bool = Field(
        default=True, alias="ENABLE_WITHDRAWAL_WHITELIST"
    )

    # Logging
    log_dir: str = Field(default="./logs", alias="LOG_DIR")
    log_max_bytes: int = Field(default=10485760, alias="LOG_MAX_BYTES")
    log_backup_count: int = Field(default=14, alias="LOG_BACKUP_COUNT")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    @field_validator("jwt_secret", mode="after")
    @classmethod
    def validate_jwt_secret(cls, v, info):
        """Validate JWT secret is not default in production"""
        production_mode = (
            info.data.get("production_mode", False)
            or info.data.get("node_env") == "production"
        )
        if production_mode and (
            not v
            or v
            in [
                "change-me-in-production-use-strong-random-secret",
                "dev-secret-change-me-in-production",
            ]
        ):
            raise ValueError(
                "JWT_SECRET must be set to a strong random secret in production"
            )
        return v

    @field_validator("exchange_key_encryption_key", mode="after")
    @classmethod
    def validate_encryption_key(cls, v, info):
        """Validate encryption key is not default in production"""
        production_mode = (
            info.data.get("production_mode", False)
            or info.data.get("node_env") == "production"
        )
        if production_mode and (
            not v
            or v
            in [
                "change-me-in-production-use-32-byte-key",
                "dev-key-32-bytes-long-change-me",
            ]
        ):
            raise ValueError(
                "EXCHANGE_KEY_ENCRYPTION_KEY must be set to a 32-byte key in production"
            )
        return v

    @field_validator("default_trading_mode")
    @classmethod
    def validate_trading_mode(cls, v):
        if v not in ["paper", "real"]:
            raise ValueError("DEFAULT_TRADING_MODE must be 'paper' or 'real'")
        return v

    @field_validator("node_env")
    @classmethod
    def validate_node_env(cls, v):
        if v not in ["development", "staging", "production", "test"]:
            raise ValueError(
                "NODE_ENV must be one of: development, staging, production, test"
            )
        return v

    @field_validator("enable_mock_data", mode="after")
    @classmethod
    def validate_mock_data_in_production(cls, v, info):
        """Prevent mock data in production mode"""
        production_mode = (
            info.data.get("production_mode", False)
            or info.data.get("node_env") == "production"
        )
        if production_mode and v:
            raise ValueError(
                "Cannot enable mock data in production mode. Set ENABLE_MOCK_DATA=false and PRODUCTION_MODE=true"
            )
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.node_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.node_env == "development"

    @property
    def is_testing(self) -> bool:
        """Check if running in test mode"""
        return self.node_env == "test" or os.getenv("TESTING") == "true"

    @property
    def allowed_origins_list(self) -> List[str]:
        """Get allowed origins as a list"""
        return [
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Backward-compatible export for routes that import settings directly
settings = get_settings()
