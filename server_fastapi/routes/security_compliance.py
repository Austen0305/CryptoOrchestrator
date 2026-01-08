"""
Security Compliance Routes
API endpoints for SOC 2 compliance monitoring and reporting.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies.auth import require_admin
from ..services.security.soc2_compliance_service import SOC2ComplianceService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/soc2/controls/{control_id}")
async def get_control_status(
    control_id: str,
    current_user: Annotated[dict, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    period_days: int = Query(30, ge=1, le=365, description="Period in days"),
):
    """Get status of a specific SOC 2 control"""
    try:
        service = SOC2ComplianceService(db)
        result = await service.check_control_effectiveness(control_id, period_days)
        return result
    except Exception as e:
        logger.error(f"Error getting control status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get control status")


@router.get("/soc2/report")
async def get_compliance_report(
    current_user: Annotated[dict, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    period_days: int = Query(30, ge=1, le=365, description="Period in days"),
):
    """Generate comprehensive SOC 2 compliance report"""
    try:
        service = SOC2ComplianceService(db)
        report = await service.generate_compliance_report(period_days)
        return report
    except Exception as e:
        logger.error(f"Error generating compliance report: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to generate compliance report"
        )


@router.get("/soc2/summary")
async def get_compliance_summary(
    current_user: Annotated[dict, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get quick compliance summary"""
    try:
        service = SOC2ComplianceService(db)
        report = await service.generate_compliance_report(period_days=30)

        return {
            "compliance_percentage": report["summary"]["compliance_percentage"],
            "total_controls": report["summary"]["total_controls"],
            "compliant": report["summary"]["compliant"],
            "needs_attention": report["summary"]["needs_attention"],
            "report_date": report["report_date"],
        }
    except Exception as e:
        logger.error(f"Error getting compliance summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get compliance summary")
