"""
Favorites/Watchlist API Routes
Allows users to favorite trading pairs for quick access
"""

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies.auth import get_current_user
from ..middleware.cache_manager import cached
from ..utils.query_optimizer import QueryOptimizer
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models
class AddFavoriteRequest(BaseModel):
    symbol: str = Field(..., description="Trading symbol (e.g., BTC/USDT)")
    exchange: str = Field(default="binance", description="Exchange name")
    notes: str | None = Field(None, max_length=500, description="Optional notes")

    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "BTC/USDT",
                "exchange": "binance",
                "notes": "Strong bullish momentum",
            }
        }
    }


class FavoriteResponse(BaseModel):
    id: int
    user_id: int
    symbol: str
    exchange: str
    notes: str | None
    current_price: float | None
    price_change_24h: float | None
    created_at: datetime
    last_viewed_at: datetime | None

    model_config = {"from_attributes": True}


class WatchlistSummary(BaseModel):
    total_favorites: int
    exchanges: list[str]
    top_gainers: list[dict]
    top_losers: list[dict]


@router.get("/favorites", response_model=list[FavoriteResponse], tags=["Favorites"])
@cached(ttl=120, prefix="favorites")  # 120s TTL for favorites list
async def get_favorites(
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    exchange: str | None = None,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    Get user's favorite trading pairs with pagination.

    Optionally filter by exchange.
    """
    try:
        user_id = _get_user_id(current_user)
        from sqlalchemy import func, select

        from ..models.favorite import Favorite

        # Build query
        query = select(Favorite).where(Favorite.user_id == user_id)

        if exchange:
            query = query.where(Favorite.exchange == exchange)

        query = query.order_by(Favorite.created_at.desc())

        # Get total count
        count_query = (
            select(func.count())
            .select_from(Favorite)
            .where(Favorite.user_id == user_id)
        )
        if exchange:
            count_query = count_query.where(Favorite.exchange == exchange)
        total_result = await db_session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = QueryOptimizer.paginate_query(query, page=page, page_size=page_size)

        # Execute query
        result = await db_session.execute(query)
        favorites = result.scalars().all()

        # Enrich with current market data
        enriched_favorites = []
        # Fetch market data for favorites
        from ..services.coingecko_service import get_coingecko_service
        from ..services.market_data import MarketDataService

        market_data_service = MarketDataService()
        coingecko = get_coingecko_service()

        for fav in favorites:
            # Fetch current price and 24h change
            current_price = None
            price_change_24h = None

            try:
                # Try to get price from market data service
                symbol_key = f"{fav.symbol.replace('/', '')}"
                price = await market_data_service.get_price_with_fallback(fav.symbol)
                if price:
                    current_price = float(price)

                # Try to get 24h change from CoinGecko
                if coingecko:
                    try:
                        ticker_data = await coingecko.get_ticker(fav.symbol)
                        if ticker_data and "price_change_percentage_24h" in ticker_data:
                            price_change_24h = float(
                                ticker_data["price_change_percentage_24h"]
                            )
                    except Exception:
                        pass  # Fallback if CoinGecko fails
            except Exception as e:
                logger.debug(f"Failed to fetch market data for {fav.symbol}: {e}")

            fav_dict = {
                "id": fav.id,
                "user_id": fav.user_id,
                "symbol": fav.symbol,
                "exchange": fav.exchange,
                "notes": fav.notes,
                "created_at": fav.created_at,
                "last_viewed_at": fav.last_viewed_at,
                "current_price": current_price,
                "price_change_24h": price_change_24h,
            }
            enriched_favorites.append(fav_dict)

        return enriched_favorites

    except Exception as e:
        logger.error(f"Error fetching favorites: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch favorites",
        )


@router.post(
    "/favorites",
    response_model=FavoriteResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Favorites"],
)
async def add_favorite(
    request: AddFavoriteRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Add a trading pair to favorites.
    """
    try:
        user_id = _get_user_id(current_user)
        from sqlalchemy import select

        from ..models.favorite import Favorite

        # Check if already favorited
        query = select(Favorite).where(
            and_(
                Favorite.user_id == user_id,
                Favorite.symbol == request.symbol,
                Favorite.exchange == request.exchange,
            )
        )
        result = await db_session.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{request.symbol} on {request.exchange} is already in your favorites",
            )

        # Create new favorite
        favorite = Favorite(
            user_id=user_id,
            symbol=request.symbol,
            exchange=request.exchange,
            notes=request.notes,
            created_at=datetime.utcnow(),
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
            price_change_24h=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding favorite: {e}", exc_info=True)
        await db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add favorite",
        )


