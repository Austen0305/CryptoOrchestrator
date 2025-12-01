"""
Staking Routes
API endpoints for staking rewards.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.staking_service import StakingService
from ..dependencies.auth import get_current_user
from ..database import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter()


class StakeRequest(BaseModel):
    asset: str
    amount: float


class UnstakeRequest(BaseModel):
    asset: str
    amount: float


@router.get("/options")
async def get_staking_options(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get available staking options"""
    try:
        service = StakingService(db)
        options = await service.get_staking_options()
        return {"options": options}
    except Exception as e:
        logger.error(f"Error getting staking options: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get staking options")


@router.post("/stake")
async def stake_assets(
    request: StakeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Stake assets to earn rewards"""
    try:
        if request.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")
        
        user_id = current_user.get("id")
        service = StakingService(db)
        
        result = await service.stake_assets(
            user_id=user_id,
            asset=request.asset,
            amount=request.amount
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
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Unstake assets"""
    try:
        if request.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")
        
        user_id = current_user.get("id")
        service = StakingService(db)
        
        result = await service.unstake_assets(
            user_id=user_id,
            asset=request.asset,
            amount=request.amount
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
async def get_staking_rewards(
    asset: str = Query(..., description="Asset to check rewards for"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get staking rewards for a user"""
    try:
        user_id = current_user.get("id")
        service = StakingService(db)
        
        rewards = await service.calculate_staking_rewards(user_id, asset)
        return rewards
    except Exception as e:
        logger.error(f"Error getting staking rewards: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get staking rewards")


@router.get("/my-stakes")
async def get_my_stakes(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get all staked assets for current user"""
    try:
        from ..models.wallet import Wallet
        from sqlalchemy import select, and_
        
        user_id = current_user.get("id")
        stmt = select(Wallet).where(
            and_(
                Wallet.user_id == user_id,
                Wallet.wallet_type == "staking",
                Wallet.balance > 0
            )
        )
        result = await db.execute(stmt)
        wallets = result.scalars().all()
        
        service = StakingService(db)
        stakes = []
        for wallet in wallets:
            rewards = await service.calculate_staking_rewards(user_id, wallet.currency)
            stakes.append({
                "asset": wallet.currency,
                "staked_amount": wallet.balance,
                "rewards": rewards
            })
        
        return {"stakes": stakes}
    except Exception as e:
        logger.error(f"Error getting user stakes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get stakes")

