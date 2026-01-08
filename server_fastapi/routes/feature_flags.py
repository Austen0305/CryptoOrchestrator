"""
Feature Flag Management Routes
Provides endpoints for managing and checking feature flags
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..config.feature_flags import feature_flags
from ..middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/feature-flags", tags=["Feature Flags"])


class FeatureFlagResponse(BaseModel):
    """Feature flag response"""

    name: str
    status: str
    description: str
    enabled: bool
    enabled_for: list[str]


@router.get("/", response_model=list[FeatureFlagResponse])
async def list_feature_flags(
    current_user: dict = Depends(get_current_user),
):
    """List all feature flags"""
    try:
        all_flags = feature_flags.get_all_flags()
        user_id = current_user.get("id")

        return [
            FeatureFlagResponse(
                name=name,
                status=flag.status.value,
                description=flag.description,
                enabled=feature_flags.is_enabled(name, user_id=user_id),
                enabled_for=flag.enabled_for,
            )
            for name, flag in all_flags.items()
        ]
    except Exception as e:
        logger.error(f"Error listing feature flags: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list feature flags: {str(e)}",
        )


@router.get("/{flag_name}")
async def get_feature_flag(
    flag_name: str,
    current_user: dict = Depends(get_current_user),
):
    """Get feature flag status"""
    try:
        flag = feature_flags.get_flag(flag_name)
        if not flag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature flag not found: {flag_name}",
            )

        user_id = current_user.get("id")
        return {
            "name": flag.name,
            "status": flag.status.value,
            "description": flag.description,
            "enabled": feature_flags.is_enabled(flag_name, user_id=user_id),
            "enabled_for": flag.enabled_for,
            "metadata": flag.metadata,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feature flag: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feature flag: {str(e)}",
        )


@router.post("/{flag_name}/enable")
async def enable_feature_flag(
    flag_name: str,
    current_user: dict = Depends(get_current_user),
):
    """Enable a feature flag (admin only)"""
    # Admin check
    if current_user.get("role") != "admin" and not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    try:
        feature_flags.enable(flag_name)
        return {"message": f"Feature flag {flag_name} enabled"}
    except Exception as e:
        logger.error(f"Error enabling feature flag: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable feature flag: {str(e)}",
        )


@router.post("/{flag_name}/disable")
async def disable_feature_flag(
    flag_name: str,
    current_user: dict = Depends(get_current_user),
):
    """Disable a feature flag (admin only)"""
    # Admin check
    if current_user.get("role") != "admin" and not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    try:
        feature_flags.disable(flag_name)
        return {"message": f"Feature flag {flag_name} disabled"}
    except Exception as e:
        logger.error(f"Error disabling feature flag: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable feature flag: {str(e)}",
        )
