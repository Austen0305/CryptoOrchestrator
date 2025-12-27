"""
MPC and TECDSA API Routes
Endpoints for multi-party computation and threshold ECDSA
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Annotated
from datetime import datetime
import logging

from ..dependencies.auth import get_current_user
from ..services.security.mpc_service import mpc_service
from ..services.security.tecdsa_service import tecdsa_service
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/security", tags=["MPC & TECDSA"])


# Request/Response Models
class RegisterPartyRequest(BaseModel):
    party_id: str = Field(..., description="Party identifier")
    name: str = Field(..., description="Party name")
    role: str = Field("signer", description="Party role")
    public_key: Optional[str] = Field(None, description="Party public key")


class GenerateMPCKeyRequest(BaseModel):
    wallet_id: str = Field(..., description="Wallet identifier")
    parties: List[str] = Field(..., description="List of party IDs")
    threshold: int = Field(..., ge=2, description="Minimum parties needed")


class MPCSignRequest(BaseModel):
    wallet_id: str = Field(..., description="Wallet identifier")
    message_hash: str = Field(..., description="Hash of message to sign")
    participating_parties: List[str] = Field(..., description="Parties participating")


class GenerateTECDSAKeyRequest(BaseModel):
    wallet_address: str = Field(..., description="Wallet address")
    parties: List[str] = Field(..., description="List of party IDs")
    threshold: int = Field(..., ge=2, description="Minimum parties needed")


class TECDSASignRequest(BaseModel):
    wallet_address: str = Field(..., description="Wallet address")
    transaction_hash: str = Field(..., description="Transaction hash to sign")
    participating_parties: List[str] = Field(..., description="Parties participating")


# MPC Endpoints
@router.post("/mpc/parties")
async def register_party(
    request: RegisterPartyRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Register a party for MPC operations"""
    try:
        party = mpc_service.register_party(
            party_id=request.party_id,
            name=request.name,
            role=request.role,
            public_key=request.public_key,
        )
        
        return {
            "party_id": party.party_id,
            "name": party.name,
            "role": party.role,
            "public_key": party.public_key,
            "enabled": party.enabled,
        }
    except Exception as e:
        logger.error(f"Error registering party: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to register party")


@router.get("/mpc/parties")
async def list_parties(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """List all registered parties"""
    try:
        parties = mpc_service.list_parties()
        
        return [
            {
                "party_id": p.party_id,
                "name": p.name,
                "role": p.role,
                "enabled": p.enabled,
            }
            for p in parties
        ]
    except Exception as e:
        logger.error(f"Error listing parties: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list parties")


@router.post("/mpc/keys/generate")
async def generate_mpc_key(
    request: GenerateMPCKeyRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Generate distributed key using MPC"""
    try:
        public_key, shares = mpc_service.generate_distributed_key(
            wallet_id=request.wallet_id,
            parties=request.parties,
            threshold=request.threshold,
        )
        
        return {
            "wallet_id": request.wallet_id,
            "public_key": public_key,
            "threshold": request.threshold,
            "total_shares": len(shares),
            "shares": [
                {
                    "share_id": s.share_id,
                    "party_id": s.party_id,
                    "threshold": s.threshold,
                }
                for s in shares
            ],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating MPC key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate MPC key")


@router.post("/mpc/sign")
async def sign_with_mpc(
    request: MPCSignRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Sign message using MPC"""
    try:
        signature = mpc_service.sign_with_mpc(
            wallet_id=request.wallet_id,
            message_hash=request.message_hash,
            participating_parties=request.participating_parties,
        )
        
        return {
            "signature_id": signature.signature_id,
            "wallet_id": signature.wallet_id,
            "message_hash": signature.message_hash,
            "signature": signature.signature.hex(),
            "parties": signature.parties,
            "verified": signature.verified,
            "created_at": signature.created_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error signing with MPC: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to sign with MPC")


@router.get("/mpc/keys/{wallet_id}")
async def get_mpc_key_shares(
    wallet_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get key shares for a wallet"""
    try:
        shares = mpc_service.get_key_shares(wallet_id)
        
        if not shares:
            raise HTTPException(status_code=404, detail="Key shares not found")
        
        return {
            "wallet_id": wallet_id,
            "shares": [
                {
                    "share_id": s.share_id,
                    "party_id": s.party_id,
                    "threshold": s.threshold,
                    "total_shares": s.total_shares,
                }
                for s in shares
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting key shares: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get key shares")


# TECDSA Endpoints
@router.post("/tecdsa/keys/generate")
async def generate_tecdsa_key(
    request: GenerateTECDSAKeyRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Generate threshold ECDSA key"""
    try:
        public_key, shares = tecdsa_service.generate_threshold_key(
            wallet_address=request.wallet_address,
            parties=request.parties,
            threshold=request.threshold,
        )
        
        return {
            "wallet_address": request.wallet_address,
            "public_key": public_key,
            "threshold": request.threshold,
            "total_shares": len(shares),
            "shares": [
                {
                    "share_id": s.share_id,
                    "party_id": s.party_id,
                    "share_index": s.share_index,
                }
                for s in shares
            ],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating TECDSA key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate TECDSA key")


@router.post("/tecdsa/sign")
async def sign_with_tecdsa(
    request: TECDSASignRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Sign transaction using threshold ECDSA"""
    try:
        signature = tecdsa_service.sign_transaction(
            wallet_address=request.wallet_address,
            transaction_hash=request.transaction_hash,
            participating_parties=request.participating_parties,
        )
        
        return {
            "signature_id": signature.signature_id,
            "wallet_address": signature.wallet_address,
            "transaction_hash": signature.transaction_hash,
            "r": signature.r,
            "s": signature.s,
            "v": signature.v,
            "parties": signature.parties,
            "verified": signature.verified,
            "created_at": signature.created_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error signing with TECDSA: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to sign with TECDSA")


@router.get("/tecdsa/keys/{wallet_address}")
async def get_tecdsa_key_shares(
    wallet_address: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get TECDSA key shares for a wallet"""
    try:
        shares = tecdsa_service.get_key_shares(wallet_address)
        
        if not shares:
            raise HTTPException(status_code=404, detail="Key shares not found")
        
        return {
            "wallet_address": wallet_address,
            "shares": [
                {
                    "share_id": s.share_id,
                    "party_id": s.party_id,
                    "share_index": s.share_index,
                    "threshold": s.threshold,
                }
                for s in shares
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting TECDSA key shares: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get key shares")
