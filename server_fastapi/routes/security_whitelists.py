"""
Security Whitelist Routes
API endpoints for managing IP and withdrawal address whitelists
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..database import get_db_context
from ..dependencies.auth import get_current_user
from ..middleware.cache_manager import cached
from ..services.security.ip_whitelist_service import ip_whitelist_service
from ..services.security.withdrawal_whitelist_service import (
    withdrawal_whitelist_service,
)
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/security/whitelists", tags=["Security Whitelists"])


class AddIPRequest(BaseModel):
    """Request to add IP to whitelist"""

    ip_address: str
    label: str | None = None


class RemoveIPRequest(BaseModel):
    """Request to remove IP from whitelist"""

    ip_address: str


class AddWithdrawalAddressRequest(BaseModel):
    """Request to add withdrawal address to whitelist"""

    address: str
    currency: str
    label: str | None = None


class RemoveWithdrawalAddressRequest(BaseModel):
    """Request to remove withdrawal address from whitelist"""

    address: str
    currency: str


# IP Whitelist Endpoints
@router.post("/ip", response_model=dict[str, Any])
async def add_ip_to_whitelist(
    request: AddIPRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """Add IP address to user's whitelist"""
    try:
        user_id = _get_user_id(current_user)

        async with get_db_context() as db:
            result = await ip_whitelist_service.add_ip_to_whitelist(
                user_id=int(user_id),
                ip_address_str=request.ip_address,
                label=request.label,
                db=db,
            )

            if not result.get("success"):
                raise HTTPException(
                    status_code=400, detail=result.get("error", "Failed to add IP")
                )

            return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding IP to whitelist: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to add IP to whitelist")


@router.delete("/ip", response_model=dict[str, Any])
async def remove_ip_from_whitelist(
    request: RemoveIPRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """Remove IP address from user's whitelist"""
    try:
        user_id = _get_user_id(current_user)

        async with get_db_context() as db:
            result = await ip_whitelist_service.remove_ip_from_whitelist(
                user_id=int(user_id), ip_address_str=request.ip_address, db=db
            )

            if not result.get("success"):
                raise HTTPException(
                    status_code=400, detail=result.get("error", "Failed to remove IP")
                )

            return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing IP from whitelist: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to remove IP from whitelist"
        )


@router.get("/ip", response_model=list[dict[str, Any]])
async def get_ip_whitelist(
    current_user: Annotated[dict, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> list[dict[str, Any]]:
    """Get user's IP whitelist with pagination"""
    try:
        user_id = _get_user_id(current_user)

        async with get_db_context() as db:
            whitelist = await ip_whitelist_service.get_whitelist(
                user_id=int(user_id), db=db
            )

            # Apply pagination
            total = len(whitelist)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_whitelist = whitelist[start_idx:end_idx]

            return paginated_whitelist
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting IP whitelist: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get IP whitelist")


# Withdrawal Address Whitelist Endpoints
@router.post("/withdrawal", response_model=dict[str, Any])
async def add_withdrawal_address(
    request: AddWithdrawalAddressRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """Add withdrawal address to user's whitelist (24-hour cooldown applies)"""
    try:
        user_id = _get_user_id(current_user)

        async with get_db_context() as db:
            result = await withdrawal_whitelist_service.add_withdrawal_address(
                user_id=int(user_id),
                address=request.address,
                currency=request.currency,
                label=request.label,
                db=db,
            )

            if not result.get("success"):
                raise HTTPException(
                    status_code=400, detail=result.get("error", "Failed to add address")
                )

            return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding withdrawal address: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to add withdrawal address")


@router.delete("/withdrawal", response_model=dict[str, Any])
async def remove_withdrawal_address(
    request: RemoveWithdrawalAddressRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """Remove withdrawal address from user's whitelist"""
    try:
        user_id = _get_user_id(current_user)

        async with get_db_context() as db:
            result = await withdrawal_whitelist_service.remove_withdrawal_address(
                user_id=int(user_id),
                address=request.address,
                currency=request.currency,
                db=db,
            )

            if not result.get("success"):
                raise HTTPException(
                    status_code=400,
                    detail=result.get("error", "Failed to remove address"),
                )

            return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing withdrawal address: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to remove withdrawal address"
        )


@router.get("/withdrawal", response_model=list[dict[str, Any]])
@cached(
    ttl=300, prefix="withdrawal_whitelist"
)  # 5min TTL for withdrawal whitelist (static config)
async def get_withdrawal_whitelist(
    current_user: Annotated[dict, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    currency: str | None = Query(None, description="Filter by currency"),
) -> list[dict[str, Any]]:
    """Get user's withdrawal address whitelist with pagination"""
    try:
        user_id = _get_user_id(current_user)

        async with get_db_context() as db:
            whitelist = await withdrawal_whitelist_service.get_whitelist(
                user_id=int(user_id), currency=currency, db=db
            )

            # Apply pagination
            total = len(whitelist)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_whitelist = whitelist[start_idx:end_idx]

            return paginated_whitelist
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting withdrawal whitelist: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to get withdrawal whitelist"
        )
