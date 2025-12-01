"""
Licensing Routes - License key generation and validation
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from ..services.licensing.license_service import license_service, LicenseType
from ..dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/licensing", tags=["Licensing"])


# Request/Response models
class GenerateLicenseRequest(BaseModel):
    """Generate license request"""
    user_id: str
    license_type: str = LicenseType.TRIAL
    expires_at: Optional[datetime] = None


class ValidateLicenseRequest(BaseModel):
    """Validate license request"""
    license_key: str
    machine_id: Optional[str] = None


class ActivateLicenseRequest(BaseModel):
    """Activate license request"""
    license_key: str
    machine_id: Optional[str] = None


@router.post("/generate", response_model=Dict)
async def generate_license(
    request: GenerateLicenseRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate a new license key"""
    try:
        # Check permissions (only admins should generate licenses)
        if str(current_user.get('id')) != request.user_id and current_user.get('role') != 'admin':
            raise HTTPException(status_code=403, detail="Not authorized to generate licenses")
        
        license_key = license_service.generate_license_key(
            user_id=request.user_id,
            license_type=request.license_type,
            expires_at=request.expires_at
        )
        
        license_data = license_service.parse_license_key(license_key)
        
        return {
            'license_key': license_key,
            'license_type': request.license_type,
            'user_id': request.user_id,
            'expires_at': license_data.get('expires_at'),
            'created_at': license_data.get('created_at'),
            'max_bots': license_data.get('max_bots'),
            'features': license_data.get('features')
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating license: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate license")


@router.post("/validate", response_model=Dict)
async def validate_license(
    request: ValidateLicenseRequest,
    current_user: dict = Depends(get_current_user)
):
    """Validate a license key"""
    try:
        status = license_service.validate_license_key(
            license_key=request.license_key,
            machine_id=request.machine_id
        )
        
        return {
            'valid': status.valid,
            'license_type': status.license_type,
            'expires_at': status.expires_at.isoformat() if status.expires_at else None,
            'activated_at': status.activated_at.isoformat() if status.activated_at else None,
            'max_bots': status.max_bots,
            'features': status.features,
            'message': status.message
        }
    except Exception as e:
        logger.error(f"Error validating license: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate license")


@router.post("/activate", response_model=Dict)
async def activate_license(
    request: ActivateLicenseRequest,
    current_user: dict = Depends(get_current_user)
):
    """Activate a license key on this machine"""
    try:
        # Validate license
        status = license_service.validate_license_key(
            license_key=request.license_key,
            machine_id=request.machine_id
        )
        
        if not status.valid:
            raise HTTPException(status_code=400, detail=status.message or "Invalid license")
        
        # Get or generate machine ID
        machine_id = request.machine_id or license_service.get_machine_id()
        
        # Bind license to machine
        bound = license_service.bind_license_to_machine(
            license_key=request.license_key,
            machine_id=machine_id
        )
        
        if not bound:
            raise HTTPException(status_code=500, detail="Failed to bind license to machine")
        
        return {
            'activated': True,
            'license_type': status.license_type,
            'machine_id': machine_id,
            'expires_at': status.expires_at.isoformat() if status.expires_at else None,
            'max_bots': status.max_bots,
            'features': status.features
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating license: {e}")
        raise HTTPException(status_code=500, detail="Failed to activate license")


@router.get("/machine-id", response_model=Dict)
async def get_machine_id(
    current_user: dict = Depends(get_current_user)
):
    """Get machine ID for license binding"""
    try:
        machine_id = license_service.get_machine_id()
        return {'machine_id': machine_id}
    except Exception as e:
        logger.error(f"Error getting machine ID: {e}")
        raise HTTPException(status_code=500, detail="Failed to get machine ID")


@router.get("/types", response_model=Dict)
async def get_license_types():
    """Get available license types and their features"""
    try:
        types = {}
        for license_type, config in license_service.LICENSE_CONFIG.items():
            types[license_type] = {
                'duration_days': config['duration_days'],
                'max_bots': config['max_bots'],
                'features': config['features']
            }
        return {'license_types': types}
    except Exception as e:
        logger.error(f"Error getting license types: {e}")
        raise HTTPException(status_code=500, detail="Failed to get license types")
