"""
Exchange Routes - Enhanced exchange integrations and smart routing
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from ..services.exchange import (
    binance_service,
    coinbase_service,
    kucoin_service,
    smart_routing_service,
    Exchange,
    RoutingStrategy
)
from ..dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/exchanges", tags=["Exchanges"])


# ===== Binance Routes =====

@router.get("/binance/ticker/{symbol}", response_model=Dict)
async def get_binance_ticker(
    symbol: str,
    current_user: dict = Depends(get_current_user)
):
    """Get Binance ticker for a symbol"""
    try:
        ticker = await binance_service.get_ticker(symbol)
        return ticker
    except Exception as e:
        logger.error(f"Error fetching Binance ticker: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch ticker: {str(e)}")


@router.get("/binance/orderbook/{symbol}", response_model=Dict)
async def get_binance_orderbook(
    symbol: str,
    depth: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get Binance order book"""
    try:
        orderbook = await binance_service.get_order_book(symbol, depth)
        return orderbook
    except Exception as e:
        logger.error(f"Error fetching Binance order book: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch order book: {str(e)}")


@router.get("/binance/fees", response_model=Dict)
async def get_binance_fees(
    current_user: dict = Depends(get_current_user)
):
    """Get Binance fee structure"""
    try:
        fees = await binance_service.get_fees()
        return {
            'maker': fees.maker,
            'taker': fees.taker,
            'bnb_discount': fees.bnb_discount
        }
    except Exception as e:
        logger.error(f"Error fetching Binance fees: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch fees: {str(e)}")


@router.get("/binance/trading-pairs", response_model=Dict)
async def get_binance_trading_pairs(
    quote: str = Query("USDT", description="Quote currency"),
    current_user: dict = Depends(get_current_user)
):
    """Get Binance trading pairs"""
    try:
        pairs = await binance_service.get_trading_pairs(quote)
        return {'pairs': pairs}
    except Exception as e:
        logger.error(f"Error fetching Binance trading pairs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch trading pairs: {str(e)}")


# ===== Coinbase Routes =====

@router.get("/coinbase/ticker/{symbol}", response_model=Dict)
async def get_coinbase_ticker(
    symbol: str,
    current_user: dict = Depends(get_current_user)
):
    """Get Coinbase ticker for a symbol"""
    try:
        ticker = await coinbase_service.get_ticker(symbol)
        return ticker
    except Exception as e:
        logger.error(f"Error fetching Coinbase ticker: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch ticker: {str(e)}")


@router.get("/coinbase/fees", response_model=Dict)
async def get_coinbase_fees(
    current_user: dict = Depends(get_current_user)
):
    """Get Coinbase fee structure"""
    try:
        fees = await coinbase_service.get_fees()
        return {
            'maker': fees.maker,
            'taker': fees.taker,
            'tier': fees.tier
        }
    except Exception as e:
        logger.error(f"Error fetching Coinbase fees: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch fees: {str(e)}")


@router.get("/coinbase/account-info", response_model=Dict)
async def get_coinbase_account_info(
    current_user: dict = Depends(get_current_user)
):
    """Get Coinbase account information"""
    try:
        info = await coinbase_service.get_account_info()
        return info
    except Exception as e:
        logger.error(f"Error fetching Coinbase account info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch account info: {str(e)}")


# ===== KuCoin Routes =====

@router.get("/kucoin/ticker/{symbol}", response_model=Dict)
async def get_kucoin_ticker(
    symbol: str,
    current_user: dict = Depends(get_current_user)
):
    """Get KuCoin ticker for a symbol"""
    try:
        ticker = await kucoin_service.get_ticker(symbol)
        return ticker
    except Exception as e:
        logger.error(f"Error fetching KuCoin ticker: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch ticker: {str(e)}")


