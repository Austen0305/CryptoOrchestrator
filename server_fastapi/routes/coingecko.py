"""
CoinGecko Market Data Routes

Free API endpoints for crypto market data using CoinGecko's public API.
No API key required for basic usage (30 calls/minute limit).
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging

from ..services.coingecko_service import get_coingecko_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/ping")
async def ping_coingecko():
    """
    Check CoinGecko API status.
    
    Returns:
        API status message
    """
    try:
        service = get_coingecko_service()
        result = await service.ping()
        return {"status": "ok", "coingecko": result}
    except Exception as e:
        logger.error(f"CoinGecko ping failed: {e}")
        raise HTTPException(status_code=503, detail="CoinGecko API unavailable")


@router.get("/prices")
async def get_prices(
    coins: str = Query(..., description="Comma-separated coin IDs (e.g., bitcoin,ethereum)"),
    currencies: str = Query("usd", description="Comma-separated currencies (e.g., usd,eur)")
):
    """
    Get current prices for specified coins.
    
    Args:
        coins: Comma-separated list of coin IDs (e.g., bitcoin,ethereum,cardano)
        currencies: Comma-separated list of target currencies (e.g., usd,eur,btc)
        
    Returns:
        Price data for each coin in each currency
        
    Example:
        GET /api/coingecko/prices?coins=bitcoin,ethereum&currencies=usd
        Returns: {"bitcoin": {"usd": 45000}, "ethereum": {"usd": 2800}}
    """
    try:
        service = get_coingecko_service()
        coin_list = [c.strip() for c in coins.split(",")]
        currency_list = [c.strip() for c in currencies.split(",")]
        
        result = await service.get_price(
            coin_ids=coin_list,
            vs_currencies=currency_list,
            include_24hr_change=True,
            include_market_cap=True
        )
        return result
    except Exception as e:
        logger.error(f"Failed to get prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/markets")
async def get_markets(
    currency: str = Query("usd", description="Target currency"),
    coins: Optional[str] = Query(None, description="Optional: comma-separated coin IDs to filter"),
    order: str = Query("market_cap_desc", description="Sort order"),
    per_page: int = Query(100, ge=1, le=250, description="Results per page"),
    page: int = Query(1, ge=1, description="Page number")
):
    """
    Get market data for coins (price, market cap, volume).
    
    Args:
        currency: Target currency (usd, eur, btc, etc.)
        coins: Optional comma-separated coin IDs to filter
        order: Sort order (market_cap_desc, volume_desc, etc.)
        per_page: Results per page (max 250)
        page: Page number
        
    Returns:
        List of market data for each coin
    """
    try:
        service = get_coingecko_service()
        coin_list = [c.strip() for c in coins.split(",")] if coins else None
        
        result = await service.get_coins_markets(
            vs_currency=currency,
            coin_ids=coin_list,
            order=order,
            per_page=per_page,
            page=page
        )
        return result
    except Exception as e:
        logger.error(f"Failed to get markets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/coin/{coin_id}")
async def get_coin(coin_id: str):
    """
    Get detailed data for a specific coin.
    
    Args:
        coin_id: Coin ID (e.g., bitcoin, ethereum)
        
    Returns:
        Detailed coin data including description, market data, links
    """
    try:
        service = get_coingecko_service()
        result = await service.get_coin_data(coin_id)
        return result
    except Exception as e:
        logger.error(f"Failed to get coin {coin_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/coin/{coin_id}/chart")
async def get_coin_chart(
    coin_id: str,
    currency: str = Query("usd", description="Target currency"),
    days: int = Query(7, ge=1, le=365, description="Number of days")
):
    """
    Get historical market chart data for a coin.
    
    Args:
        coin_id: Coin ID (e.g., bitcoin)
        currency: Target currency
        days: Number of days of history (1-365)
        
    Returns:
        Historical prices, market caps, and volumes
    """
    try:
        service = get_coingecko_service()
        result = await service.get_coin_market_chart(
            coin_id=coin_id,
            vs_currency=currency,
            days=days
        )
        return result
    except Exception as e:
        logger.error(f"Failed to get chart for {coin_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending")
async def get_trending():
    """
    Get trending coins (top 7 by search popularity).
    
    Returns:
        List of trending coins with basic info
    """
    try:
        service = get_coingecko_service()
        result = await service.get_trending()
        return result
    except Exception as e:
        logger.error(f"Failed to get trending: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/global")
async def get_global_stats():
    """
    Get global cryptocurrency market statistics.
    
    Returns:
        Total market cap, volume, BTC dominance, etc.
    """
    try:
        service = get_coingecko_service()
        result = await service.get_global()
        return result
    except Exception as e:
        logger.error(f"Failed to get global stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top")
async def get_top_coins(
    limit: int = Query(10, ge=1, le=100, description="Number of coins to return")
):
    """
    Get top coins by market cap.
    
    Args:
        limit: Number of coins (1-100)
        
    Returns:
        Top coins with market data
    """
    try:
        service = get_coingecko_service()
        result = await service.get_top_coins(limit=limit)
        return result
    except Exception as e:
        logger.error(f"Failed to get top coins: {e}")
        raise HTTPException(status_code=500, detail=str(e))
