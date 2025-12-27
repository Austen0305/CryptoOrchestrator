"""
High-Frequency Trading API Routes
Low-latency endpoints for professional traders and institutions
"""

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Annotated
from datetime import datetime
import logging
import time
import json
import struct

from ..dependencies.auth import get_current_user
from ..database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from ..utils.route_helpers import _get_user_id
from ..services.hft_orderbook_service import hft_orderbook_service, OrderBookSnapshot, OrderBookDelta
from ..services.market_microstructure_service import market_microstructure_service, MarketMicrostructure
from ..services.enterprise_api_tier import enterprise_api_tier_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["HFT"])


# Request/Response Models
class OrderBookSnapshotResponse(BaseModel):
    pair: str
    bids: List[List[float]]
    asks: List[List[float]]
    timestamp: int
    sequence: int


class OrderBookDeltaResponse(BaseModel):
    pair: str
    sequence: int
    timestamp: int
    bid_updates: List[List[float]]
    ask_updates: List[List[float]]


class BatchOrderRequest(BaseModel):
    orders: List[Dict[str, Any]] = Field(..., description="List of order objects")
    validate_only: bool = Field(False, description="Validate orders without executing")


class BatchOrderResponse(BaseModel):
    orders: List[Dict[str, Any]]
    total_count: int
    success_count: int
    failure_count: int
    latency_ms: float


class MarketMicrostructureResponse(BaseModel):
    pair: str
    timestamp: int
    bid_ask_spread: float
    mid_price: float
    weighted_mid_price: float
    bid_volume: float
    ask_volume: float
    volume_imbalance: float
    price_impact_1pct: float
    price_impact_5pct: float
    buy_volume: float
    sell_volume: float
    trade_flow_imbalance: float
    realized_volatility: float
    bid_ask_volatility: float
    market_depth: float
    effective_spread: float


class LatencyStatsResponse(BaseModel):
    pair: str
    count: int
    min_ms: float
    max_ms: float
    avg_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float


