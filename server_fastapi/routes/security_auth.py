"""
Security Authentication Routes
Hardware keys, passkeys, and advanced authentication
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
from pydantic import BaseModel

from ..services.security.hardware_key_auth import hardware_key_auth_service
from ..services.security.passkey_auth import passkey_auth_service

router = APIRouter(prefix="/api/security/auth", tags=["Security Authentication"])


# Request models
class RegistrationRequest(BaseModel):
    user_id: str
    username: str
    display_name: str
    device_name: Optional[str] = None


class AuthenticationRequest(BaseModel):
    user_id: Optional[str] = None
    response: Dict[str, Any]


# Hardware Key Endpoints
@router.post("/hardware-key/register/options")
async def generate_hardware_key_registration_options(request: RegistrationRequest):
    """Generate hardware key registration options"""
    try:
        options = hardware_key_auth_service.generate_registration_options(
            user_id=request.user_id,
            username=request.username,
            display_name=request.display_name,
        )
        return options
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hardware-key/register/verify")
async def verify_hardware_key_registration(
    user_id: str,
    response: Dict[str, Any],
    challenge: str,
):
    """Verify hardware key registration"""
    credential = hardware_key_auth_service.verify_registration(
        user_id=user_id,
        registration_response=response,
        challenge=challenge,
    )
    
    if not credential:
        raise HTTPException(status_code=400, detail="Registration verification failed")
    
    return {
        "status": "success",
        "credential_id": credential.credential_id,
        "device_name": credential.device_name,
    }


@router.post("/hardware-key/authenticate/options")
async def generate_hardware_key_authentication_options(user_id: str):
    """Generate hardware key authentication options"""
    try:
        options = hardware_key_auth_service.generate_authentication_options(user_id)
        return options
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hardware-key/authenticate/verify")
async def verify_hardware_key_authentication(
    user_id: str,
    response: Dict[str, Any],
    challenge: str,
):
    """Verify hardware key authentication"""
    success = hardware_key_auth_service.verify_authentication(
        user_id=user_id,
        authentication_response=response,
        challenge=challenge,
    )
    
    if not success:
        raise HTTPException(status_code=401, detail="Authentication failed")
    
    return {"status": "success", "authenticated": True}


@router.get("/hardware-key/credentials/{user_id}")
async def get_hardware_key_credentials(user_id: str):
    """Get all hardware key credentials for a user"""
    credentials = hardware_key_auth_service.get_user_credentials(user_id)
    return {
        "credentials": [
            {
                "credential_id": cred.credential_id,
                "device_name": cred.device_name,
                "created_at": cred.created_at.isoformat() if cred.created_at else None,
                "last_used_at": cred.last_used_at.isoformat() if cred.last_used_at else None,
                "counter": cred.counter,
            }
            for cred in credentials
        ]
    }


@router.delete("/hardware-key/credentials/{user_id}/{credential_id}")
async def remove_hardware_key_credential(user_id: str, credential_id: str):
    """Remove a hardware key credential"""
    success = hardware_key_auth_service.remove_credential(user_id, credential_id)
    if not success:
        raise HTTPException(status_code=404, detail="Credential not found")
    return {"status": "success"}


# Passkey Endpoints
@router.post("/passkey/register/options")
async def generate_passkey_registration_options(request: RegistrationRequest):
    """Generate passkey registration options"""
    try:
        options = passkey_auth_service.generate_registration_options(
            user_id=request.user_id,
            username=request.username,
            display_name=request.display_name,
        )
        return options
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/passkey/register/verify")
async def verify_passkey_registration(
    user_id: str,
    response: Dict[str, Any],
):
    """Verify passkey registration"""
    credential = passkey_auth_service.verify_registration(
        user_id=user_id,
        registration_response=response,
    )
    
    if not credential:
        raise HTTPException(status_code=400, detail="Registration verification failed")
    
    return {
        "status": "success",
        "credential_id": credential.credential_id,
        "device_name": credential.device_name,
        "is_backup_eligible": credential.is_backup_eligible,
        "is_backed_up": credential.is_backed_up,
    }


@router.post("/passkey/authenticate/options")
async def generate_passkey_authentication_options(user_id: Optional[str] = None):
    """Generate passkey authentication options"""
    try:
        options = passkey_auth_service.generate_authentication_options(user_id)
        return options
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/passkey/authenticate/verify")
async def verify_passkey_authentication(
    user_id: Optional[str] = None,
    response: Dict[str, Any] = None,
):
    """Verify passkey authentication"""
    authenticated_user_id = passkey_auth_service.verify_authentication(
        user_id=user_id,
        authentication_response=response or {},
    )
    
    if not authenticated_user_id:
        raise HTTPException(status_code=401, detail="Authentication failed")
    
    return {
        "status": "success",
        "authenticated": True,
        "user_id": authenticated_user_id,
    }


@router.get("/passkey/credentials/{user_id}")
async def get_passkey_credentials(user_id: str):
    """Get all passkeys for a user"""
    passkeys = passkey_auth_service.get_user_passkeys(user_id)
    return {
        "passkeys": [
            {
                "credential_id": pk.credential_id,
                "device_name": pk.device_name,
                "created_at": pk.created_at.isoformat() if pk.created_at else None,
                "last_used_at": pk.last_used_at.isoformat() if pk.last_used_at else None,
                "counter": pk.counter,
                "is_backup_eligible": pk.is_backup_eligible,
                "is_backed_up": pk.is_backed_up,
            }
            for pk in passkeys
        ]
    }


@router.delete("/passkey/credentials/{user_id}/{credential_id}")
async def remove_passkey(user_id: str, credential_id: str):
    """Remove a passkey"""
    success = passkey_auth_service.remove_passkey(user_id, credential_id)
    if not success:
        raise HTTPException(status_code=404, detail="Passkey not found")
    return {"status": "success"}
