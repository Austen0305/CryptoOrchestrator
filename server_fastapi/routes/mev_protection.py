"""
MEV Protection API Routes
Check MEV protection status and configuration
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from ..dependencies.auth import get_current_user
from ..services.blockchain.mev_protection import (
    MEVProtectionProvider,
    get_mev_protection_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mev-protection", tags=["MEV Protection"])


@router.get("/status/{chain_id}")
async def get_protection_status(
    chain_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """
    Get MEV protection status for a chain.

    Args:
        chain_id: Blockchain chain ID
        current_user: Current authenticated user

    Returns:
        Dict with protection status information
    """
    try:
        mev_service = get_mev_protection_service()
        status = mev_service.get_protection_status(chain_id)

        return status
    except Exception as e:
        logger.error(f"Failed to get MEV protection status: {e}", exc_info=True)
        return {"chain_id": chain_id, "supported": False, "error": str(e)}


@router.get("/should-use")
async def should_use_mev_protection(
    current_user: Annotated[dict, Depends(get_current_user)],
    trade_amount_usd: float = Query(..., description="Trade amount in USD"),
    chain_id: int = Query(..., description="Blockchain chain ID"),
) -> dict:
    """
    Determine if MEV protection should be used for a trade.

    Args:
        trade_amount_usd: Trade amount in USD
        chain_id: Blockchain chain ID
        current_user: Current authenticated user

    Returns:
        Dict with recommendation
    """
    try:
        mev_service = get_mev_protection_service()
        should_use = await mev_service.should_use_mev_protection(
            trade_amount_usd=trade_amount_usd, chain_id=chain_id
        )

        protected_rpc = await mev_service.get_protected_rpc_url(
            chain_id, MEVProtectionProvider.MEV_BLOCKER
        )

        return {
            "should_use": should_use,
            "trade_amount_usd": trade_amount_usd,
            "chain_id": chain_id,
            "threshold_usd": 1000.0,
            "protected_rpc_available": protected_rpc is not None,
            "protected_rpc": protected_rpc,
            "message": (
                f"MEV protection {'recommended' if should_use else 'not needed'} "
                f"for ${trade_amount_usd:.2f} trade on chain {chain_id}"
            ),
        }
    except Exception as e:
        logger.error(
            f"Failed to check MEV protection recommendation: {e}", exc_info=True
        )
        return {"should_use": False, "error": str(e)}
