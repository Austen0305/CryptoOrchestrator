"""
Demo Mode Routes - Feature flags and demo mode management
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List
import logging

from ..services.licensing.demo_mode import demo_mode_service
from ..services.licensing.license_service import license_service
from ..dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/demo-mode", tags=["Demo Mode"])


@router.get("/status", response_model=Dict)
async def get_demo_status(
    current_user: dict = Depends(get_current_user)
):
    """Get demo mode status and feature availability"""
    try:
        return demo_mode_service.get_demo_info()
    except Exception as e:
        logger.error(f"Error getting demo status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get demo status")


@router.get("/features", response_model=Dict)
async def get_available_features(
    current_user: dict = Depends(get_current_user)
):
    """Get list of available features"""
    try:
        return {
            'features': demo_mode_service.get_available_features(),
            'limits': demo_mode_service.get_feature_limits()
        }
    except Exception as e:
        logger.error(f"Error getting features: {e}")
        raise HTTPException(status_code=500, detail="Failed to get features")


@router.get("/features/{feature_name}", response_model=Dict)
async def check_feature(
    feature_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Check if a specific feature is available"""
    try:
        return demo_mode_service.check_feature(feature_name)
    except Exception as e:
        logger.error(f"Error checking feature: {e}")
        raise HTTPException(status_code=500, detail="Failed to check feature")


@router.post("/update-license", response_model=Dict)
async def update_license_status(
    license_key: str,
    current_user: dict = Depends(get_current_user)
):
    """Update license status from license key"""
    try:
        # Validate license
        status = license_service.validate_license_key(license_key)
        
        # Update demo mode service
        demo_mode_service.set_license(status)
        
        return {
            'updated': True,
            'status': demo_mode_service.get_demo_info()
        }
    except Exception as e:
        logger.error(f"Error updating license status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update license status")
