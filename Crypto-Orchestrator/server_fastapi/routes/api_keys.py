"""
API Key Management Routes
Endpoints for API key creation, management, and usage tracking
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db_session
from ..dependencies.auth import get_current_user
from ..utils.route_helpers import _get_user_id
from ..services.api_key_service import APIKeyService

router = APIRouter(prefix="/api/api-keys", tags=["API Keys"])


# Pydantic Models
class CreateAPIKeyRequest(BaseModel):
    key_name: str
    permissions: List[str]  # List of allowed endpoints/methods
    rate_limit: int = 1000  # Requests per hour
    expires_in_days: Optional[int] = None
    description: Optional[str] = None


@router.post("/")
async def create_api_key(
    request: CreateAPIKeyRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new API key"""
    service = APIKeyService(db)
    
    try:
        api_key, full_key = await service.create_api_key(
            user_id=_get_user_id(current_user),
            key_name=request.key_name,
            permissions=request.permissions,
            rate_limit=request.rate_limit,
            expires_in_days=request.expires_in_days,
            description=request.description,
        )
        return {
            "id": api_key.id,
            "key_name": api_key.key_name,
            "key_prefix": api_key.key_prefix,
            "full_key": full_key,  # Only returned once
            "permissions": api_key.permissions,
            "rate_limit": api_key.rate_limit,
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
            "created_at": api_key.created_at.isoformat() if api_key.created_at else None,
        }
    except Exception as e:
        logger.error(f"Error creating API key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create API key")


@router.get("/")
async def get_api_keys(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get user's API keys"""
    service = APIKeyService(db)
    
    api_keys = await service.get_user_api_keys(user_id=_get_user_id(current_user))
    
    return {
        "api_keys": [
            {
                "id": k.id,
                "key_name": k.key_name,
                "key_prefix": k.key_prefix,
                "permissions": k.permissions,
                "rate_limit": k.rate_limit,
                "is_active": k.is_active,
                "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                "request_count": k.request_count,
            }
            for k in api_keys
        ],
        "count": len(api_keys),
    }


@router.get("/{api_key_id}")
async def get_api_key(
    api_key_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get a specific API key"""
    from ..models.api_keys import APIKey
    
    api_key = await db.get(APIKey, api_key_id)
    if not api_key or api_key.user_id != _get_user_id(current_user):
        raise HTTPException(status_code=404, detail="API key not found")
    
    return {
        "id": api_key.id,
        "key_name": api_key.key_name,
        "key_prefix": api_key.key_prefix,
        "permissions": api_key.permissions,
        "rate_limit": api_key.rate_limit,
        "is_active": api_key.is_active,
        "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
        "last_used_at": api_key.last_used_at.isoformat() if api_key.last_used_at else None,
        "request_count": api_key.request_count,
        "description": api_key.description,
    }


@router.delete("/{api_key_id}")
async def revoke_api_key(
    api_key_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Revoke an API key"""
    service = APIKeyService(db)
    
    success = await service.revoke_api_key(
        api_key_id=api_key_id,
        user_id=_get_user_id(current_user),
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return {"message": "API key revoked successfully"}


@router.get("/{api_key_id}/usage")
async def get_api_key_usage(
    api_key_id: int,
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get API key usage statistics"""
    from ..models.api_keys import APIKey, APIKeyUsage
    from sqlalchemy import select, func, and_
    from datetime import timedelta
    
    # Verify ownership
    api_key = await db.get(APIKey, api_key_id)
    if not api_key or api_key.user_id != _get_user_id(current_user):
        raise HTTPException(status_code=404, detail="API key not found")
    
    # Get usage stats
    start_date = datetime.utcnow() - timedelta(days=days)
    stmt = select(
        func.count(APIKeyUsage.id).label("total_requests"),
        func.avg(APIKeyUsage.response_time_ms).label("avg_response_time"),
        func.count(func.distinct(APIKeyUsage.endpoint)).label("unique_endpoints"),
    ).where(
        and_(
            APIKeyUsage.api_key_id == api_key_id,
            APIKeyUsage.created_at >= start_date,
        )
    )
    
    result = await db.execute(stmt)
    stats = result.fetchone()
    
    return {
        "api_key_id": api_key_id,
        "period_days": days,
        "total_requests": stats.total_requests or 0,
        "avg_response_time_ms": round(stats.avg_response_time or 0, 2),
        "unique_endpoints": stats.unique_endpoints or 0,
        "rate_limit": api_key.rate_limit,
    }


import logging
logger = logging.getLogger(__name__)
