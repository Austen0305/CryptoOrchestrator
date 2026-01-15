"""
Zero-Knowledge Proofs API Routes
Endpoints for ZKP-based wallet balance verification
"""

import logging
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..dependencies.auth import get_current_user
from ..services.security.zkp_service import zkp_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/zkp", tags=["Zero-Knowledge Proofs"])


# Request/Response Models
class GenerateBalanceProofRequest(BaseModel):
    wallet_address: str = Field(..., description="Wallet address")
    balance: float = Field(..., description="Actual balance")
    secret: str | None = Field(None, description="Optional secret for proof generation")


class VerifyBalanceProofRequest(BaseModel):
    wallet_address: str = Field(..., description="Wallet address")
    balance_hash: str = Field(..., description="Hash of the balance")
    proof_data: str = Field(..., description="Proof data (hex encoded)")
    secret: str | None = Field(None, description="Optional secret for verification")


class VerifyBalanceRangeRequest(BaseModel):
    wallet_address: str = Field(..., description="Wallet address")
    min_balance: float = Field(..., description="Minimum balance threshold")
    max_balance: float = Field(..., description="Maximum balance threshold")


@router.post("/balance-proof/generate")
async def generate_balance_proof(
    request: GenerateBalanceProofRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """
    Generate a zero-knowledge proof for balance verification

    Creates a proof that a wallet has a certain balance without revealing
    the actual balance value.
    """
    try:
        balance_proof = zkp_service.generate_balance_proof(
            wallet_address=request.wallet_address,
            balance=request.balance,
            secret=request.secret,
        )

        return {
            "wallet_address": balance_proof.wallet_address,
            "balance_hash": balance_proof.balance_hash,
            "proof_id": balance_proof.proof.proof_id,
            "public_inputs": balance_proof.proof.public_inputs,
            "timestamp": balance_proof.timestamp.isoformat(),
        }
    except Exception as e:
        logger.error(f"Error generating balance proof: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate balance proof")


@router.post("/balance-proof/verify")
async def verify_balance_proof(
    request: VerifyBalanceProofRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """
    Verify a balance proof without knowing the actual balance

    Verifies that a wallet has a balance matching the hash without
    revealing the actual balance value.
    """
    try:
        # Decode proof data from hex
        import binascii

        proof_data = binascii.unhexlify(request.proof_data)

        is_valid = zkp_service.verify_balance_proof(
            wallet_address=request.wallet_address,
            balance_hash=request.balance_hash,
            proof_data=proof_data,
            secret=request.secret,
        )

        return {
            "wallet_address": request.wallet_address,
            "verified": is_valid,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error verifying balance proof: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to verify balance proof")


@router.post("/balance-proof/verify-range")
async def verify_balance_range(
    request: VerifyBalanceRangeRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """
    Verify that balance is within a range without revealing actual balance

    Uses range proofs to verify balance is between min and max values
    without revealing the exact amount.
    """
    try:
        is_in_range = zkp_service.verify_balance_range(
            wallet_address=request.wallet_address,
            min_balance=request.min_balance,
            max_balance=request.max_balance,
        )

        return {
            "wallet_address": request.wallet_address,
            "min_balance": request.min_balance,
            "max_balance": request.max_balance,
            "in_range": is_in_range,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error verifying balance range: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to verify balance range")


@router.get("/balance-proof/{wallet_address}")
async def get_balance_proof(
    wallet_address: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """Get balance proof for a wallet"""
    try:
        balance_proof = zkp_service.get_balance_proof(wallet_address)

        if not balance_proof:
            raise HTTPException(status_code=404, detail="Balance proof not found")

        return {
            "wallet_address": balance_proof.wallet_address,
            "balance_hash": balance_proof.balance_hash,
            "proof_id": balance_proof.proof.proof_id,
            "public_inputs": balance_proof.proof.public_inputs,
            "verified": balance_proof.proof.verified,
            "created_at": balance_proof.proof.created_at.isoformat(),
            "verification_timestamp": (
                balance_proof.proof.verification_timestamp.isoformat()
                if balance_proof.proof.verification_timestamp
                else None
            ),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting balance proof: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get balance proof")


@router.get("/proofs")
async def list_proofs(
    current_user: Annotated[dict, Depends(get_current_user)],
    wallet_address: str | None = Query(None, description="Filter by wallet address"),
) -> dict[str, Any]:
    """List all proofs, optionally filtered by wallet"""
    try:
        proofs = zkp_service.list_proofs(wallet_address)

        return {
            "proofs": [
                {
                    "proof_id": p.proof_id,
                    "statement": p.statement,
                    "public_inputs": p.public_inputs,
                    "created_at": p.created_at.isoformat(),
                    "verified": p.verified,
                }
                for p in proofs
            ],
            "count": len(proofs),
        }
    except Exception as e:
        logger.error(f"Error listing proofs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list proofs")


@router.get("/proof/{proof_id}/export")
async def export_proof(
    proof_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """Export proof for external verification"""
    try:
        proof_data = zkp_service.export_proof(proof_id)

        if not proof_data:
            raise HTTPException(status_code=404, detail="Proof not found")

        return proof_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting proof: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export proof")
