"""
Health Check Routes for Wallet and Staking Services
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies.auth import get_current_user
from ..database import get_db_session
from ..services.wallet_service import WalletService
from ..services.staking_service import StakingService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/wallet")
async def wallet_health_check(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> Dict:
    """Health check for wallet service"""
    try:
        user_id = current_user.get("id")
        service = WalletService(db)
        
        # Try to get wallet balance
        balance = await service.get_wallet_balance(user_id, "USD")
        
        return {
            "status": "healthy",
            "service": "wallet",
            "user_id": user_id,
            "wallet_exists": balance.get("wallet_id") is not None,
            "balance": balance.get("balance", 0.0)
        }
    except Exception as e:
        logger.error(f"Wallet health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "service": "wallet",
            "error": str(e)
        }


@router.get("/staking")
async def staking_health_check(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> Dict:
    """Health check for staking service"""
    try:
        service = StakingService(db)
        
        # Try to get staking options
        options = await service.get_staking_options()
        
        return {
            "status": "healthy",
            "service": "staking",
            "options_count": len(options),
            "supported_assets": [opt["asset"] for opt in options]
        }
    except Exception as e:
        logger.error(f"Staking health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "service": "staking",
            "error": str(e)
        }

