"""
Crypto Transfer Routes
Handle crypto transfers from external platforms and withdrawals
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Annotated
import logging

from ..services.crypto_transfer_service import CryptoTransferService
from ..dependencies.crypto_transfer import get_crypto_transfer_service
from ..dependencies.auth import get_current_user
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crypto-transfer", tags=["Crypto Transfer"])


class InitiateTransferRequest(BaseModel):
    """Request to initiate a crypto transfer from external platform"""

    currency: str
    amount: float
    source_platform: str  # 'binance', 'coinbase', 'kraken', 'external_wallet'
    source_address: Optional[str] = None
    network: Optional[str] = None  # 'ERC20', 'TRC20', 'BEP20', etc.
    memo: Optional[str] = None


class ConfirmTransferRequest(BaseModel):
    """Request to confirm a crypto transfer"""

    transaction_id: int
    tx_hash: str
    confirmations: int = 0


class WithdrawCryptoRequest(BaseModel):
    """Request to withdraw crypto to external address"""

    currency: str
    amount: float
    destination_address: str
    network: Optional[str] = None
    memo: Optional[str] = None


@router.post("/initiate")
async def initiate_crypto_transfer(
    request: InitiateTransferRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[CryptoTransferService, Depends(get_crypto_transfer_service)],
) -> Dict:
    """Initiate a crypto transfer from an external platform"""
    try:
        user_id = _get_user_id(current_user)

        result = await service.initiate_crypto_transfer(
            user_id=user_id,
            currency=request.currency,
            amount=request.amount,
            source_platform=request.source_platform,
            source_address=request.source_address,
            network=request.network,
            memo=request.memo,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error initiating crypto transfer: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to initiate crypto transfer"
        )


@router.post("/confirm")
async def confirm_crypto_transfer(
    request: ConfirmTransferRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[CryptoTransferService, Depends(get_crypto_transfer_service)],
) -> Dict:
    """Confirm a crypto transfer after blockchain confirmation"""
    try:

        success = await service.confirm_crypto_transfer(
            transaction_id=request.transaction_id,
            tx_hash=request.tx_hash,
            confirmations=request.confirmations,
        )

        if not success:
            raise HTTPException(status_code=400, detail="Transfer confirmation failed")

        return {
            "success": True,
            "transaction_id": request.transaction_id,
            "status": "completed",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming crypto transfer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to confirm crypto transfer")


@router.post("/withdraw")
async def withdraw_crypto(
    request: WithdrawCryptoRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[CryptoTransferService, Depends(get_crypto_transfer_service)],
) -> Dict:
    """Withdraw crypto to an external address"""
    try:
        user_id = _get_user_id(current_user)

        result = await service.withdraw_crypto(
            user_id=user_id,
            currency=request.currency,
            amount=request.amount,
            destination_address=request.destination_address,
            network=request.network,
            memo=request.memo,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing crypto withdrawal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process withdrawal")


@router.get("/deposit-address/{currency}")
async def get_deposit_address(
    currency: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[CryptoTransferService, Depends(get_crypto_transfer_service)],
    network: Optional[str] = None,
) -> Dict:
    """Get deposit address for a cryptocurrency"""
    try:
        user_id = _get_user_id(current_user)

        address = await service._generate_deposit_address(currency, network)

        return {
            "currency": currency,
            "address": address,
            "network": network or "default",
            "qr_code_url": f"/api/qr/{address}",  # Would generate QR code
        }

    except Exception as e:
        logger.error(f"Error getting deposit address: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get deposit address")
