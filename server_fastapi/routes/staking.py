"""
Staking Routes
API endpoints for staking rewards.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..dependencies.auth import get_current_user
from ..dependencies.staking import get_staking_service
from ..middleware.cache_manager import cached
from ..services.staking_service import StakingService
from ..utils.response_optimizer import ResponseOptimizer
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter()


class StakeRequest(BaseModel):
    asset: str
    amount: float


class UnstakeRequest(BaseModel):
    asset: str
    amount: float


@router.get("/options")
@cached(ttl=300, prefix="staking_options")  # 5min TTL for staking options (static data)
async def get_staking_options(
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[StakingService, Depends(get_staking_service)],
):
    """Get available staking options"""
    try:
        options = await service.get_staking_options()
        return {"options": options}
    except Exception as e:
        logger.error(f"Error getting staking options: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get staking options")


@router.post("/stake")
async def stake_assets(
    request: StakeRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[StakingService, Depends(get_staking_service)],
):
    """Stake assets to earn rewards"""
    try:
        if request.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")

        user_id = _get_user_id(current_user)

        result = await service.stake_assets(
            user_id=user_id, asset=request.asset, amount=request.amount
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error staking assets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to stake assets")


@router.post("/unstake")
async def unstake_assets(
    request: UnstakeRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[StakingService, Depends(get_staking_service)],
):
    """Unstake assets"""
    try:
        if request.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")

        user_id = _get_user_id(current_user)

        result = await service.unstake_assets(
            user_id=user_id, asset=request.asset, amount=request.amount
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unstaking assets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to unstake assets")


@router.get("/rewards")
@cached(ttl=60, prefix="staking_rewards")  # 60s TTL for staking rewards
async def get_staking_rewards(
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[StakingService, Depends(get_staking_service)],
    asset: str = Query(..., description="Asset to check rewards for"),
):
    """Get staking rewards for a user"""
    try:
        user_id = _get_user_id(current_user)

        rewards = await service.calculate_staking_rewards(user_id, asset)
        return rewards
    except Exception as e:
        logger.error(f"Error getting staking rewards: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get staking rewards")


@router.get("/my-stakes")
@cached(ttl=120, prefix="my_stakes")  # 120s TTL for user stakes list
async def get_my_stakes(
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[StakingService, Depends(get_staking_service)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """Get all staked assets for current user with pagination"""
    try:
        user_id = _get_user_id(current_user)

        # ✅ Use repository through service (service has repository injected)
        # Get wallets using service's repository
        wallets = await service.wallet_repository.get_by_user(
            service.db, user_id, wallet_type="staking"
        )

        # Filter wallets with balance > 0
        wallets = [w for w in wallets if w.balance > 0]

        # Apply pagination
        total = len(wallets)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_wallets = wallets[start_idx:end_idx]

        stakes = []
        for wallet in paginated_wallets:
            rewards = await service.calculate_staking_rewards(user_id, wallet.currency)
            stakes.append(
                {
                    "asset": wallet.currency,
                    "staked_amount": wallet.balance,
                    "rewards": rewards,
                }
            )

        return ResponseOptimizer.paginate_response(stakes, page, page_size, total)
    except Exception as e:
        logger.error(f"Error getting user stakes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get stakes")
