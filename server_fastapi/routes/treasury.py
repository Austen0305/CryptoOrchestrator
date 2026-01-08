"""
Treasury Dashboard API Routes
Endpoints for treasury management and monitoring
"""

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies.auth import get_current_user
from ..middleware.cache_manager import cached
from ..services.institutional.treasury_service import TreasuryService
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/institutional/treasury", tags=["Treasury"])


class TreasurySummary(BaseModel):
    total_balance_usd: float
    total_wallets: int
    active_wallets: int
    pending_transactions: int
    total_transactions_24h: int
    total_volume_24h_usd: float
    average_transaction_size_usd: float
    largest_wallet_balance_usd: float
    smallest_wallet_balance_usd: float


class TreasuryBalance(BaseModel):
    wallet_id: str
    wallet_name: str
    balance_usd: float
    balance_native: float
    currency: str
    pending_balance_usd: float
    available_balance_usd: float
    last_activity: str | None
    signer_count: int
    required_signatures: int


class TreasuryActivity(BaseModel):
    timestamp: str
    wallet_id: str
    wallet_name: str
    activity_type: str
    amount_usd: float | None
    currency: str
    status: str
    description: str


class RiskMetrics(BaseModel):
    concentration_risk: float
    diversification_score: float
    liquidity_ratio: float
    exposure_by_chain: dict[str, float]
    exposure_by_asset: dict[str, float]
    risk_level: str


@router.get(
    "/summary",
    response_model=TreasurySummary,
    summary="Get treasury summary",
    description="""
    Get comprehensive treasury summary with balances, transactions, and metrics.
    
    **Example Response:**
    ```json
    {
      "total_balance_usd": 5000000.0,
      "total_wallets": 15,
      "active_wallets": 12,
      "pending_transactions": 3,
      "total_transactions_24h": 45,
      "total_volume_24h_usd": 250000.0,
      "average_transaction_size_usd": 5555.56,
      "largest_wallet_balance_usd": 1000000.0,
      "smallest_wallet_balance_usd": 50000.0
    }
    ```
    
    **Query Parameters:**
    - `wallet_id` (optional): Filter summary for a specific wallet
    """,
)
@cached(ttl=60, prefix="treasury_summary")
async def get_treasury_summary(
    wallet_id: str | None = Query(None, description="Filter by wallet ID"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db_session)] = None,
) -> TreasurySummary:
    """Get comprehensive treasury summary"""
    try:
        user_id = _get_user_id(current_user)
        service = TreasuryService(lambda: db)

        summary = service.get_treasury_summary(user_id, wallet_id=wallet_id)

        return TreasurySummary(
            total_balance_usd=float(summary.total_balance_usd),
            total_wallets=summary.total_wallets,
            active_wallets=summary.active_wallets,
            pending_transactions=summary.pending_transactions,
            total_transactions_24h=summary.total_transactions_24h,
            total_volume_24h_usd=float(summary.total_volume_24h_usd),
            average_transaction_size_usd=float(summary.average_transaction_size_usd),
            largest_wallet_balance_usd=float(summary.largest_wallet_balance_usd),
            smallest_wallet_balance_usd=float(summary.smallest_wallet_balance_usd),
        )
    except Exception as e:
        logger.error(f"Error getting treasury summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get treasury summary")


@router.get(
    "/balances",
    response_model=list[TreasuryBalance],
    summary="Get treasury wallet balances",
    description="""
    Get balances for all treasury wallets with optional filtering.
    
    **Example Response:**
    ```json
    [
      {
        "wallet_id": "wallet-123",
        "wallet_name": "Main Treasury",
        "balance_usd": 1000000.0,
        "balance_native": 25.5,
        "currency": "ETH",
        "pending_balance_usd": 50000.0,
        "available_balance_usd": 950000.0,
        "last_activity": "2024-01-15T10:00:00Z",
        "signer_count": 3,
        "required_signatures": 2
      }
    ]
    ```
    """,
)
@cached(ttl=60, prefix="treasury_balances")
async def get_treasury_balances(
    wallet_id: str | None = Query(None, description="Filter by wallet ID"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db_session)] = None,
) -> list[TreasuryBalance]:
    """Get balances for all treasury wallets"""
    try:
        user_id = _get_user_id(current_user)
        service = TreasuryService(lambda: db)

        balances = service.get_wallet_balances(user_id, wallet_id=wallet_id)

        return [
            TreasuryBalance(
                wallet_id=str(b.wallet_id),
                wallet_name=b.wallet_name,
                balance_usd=float(b.balance_usd),
                balance_native=float(b.balance_native),
                currency=b.currency,
                pending_balance_usd=float(b.pending_balance_usd),
                available_balance_usd=float(b.available_balance_usd),
                last_activity=b.last_activity.isoformat() if b.last_activity else None,
                signer_count=b.signer_count,
                required_signatures=b.required_signatures,
            )
            for b in balances
        ]
    except Exception as e:
        logger.error(f"Error getting treasury balances: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get treasury balances")


