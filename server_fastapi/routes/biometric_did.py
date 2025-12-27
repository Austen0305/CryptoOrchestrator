"""
Biometric Authentication and DID API Routes
Endpoints for biometric auth and decentralized identity
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Annotated
from datetime import datetime
import logging

from ..dependencies.auth import get_current_user
from ..services.security.biometric_auth import biometric_auth_service
from ..services.security.did_service import did_service
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/security", tags=["Biometric & DID"])


# Request/Response Models
class RegisterBiometricRequest(BaseModel):
    biometric_type: str = Field(..., description="Type: fingerprint, face_id, voice")
    device_id: str = Field(..., description="Device identifier")
    public_key: str = Field(..., description="Public key (base64)")
    credential_id: Optional[str] = None


class VerifyBiometricRequest(BaseModel):
    challenge_id: str = Field(..., description="Challenge ID")
    credential_id: str = Field(..., description="Credential ID")
    signature: str = Field(..., description="Signature (base64)")
    authenticator_data: str = Field(..., description="Authenticator data (base64)")


class CreateDIDRequest(BaseModel):
    method: str = Field("key", description="DID method")
    user_id: Optional[int] = None


class IssueCredentialRequest(BaseModel):
    issuer_did: str = Field(..., description="Issuer DID")
    subject_did: str = Field(..., description="Subject DID")
    credential_type: List[str] = Field(..., description="Credential types")
    claims: Dict[str, Any] = Field(..., description="Credential claims")
    expires_days: Optional[int] = None


class CreatePresentationRequest(BaseModel):
    holder_did: str = Field(..., description="Holder DID")
    credential_ids: List[str] = Field(..., description="Credential IDs")


# Biometric Endpoints
@router.post("/biometric/register")
async def register_biometric(
    request: RegisterBiometricRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Register biometric credential"""
    try:
        import base64
        user_id = _get_user_id(current_user)
        
        public_key_bytes = base64.b64decode(request.public_key)
        
        credential = biometric_auth_service.register_biometric(
            user_id=user_id,
            biometric_type=request.biometric_type,
            device_id=request.device_id,
            public_key=public_key_bytes,
            credential_id=request.credential_id,
        )
        
        return {
            "credential_id": credential.credential_id,
            "biometric_type": credential.biometric_type,
            "device_id": credential.device_id,
            "created_at": credential.created_at.isoformat(),
        }
    except Exception as e:
        logger.error(f"Error registering biometric: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to register biometric")


@router.post("/biometric/challenge")
async def create_biometric_challenge(
    timeout_seconds: int = Query(60, ge=10, le=300),
    credential_id: Optional[str] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """Create biometric authentication challenge"""
    try:
        user_id = _get_user_id(current_user) if current_user else 0
        
        challenge = biometric_auth_service.create_challenge(
            user_id=user_id,
            credential_id=credential_id,
            timeout_seconds=timeout_seconds,
        )
        
        import base64
        return {
            "challenge_id": challenge.challenge_id,
            "challenge_data": base64.b64encode(challenge.challenge_data).decode(),
            "expires_at": challenge.expires_at.isoformat(),
        }
    except Exception as e:
        logger.error(f"Error creating challenge: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create challenge")


@router.post("/biometric/verify")
async def verify_biometric(
    request: VerifyBiometricRequest,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """Verify biometric authentication"""
    try:
        import base64
        signature = base64.b64decode(request.signature)
        authenticator_data = base64.b64decode(request.authenticator_data)
        
        is_valid = biometric_auth_service.verify_biometric(
            challenge_id=request.challenge_id,
            credential_id=request.credential_id,
            signature=signature,
            authenticator_data=authenticator_data,
        )
        
        return {
            "verified": is_valid,
            "credential_id": request.credential_id,
        }
    except Exception as e:
        logger.error(f"Error verifying biometric: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to verify biometric")


@router.get("/biometric/credentials")
async def get_biometric_credentials(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get user's biometric credentials"""
    try:
        user_id = _get_user_id(current_user)
        credentials = biometric_auth_service.get_user_credentials(user_id)
        
        return [
            {
                "credential_id": c.credential_id,
                "biometric_type": c.biometric_type,
                "device_id": c.device_id,
                "last_used": c.last_used.isoformat() if c.last_used else None,
                "created_at": c.created_at.isoformat(),
            }
            for c in credentials
        ]
    except Exception as e:
        logger.error(f"Error getting credentials: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get credentials")


# DID Endpoints
@router.post("/did/create")
async def create_did(
    request: CreateDIDRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Create a new DID"""
    try:
        user_id = _get_user_id(current_user)
        
        document = did_service.create_did(
            method=request.method,
            user_id=user_id,
        )
        
        return {
            "did": document.did,
            "verification_methods": document.verification_methods,
            "authentication": document.authentication,
            "created": document.created.isoformat(),
        }
    except Exception as e:
        logger.error(f"Error creating DID: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create DID")


@router.get("/did/{did}")
async def resolve_did(
    did: str,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """Resolve a DID to its document"""
    try:
        document = did_service.resolve_did(did)
        
        if not document:
            raise HTTPException(status_code=404, detail="DID not found")
        
        return {
            "did": document.did,
            "context": document.context,
            "verification_methods": document.verification_methods,
            "authentication": document.authentication,
            "service_endpoints": document.service_endpoints,
            "created": document.created.isoformat(),
            "updated": document.updated.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving DID: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to resolve DID")


@router.post("/did/credentials/issue")
async def issue_credential(
    request: IssueCredentialRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Issue a verifiable credential"""
    try:
        credential = did_service.issue_credential(
            issuer_did=request.issuer_did,
            subject_did=request.subject_did,
            credential_type=request.credential_type,
            claims=request.claims,
            expires_days=request.expires_days,
        )
        
        return {
            "credential_id": credential.credential_id,
            "did": credential.did,
            "subject_did": credential.subject_did,
            "credential_type": credential.credential_type,
            "claims": credential.claims,
            "issued": credential.issued.isoformat(),
            "expires": credential.expires.isoformat() if credential.expires else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error issuing credential: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to issue credential")


@router.post("/did/presentations/create")
async def create_presentation(
    request: CreatePresentationRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Create a verifiable presentation"""
    try:
        presentation = did_service.create_presentation(
            holder_did=request.holder_did,
            credential_ids=request.credential_ids,
        )
        
        return {
            "presentation_id": presentation.presentation_id,
            "holder_did": presentation.holder_did,
            "credential_count": len(presentation.verifiable_credentials),
            "created": presentation.created.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating presentation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create presentation")


@router.post("/did/credentials/{credential_id}/verify")
async def verify_credential(
    credential_id: str,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """Verify a verifiable credential"""
    try:
        is_valid = did_service.verify_credential(credential_id)
        
        return {
            "credential_id": credential_id,
            "verified": is_valid,
        }
    except Exception as e:
        logger.error(f"Error verifying credential: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to verify credential")


@router.post("/did/presentations/{presentation_id}/verify")
async def verify_presentation(
    presentation_id: str,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """Verify a verifiable presentation"""
    try:
        is_valid = did_service.verify_presentation(presentation_id)
        
        return {
            "presentation_id": presentation_id,
            "verified": is_valid,
        }
    except Exception as e:
        logger.error(f"Error verifying presentation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to verify presentation")
