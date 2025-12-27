"""
Two-Factor Authentication Routes
API endpoints for 2FA setup and verification.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Annotated
import logging

from ..services.two_factor_service import two_factor_service
from ..dependencies.auth import get_current_user
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter()


class VerifyTokenRequest(BaseModel):
    token: str


class Setup2FAResponse(BaseModel):
    secret: str
    qr_code: str
    backup_codes: List[str]


@router.post("/setup")
async def setup_2fa(current_user: Annotated[dict, Depends(get_current_user)]):
    """Set up 2FA for the current user"""
    try:
        user_id = _get_user_id(current_user)
        email = current_user.get("email", "")

        # Generate secret
        secret = two_factor_service.generate_secret(user_id)

        # Generate QR code
        qr_code = two_factor_service.generate_qr_code(user_id, email)

        # Generate backup codes (in production, store these securely)
        import secrets

        backup_codes = [secrets.token_urlsafe(8) for _ in range(10)]

        return {
            "secret": secret,
            "qr_code": qr_code,
            "backup_codes": backup_codes,
            "message": "Save your backup codes in a secure location",
        }
    except Exception as e:
        logger.error(f"Error setting up 2FA: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to set up 2FA")


@router.post("/verify")
async def verify_2fa_token(
    request: VerifyTokenRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Verify a 2FA token"""
    try:
        user_id = _get_user_id(current_user)

        is_valid = two_factor_service.verify_token(user_id, request.token)

        if is_valid:
            return {"verified": True, "message": "Token verified successfully"}
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying 2FA token: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to verify token")


@router.get("/status")
async def get_2fa_status(current_user: Annotated[dict, Depends(get_current_user)]):
    """Get 2FA status for current user"""
    try:
        user_id = _get_user_id(current_user)
        is_enabled = two_factor_service.is_2fa_enabled(user_id)

        return {
            "enabled": is_enabled,
            "required_for_trading": (
                two_factor_service.require_2fa_for_trading(user_id)
                if is_enabled
                else False
            ),
        }
    except Exception as e:
        logger.error(f"Error getting 2FA status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get 2FA status")


@router.delete("/disable")
async def disable_2fa(current_user: Annotated[dict, Depends(get_current_user)]):
    """Disable 2FA for current user"""
    try:
        user_id = _get_user_id(current_user)
        # In production, would remove from database
        # For now, just remove from in-memory storage
        if user_id in two_factor_service.user_secrets:
            del two_factor_service.user_secrets[user_id]

        return {"message": "2FA disabled successfully"}
    except Exception as e:
        logger.error(f"Error disabling 2FA: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to disable 2FA")
