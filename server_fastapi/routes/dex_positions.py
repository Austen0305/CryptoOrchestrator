"""
DEX Positions API Routes
Manage and query DEX positions for users
"""

import logging
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from ..models.dex_position import DEXPosition
from ..services.trading.dex_position_service import DEXPositionService
from ..dependencies.dex_positions import get_dex_position_service
from ..dependencies.auth import get_current_user
from ..utils.route_helpers import _get_user_id
from ..middleware.cache_manager import cached
from ..utils.query_optimizer import QueryOptimizer
from ..utils.response_optimizer import ResponseOptimizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/positions", tags=["DEX Positions"])


@router.get("/", response_model=List[dict])
@cached(ttl=60, prefix="dex_positions")  # 60s TTL for DEX positions
async def get_positions(
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[DEXPositionService, Depends(get_dex_position_service)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    chain_id: Optional[int] = Query(None, description="Filter by chain ID"),
    is_open: Optional[bool] = Query(None, description="Filter by open/closed status"),
) -> List[dict]:
    """
    Get user's DEX positions with pagination.

    Args:
        current_user: Current authenticated user
        page: Page number (1-indexed)
        page_size: Items per page
        chain_id: Optional chain ID filter
        is_open: Optional open/closed status filter
        db: Database session

    Returns:
        List of position dictionaries
    """
    try:
        user_id = _get_user_id(current_user)

        positions = await service.get_user_positions(
            user_id=user_id,
            chain_id=chain_id,
            is_open=is_open,
        )

        # Apply pagination (service returns all, paginate in route)
        total = len(positions)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_positions = positions[start_idx:end_idx]

        return [position.to_dict() for position in paginated_positions]
    except Exception as e:
        logger.error(f"Failed to get positions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get positions")


@router.get("/{position_id}", response_model=dict)
async def get_position(
    position_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[DEXPositionService, Depends(get_dex_position_service)],
) -> dict:
    """
    Get a specific position by ID.

    Args:
        position_id: Position ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Position dictionary
    """
    try:
        user_id = _get_user_id(current_user)

        # ✅ Use repository through service (service has repository injected)
        position = await service.position_repository.get_by_id(service.db, position_id)

        if not position:
            raise HTTPException(status_code=404, detail="Position not found")

        # Verify ownership
        if position.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        return position.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get position: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get position")


@router.post("/{position_id}/update-pnl")
async def update_position_pnl(
    position_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[DEXPositionService, Depends(get_dex_position_service)],
) -> dict:
    """
    Update position P&L with current price.

    Args:
        position_id: Position ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated position dictionary
    """
    try:
        user_id = _get_user_id(current_user)

        # ✅ Use repository through service to verify ownership
        position = await service.position_repository.get_by_id(service.db, position_id)

        if not position:
            raise HTTPException(status_code=404, detail="Position not found")

        if position.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Update P&L
        updated_position = await service.update_position_pnl(position_id)

        if not updated_position:
            raise HTTPException(status_code=404, detail="Position not found")

        return updated_position.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update position P&L: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update position P&L")


@router.post("/update-all-pnl")
async def update_all_positions_pnl(
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[DEXPositionService, Depends(get_dex_position_service)],
) -> dict:
    """
    Update P&L for all open positions.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Dict with update count
    """
    try:
        user_id = _get_user_id(current_user)

        updated_count = await service.update_all_positions_pnl(user_id=user_id)

        return {
            "updated_count": updated_count,
            "message": f"Updated P&L for {updated_count} positions",
        }
    except Exception as e:
        logger.error(f"Failed to update all positions P&L: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to update all positions P&L"
        )
