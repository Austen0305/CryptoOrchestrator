"""Performance and optimization settings"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os

class PerformanceSettings(BaseSettings):
    """Performance and optimization settings"""
    
    # Server settings
    workers: int = os.cpu_count() or 4
    max_connections: int = 1000
    keepalive_timeout: int = 65
    request_timeout: int = 30
    
    # Cache settings
    cache_ttl: int = 300  # 5 minutes
    cache_max_size: int = 1000
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_pool_size: int = 10
    
    # Database settings
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 100
    
    # WebSocket settings
    ws_ping_interval: int = 20
    ws_ping_timeout: int = 10
    ws_max_message_size: int = 1024 * 1024  # 1MB
    
    # Monitoring
    enable_prometheus: bool = True
    enable_sentry: bool = os.getenv("NODE_ENV") == "production"
    sentry_dsn: str = os.getenv("SENTRY_DSN", "")
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = "json" if os.getenv("NODE_ENV") == "production" else "text"
    
    model_config = SettingsConfigDict(env_prefix="PERF_")

@lru_cache()
def get_performance_settings() -> PerformanceSettings:
    return PerformanceSettings()
