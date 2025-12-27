"""
Yield Farming API Routes
Endpoints for automated yield farming and liquidity provision
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from ..database import get_db_session
from ..dependencies.auth import get_current_user
from ..utils.route_helpers import _get_user_id
from ..services.yield_farming_service import YieldFarmingService

router = APIRouter(prefix="/api/yield-farming", tags=["Yield Farming"])


# Pydantic Models
class CreatePositionRequest(BaseModel):
    pool_id: str
    amount: float
    chain_id: int = 1
    auto_compound: bool = True
    risk_limit: Optional[float] = None


class RebalanceRequest(BaseModel):
    target_allocation: Dict[str, float]  # pool_id -> percentage


@router.get("/pools")
async def get_available_pools(
    chain_id: int = Query(1, description="Blockchain chain ID"),
    min_apy: Optional[float] = Query(None, description="Minimum APY filter"),
    protocol: Optional[str] = Query(None, description="Protocol filter"),
    db: AsyncSession = Depends(get_db_session),
):
    """Get available yield farming pools"""
    service = YieldFarmingService(db)
    
    pools = await service.get_available_pools(
        chain_id=chain_id,
        min_apy=min_apy,
        protocol=protocol,
    )
    
    return {"pools": pools, "count": len(pools)}


@router.post("/positions")
async def create_farming_position(
    request: CreatePositionRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a yield farming position"""
    service = YieldFarmingService(db)
    
    try:
        position = await service.create_farming_position(
            user_id=_get_user_id(current_user),
            pool_id=request.pool_id,
            amount=request.amount,
            chain_id=request.chain_id,
            auto_compound=request.auto_compound,
            risk_limit=request.risk_limit,
        )
        return position
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating farming position: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create farming position")


@router.get("/positions")
async def get_user_positions(
    chain_id: Optional[int] = Query(None, description="Filter by chain ID"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get user's yield farming positions"""
    service = YieldFarmingService(db)
    
    positions = await service.get_user_positions(
        user_id=_get_user_id(current_user),
        chain_id=chain_id,
    )
    
    return {"positions": positions, "count": len(positions)}


@router.get("/positions/{position_id}/yield")
async def calculate_yield(
    position_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Calculate yield for a position"""
    service = YieldFarmingService(db)
    
    yield_calc = await service.calculate_yield(
        position_id=position_id,
        days=days,
    )
    
    return yield_calc


@router.post("/rebalance")
async def rebalance_positions(
    request: RebalanceRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Rebalance yield farming positions"""
    service = YieldFarmingService(db)
    
    result = await service.rebalance_positions(
        user_id=_get_user_id(current_user),
        target_allocation=request.target_allocation,
    )
    
    return result


@router.get("/optimize")
async def optimize_yield(
    risk_tolerance: str = Query("medium", pattern="^(low|medium|high)$"),
    min_apy: Optional[float] = Query(None, description="Minimum APY requirement"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get yield optimization recommendations"""
    service = YieldFarmingService(db)
    
    recommendations = await service.optimize_yield(
        user_id=_get_user_id(current_user),
        risk_tolerance=risk_tolerance,
        min_apy=min_apy,
    )
    
    return recommendations
