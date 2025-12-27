"""
Institutional Wallet Routes
API endpoints for multi-signature wallets, team access, and institutional custody
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Annotated
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.institutional_wallet_service import InstitutionalWalletService
from ..services.institutional.treasury_service import TreasuryService
from ..services.institutional.social_recovery import SocialRecoveryService
from ..services.institutional.threshold_signatures import threshold_signature_service
from ..dependencies.auth import get_current_user
from ..database import get_db_session
from ..utils.route_helpers import _get_user_id
from ..middleware.cache_manager import cached
from ..models.institutional_wallet import (
    InstitutionalWallet,
    PendingTransaction,
    WalletType,
    MultisigType,
    WalletStatus,
    SignerRole,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class CreateInstitutionalWalletRequest(BaseModel):
    wallet_type: str = Field(..., description="Wallet type: multisig, timelock, treasury, custodial")
    chain_id: int = Field(1, description="Blockchain ID")
    multisig_type: Optional[str] = Field(None, description="Multi-signature type: 2_of_3, 3_of_5, custom")
    required_signatures: int = Field(1, ge=1, description="M in M-of-N (minimum signatures required)")
    total_signers: int = Field(1, ge=1, description="N in M-of-N (total number of signers)")
    signer_user_ids: Optional[List[int]] = Field(None, description="List of user IDs to add as signers")
    label: Optional[str] = Field(None, description="User-friendly label")
    description: Optional[str] = Field(None, description="Wallet description")
    unlock_time: Optional[datetime] = Field(None, description="When time-locked wallet unlocks")
    config: Optional[dict] = Field(None, description="Additional configuration")


class AddSignerRequest(BaseModel):
    signer_user_id: int
    role: str = Field(SignerRole.SIGNER.value, description="Signer role: owner, signer, viewer, admin")


class CreatePendingTransactionRequest(BaseModel):
    transaction_type: str = Field(..., description="Type: withdrawal, transfer, approval, etc.")
    transaction_data: dict = Field(..., description="Full transaction data")
    description: Optional[str] = None
    expires_in_hours: int = Field(24, ge=1, le=168, description="Hours until transaction expires")


class SignTransactionRequest(BaseModel):
    signature_data: dict = Field(..., description="Signature data (signature, message hash, etc.)")


class InstitutionalWalletResponse(BaseModel):
    id: int
    user_id: int
    wallet_type: str
    wallet_address: Optional[str]
    chain_id: int
    multisig_type: Optional[str]
    required_signatures: int
    total_signers: int
    status: str
    label: Optional[str]
    description: Optional[str]
    balance: Optional[dict]
    created_at: str
    updated_at: str


class PendingTransactionResponse(BaseModel):
    id: int
    wallet_id: int
    transaction_type: str
    to_address: Optional[str]
    amount: Optional[float]
    currency: Optional[str]
    status: str
    signatures: dict
    required_signatures: int
    signature_count: int
    expires_at: Optional[str]
    description: Optional[str]
    created_at: str


@router.post("/", response_model=InstitutionalWalletResponse)
async def create_institutional_wallet(
    request: CreateInstitutionalWalletRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Create a new institutional wallet"""
    try:
        user_id = _get_user_id(current_user)
        service = InstitutionalWalletService(db)
        
        wallet = await service.create_institutional_wallet(
            user_id=user_id,
            wallet_type=request.wallet_type,
            chain_id=request.chain_id,
            multisig_type=request.multisig_type,
            required_signatures=request.required_signatures,
            total_signers=request.total_signers,
            signer_user_ids=request.signer_user_ids,
            label=request.label,
            description=request.description,
            unlock_time=request.unlock_time,
            config=request.config,
        )
        
        return InstitutionalWalletResponse(
            id=wallet.id,
            user_id=wallet.user_id,
            wallet_type=wallet.wallet_type,
            wallet_address=wallet.wallet_address,
            chain_id=wallet.chain_id,
            multisig_type=wallet.multisig_type,
            required_signatures=wallet.required_signatures,
            total_signers=wallet.total_signers,
            status=wallet.status,
            label=wallet.label,
            description=wallet.description,
            balance=wallet.balance,
            created_at=wallet.created_at.isoformat(),
            updated_at=wallet.updated_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating institutional wallet: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create institutional wallet")


@router.get("/", response_model=List[InstitutionalWalletResponse])
async def list_institutional_wallets(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    wallet_type: Optional[str] = Query(None, description="Filter by wallet type"),
    status: Optional[str] = Query(None, description="Filter by status"),
):
    """List institutional wallets accessible by current user"""
    try:
        user_id = _get_user_id(current_user)
        service = InstitutionalWalletService(db)
        
        wallets = await service.list_wallets(
            user_id=user_id,
            wallet_type=wallet_type,
            status=status,
        )
        
        return [
            InstitutionalWalletResponse(
                id=w.id,
                user_id=w.user_id,
                wallet_type=w.wallet_type,
                wallet_address=w.wallet_address,
                chain_id=w.chain_id,
                multisig_type=w.multisig_type,
                required_signatures=w.required_signatures,
                total_signers=w.total_signers,
                status=w.status,
                label=w.label,
                description=w.description,
                balance=w.balance,
                created_at=w.created_at.isoformat(),
                updated_at=w.updated_at.isoformat(),
            )
            for w in wallets
        ]
    except Exception as e:
        logger.error(f"Error listing institutional wallets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list institutional wallets")


@router.get("/{wallet_id}", response_model=InstitutionalWalletResponse)
async def get_institutional_wallet(
    wallet_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get institutional wallet details"""
    try:
        user_id = _get_user_id(current_user)
        service = InstitutionalWalletService(db)
        
        wallet = await service.get_wallet(wallet_id, user_id)
        
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found or access denied")
        
        return InstitutionalWalletResponse(
            id=wallet.id,
            user_id=wallet.user_id,
            wallet_type=wallet.wallet_type,
            wallet_address=wallet.wallet_address,
            chain_id=wallet.chain_id,
            multisig_type=wallet.multisig_type,
            required_signatures=wallet.required_signatures,
            total_signers=wallet.total_signers,
            status=wallet.status,
            label=wallet.label,
            description=wallet.description,
            balance=wallet.balance,
            created_at=wallet.created_at.isoformat(),
            updated_at=wallet.updated_at.isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting institutional wallet: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get institutional wallet")


@router.post("/{wallet_id}/signers", response_model=dict)
async def add_signer(
    wallet_id: int,
    request: AddSignerRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Add a signer to an institutional wallet"""
    try:
        user_id = _get_user_id(current_user)
        service = InstitutionalWalletService(db)
        
        success = await service.add_signer(
            wallet_id=wallet_id,
            signer_user_id=request.signer_user_id,
            role=request.role,
            added_by_user_id=user_id,
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add signer")
        
        return {"success": True, "message": "Signer added successfully"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding signer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to add signer")


@router.delete("/{wallet_id}/signers/{signer_user_id}", response_model=dict)
async def remove_signer(
    wallet_id: int,
    signer_user_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Remove a signer from an institutional wallet"""
    try:
        user_id = _get_user_id(current_user)
        service = InstitutionalWalletService(db)
        
        success = await service.remove_signer(
            wallet_id=wallet_id,
            signer_user_id=signer_user_id,
            removed_by_user_id=user_id,
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to remove signer")
        
        return {"success": True, "message": "Signer removed successfully"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error removing signer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to remove signer")


@router.post("/{wallet_id}/transactions", response_model=PendingTransactionResponse)
async def create_pending_transaction(
    wallet_id: int,
    request: CreatePendingTransactionRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Create a pending transaction requiring signatures"""
    try:
        user_id = _get_user_id(current_user)
        service = InstitutionalWalletService(db)
        
        pending_tx = await service.create_pending_transaction(
            wallet_id=wallet_id,
            transaction_type=request.transaction_type,
            transaction_data=request.transaction_data,
            created_by_user_id=user_id,
            description=request.description,
            expires_in_hours=request.expires_in_hours,
        )
        
        return PendingTransactionResponse(
            id=pending_tx.id,
            wallet_id=pending_tx.wallet_id,
            transaction_type=pending_tx.transaction_type,
            to_address=pending_tx.to_address,
            amount=pending_tx.amount,
            currency=pending_tx.currency,
            status=pending_tx.status,
            signatures=pending_tx.signatures,
            required_signatures=pending_tx.required_signatures,
            signature_count=len(pending_tx.signatures),
            expires_at=pending_tx.expires_at.isoformat() if pending_tx.expires_at else None,
            description=pending_tx.description,
            created_at=pending_tx.created_at.isoformat(),
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating pending transaction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create pending transaction")


@router.post("/transactions/{transaction_id}/sign", response_model=dict)
async def sign_transaction(
    transaction_id: int,
    request: SignTransactionRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Sign a pending transaction"""
    try:
        user_id = _get_user_id(current_user)
        service = InstitutionalWalletService(db)
        
        fully_signed = await service.sign_transaction(
            transaction_id=transaction_id,
            user_id=user_id,
            signature_data=request.signature_data,
        )
        
        return {
            "success": True,
            "fully_signed": fully_signed,
            "message": "Transaction fully signed and ready to execute" if fully_signed else "Transaction signed, awaiting more signatures",
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error signing transaction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to sign transaction")


@router.get("/{wallet_id}/transactions", response_model=List[PendingTransactionResponse])
async def list_pending_transactions(
    wallet_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: Optional[str] = Query(None, description="Filter by status"),
):
    """List pending transactions for a wallet"""
    try:
        user_id = _get_user_id(current_user)
        service = InstitutionalWalletService(db)
        
        # Check permissions
        wallet = await service.get_wallet(wallet_id, user_id)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found or access denied")
        
        # Get pending transactions
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        query = select(PendingTransaction).where(
            PendingTransaction.wallet_id == wallet_id
        )
        
        if status:
            query = query.where(PendingTransaction.status == status)
        
        query = query.order_by(PendingTransaction.created_at.desc())
        
        result = await db.execute(query.options(selectinload(PendingTransaction.wallet)))
        pending_txs = result.scalars().all()
        
        return [
            PendingTransactionResponse(
                id=tx.id,
                wallet_id=tx.wallet_id,
                transaction_type=tx.transaction_type,
                to_address=tx.to_address,
                amount=tx.amount,
                currency=tx.currency,
                status=tx.status,
                signatures=tx.signatures,
                required_signatures=tx.required_signatures,
                signature_count=len(tx.signatures),
                expires_at=tx.expires_at.isoformat() if tx.expires_at else None,
                description=tx.description,
                created_at=tx.created_at.isoformat(),
            )
            for tx in pending_txs
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing pending transactions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list pending transactions")


@router.get("/{wallet_id}/audit-logs", response_model=List[dict])
async def get_audit_logs(
    wallet_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    start_date: Optional[datetime] = Query(None, description="Start date for audit log export"),
    end_date: Optional[datetime] = Query(None, description="End date for audit log export"),
    user_id_filter: Optional[int] = Query(None, alias="user_id", description="Filter by user ID"),
):
    """Export audit logs for compliance"""
    try:
        current_user_id = _get_user_id(current_user)
        service = InstitutionalWalletService(db)
        
        # Check permissions (admin or owner)
        wallet = await service.get_wallet(wallet_id, current_user_id)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found or access denied")
        
        if not await service.has_permission(wallet_id, current_user_id, "admin"):
            raise HTTPException(status_code=403, detail="Admin access required for audit logs")
        
        logs = await service.export_audit_logs(
            wallet_id=wallet_id,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id_filter,
        )
        
        return [
            {
                "id": log.id,
                "wallet_id": log.wallet_id,
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "success": log.success,
                "error_message": log.error_message,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "details": log.details,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting audit logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export audit logs")


# Treasury Management Endpoints
@router.get("/treasury/summary", response_model=dict)
async def get_treasury_summary(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get comprehensive treasury summary"""
    try:
        user_id = _get_user_id(current_user)
        service = TreasuryService(lambda: db)
        
        summary = service.get_treasury_summary(user_id)
        
        return {
            "total_balance_usd": float(summary.total_balance_usd),
            "total_wallets": summary.total_wallets,
            "active_wallets": summary.active_wallets,
            "pending_transactions": summary.pending_transactions,
            "total_transactions_24h": summary.total_transactions_24h,
            "total_volume_24h_usd": float(summary.total_volume_24h_usd),
            "average_transaction_size_usd": float(summary.average_transaction_size_usd),
            "largest_wallet_balance_usd": float(summary.largest_wallet_balance_usd),
            "smallest_wallet_balance_usd": float(summary.smallest_wallet_balance_usd),
        }
    except Exception as e:
        logger.error(f"Error getting treasury summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get treasury summary")


@router.get("/treasury/balances", response_model=List[dict])
async def get_wallet_balances(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get balances for all wallets"""
    try:
        user_id = _get_user_id(current_user)
        service = TreasuryService(lambda: db)
        
        balances = service.get_wallet_balances(user_id)
        
        return [
            {
                "wallet_id": b.wallet_id,
                "wallet_name": b.wallet_name,
                "balance_usd": float(b.balance_usd),
                "balance_native": float(b.balance_native),
                "currency": b.currency,
                "pending_balance_usd": float(b.pending_balance_usd),
                "available_balance_usd": float(b.available_balance_usd),
                "last_activity": b.last_activity.isoformat() if b.last_activity else None,
                "signer_count": b.signer_count,
                "required_signatures": b.required_signatures,
            }
            for b in balances
        ]
    except Exception as e:
        logger.error(f"Error getting wallet balances: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get wallet balances")


@router.get("/treasury/activity", response_model=List[dict])
async def get_treasury_activity(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(100, ge=1, le=1000),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
):
    """Get treasury activity log"""
    try:
        user_id = _get_user_id(current_user)
        service = TreasuryService(lambda: db)
        
        activities = service.get_treasury_activity(
            user_id=user_id,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
        )
        
        return [
            {
                "timestamp": a.timestamp.isoformat(),
                "wallet_id": a.wallet_id,
                "wallet_name": a.wallet_name,
                "activity_type": a.activity_type,
                "amount_usd": float(a.amount_usd) if a.amount_usd else None,
                "currency": a.currency,
                "status": a.status,
                "description": a.description,
            }
            for a in activities
        ]
    except Exception as e:
        logger.error(f"Error getting treasury activity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get treasury activity")


@router.get("/treasury/risk-metrics", response_model=dict)
async def get_risk_metrics(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get treasury risk metrics"""
    try:
        user_id = _get_user_id(current_user)
        service = TreasuryService(lambda: db)
        
        metrics = service.get_risk_metrics(user_id)
        return metrics
    except Exception as e:
        logger.error(f"Error getting risk metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get risk metrics")


# Social Recovery Endpoints
class CreateRecoveryRequest(BaseModel):
    wallet_id: int
    reason: str = Field(..., description="Reason for recovery")
    required_approvals: int = Field(3, ge=1, le=10, description="Number of approvals needed")
    timeout_hours: Optional[int] = Field(72, ge=1, le=168, description="Timeout in hours")


class ApproveRecoveryRequest(BaseModel):
    signature: Optional[str] = Field(None, description="Optional cryptographic signature")


class RejectRecoveryRequest(BaseModel):
    reason: Optional[str] = Field(None, description="Rejection reason")


# Guardian Management Endpoints
class AddGuardianRequest(BaseModel):
    guardian_user_id: Optional[int] = Field(None, description="User ID of guardian (if platform user)")
    email: Optional[str] = Field(None, description="Guardian email (if not platform user)")
    phone: Optional[str] = Field(None, description="Guardian phone (for SMS verification)")
    notes: Optional[str] = Field(None, description="Optional notes about guardian")


@router.post("/{wallet_id}/guardians", response_model=dict)
async def add_guardian(
    wallet_id: int,
    request: AddGuardianRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Add a guardian to an institutional wallet"""
    try:
        user_id = _get_user_id(current_user)
        service = SocialRecoveryService(db)
        
        guardian = await service.add_guardian(
            wallet_id=wallet_id,
            guardian_user_id=request.guardian_user_id,
            email=request.email,
            phone=request.phone,
            added_by=user_id,
            notes=request.notes,
        )
        
        return {
            "id": guardian.id,
            "wallet_id": guardian.wallet_id,
            "guardian_user_id": guardian.guardian_user_id,
            "email": guardian.email,
            "phone": guardian.phone,
            "status": guardian.status,
            "created_at": guardian.created_at.isoformat(),
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding guardian: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to add guardian")


@router.delete("/{wallet_id}/guardians/{guardian_id}", response_model=dict)
async def remove_guardian(
    wallet_id: int,
    guardian_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Remove a guardian from an institutional wallet"""
    try:
        user_id = _get_user_id(current_user)
        service = SocialRecoveryService(db)
        
        success = await service.remove_guardian(
            wallet_id=wallet_id,
            guardian_id=guardian_id,
            removed_by=user_id,
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to remove guardian")
        
        return {"success": True, "guardian_id": guardian_id}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error removing guardian: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to remove guardian")


@router.get("/{wallet_id}/guardians", response_model=List[dict])
async def get_guardians(
    wallet_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: Optional[str] = Query(None, description="Filter by status"),
):
    """Get all guardians for a wallet"""
    try:
        service = SocialRecoveryService(db)
        
        guardian_status = None
        if status:
            from ...models.social_recovery import GuardianStatus
            guardian_status = GuardianStatus(status)
        
        guardians = await service.get_guardians(wallet_id, guardian_status)
        
        return [
            {
                "id": g.id,
                "wallet_id": g.wallet_id,
                "guardian_user_id": g.guardian_user_id,
                "email": g.email,
                "phone": g.phone,
                "status": g.status,
                "verified_at": g.verified_at.isoformat() if g.verified_at else None,
                "added_by": g.added_by,
                "notes": g.notes,
                "created_at": g.created_at.isoformat(),
            }
            for g in guardians
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid status: {e}")
    except Exception as e:
        logger.error(f"Error getting guardians: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get guardians")


@router.post("/recovery/requests", response_model=dict)
async def create_recovery_request(
    request: CreateRecoveryRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Create a social recovery request"""
    try:
        user_id = _get_user_id(current_user)
        service = SocialRecoveryService(db)
        
        recovery_request = await service.create_recovery_request(
            wallet_id=request.wallet_id,
            requester_id=user_id,
            reason=request.reason,
            required_approvals=request.required_approvals,
            time_lock_days=7,  # Default 7 days, can be made configurable
        )
        
        return {
            "id": recovery_request.id,
            "wallet_id": recovery_request.wallet_id,
            "requester_id": recovery_request.requester_id,
            "reason": recovery_request.reason,
            "status": recovery_request.status,
            "required_approvals": recovery_request.required_approvals,
            "current_approvals": recovery_request.current_approvals,
            "time_lock_days": recovery_request.time_lock_days,
            "unlock_time": recovery_request.unlock_time.isoformat() if recovery_request.unlock_time else None,
            "expires_at": recovery_request.expires_at.isoformat() if recovery_request.expires_at else None,
            "created_at": recovery_request.created_at.isoformat(),
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating recovery request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create recovery request")


@router.post("/recovery/requests/{recovery_request_id}/approve", response_model=dict)
async def approve_recovery(
    recovery_request_id: int,
    request: ApproveRecoveryRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Approve a recovery request"""
    try:
        user_id = _get_user_id(current_user)
        service = SocialRecoveryService(db)
        
        # Get recovery request to find wallet_id
        recovery_request = await service.get_recovery_request(recovery_request_id)
        if not recovery_request:
            raise HTTPException(status_code=404, detail="Recovery request not found")
        
        # Get guardian_id for this user
        guardians = await service.get_guardians(recovery_request.wallet_id)
        guardian_id = None
        for g in guardians:
            if g.guardian_user_id == user_id:
                guardian_id = g.id
                break
        
        if not guardian_id:
            raise HTTPException(status_code=403, detail="User is not a guardian for this wallet")
        
        success = await service.approve_recovery(
            recovery_request_id=recovery_request_id,
            guardian_id=guardian_id,
            approver_id=user_id,
            signature=request.signature,
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to approve recovery request")
        
        recovery_request = await service.get_recovery_request(recovery_request_id)
        
        return {
            "success": True,
            "recovery_request_id": recovery_request_id,
            "current_approvals": recovery_request.current_approvals,
            "required_approvals": recovery_request.required_approvals,
            "status": recovery_request.status,
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error approving recovery: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to approve recovery")


@router.post("/recovery/requests/{recovery_request_id}/reject", response_model=dict)
async def reject_recovery(
    recovery_request_id: int,
    request: RejectRecoveryRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Reject a recovery request"""
    try:
        user_id = _get_user_id(current_user)
        service = SocialRecoveryService(db)
        
        # Get recovery request to find wallet_id
        recovery_request = await service.get_recovery_request(recovery_request_id)
        if not recovery_request:
            raise HTTPException(status_code=404, detail="Recovery request not found")
        
        # Get guardian_id for this user
        guardians = await service.get_guardians(recovery_request.wallet_id)
        guardian_id = None
        for g in guardians:
            if g.guardian_user_id == user_id:
                guardian_id = g.id
                break
        
        if not guardian_id:
            raise HTTPException(status_code=403, detail="User is not a guardian for this wallet")
        
        success = await service.reject_recovery(
            recovery_request_id=recovery_request_id,
            guardian_id=guardian_id,
            rejector_id=user_id,
            reason=request.reason,
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to reject recovery request")
        
        return {"success": True, "recovery_request_id": recovery_request_id}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error rejecting recovery: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to reject recovery")


@router.post("/recovery/requests/{recovery_request_id}/execute", response_model=dict)
async def execute_recovery(
    recovery_request_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Execute a recovery (after approvals and time-lock)"""
    try:
        user_id = _get_user_id(current_user)
        service = SocialRecoveryService(db)
        
        success = await service.execute_recovery(
            recovery_request_id=recovery_request_id,
            executor_id=user_id,
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to execute recovery")
        
        return {"success": True, "recovery_request_id": recovery_request_id}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing recovery: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to execute recovery")


@router.get("/recovery/requests/{recovery_request_id}", response_model=dict)
async def get_recovery_request(
    recovery_request_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get a recovery request"""
    try:
        service = SocialRecoveryService(db)
        recovery_request = await service.get_recovery_request(recovery_request_id)
        
        if not recovery_request:
            raise HTTPException(status_code=404, detail="Recovery request not found")
        
        approvals = await service.get_recovery_approvals(recovery_request_id)
        
        return {
            "id": recovery_request.id,
            "wallet_id": recovery_request.wallet_id,
            "requester_id": recovery_request.requester_id,
            "reason": recovery_request.reason,
            "status": recovery_request.status,
            "required_approvals": recovery_request.required_approvals,
            "current_approvals": recovery_request.current_approvals,
            "time_lock_days": recovery_request.time_lock_days,
            "unlock_time": recovery_request.unlock_time.isoformat() if recovery_request.unlock_time else None,
            "created_at": recovery_request.created_at.isoformat(),
            "expires_at": recovery_request.expires_at.isoformat() if recovery_request.expires_at else None,
            "completed_at": recovery_request.completed_at.isoformat() if recovery_request.completed_at else None,
            "approvals": [
                {
                    "guardian_id": a.guardian_id,
                    "approver_id": a.approver_id,
                    "approved_at": a.approved_at.isoformat(),
                }
                for a in approvals
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recovery request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get recovery request")


@router.get("/wallets/{wallet_id}/recovery-requests", response_model=List[dict])
async def get_wallet_recovery_requests(
    wallet_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: Optional[str] = Query(None, description="Filter by status"),
):
    """Get all recovery requests for a wallet"""
    try:
        service = SocialRecoveryService(db)
        
        recovery_status = None
        if status:
            from ...models.social_recovery import RecoveryRequestStatus
            recovery_status = RecoveryRequestStatus(status)
        
        requests = await service.get_wallet_recovery_requests(wallet_id, recovery_status)
        
        return [
            {
                "id": r.id,
                "wallet_id": r.wallet_id,
                "requester_id": r.requester_id,
                "reason": r.reason,
                "status": r.status,
                "required_approvals": r.required_approvals,
                "current_approvals": r.current_approvals,
                "time_lock_days": r.time_lock_days,
                "unlock_time": r.unlock_time.isoformat() if r.unlock_time else None,
                "created_at": r.created_at.isoformat(),
                "expires_at": r.expires_at.isoformat() if r.expires_at else None,
            }
            for r in requests
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid status: {e}")
    except Exception as e:
        logger.error(f"Error getting recovery requests: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get recovery requests")


# Threshold Signature Schemes (TSS) Endpoints
class GenerateTSSKeyRequest(BaseModel):
    wallet_id: str = Field(..., description="Wallet identifier")
    parties: List[str] = Field(..., description="List of party IDs")
    threshold: int = Field(..., ge=2, description="Minimum parties needed (t-of-n)")


class GeneratePartialSignatureRequest(BaseModel):
    wallet_id: str = Field(..., description="Wallet identifier")
    message_hash: str = Field(..., description="Hash of message to sign")
    party_id: str = Field(..., description="Party ID generating partial signature")


class CombineTSSSignaturesRequest(BaseModel):
    wallet_id: str = Field(..., description="Wallet identifier")
    message_hash: str = Field(..., description="Hash of message")
    participating_parties: List[str] = Field(..., description="Parties that provided partial signatures")


@router.post("/tss/keys/generate")
async def generate_tss_key(
    request: GenerateTSSKeyRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Generate threshold signature key using DKG"""
    try:
        public_key, shares = threshold_signature_service.generate_threshold_key(
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
                    "share_index": s.share_index,
                }
                for s in shares
            ],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating TSS key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate TSS key")


@router.post("/tss/partial-signature")
async def generate_partial_signature(
    request: GeneratePartialSignatureRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Generate partial signature from a party's share"""
    try:
        partial_sig = threshold_signature_service.generate_partial_signature(
            wallet_id=request.wallet_id,
            message_hash=request.message_hash,
            party_id=request.party_id,
        )
        
        return {
            "partial_sig_id": partial_sig.partial_sig_id,
            "wallet_id": partial_sig.wallet_id,
            "message_hash": partial_sig.message_hash,
            "party_id": partial_sig.party_id,
            "created_at": partial_sig.created_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating partial signature: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate partial signature")


@router.post("/tss/combine-signatures")
async def combine_tss_signatures(
    request: CombineTSSSignaturesRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Combine partial signatures into complete TSS signature"""
    try:
        signature = threshold_signature_service.combine_signatures(
            wallet_id=request.wallet_id,
            message_hash=request.message_hash,
            participating_parties=request.participating_parties,
        )
        
        return {
            "signature_id": signature.signature_id,
            "wallet_id": signature.wallet_id,
            "message_hash": signature.message_hash,
            "r": signature.r,
            "s": signature.s,
            "v": signature.v,
            "participating_parties": signature.participating_parties,
            "verified": signature.verified,
            "created_at": signature.created_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error combining signatures: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to combine signatures")


@router.get("/tss/keys/{wallet_id}")
async def get_tss_key_shares(
    wallet_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get TSS key shares for a wallet"""
    try:
        shares = threshold_signature_service.get_key_shares(wallet_id)
        
        if not shares:
            raise HTTPException(status_code=404, detail="TSS key shares not found")
        
        return {
            "wallet_id": wallet_id,
            "shares": [
                {
                    "share_id": s.share_id,
                    "party_id": s.party_id,
                    "share_index": s.share_index,
                    "threshold": s.threshold,
                    "total_parties": s.total_parties,
                }
                for s in shares
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting TSS key shares: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get TSS key shares")
