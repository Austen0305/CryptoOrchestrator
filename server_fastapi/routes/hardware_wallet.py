"""
Hardware Wallet API Routes
Endpoints for Ledger and Trezor integration
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Annotated
from datetime import datetime
import logging

from ..dependencies.auth import get_current_user
from ..services.blockchain.hardware_wallet import (
    hardware_wallet_service,
    HardwareWalletType,
)
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/hardware-wallet", tags=["Hardware Wallet"])


# Request/Response Models
class ConnectDeviceRequest(BaseModel):
    device_id: str = Field(..., description="Device identifier")
    wallet_type: str = Field(..., description="Wallet type: ledger or trezor")


class DeriveAddressRequest(BaseModel):
    device_id: str = Field(..., description="Device identifier")
    account_index: int = Field(0, description="Account index (BIP44)")
    address_index: int = Field(0, description="Address index (BIP44)")
    path: Optional[str] = Field(None, description="Custom derivation path")


class SignTransactionRequest(BaseModel):
    device_id: str = Field(..., description="Device identifier")
    transaction_hash: str = Field(..., description="Transaction hash to sign")
    account_index: int = Field(0, description="Account index")


@router.get("/devices")
async def detect_devices(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """Detect connected hardware wallets"""
    try:
        devices = hardware_wallet_service.detect_devices()
        
        return [
            {
                "device_id": d.device_id,
                "wallet_type": d.wallet_type.value,
                "model": d.model,
                "firmware_version": d.firmware_version,
                "connected": d.connected,
            }
            for d in devices
        ]
    except Exception as e:
        logger.error(f"Error detecting devices: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to detect devices")


@router.post("/devices/connect")
async def connect_device(
    request: ConnectDeviceRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Connect to a hardware wallet device"""
    try:
        wallet_type = HardwareWalletType(request.wallet_type.lower())
        
        device = hardware_wallet_service.connect_device(
            device_id=request.device_id,
            wallet_type=wallet_type,
        )
        
        if not device:
            raise HTTPException(status_code=400, detail="Failed to connect to device")
        
        return {
            "device_id": device.device_id,
            "wallet_type": device.wallet_type.value,
            "model": device.model,
            "firmware_version": device.firmware_version,
            "connected": device.connected,
            "connected_at": device.connected_at.isoformat() if device.connected_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error connecting device: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to connect device")


@router.post("/devices/{device_id}/disconnect")
async def disconnect_device(
    device_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Disconnect from a hardware wallet"""
    try:
        success = hardware_wallet_service.disconnect_device(device_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Device not found")
        
        return {"status": "ok", "device_id": device_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting device: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to disconnect device")


@router.post("/devices/{device_id}/derive-address")
async def derive_address(
    device_id: str,
    request: DeriveAddressRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Derive address from hardware wallet"""
    try:
        address = hardware_wallet_service.derive_address(
            device_id=device_id,
            account_index=request.account_index,
            address_index=request.address_index,
            path=request.path,
        )
        
        if not address:
            raise HTTPException(status_code=400, detail="Failed to derive address")
        
        return {
            "device_id": device_id,
            "address": address,
            "account_index": request.account_index,
            "address_index": request.address_index,
            "path": request.path,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deriving address: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to derive address")


@router.post("/devices/{device_id}/sign")
async def sign_transaction(
    device_id: str,
    request: SignTransactionRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Sign transaction using hardware wallet"""
    try:
        signature = hardware_wallet_service.sign_transaction(
            device_id=device_id,
            transaction_hash=request.transaction_hash,
            account_index=request.account_index,
        )
        
        return {
            "signature_id": signature.signature_id,
            "transaction_hash": signature.transaction_hash,
            "r": signature.r,
            "s": signature.s,
            "v": signature.v,
            "signed_at": signature.signed_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error signing transaction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to sign transaction")


@router.get("/devices/{device_id}")
async def get_device(
    device_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get device information"""
    try:
        device = hardware_wallet_service.get_device(device_id)
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        return {
            "device_id": device.device_id,
            "wallet_type": device.wallet_type.value,
            "model": device.model,
            "firmware_version": device.firmware_version,
            "connected": device.connected,
            "address": device.address,
            "connected_at": device.connected_at.isoformat() if device.connected_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get device")


@router.get("/statistics")
async def get_statistics(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """Get hardware wallet statistics"""
    try:
        return hardware_wallet_service.get_statistics()
    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get statistics")