@router.get(
    "/activity",
    response_model=list[TreasuryActivity],
    summary="Get treasury activity log",
    description="""
    Get treasury activity log with optional filtering by wallet and time range.
    
    **Query Parameters:**
    - `wallet_id` (optional): Filter by specific wallet ID
    - `time_range`: Time range for activity ("1h", "24h", "7d", "30d")
    
    **Example Response:**
    ```json
    [
      {
        "timestamp": "2024-01-15T10:00:00Z",
        "wallet_id": "wallet-123",
        "wallet_name": "Main Treasury",
        "activity_type": "deposit",
        "amount_usd": 100000.0,
        "currency": "USDC",
        "status": "completed",
        "description": "Deposit from exchange"
      }
    ]
    ```
    """,
)
@cached(ttl=30, prefix="treasury_activity")
async def get_treasury_activity(
    wallet_id: str | None = Query(None, description="Filter by wallet ID"),
    time_range: str = Query("24h", description="Time range: 1h, 24h, 7d, 30d"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db_session)] = None,
) -> list[TreasuryActivity]:
    """Get treasury activity log"""
    try:
        from datetime import timedelta

        user_id = _get_user_id(current_user)
        service = TreasuryService(lambda: db)

        # Parse time range
        end_date = datetime.now()
        if time_range == "1h":
            start_date = end_date - timedelta(hours=1)
        elif time_range == "24h":
            start_date = end_date - timedelta(days=1)
        elif time_range == "7d":
            start_date = end_date - timedelta(days=7)
        elif time_range == "30d":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=1)

        activities = service.get_treasury_activity(
            user_id=user_id,
            wallet_id=wallet_id,
            limit=1000,
            start_date=start_date,
            end_date=end_date,
        )

        return [
            TreasuryActivity(
                timestamp=a.timestamp.isoformat(),
                wallet_id=str(a.wallet_id),
                wallet_name=a.wallet_name,
                activity_type=a.activity_type,
                amount_usd=float(a.amount_usd) if a.amount_usd else None,
                currency=a.currency,
                status=a.status,
                description=a.description,
            )
            for a in activities
        ]
    except Exception as e:
        logger.error(f"Error getting treasury activity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get treasury activity")


@router.get(
    "/risk-metrics",
    response_model=RiskMetrics,
    summary="Get treasury risk metrics",
    description="""
    Get comprehensive risk metrics for treasury operations.
    
    **Example Response:**
    ```json
    {
      "concentration_risk": 0.35,
      "diversification_score": 0.75,
      "liquidity_ratio": 0.85,
      "exposure_by_chain": {
        "ethereum": 0.60,
        "base": 0.25,
        "arbitrum": 0.15
      },
      "exposure_by_asset": {
        "ETH": 0.50,
        "USDC": 0.30,
        "BTC": 0.20
      },
      "risk_level": "moderate"
    }
    ```
    """,
)
@cached(ttl=120, prefix="treasury_risk_metrics")
async def get_treasury_risk_metrics(
    wallet_id: str | None = Query(None, description="Filter by wallet ID"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db_session)] = None,
) -> RiskMetrics:
    """Get treasury risk metrics"""
    try:
        user_id = _get_user_id(current_user)
        service = TreasuryService(lambda: db)

        metrics = service.get_risk_metrics(user_id, wallet_id=wallet_id)

        return RiskMetrics(
            concentration_risk=float(metrics.get("concentration_risk", 0.0)),
            diversification_score=float(metrics.get("diversification_score", 0.0)),
            liquidity_ratio=float(metrics.get("liquidity_ratio", 0.0)),
            exposure_by_chain=metrics.get("exposure_by_chain", {}),
            exposure_by_asset=metrics.get("exposure_by_asset", {}),
            risk_level=metrics.get("risk_level", "medium"),
        )
    except Exception as e:
        logger.error(f"Error getting treasury risk metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to get treasury risk metrics"
        )
