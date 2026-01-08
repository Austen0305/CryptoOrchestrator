"""
Batch API Routes
JSON-RPC style request batching for high-performance API access
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ..dependencies.auth import get_current_user
from ..services.performance.request_batching import request_batching_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/batch", tags=["Batch API"])


class BatchRequest(BaseModel):
    """Single request in a batch"""

    method: str = Field(..., description="API method name")
    params: dict[str, Any] | None = Field(None, description="Method parameters")
    id: str | None = Field(None, description="Request ID for correlation")


class BatchRequestPayload(BaseModel):
    """Batch request payload"""

    requests: list[BatchRequest] = Field(..., description="List of requests to batch")


@router.post("/")
async def batch_request(
    payload: BatchRequestPayload,
    current_user: Annotated[dict, Depends(get_current_user)],
    request: Request,
) -> list[dict[str, Any]]:
    """
    Process a batch of API requests

    Allows sending multiple API requests in a single HTTP request to reduce
    latency and overhead. Supports JSON-RPC 2.0 style batching.

    Example:
    {
      "requests": [
        {"method": "get_market_data", "params": {"pair": "BTC/USD"}, "id": "1"},
        {"method": "get_orderbook", "params": {"pair": "ETH/USD"}, "id": "2"}
      ]
    }
    """
    try:
        # Convert to list of dicts
        requests = [req.dict() for req in payload.requests]

        # Create context with current user
        context = {
            "user": current_user,
            "request": request,
        }

        # Process batch
        responses = await request_batching_service.process_batch(requests, context)

        return responses
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing batch request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process batch request")


# Register common batch handlers
def register_batch_handlers():
    """Register handlers for common batch methods"""
    from ..services.coingecko_service import CoinGeckoService
    from ..services.hft_orderbook_service import hft_orderbook_service

    coingecko = CoinGeckoService()

    async def get_market_data_handler(params: dict, context: dict) -> dict:
        """Handler for get_market_data batch method"""
        pair = params.get("pair", "BTC/USD")
        price = await coingecko.get_price(pair)
        return {"pair": pair, "price": price}

    async def get_orderbook_snapshot_handler(params: dict, context: dict) -> dict:
        """Handler for get_orderbook_snapshot batch method"""
        pair = params.get("pair", "BTC/USD")
        snapshot = await hft_orderbook_service.get_snapshot(pair)
        if snapshot:
            return snapshot.to_dict()
        return {}

    # Register handlers
    request_batching_service.register_handler(
        "get_market_data", get_market_data_handler
    )
    request_batching_service.register_handler(
        "get_orderbook_snapshot", get_orderbook_snapshot_handler
    )

    logger.info("Batch API handlers registered")


# Initialize handlers on module load
register_batch_handlers()
