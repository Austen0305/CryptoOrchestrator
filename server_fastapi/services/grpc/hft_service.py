"""
gRPC HFT Service Implementation
High-performance gRPC endpoints for high-frequency trading
"""

import logging
from typing import Iterator
import time

from ...services.hft_orderbook_service import hft_orderbook_service, OrderBookSnapshot, OrderBookDelta
from ...services.market_microstructure_service import market_microstructure_service, MarketMicrostructure

logger = logging.getLogger(__name__)

# Import generated gRPC code (will be generated from proto file)
try:
    from ...proto import hft_pb2, hft_pb2_grpc
except ImportError:
    # Fallback if proto files not generated yet
    logger.warning("gRPC proto files not generated. Run: python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/hft.proto")
    hft_pb2 = None
    hft_pb2_grpc = None

# Import asyncio and grpc for the service
import asyncio
import grpc


class HFTService(hft_pb2_grpc.HFTServiceServicer if hft_pb2_grpc else object):
    """
    gRPC service implementation for high-frequency trading
    
    Provides low-latency endpoints for:
    - Order book snapshots and deltas
    - Market microstructure data
    - Batch order processing
    - Latency statistics
    """
    
    async def GetOrderBookSnapshot(
        self,
        request: 'hft_pb2.OrderBookRequest',
        context,
    ) -> 'hft_pb2.OrderBookSnapshot':
        """Get current order book snapshot"""
        try:
            snapshot = await hft_orderbook_service.get_snapshot(request.pair)
            
            if not snapshot:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Order book snapshot not available for {request.pair}")
                return hft_pb2.OrderBookSnapshot()
            
            # Convert to protobuf message
            return hft_pb2.OrderBookSnapshot(
                pair=snapshot.pair,
                bids=[
                    hft_pb2.PriceLevel(price=float(price), quantity=float(qty))
                    for price, qty in snapshot.bids
                ],
                asks=[
                    hft_pb2.PriceLevel(price=float(price), quantity=float(qty))
                    for price, qty in snapshot.asks
                ],
                timestamp=snapshot.timestamp,
                sequence=snapshot.sequence,
            )
        except Exception as e:
            logger.error(f"Error getting orderbook snapshot: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return hft_pb2.OrderBookSnapshot()
    
    async def GetOrderBookDeltas(
        self,
        request: 'hft_pb2.OrderBookDeltaRequest',
        context,
    ) -> 'hft_pb2.OrderBookDeltas':
        """Get order book delta updates"""
        try:
            deltas = await hft_orderbook_service.get_delta_history(
                request.pair,
                since_sequence=request.since_sequence if request.since_sequence > 0 else None,
                limit=request.limit if request.limit > 0 else 100,
            )
            
            # Convert to protobuf messages
            delta_messages = []
            for delta in deltas:
                delta_msg = hft_pb2.OrderBookDelta(
                    pair=delta.pair,
                    sequence=delta.sequence,
                    timestamp=delta.timestamp,
                    bid_updates=[
                        hft_pb2.PriceLevel(price=float(price), quantity=float(qty))
                        for price, qty in delta.bid_updates
                    ],
                    ask_updates=[
                        hft_pb2.PriceLevel(price=float(price), quantity=float(qty))
                        for price, qty in delta.ask_updates
                    ],
                )
                delta_messages.append(delta_msg)
            
            return hft_pb2.OrderBookDeltas(deltas=delta_messages)
        except Exception as e:
            logger.error(f"Error getting orderbook deltas: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return hft_pb2.OrderBookDeltas()
    
    async def StreamOrderBook(
        self,
        request: 'hft_pb2.OrderBookRequest',
        context,
    ) -> Iterator['hft_pb2.OrderBookUpdate']:
        """Stream order book updates in real-time"""
        try:
            # Subscribe to deltas
            delta_queue = await hft_orderbook_service.subscribe_deltas(request.pair)
            
            # Send initial snapshot
            snapshot = await hft_orderbook_service.get_snapshot(request.pair)
            if snapshot:
                yield hft_pb2.OrderBookUpdate(
                    snapshot=hft_pb2.OrderBookSnapshot(
                        pair=snapshot.pair,
                        bids=[
                            hft_pb2.PriceLevel(price=float(price), quantity=float(qty))
                            for price, qty in snapshot.bids
                        ],
                        asks=[
                            hft_pb2.PriceLevel(price=float(price), quantity=float(qty))
                            for price, qty in snapshot.asks
                        ],
                        timestamp=snapshot.timestamp,
                        sequence=snapshot.sequence,
                    )
                )
            
            # Stream deltas
            while True:
                try:
                    delta = await asyncio.wait_for(delta_queue.get(), timeout=1.0)
                    
                    yield hft_pb2.OrderBookUpdate(
                        delta=hft_pb2.OrderBookDelta(
                            pair=delta.pair,
                            sequence=delta.sequence,
                            timestamp=delta.timestamp,
                            bid_updates=[
                                hft_pb2.PriceLevel(price=float(price), quantity=float(qty))
                                for price, qty in delta.bid_updates
                            ],
                            ask_updates=[
                                hft_pb2.PriceLevel(price=float(price), quantity=float(qty))
                                for price, qty in delta.ask_updates
                            ],
                        )
                    )
                except asyncio.TimeoutError:
                    # Send heartbeat
                    continue
                except Exception as e:
                    logger.error(f"Error in orderbook stream: {e}")
                    break
        except Exception as e:
            logger.error(f"Error streaming orderbook: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
        finally:
            await hft_orderbook_service.unsubscribe_deltas(request.pair, delta_queue)
    
    async def GetMicrostructure(
        self,
        request: 'hft_pb2.MicrostructureRequest',
        context,
    ) -> 'hft_pb2.Microstructure':
        """Get market microstructure data"""
        try:
            microstructure = await market_microstructure_service.get_microstructure(request.pair)
            
            if not microstructure:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Microstructure data not available for {request.pair}")
                return hft_pb2.Microstructure()
            
            return hft_pb2.Microstructure(
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
        except Exception as e:
            logger.error(f"Error getting microstructure: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return hft_pb2.Microstructure()
    
    async def BatchOrders(
        self,
        request: 'hft_pb2.BatchOrderRequest',
        context,
    ) -> 'hft_pb2.BatchOrderResponse':
        """Process batch orders"""
        start_time = time.time_ns()
        
        try:
            results = []
            success_count = 0
            failure_count = 0
            
            # Process orders (simplified - would integrate with trading engine)
            for order in request.orders:
                try:
                    if request.validate_only:
                        result = hft_pb2.OrderResult(
                            order=order,
                            status="validated",
                        )
                    else:
                        result = hft_pb2.OrderResult(
                            order=order,
                            status="submitted",
                            order_id=f"order_{time.time_ns()}",
                        )
                        success_count += 1
                    
                    results.append(result)
                except Exception as e:
                    results.append(hft_pb2.OrderResult(
                        order=order,
                        status="failed",
                        error=str(e),
                    ))
                    failure_count += 1
            
            latency_ms = (time.time_ns() - start_time) / 1_000_000
            
            return hft_pb2.BatchOrderResponse(
                results=results,
                total_count=len(request.orders),
                success_count=success_count,
                failure_count=failure_count,
                latency_ms=latency_ms,
            )
        except Exception as e:
            logger.error(f"Error processing batch orders: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return hft_pb2.BatchOrderResponse()
    
    async def GetLatencyStats(
        self,
        request: 'hft_pb2.LatencyRequest',
        context,
    ) -> 'hft_pb2.LatencyStats':
        """Get latency statistics"""
        try:
            stats = hft_orderbook_service.get_latency_stats(request.pair)
            
            if not stats:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Latency statistics not available for {request.pair}")
                return hft_pb2.LatencyStats()
            
            return hft_pb2.LatencyStats(
                pair=stats["pair"],
                count=stats["count"],
                min_ms=stats["min_ms"],
                max_ms=stats["max_ms"],
                avg_ms=stats["avg_ms"],
                p50_ms=stats["p50_ms"],
                p95_ms=stats["p95_ms"],
                p99_ms=stats["p99_ms"],
            )
        except Exception as e:
            logger.error(f"Error getting latency stats: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return hft_pb2.LatencyStats()
