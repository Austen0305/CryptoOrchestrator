"""
Demo Mode Service - Feature-limited trial mode
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime
import logging

from .license_service import license_service, LicenseStatus, LicenseType

logger = logging.getLogger(__name__)


class FeatureFlag(BaseModel):
    """Feature flag configuration"""

    name: str
    enabled: bool
    limit: Optional[int] = None  # Usage limit for demo mode
    message: Optional[str] = None  # Message when feature is disabled


class DemoModeService:
    """Service for managing demo mode and feature limitations"""

    # Feature flags for demo mode
    DEMO_FEATURES = {
        "paper_trading": FeatureFlag(name="paper_trading", enabled=True, limit=None),
        "live_trading": FeatureFlag(
            name="live_trading",
            enabled=False,
            limit=None,
            message="Live trading requires a license",
        ),
        "basic_strategies": FeatureFlag(
            name="basic_strategies",
            enabled=True,
            limit=3,
            message="Demo mode limited to 3 strategies",
        ),
        "advanced_strategies": FeatureFlag(
            name="advanced_strategies",
            enabled=False,
            limit=None,
            message="Advanced strategies require a license",
        ),
        "ml_models": FeatureFlag(
            name="ml_models",
            enabled=False,
            limit=None,
            message="ML models require a license",
        ),
        "api_access": FeatureFlag(
            name="api_access",
            enabled=False,
            limit=None,
            message="API access requires a license",
        ),
        "multiple_bots": FeatureFlag(
            name="multiple_bots",
            enabled=True,
            limit=3,
            message="Demo mode limited to 3 bots",
        ),
        "backtesting": FeatureFlag(
            name="backtesting",
            enabled=True,
            limit=10,
            message="Demo mode limited to 10 backtests per day",
        ),
    }

    def __init__(self):
        self.current_license: Optional[LicenseStatus] = None
        self.is_demo_mode = True

    def set_license(self, license_status: LicenseStatus) -> None:
        """Set current license status"""
        self.current_license = license_status
        self.is_demo_mode = (
            not license_status.valid or license_status.license_type == LicenseType.TRIAL
        )

    def check_feature(self, feature_name: str) -> Dict[str, Any]:
        """Check if a feature is available"""
        if (
            not self.is_demo_mode
            and self.current_license
            and self.current_license.valid
        ):
            # Full license - check if feature is in license features
            if feature_name in self.current_license.features:
                return {"enabled": True, "message": None}
            else:
                return {
                    "enabled": False,
                    "message": f'{feature_name.replace("_", " ").title()} is not available in your license tier',
                }

        # Demo mode - check demo features
        feature = self.DEMO_FEATURES.get(feature_name)
        if not feature:
            # Unknown feature - allow by default
            return {"enabled": True, "message": None}

        return {
            "enabled": feature.enabled,
            "limit": feature.limit,
            "message": feature.message,
        }

    def get_available_features(self) -> List[str]:
        """Get list of available features"""
        if (
            not self.is_demo_mode
            and self.current_license
            and self.current_license.valid
        ):
            return self.current_license.features

        # Demo mode features
        return [name for name, flag in self.DEMO_FEATURES.items() if flag.enabled]

    def get_feature_limits(self) -> Dict[str, int]:
        """Get feature limits for current mode"""
        limits = {}

        if self.is_demo_mode:
            for name, flag in self.DEMO_FEATURES.items():
                if flag.limit is not None:
                    limits[name] = flag.limit

        if self.current_license and self.current_license.valid:
            if self.current_license.max_bots > 0:
                limits["bots"] = self.current_license.max_bots

        return limits

    def get_demo_info(self) -> Dict[str, Any]:
        """Get demo mode information"""
        return {
            "is_demo_mode": self.is_demo_mode,
            "license_type": (
                self.current_license.license_type if self.current_license else "demo"
            ),
            "license_valid": (
                self.current_license.valid if self.current_license else False
            ),
            "features": self.get_available_features(),
            "limits": self.get_feature_limits(),
            "expires_at": (
                self.current_license.expires_at.isoformat()
                if self.current_license and self.current_license.expires_at
                else None
            ),
        }


# Global service instance
demo_mode_service = DemoModeService()