@router.get("/rate-limits", response_model=Dict)
async def get_rate_limits(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Dict:
    """
    Get rate limit information for current user
    
    Provides transparency about rate limits and current usage.
    """
    user_id = _get_user_id(current_user)
    return enterprise_api_tier_service.get_rate_limit_info(user_id)


@router.get("/orderbook/{pair}/snapshot", response_model=OrderBookSnapshotResponse)
async def get_orderbook_snapshot(
    pair: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> OrderBookSnapshotResponse:
    """
    Get current order book snapshot (low-latency endpoint)
    
    Optimized for high-frequency trading with minimal processing overhead.
    Requires HFT tier access.
    """
    user_id = _get_user_id(current_user)
    
    # Check tier access
    if not enterprise_api_tier_service.has_feature_access(user_id, "hft_orderbook"):
        raise HTTPException(
            status_code=403,
            detail="HFT tier required for orderbook snapshots. Upgrade to HFT tier.",
        )
    
    # Check rate limit
    allowed, error_msg = enterprise_api_tier_service.check_rate_limit(user_id, "orderbook_snapshot")
    if not allowed:
        raise HTTPException(status_code=429, detail=error_msg)
    
    start_time = time.time_ns()
    
    try:
        snapshot = await hft_orderbook_service.get_snapshot(pair)
        
        if not snapshot:
            raise HTTPException(
                status_code=404,
                detail=f"Order book snapshot not available for {pair}",
            )
        
        latency_ms = (time.time_ns() - start_time) / 1_000_000
        
        # Log latency for monitoring
        if latency_ms > 10:  # Warn if latency > 10ms
            logger.warning(f"High latency for orderbook snapshot: {latency_ms:.2f}ms")
        
        return OrderBookSnapshotResponse(
            pair=snapshot.pair,
            bids=[[float(price), float(qty)] for price, qty in snapshot.bids],
            asks=[[float(price), float(qty)] for price, qty in snapshot.asks],
            timestamp=snapshot.timestamp,
            sequence=snapshot.sequence,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting orderbook snapshot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get orderbook snapshot")


@router.get("/orderbook/{pair}/deltas", response_model=List[OrderBookDeltaResponse])
async def get_orderbook_deltas(
    pair: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    since_sequence: Optional[int] = Query(None, description="Get deltas after this sequence"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of deltas"),
) -> List[OrderBookDeltaResponse]:
    """
    Get order book delta updates
    
    Returns only changes since the last snapshot or specified sequence number.
    This reduces bandwidth and latency for high-frequency trading.
    """
    try:
        deltas = await hft_orderbook_service.get_delta_history(
            pair, since_sequence=since_sequence, limit=limit
        )
        
        return [
            OrderBookDeltaResponse(
                pair=delta.pair,
                sequence=delta.sequence,
                timestamp=delta.timestamp,
                bid_updates=[[float(price), float(qty)] for price, qty in delta.bid_updates],
                ask_updates=[[float(price), float(qty)] for price, qty in delta.ask_updates],
            )
            for delta in deltas
        ]
    except Exception as e:
        logger.error(f"Error getting orderbook deltas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get orderbook deltas")


@router.websocket("/ws/orderbook/{pair}")
async def websocket_orderbook_deltas(
    websocket: WebSocket,
    pair: str,
    format: str = Query("json", description="Format: json or binary"),
):
    """
    WebSocket endpoint for real-time order book delta updates
    
    Supports both JSON and binary protocols for low-latency trading.
    """
    await websocket.accept()
    
    try:
        # Subscribe to deltas
        delta_queue = await hft_orderbook_service.subscribe_deltas(pair)
        
        # Send initial snapshot
        snapshot = await hft_orderbook_service.get_snapshot(pair)
        if snapshot:
            if format == "binary":
                # Binary protocol (more efficient)
                await _send_binary_snapshot(websocket, snapshot)
            else:
                # JSON protocol (default)
                await websocket.send_json({
                    "type": "snapshot",
                    "data": snapshot.to_dict(),
                })
        
        # Stream deltas
        while True:
            try:
                delta = await asyncio.wait_for(delta_queue.get(), timeout=1.0)
                
                if format == "binary":
                    await _send_binary_delta(websocket, delta)
                else:
                    await websocket.send_json({
                        "type": "delta",
                        "data": delta.to_dict(),
                    })
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat", "timestamp": time.time_ns()})
            except WebSocketDisconnect:
                break
                
    except Exception as e:
        logger.error(f"Error in orderbook WebSocket: {e}", exc_info=True)
    finally:
        await hft_orderbook_service.unsubscribe_deltas(pair, delta_queue)
        try:
            await websocket.close()
        except:
            pass


async def _send_binary_snapshot(websocket: WebSocket, snapshot: OrderBookSnapshot):
    """Send snapshot in binary format"""
    # Binary format: [type:1B][pair_len:2B][pair:str][timestamp:8B][sequence:4B][bids_count:2B][bids:...][asks_count:2B][asks:...]
    pair_bytes = snapshot.pair.encode('utf-8')
    pair_len = len(pair_bytes)
    
    bids_count = len(snapshot.bids)
    asks_count = len(snapshot.asks)
    
    # Build binary message
    data = struct.pack('!B', 0)  # Type: 0 = snapshot
    data += struct.pack('!H', pair_len)
    data += pair_bytes
    data += struct.pack('!Q', snapshot.timestamp)
    data += struct.pack('!I', snapshot.sequence)
    data += struct.pack('!H', bids_count)
    
    for price, qty in snapshot.bids:
        data += struct.pack('!dd', price, qty)
    
    data += struct.pack('!H', asks_count)
    for price, qty in snapshot.asks:
        data += struct.pack('!dd', price, qty)
    
    await websocket.send_bytes(data)


async def _send_binary_delta(websocket: WebSocket, delta: OrderBookDelta):
    """Send delta in binary format"""
    # Binary format: [type:1B][pair_len:2B][pair:str][timestamp:8B][sequence:4B][bid_updates_count:2B][bid_updates:...][ask_updates_count:2B][ask_updates:...]
    pair_bytes = delta.pair.encode('utf-8')
    pair_len = len(pair_bytes)
    
    bid_updates_count = len(delta.bid_updates)
    ask_updates_count = len(delta.ask_updates)
    
    data = struct.pack('!B', 1)  # Type: 1 = delta
    data += struct.pack('!H', pair_len)
    data += pair_bytes
    data += struct.pack('!Q', delta.timestamp)
    data += struct.pack('!I', delta.sequence)
    data += struct.pack('!H', bid_updates_count)
    
    for price, qty in delta.bid_updates:
        data += struct.pack('!dd', price, qty)
    
    data += struct.pack('!H', ask_updates_count)
    for price, qty in delta.ask_updates:
        data += struct.pack('!dd', price, qty)
    
    await websocket.send_bytes(data)


@router.post("/orders/batch", response_model=BatchOrderResponse)
async def batch_orders(
    request: BatchOrderRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BatchOrderResponse:
    """
    Batch order endpoint for high-frequency trading
    
    Allows submitting multiple orders in a single request to reduce latency.
    Optimized for low-latency processing.
    """
    start_time = time.time_ns()
    user_id = _get_user_id(current_user)
    
    try:
        if not request.orders:
            raise HTTPException(status_code=400, detail="No orders provided")
        
        if len(request.orders) > 100:  # Limit batch size
            raise HTTPException(
                status_code=400,
                detail="Maximum 100 orders per batch",
            )
        
        results = []
        success_count = 0
        failure_count = 0
        
        # Process orders (in production, this would integrate with trading engine)
        for order in request.orders:
            try:
                # Validate order
                if request.validate_only:
                    # Just validate, don't execute
                    result = {"status": "validated", "order": order}
                else:
                    # Execute order (placeholder - integrate with trading service)
                    result = {
                        "status": "submitted",
                        "order": order,
                        "order_id": f"order_{time.time_ns()}",
                    }
                    success_count += 1
                
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing order: {e}")
                results.append({
                    "status": "failed",
                    "order": order,
                    "error": str(e),
                })
                failure_count += 1
        
        latency_ms = (time.time_ns() - start_time) / 1_000_000
        
        return BatchOrderResponse(
            orders=results,
            total_count=len(request.orders),
            success_count=success_count,
            failure_count=failure_count,
            latency_ms=latency_ms,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing batch orders: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process batch orders")


@router.get("/microstructure/{pair}", response_model=MarketMicrostructureResponse)
async def get_market_microstructure(
    pair: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> MarketMicrostructureResponse:
    """
    Get market microstructure data
    
    Provides detailed microstructure metrics for high-frequency trading strategies.
    """
    try:
        microstructure = await market_microstructure_service.get_microstructure(pair)
        
        if not microstructure:
            raise HTTPException(
                status_code=404,
                detail=f"Microstructure data not available for {pair}",
            )
        
        return MarketMicrostructureResponse(
            pair=microstructure.pair,
            timestamp=microstructure.timestamp,
            bid_ask_spread=microstructure.bid_ask_spread,
            mid_price=microstructure.mid_price,
            weighted_mid_price=microstructure.weighted_mid_price,
            bid_volume=microstructure.bid_volume,
            ask_volume=microstructure.ask_volume,
            volume_imbalance=microstructure.volume_imbalance,
            price_impact_1pct=microstructure.price_impact_1pct,
            price_impact_5pct=microstructure.price_impact_5pct,
            buy_volume=microstructure.buy_volume,
            sell_volume=microstructure.sell_volume,
            trade_flow_imbalance=microstructure.trade_flow_imbalance,
            realized_volatility=microstructure.realized_volatility,
            bid_ask_volatility=microstructure.bid_ask_volatility,
            market_depth=microstructure.market_depth,
            effective_spread=microstructure.effective_spread,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting microstructure: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get microstructure data")


@router.get("/latency/{pair}", response_model=LatencyStatsResponse)
async def get_latency_stats(
    pair: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> LatencyStatsResponse:
    """
    Get latency statistics for a trading pair
    
    Provides p50, p95, p99 latency metrics for monitoring and SLA tracking.
    """
    try:
        stats = hft_orderbook_service.get_latency_stats(pair)
        
        if not stats:
            raise HTTPException(
                status_code=404,
                detail=f"Latency statistics not available for {pair}",
            )
        
        return LatencyStatsResponse(**stats)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latency stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get latency statistics")


# Import asyncio for WebSocket
import asyncio
