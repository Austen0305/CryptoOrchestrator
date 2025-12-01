"""
Production Monitoring Routes
Health checks, system status, and production alerts
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
import logging
from ..services.monitoring.production_monitor import production_monitor
from ..dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitoring", tags=["Production Monitoring"])


@router.get("/health")
async def get_system_health() -> Dict[str, Any]:
    """Get overall system health status"""
    try:
        health = await production_monitor.get_system_health()
        return health
    except Exception as e:
        logger.error(f"Error getting system health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get system health")


@router.get("/exchanges")
async def get_exchange_status() -> Dict[str, Dict[str, Any]]:
    """Get status of all exchanges"""
    try:
        exchange_statuses = {}
        supported_exchanges = ["binance", "kraken", "coinbasepro", "kucoin", "bybit"]
        
        for exchange in supported_exchanges:
            status = await production_monitor.get_exchange_status(exchange)
            exchange_statuses[exchange] = status
        
        return exchange_statuses
    except Exception as e:
        logger.error(f"Error getting exchange status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get exchange status")


@router.get("/exchange/{exchange_name}")
async def get_exchange_health(exchange_name: str) -> Dict[str, Any]:
    """Get detailed health status for a specific exchange"""
    try:
        status = await production_monitor.get_exchange_status(exchange_name)
        return status
    except Exception as e:
        logger.error(f"Error getting exchange health for {exchange_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get exchange health for {exchange_name}")


@router.get("/alerts")
async def get_production_alerts(
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get production alerts (requires authentication)"""
    try:
        alerts = await production_monitor.get_alerts()
        return alerts
    except Exception as e:
        logger.error(f"Error getting production alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get production alerts")


@router.get("/metrics")
async def get_trading_metrics() -> Dict[str, Any]:
    """Get trading metrics (24h)"""
    try:
        return production_monitor.trading_metrics.copy()
    except Exception as e:
        logger.error(f"Error getting trading metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get trading metrics")

