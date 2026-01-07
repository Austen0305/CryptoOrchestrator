"""
Middleware Configuration Manager
Centralized configuration for all middleware components
"""

import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class MiddlewarePriority(Enum):
    """Middleware execution priority (lower = earlier in chain)"""

    CRITICAL = 0  # Security, request ID
    HIGH = 1  # CORS, validation, rate limiting
    MEDIUM = 2  # Logging, monitoring
    LOW = 3  # Compression, caching
    OPTIONAL = 4  # Performance profiling, advanced features


@dataclass
class MiddlewareConfig:
    """Configuration for a single middleware"""

    name: str
    enabled: bool = True
    priority: MiddlewarePriority = MiddlewarePriority.MEDIUM
    module_path: str = ""
    class_name: str = ""
    kwargs: Dict[str, Any] = field(default_factory=dict)
    condition: Optional[str] = None  # Environment variable to check


class MiddlewareManager:
    """Manages middleware configuration and registration"""

    def __init__(self):
        self.middlewares: List[MiddlewareConfig] = []
        self._load_config()

    def _load_config(self):
        """Load middleware configuration from environment and defaults"""
        is_production = os.getenv("NODE_ENV") == "production"
        is_testing = os.getenv("TESTING", "false").lower() == "true"
        enable_heavy = os.getenv("ENABLE_HEAVY_MIDDLEWARE", "false").lower() == "true"

        # Core middleware (always enabled)
        self.middlewares = [
            # CRITICAL: Request ID must be first for traceability
            MiddlewareConfig(
                name="request_id",
                enabled=True,
                priority=MiddlewarePriority.CRITICAL,
                module_path="server_fastapi.middleware.request_id",
                class_name="RequestIDMiddleware",
            ),
            # CRITICAL: Security headers (2026 enhanced version)
            MiddlewareConfig(
                name="security_headers",
                enabled=True,  # Phase 1: Re-enabled
                priority=MiddlewarePriority.CRITICAL,
                module_path="server_fastapi.middleware.security_headers_2026",
                class_name="SecurityHeadersMiddleware2026",
            ),
            # HIGH: CORS (handled separately in main.py but tracked here)
            MiddlewareConfig(
                name="cors",
                enabled=True,
                priority=MiddlewarePriority.HIGH,
                module_path="fastapi.middleware.cors",
                class_name="CORSMiddleware",
            ),
            # HIGH: Request correlation (must be early for trace propagation)
            MiddlewareConfig(
                name="request_correlation",
                enabled=True,  # Phase 1: Re-enabled
                priority=MiddlewarePriority.CRITICAL,
                module_path="server_fastapi.middleware.request_correlation",
                class_name="RequestCorrelationMiddleware",
            ),
            # HIGH: Structured logging (try enhanced version first)
            MiddlewareConfig(
                name="structured_logging",
                enabled=False,  # TEMPORARILY DISABLED to debug connection reset
                priority=MiddlewarePriority.HIGH,
                module_path="server_fastapi.middleware.structured_logging_enhanced",
                class_name="EnhancedStructuredLoggingMiddleware",
                kwargs={"log_request_body": False, "log_response_body": False},
            ),
            # HIGH: API Analytics
            MiddlewareConfig(
                name="api_analytics",
                enabled=enable_heavy and not is_testing,
                priority=MiddlewarePriority.MEDIUM,
                module_path="server_fastapi.middleware.api_analytics",
                class_name="APIAnalyticsMiddleware",
            ),
            # HIGH: Request Deduplication
            MiddlewareConfig(
                name="request_deduplication",
                enabled=enable_heavy and not is_testing,
                priority=MiddlewarePriority.HIGH,
                module_path="server_fastapi.middleware.request_deduplication",
                class_name="RequestDeduplicationMiddleware",
                kwargs={"default_ttl": 300, "enable_auto_dedup": True},
            ),
            # MEDIUM: Response Transformer
            MiddlewareConfig(
                name="response_transformer",
                enabled=True,  # Phase 1: Re-enabled
                priority=MiddlewarePriority.MEDIUM,
                module_path="server_fastapi.middleware.response_transformer",
                class_name="ResponseTransformerMiddleware",
                kwargs={"enable_transformation": True},
            ),
            # MEDIUM: Request/Response Logging (development only)
            MiddlewareConfig(
                name="request_response_logging",
                enabled=os.getenv("NODE_ENV") == "development" and not is_testing,
                priority=MiddlewarePriority.MEDIUM,
                module_path="server_fastapi.middleware.request_response_logging",
                class_name="RequestResponseLoggingMiddleware",
                kwargs={
                    "log_request_body": os.getenv("LOG_REQUEST_BODY", "false").lower()
                    == "true",
                    "log_response_body": os.getenv("LOG_RESPONSE_BODY", "false").lower()
                    == "true",
                    "log_headers": True,
                },
            ),
            # HIGH: Advanced Security
            MiddlewareConfig(
                name="advanced_security",
                enabled=False,  # TEMPORARILY DISABLED to isolate connection reset
                priority=MiddlewarePriority.HIGH,
                module_path="server_fastapi.middleware.security_advanced",
                class_name="AdvancedSecurityMiddleware",
            ),
            # MEDIUM: Distributed Tracing
            MiddlewareConfig(
                name="distributed_tracing",
                enabled=os.getenv("ENABLE_OPENTELEMETRY", "false").lower() == "true",
                priority=MiddlewarePriority.MEDIUM,
                module_path="server_fastapi.middleware.distributed_tracing",
                class_name="DistributedTracingMiddleware",
            ),
            # HIGH: Timeout
            MiddlewareConfig(
                name="timeout",
                enabled=False,  # TEMPORARILY DISABLED to debug connection reset
                priority=MiddlewarePriority.HIGH,
                module_path="server_fastapi.middleware.timeout_middleware",
                class_name="TimeoutMiddleware",
                kwargs={"timeout_seconds": int(os.getenv("REQUEST_TIMEOUT", "30"))},
            ),
            # HIGH: Rate limiting (if enabled)
            MiddlewareConfig(
                name="rate_limit",
                enabled=False,  # TEMPORARILY DISABLED to debug connection reset
                priority=MiddlewarePriority.HIGH,
                module_path="server_fastapi.middleware.rate_limit_middleware",
                class_name="RateLimitMiddleware",
                condition="ENABLE_DISTRIBUTED_RATE_LIMIT",
            ),
            # MEDIUM: Error handling (registered as exception handlers, not middleware)
            # MEDIUM: Optimized caching (use optimized version if available)
            MiddlewareConfig(
                name="optimized_caching",
                enabled=enable_heavy and not is_testing,
                priority=MiddlewarePriority.LOW,
                module_path="server_fastapi.middleware.optimized_caching",
                class_name="OptimizedCacheMiddleware",
                kwargs={
                    "default_ttl": 300,
                    "compress_threshold": 1024,
                    "enable_stats": True,
                },
            ),
            # MEDIUM: Compression (2026 optimization - enabled by default for all environments)
            # Compression is lightweight and beneficial for all environments
            MiddlewareConfig(
                name="compression",
                enabled=False,  # TEMPORARILY DISABLED due to 2026 middleware crash
                priority=MiddlewarePriority.LOW,
                module_path="server_fastapi.middleware.compression",
                class_name="CompressionMiddleware",
                kwargs={"minimum_size": 1024, "compress_level": 6},
            ),
            # HIGH: Request Validation (2026 best practice - comprehensive input validation)
            MiddlewareConfig(
                name="request_validation_2026",
                enabled=False,  # TEMPORARILY DISABLED to fix JSONDecodeError crash
                priority=MiddlewarePriority.HIGH,
                module_path="server_fastapi.middleware.request_validation_2026",
                class_name="RequestValidationMiddleware2026",
                kwargs={"max_request_size": 10 * 1024 * 1024},  # 10MB
            ),
            # MEDIUM: ETag
            MiddlewareConfig(
                name="etag",
                enabled=enable_heavy and not is_testing,
                priority=MiddlewarePriority.LOW,
                module_path="server_fastapi.middleware.etag",
                class_name="ETagMiddleware",
                kwargs={"weak": False},
            ),
        ]

        # Optional middleware (behind feature flags)
        if enable_heavy and not is_testing:
            self.middlewares.extend(
                [
                    # IP Whitelist (optional)
                    MiddlewareConfig(
                        name="ip_whitelist",
                        enabled=os.getenv("ENABLE_IP_WHITELIST", "false").lower()
                        == "true",
                        priority=MiddlewarePriority.CRITICAL,
                        module_path="server_fastapi.middleware.ip_whitelist_middleware",
                        class_name="IPWhitelistMiddleware",
                        kwargs={"enabled": True},
                    ),
                    # CSRF Protection (optional)
                    MiddlewareConfig(
                        name="csrf_protection",
                        enabled=os.getenv("ENABLE_CSRF_PROTECTION", "false").lower()
                        == "true",
                        priority=MiddlewarePriority.CRITICAL,
                        module_path="server_fastapi.middleware.csrf_protection",
                        class_name="CSRFProtectionMiddleware",
                    ),
                    # Enhanced Security (use enhanced version if available)
                    MiddlewareConfig(
                        name="enhanced_security",
                        enabled=True,
                        priority=MiddlewarePriority.CRITICAL,
                        module_path="server_fastapi.middleware.security_enhanced",
                        class_name="EnhancedSecurityMiddleware",
                        kwargs={"block_threats": True, "log_threats": True},
                    ),
                    # Input Validation
                    MiddlewareConfig(
                        name="input_validation",
                        enabled=True,
                        priority=MiddlewarePriority.HIGH,
                        module_path="server_fastapi.middleware.validation",
                        class_name="InputValidationMiddleware",
                    ),
                    # Request Validation
                    MiddlewareConfig(
                        name="request_validation",
                        enabled=False,  # TEMPORARILY DISABLED to fix JSONDecodeError crash
                        priority=MiddlewarePriority.HIGH,
                        module_path="server_fastapi.middleware.request_validator",
                        class_name="RequestValidatorMiddleware",
                    ),
                    # Performance Monitoring
                    MiddlewareConfig(
                        name="performance_monitor",
                        enabled=True,
                        priority=MiddlewarePriority.MEDIUM,
                        module_path="server_fastapi.middleware.performance_monitor",
                        class_name="PerformanceMonitoringMiddleware",
                    ),
                    # Distributed Tracing
                    MiddlewareConfig(
                        name="distributed_tracing",
                        enabled=os.getenv("ENABLE_OPENTELEMETRY", "false").lower()
                        == "true",
                        priority=MiddlewarePriority.MEDIUM,
                        module_path="server_fastapi.middleware.distributed_tracing",
                        class_name="DistributedTracingMiddleware",
                    ),
                    # Audit Logging
                    MiddlewareConfig(
                        name="audit_logger",
                        enabled=True,
                        priority=MiddlewarePriority.MEDIUM,
                        module_path="server_fastapi.middleware.audit_logger",
                        class_name="AuditLoggerMiddleware",
                    ),
                    # Performance Profiling
                    MiddlewareConfig(
                        name="performance_profiling",
                        enabled=True,
                        priority=MiddlewarePriority.OPTIONAL,
                        module_path="server_fastapi.middleware.performance_profiling",
                        class_name="PerformanceProfilingMiddleware",
                    ),
                    # Query Monitoring
                    MiddlewareConfig(
                        name="query_monitoring",
                        enabled=True,
                        priority=MiddlewarePriority.MEDIUM,
                        module_path="server_fastapi.middleware.query_monitoring",
                        class_name="QueryMonitoringMiddleware",
                    ),
                    # API Key Auth
                    MiddlewareConfig(
                        name="api_key_auth",
                        enabled=True,
                        priority=MiddlewarePriority.HIGH,
                        module_path="server_fastapi.middleware.api_key_auth",
                        class_name="APIKeyAuthMiddleware",
                    ),
                    # Advanced Rate Limiting
                    MiddlewareConfig(
                        name="advanced_rate_limit",
                        enabled=True,
                        priority=MiddlewarePriority.HIGH,
                        module_path="server_fastapi.middleware.advanced_rate_limit",
                        class_name="AdvancedRateLimitMiddleware",
                    ),
                ]
            )

    def get_enabled_middlewares(self) -> List[MiddlewareConfig]:
        """Get list of enabled middlewares sorted by priority"""
        enabled = [
            m for m in self.middlewares if m.enabled and self._check_condition(m)
        ]
        # Sort by priority
        enabled.sort(key=lambda m: m.priority.value)
        return enabled

    def _check_condition(self, config: MiddlewareConfig) -> bool:
        """Check if middleware condition is met"""
        if not config.condition:
            return True
        return os.getenv(config.condition, "false").lower() == "true"

    def get_middleware_config(self, name: str) -> Optional[MiddlewareConfig]:
        """Get configuration for a specific middleware"""
        for mw in self.middlewares:
            if mw.name == name:
                return mw
        return None


# Global middleware manager instance
middleware_manager = MiddlewareManager()
