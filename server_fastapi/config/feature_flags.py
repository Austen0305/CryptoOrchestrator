"""
Feature Flag Management System
Enables/disables features dynamically without code changes
"""

import logging
import os
from typing import Dict, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class FeatureFlagStatus(str, Enum):
    """Feature flag status"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    EXPERIMENTAL = "experimental"  # Enabled for specific users/groups


@dataclass
class FeatureFlag:
    """Feature flag definition"""
    name: str
    status: FeatureFlagStatus
    description: str
    default_value: bool = False
    enabled_for: Optional[list] = None  # User IDs or groups
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.enabled_for is None:
            self.enabled_for = []


class FeatureFlagManager:
    """
    Feature flag manager
    
    Features:
    - Environment variable support
    - Per-user flags
    - Group-based flags
    - Dynamic toggling
    - Metadata support
    """

    def __init__(self):
        self.flags: Dict[str, FeatureFlag] = {}
        self._load_from_env()

    def _load_from_env(self):
        """Load feature flags from environment variables"""
        # Load flags from env (ENABLE_* pattern)
        for key, value in os.environ.items():
            if key.startswith("ENABLE_") and key not in ["ENABLE_PROMETHEUS", "ENABLE_SENTRY"]:
                flag_name = key.replace("ENABLE_", "").lower()
                enabled = value.lower() in ("true", "1", "yes")
                self.register(
                    flag_name,
                    FeatureFlagStatus.ENABLED if enabled else FeatureFlagStatus.DISABLED,
                    f"Feature flag from environment variable {key}",
                    default_value=enabled,
                )

    def register(
        self,
        name: str,
        status: FeatureFlagStatus,
        description: str,
        default_value: bool = False,
        enabled_for: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Register a feature flag"""
        flag = FeatureFlag(
            name=name,
            status=status,
            description=description,
            default_value=default_value,
            enabled_for=enabled_for or [],
            metadata=metadata or {},
        )
        self.flags[name] = flag
        logger.info(f"Feature flag registered: {name} ({status})")

    def is_enabled(
        self,
        name: str,
        user_id: Optional[str] = None,
        default: bool = False,
    ) -> bool:
        """Check if feature flag is enabled"""
        flag = self.flags.get(name)
        
        if not flag:
            # Check environment variable as fallback
            env_key = f"ENABLE_{name.upper()}"
            env_value = os.getenv(env_key)
            if env_value:
                return env_value.lower() in ("true", "1", "yes")
            return default

        # Check status
        if flag.status == FeatureFlagStatus.DISABLED:
            return False
        
        if flag.status == FeatureFlagStatus.ENABLED:
            return True
        
        # Experimental: check if user is in enabled list
        if flag.status == FeatureFlagStatus.EXPERIMENTAL:
            if user_id and user_id in flag.enabled_for:
                return True
            return flag.default_value

        return flag.default_value

    def enable(self, name: str):
        """Enable a feature flag"""
        if name in self.flags:
            self.flags[name].status = FeatureFlagStatus.ENABLED
            logger.info(f"Feature flag enabled: {name}")
        else:
            logger.warning(f"Feature flag not found: {name}")

    def disable(self, name: str):
        """Disable a feature flag"""
        if name in self.flags:
            self.flags[name].status = FeatureFlagStatus.DISABLED
            logger.info(f"Feature flag disabled: {name}")
        else:
            logger.warning(f"Feature flag not found: {name}")

    def get_flag(self, name: str) -> Optional[FeatureFlag]:
        """Get feature flag"""
        return self.flags.get(name)

    def get_all_flags(self) -> Dict[str, FeatureFlag]:
        """Get all feature flags"""
        return self.flags.copy()


# Global feature flag manager
feature_flags = FeatureFlagManager()

# Register common flags from .env
feature_flags.register(
    "ml_predictions",
    FeatureFlagStatus.ENABLED if os.getenv("ENABLE_ML_PREDICTIONS", "true").lower() == "true" else FeatureFlagStatus.DISABLED,
    "Machine learning predictions",
)
feature_flags.register(
    "arbitrage",
    FeatureFlagStatus.ENABLED if os.getenv("ENABLE_ARBITRAGE", "true").lower() == "true" else FeatureFlagStatus.DISABLED,
    "Arbitrage trading",
)
feature_flags.register(
    "copy_trading",
    FeatureFlagStatus.ENABLED if os.getenv("ENABLE_COPY_TRADING", "true").lower() == "true" else FeatureFlagStatus.DISABLED,
    "Copy trading",
)
feature_flags.register(
    "staking",
    FeatureFlagStatus.ENABLED if os.getenv("ENABLE_STAKING", "true").lower() == "true" else FeatureFlagStatus.DISABLED,
    "Staking",
)
feature_flags.register(
    "wallet",
    FeatureFlagStatus.ENABLED if os.getenv("ENABLE_WALLET", "true").lower() == "true" else FeatureFlagStatus.DISABLED,
    "Wallet management",
)


# Decorator for feature-gated endpoints
def feature_required(flag_name: str):
    """Decorator to require a feature flag"""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # Check if feature is enabled
            # Note: This would need access to request/user context
            # For now, just check global flag
            if not feature_flags.is_enabled(flag_name):
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Feature '{flag_name}' is not enabled",
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

