"""
KYC Routes
API endpoints for KYC verification.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Annotated
import logging

from ..services.kyc_service import kyc_service, KYCStatus
from ..dependencies.auth import get_current_user, require_permission
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter()


class KYCSubmissionRequest(BaseModel):
    full_name: str
    date_of_birth: str  # YYYY-MM-DD
    country: str
    document_type: str = "passport"


class KYCStatusUpdateRequest(BaseModel):
    user_id: int
    status: str
    notes: Optional[str] = None


@router.post("/submit")
async def submit_kyc(
    request: KYCSubmissionRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Submit KYC information"""
    try:
        user_id = _get_user_id(current_user)
        email = current_user.get("email", "")

        result = await kyc_service.initiate_kyc(
            user_id=user_id,
            email=email,
            full_name=request.full_name,
            date_of_birth=request.date_of_birth,
            country=request.country,
            document_type=request.document_type,
        )

        return {
            "message": "KYC submission received",
            "status": result["status"],
            "submitted_at": result["submitted_at"],
        }
    except Exception as e:
        logger.error(f"Error submitting KYC: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit KYC")


@router.get("/status")
async def get_kyc_status(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get KYC status for current user"""
    try:
        user_id = _get_user_id(current_user)
        kyc_record = await kyc_service.get_kyc_status(user_id)

        if kyc_record:
            return {
                "status": kyc_record["status"],
                "submitted_at": kyc_record["submitted_at"],
                "reviewed_at": kyc_record.get("reviewed_at"),
                "is_verified": kyc_record["status"] == KYCStatus.APPROVED,
            }
        else:
            return {"status": KYCStatus.NOT_STARTED, "is_verified": False}
    except Exception as e:
        logger.error(f"Error getting KYC status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get KYC status")


@router.post("/update-status")
async def update_kyc_status(
    request: KYCStatusUpdateRequest,
    current_user: Annotated[dict, Depends(require_permission("admin:kyc"))],
):
    """Update KYC status (admin only)"""
    try:
        reviewer_id = _get_user_id(current_user)

        try:
            status = KYCStatus(request.status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid KYC status")

        success = await kyc_service.update_kyc_status(
            user_id=request.user_id,
            status=status,
            reviewer_id=reviewer_id,
            notes=request.notes,
        )

        if success:
            return {"message": "KYC status updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="KYC record not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating KYC status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update KYC status")
