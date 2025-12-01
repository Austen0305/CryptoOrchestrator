"""
Exchange API Keys Routes
Manages exchange API keys for users
"""

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import jwt
import os

from ..services.auth.exchange_key_service import exchange_key_service
from ..dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/exchange-keys", tags=["exchange-keys"])
security = HTTPBearer()

JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")


class ExchangeKeyCreate(BaseModel):
    exchange: str = Field(..., description="Exchange name (e.g., 'binance', 'kraken')")
    api_key: str = Field(..., description="Exchange API key")
    api_secret: str = Field(..., description="Exchange API secret")
    passphrase: Optional[str] = Field(None, description="Exchange passphrase (for some exchanges)")
    label: Optional[str] = Field(None, description="User-friendly label")
    permissions: Optional[str] = Field(None, description="Comma-separated permissions")
    is_testnet: bool = Field(False, description="Whether this is a testnet key")
    ip_whitelist: Optional[str] = Field(None, description="Comma-separated IP addresses")


class ExchangeKeyResponse(BaseModel):
    id: str
    exchange: str
    label: Optional[str]
    permissions: Optional[str]
    is_active: bool
    is_testnet: bool
    is_validated: bool
    validated_at: Optional[str]
    last_used_at: Optional[str]
    created_at: Optional[str]


@router.post("/", response_model=ExchangeKeyResponse)
async def create_exchange_key(
    key_data: ExchangeKeyCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create exchange API key"""
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Convert user_id to int for audit logging
        user_id_int = int(user_id) if isinstance(user_id, str) and user_id.isdigit() else user_id
        if not isinstance(user_id_int, int):
            user_id_int = int(user_id) if user_id else 1

        api_key_obj = await exchange_key_service.create_api_key(
            user_id=user_id,
            exchange=key_data.exchange,
            api_key=key_data.api_key,
            api_secret=key_data.api_secret,
            passphrase=key_data.passphrase,
            label=key_data.label,
            permissions=key_data.permissions,
            is_testnet=key_data.is_testnet,
            ip_whitelist=key_data.ip_whitelist,
        )
        
        # Log audit event
        try:
            from ..services.audit.audit_logger import audit_logger
            audit_logger.log_api_key_operation(
                user_id=user_id_int,
                operation="create",
                exchange=key_data.exchange,
                success=True,
            )
        except Exception as e:
            logger.warning(f"Failed to log audit event: {e}")

        # Handle both dict (in-memory) and object (database) responses
        if isinstance(api_key_obj, dict):
            return ExchangeKeyResponse(
                id=api_key_obj.get("id", ""),
                exchange=api_key_obj.get("exchange", ""),
                label=api_key_obj.get("label"),
                permissions=api_key_obj.get("permissions"),
                is_active=api_key_obj.get("is_active", True),
                is_testnet=api_key_obj.get("is_testnet", False),
                is_validated=api_key_obj.get("is_validated", False),
                validated_at=api_key_obj.get("validated_at"),
                last_used_at=api_key_obj.get("last_used_at"),
                created_at=api_key_obj.get("created_at"),
            )
        else:
            return ExchangeKeyResponse(
                id=str(api_key_obj.id),
                exchange=api_key_obj.exchange,
                label=api_key_obj.label,
                permissions=api_key_obj.permissions,
                is_active=api_key_obj.is_active,
                is_testnet=api_key_obj.is_testnet,
                is_validated=api_key_obj.is_validated,
                validated_at=api_key_obj.validated_at.isoformat() if api_key_obj.validated_at else None,
                last_used_at=api_key_obj.last_used_at.isoformat() if api_key_obj.last_used_at else None,
                created_at=api_key_obj.created_at.isoformat() if api_key_obj.created_at else None,
            )

    except Exception as e:
        logger.error(f"Failed to create exchange API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[ExchangeKeyResponse])
async def list_exchange_keys(
    current_user: dict = Depends(get_current_user),
):
    """List all exchange API keys for user"""
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        api_keys = await exchange_key_service.list_api_keys(user_id)
        return [
            ExchangeKeyResponse(
                id=key["id"],
                exchange=key["exchange"],
                label=key["label"],
                permissions=key["permissions"],
                is_active=key["is_active"],
                is_testnet=key["is_testnet"],
                is_validated=key["is_validated"],
                validated_at=key["validated_at"],
                last_used_at=key["last_used_at"],
                created_at=key["created_at"],
            )
            for key in api_keys
        ]

    except Exception as e:
        logger.error(f"Failed to list exchange API keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{exchange}", response_model=ExchangeKeyResponse)
async def get_exchange_key(
    exchange: str,
    current_user: dict = Depends(get_current_user),
):
    """Get exchange API key"""
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        api_key = await exchange_key_service.get_api_key(user_id, exchange, include_secrets=False)
        if not api_key:
            raise HTTPException(status_code=404, detail="Exchange API key not found")

        return ExchangeKeyResponse(
            id=api_key["id"],
            exchange=api_key["exchange"],
            label=api_key["label"],
            permissions=api_key["permissions"],
            is_active=api_key["is_active"],
            is_testnet=api_key["is_testnet"],
            is_validated=api_key["is_validated"],
            validated_at=api_key["validated_at"],
            last_used_at=api_key["last_used_at"],
            created_at=api_key["created_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get exchange API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{exchange}/validate")
async def validate_exchange_key(
    exchange: str,
    current_user: dict = Depends(get_current_user),
):
    """Validate exchange API key"""
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Convert user_id to int for audit logging
        user_id_int = int(user_id) if isinstance(user_id, str) and user_id.isdigit() else user_id
        if not isinstance(user_id_int, int):
            user_id_int = int(user_id) if user_id else 1

        is_valid = await exchange_key_service.validate_api_key(user_id, exchange)
        if not is_valid:
            # Log audit event for failed validation
            try:
                from ..services.audit.audit_logger import audit_logger
                audit_logger.log_api_key_operation(
                    user_id=user_id_int,
                    operation="validate",
                    exchange=exchange,
                    success=False,
                    error="Validation failed",
                )
            except Exception as e:
                logger.warning(f"Failed to log audit event: {e}")
            raise HTTPException(status_code=400, detail="Failed to validate API key")

        # Log audit event for successful validation
        try:
            from ..services.audit.audit_logger import audit_logger
            audit_logger.log_api_key_operation(
                user_id=user_id_int,
                operation="validate",
                exchange=exchange,
                success=True,
            )
        except Exception as e:
            logger.warning(f"Failed to log audit event: {e}")

        return {"message": "API key validated successfully", "is_valid": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate exchange API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{exchange}")
async def delete_exchange_key(
    exchange: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete exchange API key"""
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Convert user_id to int for audit logging
        user_id_int = int(user_id) if isinstance(user_id, str) and user_id.isdigit() else user_id
        if not isinstance(user_id_int, int):
            user_id_int = int(user_id) if user_id else 1

        deleted = await exchange_key_service.delete_api_key(user_id, exchange)
        if not deleted:
            raise HTTPException(status_code=404, detail="Exchange API key not found")

        # Log audit event
        try:
            from ..services.audit.audit_logger import audit_logger
            audit_logger.log_api_key_operation(
                user_id=user_id_int,
                operation="delete",
                exchange=exchange,
                success=True,
            )
        except Exception as e:
            logger.warning(f"Failed to log audit event: {e}")

        return {"message": "Exchange API key deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete exchange API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))

