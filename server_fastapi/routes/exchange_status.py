"""
Exchange Status Routes
Provides exchange connectivity status and health checks
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import jwt
import os
import asyncio

from ..services.auth.exchange_key_service import exchange_key_service
from ..services.auth.auth_service import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/exchange-status", tags=["exchange-status"])
security = HTTPBearer()

JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")


class ExchangeStatusData(BaseModel):
    exchange: str
    is_connected: bool
    is_validated: bool
    last_checked: Optional[str]
    error: Optional[str] = None
    latency_ms: Optional[float] = None


class ExchangeStatusResponse(BaseModel):
    exchanges: List[ExchangeStatusData]
    total_exchanges: int
    connected_exchanges: int
    validated_exchanges: int


@router.get("/", response_model=ExchangeStatusResponse)
async def get_exchange_status(
    current_user: dict = Depends(get_current_user),
):
    """Get connectivity status for all user's exchange API keys"""
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Get all API keys for user
        api_keys = await exchange_key_service.list_api_keys(user_id)
        
        if not api_keys:
            return ExchangeStatusResponse(
                exchanges=[],
                total_exchanges=0,
                connected_exchanges=0,
                validated_exchanges=0,
            )

        # Check status for each exchange
        statuses = []
        for key in api_keys:
            exchange = key["exchange"]
            is_validated = key.get("is_validated", False)
            
            # Quick connectivity check
            is_connected = False
            latency_ms = None
            error = None
            
            if is_validated:
                try:
                    import time
                    import ccxt
                    
                    # Get API key data
                    api_key_data = await exchange_key_service.get_api_key(
                        user_id, exchange, include_secrets=True
                    )
                    
                    if api_key_data:
                        # Create exchange instance
                        exchange_class = getattr(ccxt, exchange, None)
                        if exchange_class:
                            exchange_instance = exchange_class({
                                "apiKey": api_key_data["api_key"],
                                "secret": api_key_data["api_secret"],
                                "enableRateLimit": True,
                                "options": {
                                    "testnet": api_key_data.get("is_testnet", False),
                                },
                            })
                            
                            # Quick connectivity test with timeout
                            start_time = time.time()
                            try:
                                await asyncio.wait_for(
                                    exchange_instance.load_markets(),
                                    timeout=5.0
                                )
                                latency_ms = (time.time() - start_time) * 1000
                                is_connected = True
                            except asyncio.TimeoutError:
                                error = "Connection timeout"
                                latency_ms = 5000.0
                            except Exception as e:
                                error = str(e)[:100]  # Limit error message length
                except Exception as e:
                    logger.error(f"Failed to check connectivity for {exchange}: {e}")
                    error = str(e)[:100]
            
            statuses.append(ExchangeStatusData(
                exchange=exchange,
                is_connected=is_connected,
                is_validated=is_validated,
                last_checked=None,  # TODO: Store last checked timestamp
                error=error,
                latency_ms=latency_ms,
            ))

        connected_count = sum(1 for s in statuses if s.is_connected)
        validated_count = sum(1 for s in statuses if s.is_validated)

        return ExchangeStatusResponse(
            exchanges=statuses,
            total_exchanges=len(statuses),
            connected_exchanges=connected_count,
            validated_exchanges=validated_count,
        )

    except Exception as e:
        logger.error(f"Failed to get exchange status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{exchange}", response_model=ExchangeStatusData)
async def get_exchange_status_detail(
    exchange: str,
    current_user: dict = Depends(get_current_user),
):
    """Get detailed connectivity status for a specific exchange"""
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Get API key for exchange
        api_key = await exchange_key_service.get_api_key(user_id, exchange, include_secrets=False)
        if not api_key:
            raise HTTPException(status_code=404, detail="Exchange API key not found")

        is_validated = api_key.get("is_validated", False)
        is_connected = False
        latency_ms = None
        error = None

        if is_validated:
            try:
                import time
                import ccxt
                
                # Get API key data with secrets
                api_key_data = await exchange_key_service.get_api_key(
                    user_id, exchange, include_secrets=True
                )
                
                if api_key_data:
                    # Create exchange instance
                    exchange_class = getattr(ccxt, exchange, None)
                    if exchange_class:
                        exchange_instance = exchange_class({
                            "apiKey": api_key_data["api_key"],
                            "secret": api_key_data["api_secret"],
                            "enableRateLimit": True,
                            "options": {
                                "testnet": api_key_data.get("is_testnet", False),
                            },
                        })
                        
                        # Quick connectivity test
                        start_time = time.time()
                        try:
                            await asyncio.wait_for(
                                exchange_instance.load_markets(),
                                timeout=5.0
                            )
                            latency_ms = (time.time() - start_time) * 1000
                            is_connected = True
                        except asyncio.TimeoutError:
                            error = "Connection timeout"
                            latency_ms = 5000.0
                        except Exception as e:
                            error = str(e)[:100]
            except Exception as e:
                logger.error(f"Failed to check connectivity for {exchange}: {e}")
                error = str(e)[:100]

        return ExchangeStatusData(
            exchange=exchange,
            is_connected=is_connected,
            is_validated=is_validated,
            last_checked=None,
            error=error,
            latency_ms=latency_ms,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get exchange status for {exchange}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