@router.delete(
    "/favorites/{favorite_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Favorites"],
)
async def remove_favorite(
    favorite_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Remove a trading pair from favorites.
    """
    try:
        user_id = _get_user_id(current_user)
        from sqlalchemy import and_, select

        from ..models.favorite import Favorite

        # Verify ownership and existence
        query = select(Favorite).where(
            and_(Favorite.id == favorite_id, Favorite.user_id == user_id)
        )
        result = await db_session.execute(query)
        favorite = result.scalar_one_or_none()

        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Favorite not found"
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
            detail="Failed to remove favorite",
        )


@router.put(
    "/favorites/{favorite_id}/notes",
    response_model=FavoriteResponse,
    tags=["Favorites"],
)
async def update_favorite_notes(
    favorite_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    notes: str = Body(..., max_length=500, description="Notes to update"),
):
    """
    Update notes for a favorite.
    """
    try:
        user_id = _get_user_id(current_user)
        from sqlalchemy import and_, select

        from ..models.favorite import Favorite

        # Get favorite
        query = select(Favorite).where(
            and_(Favorite.id == favorite_id, Favorite.user_id == user_id)
        )
        result = await db_session.execute(query)
        favorite = result.scalar_one_or_none()

        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Favorite not found"
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
            price_change_24h=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating favorite notes: {e}", exc_info=True)
        await db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update favorite notes",
        )


@router.get("/favorites/summary", response_model=WatchlistSummary, tags=["Favorites"])
@cached(ttl=120, prefix="watchlist_summary")  # 120s TTL for watchlist summary
async def get_watchlist_summary(
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Get summary statistics for user's watchlist.
    """
    try:
        user_id = _get_user_id(current_user)
        from sqlalchemy import func, select

        from ..models.favorite import Favorite

        # Count total favorites
        count_query = select(func.count(Favorite.id)).where(Favorite.user_id == user_id)
        count_result = await db_session.execute(count_query)
        total = count_result.scalar() or 0

        # Get unique exchanges
        exchanges_query = (
            select(Favorite.exchange).where(Favorite.user_id == user_id).distinct()
        )
        exchanges_result = await db_session.execute(exchanges_query)
        exchanges = [row[0] for row in exchanges_result.all()]

        # Fetch actual market data for top gainers/losers
        from ..services.coingecko_service import get_coingecko_service

        top_gainers = []
        top_losers = []

        try:
            coingecko = get_coingecko_service()
            if coingecko:
                # Get trending coins (top gainers/losers)
                trending = await coingecko.get_trending()
                if trending:
                    # Sort by 24h change
                    sorted_coins = sorted(
                        trending.get("coins", []),
                        key=lambda x: x.get("price_change_percentage_24h", 0),
                        reverse=True,
                    )
                    top_gainers = sorted_coins[:5]  # Top 5 gainers
                    top_losers = (
                        sorted_coins[-5:] if len(sorted_coins) >= 5 else []
                    )  # Top 5 losers
        except Exception as e:
            logger.debug(f"Failed to fetch trending data: {e}")
            # Keep empty arrays if fetch fails

        return WatchlistSummary(
            total_favorites=total,
            exchanges=exchanges,
            top_gainers=top_gainers,
            top_losers=top_losers,
        )

    except Exception as e:
        logger.error(f"Error fetching watchlist summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch watchlist summary",
        )
