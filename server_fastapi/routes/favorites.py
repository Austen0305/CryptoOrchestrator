"""
Favorites/Watchlist API Routes
Allows users to favorite trading pairs for quick access
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies.auth import get_current_user
from ..database import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models
class AddFavoriteRequest(BaseModel):
    symbol: str = Field(..., description="Trading symbol (e.g., BTC/USDT)")
    exchange: str = Field(default="binance", description="Exchange name")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")

    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "BTC/USDT",
                "exchange": "binance",
                "notes": "Strong bullish momentum"
            }
        }
    }


class FavoriteResponse(BaseModel):
    id: int
    user_id: int
    symbol: str
    exchange: str
    notes: Optional[str]
    current_price: Optional[float]
    price_change_24h: Optional[float]
    created_at: datetime
    last_viewed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class WatchlistSummary(BaseModel):
    total_favorites: int
    exchanges: List[str]
    top_gainers: List[dict]
    top_losers: List[dict]


@router.get("/favorites", response_model=List[FavoriteResponse], tags=["Favorites"])
async def get_favorites(
    exchange: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Get user's favorite trading pairs.
    
    Optionally filter by exchange.
    """
    try:
        from sqlalchemy import select, and_
        from ..models.favorite import Favorite
        
        # Build query
        query = select(Favorite).where(Favorite.user_id == current_user["id"])
        
        if exchange:
            query = query.where(Favorite.exchange == exchange)
        
        query = query.order_by(Favorite.created_at.desc())
        
        # Execute query
        result = await db_session.execute(query)
        favorites = result.scalars().all()
        
        # Enrich with current market data
        enriched_favorites = []
        for fav in favorites:
            fav_dict = {
                "id": fav.id,
                "user_id": fav.user_id,
                "symbol": fav.symbol,
                "exchange": fav.exchange,
                "notes": fav.notes,
                "created_at": fav.created_at,
                "last_viewed_at": fav.last_viewed_at,
                "current_price": None,  # TODO: Fetch from market data
                "price_change_24h": None  # TODO: Fetch from market data
            }
            enriched_favorites.append(fav_dict)
        
        return enriched_favorites
    
    except Exception as e:
        logger.error(f"Error fetching favorites: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch favorites"
        )


@router.post("/favorites", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED, tags=["Favorites"])
async def add_favorite(
    request: AddFavoriteRequest,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Add a trading pair to favorites.
    """
    try:
        from sqlalchemy import select
        from ..models.favorite import Favorite
        
        # Check if already favorited
        query = select(Favorite).where(
            and_(
                Favorite.user_id == current_user["id"],
                Favorite.symbol == request.symbol,
                Favorite.exchange == request.exchange
            )
        )
        result = await db_session.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{request.symbol} on {request.exchange} is already in your favorites"
            )
        
        # Create new favorite
        favorite = Favorite(
            user_id=current_user["id"],
            symbol=request.symbol,
            exchange=request.exchange,
            notes=request.notes,
            created_at=datetime.utcnow()
        )
        
        db_session.add(favorite)
        await db_session.commit()
        await db_session.refresh(favorite)
        
        return FavoriteResponse(
            id=favorite.id,
            user_id=favorite.user_id,
            symbol=favorite.symbol,
            exchange=favorite.exchange,
            notes=favorite.notes,
            created_at=favorite.created_at,
            last_viewed_at=favorite.last_viewed_at,
            current_price=None,
            price_change_24h=None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding favorite: {e}", exc_info=True)
        await db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add favorite"
        )


@router.delete("/favorites/{favorite_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Favorites"])
async def remove_favorite(
    favorite_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Remove a trading pair from favorites.
    """
    try:
        from sqlalchemy import select, and_, delete
        from ..models.favorite import Favorite
        
        # Verify ownership and existence
        query = select(Favorite).where(
            and_(
                Favorite.id == favorite_id,
                Favorite.user_id == current_user["id"]
            )
        )
        result = await db_session.execute(query)
        favorite = result.scalar_one_or_none()
        
        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Favorite not found"
            )
        
        # Delete
        await db_session.delete(favorite)
        await db_session.commit()
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing favorite: {e}", exc_info=True)
        await db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove favorite"
        )


@router.put("/favorites/{favorite_id}/notes", response_model=FavoriteResponse, tags=["Favorites"])
async def update_favorite_notes(
    favorite_id: int,
    notes: str = Field(..., max_length=500),
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Update notes for a favorite.
    """
    try:
        from sqlalchemy import select, and_
        from ..models.favorite import Favorite
        
        # Get favorite
        query = select(Favorite).where(
            and_(
                Favorite.id == favorite_id,
                Favorite.user_id == current_user["id"]
            )
        )
        result = await db_session.execute(query)
        favorite = result.scalar_one_or_none()
        
        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Favorite not found"
            )
        
        # Update notes
        favorite.notes = notes
        await db_session.commit()
        await db_session.refresh(favorite)
        
        return FavoriteResponse(
            id=favorite.id,
            user_id=favorite.user_id,
            symbol=favorite.symbol,
            exchange=favorite.exchange,
            notes=favorite.notes,
            created_at=favorite.created_at,
            last_viewed_at=favorite.last_viewed_at,
            current_price=None,
            price_change_24h=None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating favorite notes: {e}", exc_info=True)
        await db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update favorite notes"
        )


@router.get("/favorites/summary", response_model=WatchlistSummary, tags=["Favorites"])
async def get_watchlist_summary(
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Get summary statistics for user's watchlist.
    """
    try:
        from sqlalchemy import select, func
        from ..models.favorite import Favorite
        
        # Count total favorites
        count_query = select(func.count(Favorite.id)).where(
            Favorite.user_id == current_user["id"]
        )
        count_result = await db_session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Get unique exchanges
        exchanges_query = select(Favorite.exchange).where(
            Favorite.user_id == current_user["id"]
        ).distinct()
        exchanges_result = await db_session.execute(exchanges_query)
        exchanges = [row[0] for row in exchanges_result.all()]
        
        # TODO: Fetch actual market data for top gainers/losers
        top_gainers = []
        top_losers = []
        
        return WatchlistSummary(
            total_favorites=total,
            exchanges=exchanges,
            top_gainers=top_gainers,
            top_losers=top_losers
        )
    
    except Exception as e:
        logger.error(f"Error fetching watchlist summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch watchlist summary"
        )
