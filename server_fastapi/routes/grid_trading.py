"""
Grid Trading API Routes
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies.auth import get_current_user
from ..database import get_db_session
from ..services.trading.grid_trading_service import GridTradingService

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic request/response models
class CreateGridBotRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Bot name")
    symbol: str = Field(..., description="Trading symbol (e.g., BTC/USD)")
    exchange: str = Field(..., description="Exchange name")
    upper_price: float = Field(..., gt=0, description="Upper bound of grid")
    lower_price: float = Field(..., gt=0, description="Lower bound of grid")
    grid_count: int = Field(..., ge=2, le=100, description="Number of grid levels")
    order_amount: float = Field(..., gt=0, description="Amount per order")
    trading_mode: str = Field(default="paper", pattern="^(paper|real)$", description="Trading mode")
    grid_spacing_type: str = Field(default="arithmetic", pattern="^(arithmetic|geometric)$", description="Grid spacing type")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Additional configuration")

    @field_validator('upper_price', 'lower_price')
    @classmethod
    def validate_prices(cls, v, info):
        if info.data.get('upper_price') and info.data.get('lower_price'):
            if info.data['upper_price'] <= info.data['lower_price']:
                raise ValueError("Upper price must be greater than lower price")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "BTC Grid Bot",
                "symbol": "BTC/USD",
                "exchange": "binance",
                "upper_price": 52000.0,
                "lower_price": 48000.0,
                "grid_count": 10,
                "order_amount": 100.0,
                "trading_mode": "paper",
                "grid_spacing_type": "arithmetic"
            }
        }
    }


class GridBotResponse(BaseModel):
    id: str
    user_id: int
    name: str
    symbol: str
    exchange: str
    trading_mode: str
    upper_price: float
    lower_price: float
    grid_count: int
    grid_spacing_type: str
    order_amount: float
    is_active: bool
    status: str
    total_profit: float
    total_trades: int
    win_rate: float
    grid_state: Dict[str, Any]
    config: Dict[str, Any]
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class UpdateGridBotRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    upper_price: Optional[float] = Field(None, gt=0)
    lower_price: Optional[float] = Field(None, gt=0)
    grid_count: Optional[int] = Field(None, ge=2, le=100)
    order_amount: Optional[float] = Field(None, gt=0)
    config: Optional[Dict[str, Any]] = None


@router.post("/grid-bots", response_model=Dict[str, str], status_code=status.HTTP_201_CREATED, tags=["Grid Trading"])
async def create_grid_bot(
    request: CreateGridBotRequest,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Create a new grid trading bot.
    
    Grid trading places buy and sell orders in a grid pattern to profit from volatility.
    """
    try:
        service = GridTradingService(session=db_session)
        bot_id = await service.create_grid_bot(
            user_id=current_user["id"],
            name=request.name,
            symbol=request.symbol,
            exchange=request.exchange,
            upper_price=request.upper_price,
            lower_price=request.lower_price,
            grid_count=request.grid_count,
            order_amount=request.order_amount,
            trading_mode=request.trading_mode,
            grid_spacing_type=request.grid_spacing_type,
            config=request.config
        )
        
        if not bot_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create grid bot"
            )
        
        return {"id": bot_id, "message": "Grid bot created successfully"}
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating grid bot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create grid bot"
        )


@router.get("/grid-bots", response_model=List[GridBotResponse], tags=["Grid Trading"])
async def list_grid_bots(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """List all grid bots for the current user."""
    try:
        service = GridTradingService(session=db_session)
        bots = await service.list_user_grid_bots(current_user["id"], skip, limit)
        return bots
    
    except Exception as e:
        logger.error(f"Error listing grid bots: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list grid bots"
        )


@router.get("/grid-bots/{bot_id}", response_model=GridBotResponse, tags=["Grid Trading"])
async def get_grid_bot(
    bot_id: str,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """Get a specific grid bot by ID."""
    try:
        service = GridTradingService(session=db_session)
        bot = await service.get_grid_bot(bot_id, current_user["id"])
        
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grid bot not found"
            )
        
        return bot
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting grid bot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get grid bot"
        )


@router.post("/grid-bots/{bot_id}/start", response_model=Dict[str, str], tags=["Grid Trading"])
async def start_grid_bot(
    bot_id: str,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """Start a grid trading bot."""
    try:
        service = GridTradingService(session=db_session)
        success = await service.start_grid_bot(bot_id, current_user["id"])
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to start grid bot"
            )
        
        return {"message": "Grid bot started successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting grid bot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start grid bot"
        )


@router.post("/grid-bots/{bot_id}/stop", response_model=Dict[str, str], tags=["Grid Trading"])
async def stop_grid_bot(
    bot_id: str,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """Stop a grid trading bot."""
    try:
        service = GridTradingService(session=db_session)
        success = await service.stop_grid_bot(bot_id, current_user["id"])
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to stop grid bot"
            )
        
        return {"message": "Grid bot stopped successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping grid bot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop grid bot"
        )


@router.delete("/grid-bots/{bot_id}", response_model=Dict[str, str], tags=["Grid Trading"])
async def delete_grid_bot(
    bot_id: str,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """Delete a grid trading bot."""
    try:
        # First stop the bot if it's running
        service = GridTradingService(session=db_session)
        await service.stop_grid_bot(bot_id, current_user["id"])
        
        # Then soft delete
        from ...repositories.grid_bot_repository import GridBotRepository
        repository = GridBotRepository()
        bot = await repository.get_by_user_and_id(db_session, bot_id, current_user["id"])
        
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grid bot not found"
            )
        
        bot.soft_delete()
        await db_session.commit()
        
        return {"message": "Grid bot deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting grid bot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete grid bot"
        )

