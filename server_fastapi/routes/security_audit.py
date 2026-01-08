"""
Security Audit Routes
Provides endpoints for security auditing
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from ..middleware.auth import get_current_user
from ..utils.security_audit import security_auditor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/security", tags=["Security"])


@router.get("/audit")
async def run_security_audit(
    current_user: dict = Depends(get_current_user),
):
    """Run comprehensive security audit (admin only)"""
    # Admin check
    if current_user.get("role") != "admin" and not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    try:
        audit_results = security_auditor.run_full_audit()
        return audit_results
    except Exception as e:
        logger.error(f"Error running security audit: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run security audit: {str(e)}",
        )


@router.get("/audit/configuration")
async def audit_configuration(
    current_user: dict = Depends(get_current_user),
):
    """Audit configuration security"""
    try:
        return security_auditor.audit_configuration()
    except Exception as e:
        logger.error(f"Error auditing configuration: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to audit configuration: {str(e)}",
        )


@router.get("/audit/secrets")
async def scan_secrets(
    current_user: dict = Depends(get_current_user),
):
    """Scan for exposed secrets"""
    try:
        return security_auditor.scan_for_secrets()
    except Exception as e:
        logger.error(f"Error scanning for secrets: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scan for secrets: {str(e)}",
        )


@router.get("/audit/dependencies")
async def audit_dependencies(
    current_user: dict = Depends(get_current_user),
):
    """Audit dependencies for vulnerabilities"""
    try:
        return security_auditor.audit_dependencies()
    except Exception as e:
        logger.error(f"Error auditing dependencies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to audit dependencies: {str(e)}",
        )
