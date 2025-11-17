"""
SaaS Exchange Keys Routes
Secure exchange API key management with encryption
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import logging

from ..database import get_db_session
from ..dependencies.auth import get_current_user
from ..services.exchange_keys_service import ExchangeKeysService
from ..models.exchange_api_key import ExchangeAPIKey

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exchange-keys", tags=["Exchange Keys"])


# Request Models
class CreateExchangeKeyRequest(BaseModel):
    exchange: str
    api_key: str
    api_secret: str
    passphrase: Optional[str] = None
    label: Optional[str] = None
    is_testnet: bool = False


class UpdateExchangeKeyRequest(BaseModel):
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    passphrase: Optional[str] = None
    label: Optional[str] = None
    is_testnet: Optional[bool] = None


# Response Models
class ExchangeKeyResponse(BaseModel):
    id: int
    exchange: str
    label: Optional[str] = None
    is_testnet: bool
    is_validated: bool
    validated_at: Optional[str] = None
    last_used_at: Optional[str] = None
    created_at: str


@router.post("")
async def create_exchange_key(
    request: CreateExchangeKeyRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Create encrypted exchange API key"""
    try:
        service = ExchangeKeysService()
        
        exchange_key = await service.create_exchange_key(
            db=db,
            user_id=current_user["id"],
            exchange=request.exchange,
            api_key=request.api_key,
            api_secret=request.api_secret,
            passphrase=request.passphrase,
            label=request.label,
            is_testnet=request.is_testnet,
        )
        
        if not exchange_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create exchange key"
            )
        
        return ExchangeKeyResponse(
            id=exchange_key.id,
            exchange=exchange_key.exchange,
            label=exchange_key.label,
            is_testnet=exchange_key.is_testnet,
            is_validated=exchange_key.is_validated,
            validated_at=exchange_key.validated_at.isoformat() if exchange_key.validated_at else None,
            last_used_at=exchange_key.last_used_at.isoformat() if exchange_key.last_used_at else None,
            created_at=exchange_key.created_at.isoformat(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create exchange key: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create exchange key"
        )


@router.get("")
async def get_exchange_keys(
    exchange: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get user's exchange API keys"""
    try:
        service = ExchangeKeysService()
        
        keys = await service.get_exchange_keys(
            db=db,
            user_id=current_user["id"],
            exchange=exchange,
        )
        
        return [
            ExchangeKeyResponse(
                id=key.id,
                exchange=key.exchange,
                label=key.label,
                is_testnet=key.is_testnet,
                is_validated=key.is_validated,
                validated_at=key.validated_at.isoformat() if key.validated_at else None,
                last_used_at=key.last_used_at.isoformat() if key.last_used_at else None,
                created_at=key.created_at.isoformat(),
            )
            for key in keys
        ]
        
    except Exception as e:
        logger.error(f"Failed to get exchange keys: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get exchange keys"
        )


@router.delete("/{exchange}")
async def delete_exchange_key(
    exchange: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete exchange API key"""
    try:
        service = ExchangeKeysService()
        
        success = await service.delete_exchange_key(
            db=db,
            user_id=current_user["id"],
            exchange=exchange,
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exchange key not found"
            )
        
        return {
            "success": True,
            "message": f"Exchange key for {exchange} deleted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete exchange key: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete exchange key"
        )


@router.post("/{exchange}/test")
async def test_connection(
    exchange: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Test exchange API connection"""
    try:
        service = ExchangeKeysService()
        
        result = await service.test_connection(
            db=db,
            user_id=current_user["id"],
            exchange=exchange,
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Connection test failed"
        )

