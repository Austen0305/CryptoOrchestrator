"""
GDPR Compliance API Routes
Endpoints for data export, deletion, and consent management
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies.auth import get_current_user
from ..services.gdpr_service import GDPRService
from ..utils.route_helpers import _get_user_id

router = APIRouter(prefix="/api/gdpr", tags=["GDPR"])


# Pydantic Models
class DeleteRequestRequest(BaseModel):
    reason: str = "User requested data deletion"


class ConsentUpdateRequest(BaseModel):
    consent_type: str
    granted: bool


@router.get("/export")
async def export_user_data(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Export all user data (GDPR right to data portability)"""
    service = GDPRService(db)

    try:
        export_data = await service.export_user_data(user_id=_get_user_id(current_user))
        return export_data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error exporting user data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export user data")


@router.post("/delete")
async def delete_user_data(
    request: DeleteRequestRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete all user data (GDPR right to be forgotten)"""
    service = GDPRService(db)

    try:
        deletion_summary = await service.delete_user_data(
            user_id=_get_user_id(current_user),
            reason=request.reason,
        )
        return deletion_summary
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting user data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete user data")


@router.get("/consent")
async def get_consent_status(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get user consent status"""
    service = GDPRService(db)

    try:
        consent_status = await service.get_consent_status(
            user_id=_get_user_id(current_user)
        )
        return consent_status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/consent")
async def update_consent(
    request: ConsentUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Update user consent"""
    service = GDPRService(db)

    try:
        result = await service.update_consent(
            user_id=_get_user_id(current_user),
            consent_type=request.consent_type,
            granted=request.granted,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