@router.get("/kucoin/fees", response_model=Dict)
async def get_kucoin_fees(
    current_user: dict = Depends(get_current_user)
):
    """Get KuCoin fee structure with VIP level"""
    try:
        fees = await kucoin_service.get_fees()
        return {
            'maker': fees.maker,
            'taker': fees.taker,
            'vip_level': fees.vip_level
        }
    except Exception as e:
        logger.error(f"Error fetching KuCoin fees: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch fees: {str(e)}")


@router.get("/kucoin/symbols", response_model=Dict)
async def get_kucoin_symbols(
    quote: str = Query("USDT", description="Quote currency"),
    current_user: dict = Depends(get_current_user)
):
    """Get KuCoin trading symbols"""
    try:
        symbols = await kucoin_service.get_symbols_list(quote)
        return {'symbols': symbols}
    except Exception as e:
        logger.error(f"Error fetching KuCoin symbols: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch symbols: {str(e)}")


# ===== Smart Routing Routes =====

class RoutingRequest(BaseModel):
    """Smart routing request"""
    symbol: str
    side: str  # 'buy' or 'sell'
    amount: float
    strategy: str = "combined"  # 'best_price', 'fee_optimized', 'slippage_aware', 'combined'
    exchanges: Optional[List[str]] = None
    max_slippage: Optional[float] = None
    price_weight: Optional[float] = None
    fee_weight: Optional[float] = None
    slippage_weight: Optional[float] = None


@router.post("/smart-routing/quote", response_model=Dict)
async def get_smart_routing_quote(
    request: RoutingRequest,
    current_user: dict = Depends(get_current_user)
):
    """Get smart routing quote across exchanges"""
    try:
        strategy = RoutingStrategy(request.strategy)
        
        kwargs = {}
        if request.max_slippage is not None:
            kwargs['max_slippage'] = request.max_slippage
        if request.price_weight is not None:
            kwargs['price_weight'] = request.price_weight
        if request.fee_weight is not None:
            kwargs['fee_weight'] = request.fee_weight
        if request.slippage_weight is not None:
            kwargs['slippage_weight'] = request.slippage_weight
        
        result = await smart_routing_service.route_order(
            symbol=request.symbol,
            side=request.side,
            amount=request.amount,
            strategy=strategy,
            exchanges=request.exchanges,
            **kwargs
        )
        
        best_exchange, quote = result
        
        return {
            'best_exchange': best_exchange,
            'quote': quote,
            'strategy': request.strategy
        }
    
    except Exception as e:
        logger.error(f"Error getting smart routing quote: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get routing quote: {str(e)}")


@router.post("/smart-routing/compare", response_model=Dict)
async def compare_exchange_prices(
    request: RoutingRequest,
    current_user: dict = Depends(get_current_user)
):
    """Compare prices across all exchanges"""
    try:
        strategy = RoutingStrategy(request.strategy)
        
        if strategy == RoutingStrategy.BEST_PRICE:
            result = await smart_routing_service.get_best_price(
                request.symbol,
                request.side,
                request.amount,
                request.exchanges
            )
        elif strategy == RoutingStrategy.FEE_OPTIMIZED:
            result = await smart_routing_service.get_fee_optimized_route(
                request.symbol,
                request.side,
                request.amount,
                request.exchanges
            )
        elif strategy == RoutingStrategy.SLIPPAGE_AWARE:
            max_slippage = request.max_slippage or 0.005
            result = await smart_routing_service.get_slippage_aware_route(
                request.symbol,
                request.side,
                request.amount,
                request.exchanges,
                max_slippage
            )
        else:  # COMBINED
            price_weight = request.price_weight or 0.5
            fee_weight = request.fee_weight or 0.3
            slippage_weight = request.slippage_weight or 0.2
            result = await smart_routing_service.get_combined_route(
                request.symbol,
                request.side,
                request.amount,
                request.exchanges,
                price_weight,
                fee_weight,
                slippage_weight
            )
        
        return {
            'best_exchange': result.best_exchange,
            'quotes': [quote.dict() for quote in result.quotes],
            'strategy': result.routing_strategy,
            'savings': result.savings,
            'timestamp': result.timestamp.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error comparing exchange prices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compare prices: {str(e)}")
