"""
Transaction Monitoring Routes
API endpoints for transaction monitoring and statistics
"""

import logging
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from ..dependencies.auth import get_current_user
from ..middleware.cache_manager import cached
from ..services.monitoring.transaction_monitor import transaction_monitor
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/monitoring/transactions", tags=["Transaction Monitoring"]
)


class TransactionStatsResponse(BaseModel):
    """Response model for transaction statistics"""

    total: int
    successful: int
    failed: int
    pending: int
    success_rate: float
    total_amount: str
    total_gas: str
    avg_latency_seconds: float
    chain_id: int | None = None
    transaction_type: str | None = None
    period: dict[str, str | None] | None = None


class SuspiciousPatternResponse(BaseModel):
    """Response model for suspicious pattern"""

    pattern: str
    user_id: int | None = None
    transaction_hash: str | None = None
    amount: str | None = None
    severity: str
    description: str


class TransactionReportResponse(BaseModel):
    """Response model for transaction report"""

    period: dict[str, str]
    summary: dict[str, Any]
    chain_breakdown: dict[str, dict[str, int]]
    suspicious_patterns: list[dict[str, Any]]
    generated_at: str


@router.get(
    "/stats", response_model=TransactionStatsResponse, tags=["Transaction Monitoring"]
)
@cached(ttl=60, prefix="transaction_stats")  # 60s TTL for transaction statistics
async def get_transaction_stats(
    chain_id: int | None = Query(None, description="Filter by chain ID"),
    transaction_type: str | None = Query(
        None, description="Filter by transaction type (deposit, withdrawal, swap)"
    ),
    start_date: str | None = Query(None, description="Start date (ISO format)"),
    end_date: str | None = Query(None, description="End date (ISO format)"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> TransactionStatsResponse:
    """
    Get transaction statistics

    Returns success rates, latency, and volume metrics.
    """
    try:
        # Parse dates
        start_datetime = None
        end_datetime = None

        if start_date:
            try:
                start_datetime = datetime.fromisoformat(
                    start_date.replace("Z", "+00:00")
                )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use ISO format (e.g., 2025-12-06T00:00:00Z)",
                )

        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use ISO format (e.g., 2025-12-06T23:59:59Z)",
                )

        # Get stats
        stats = await transaction_monitor.get_transaction_stats(
            chain_id=chain_id,
            transaction_type=transaction_type,
            start_date=start_datetime,
            end_date=end_datetime,
        )

        return TransactionStatsResponse(**stats)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transaction stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transaction statistics",
        )


@router.get(
    "/suspicious",
    response_model=list[SuspiciousPatternResponse],
    tags=["Transaction Monitoring"],
)
@cached(ttl=120, prefix="suspicious_patterns")  # 120s TTL for suspicious patterns
async def get_suspicious_patterns(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    user_id: int | None = Query(None, description="Filter by user ID"),
    chain_id: int | None = Query(None, description="Filter by chain ID"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> list[SuspiciousPatternResponse]:
    """
    Get detected suspicious transaction patterns with pagination

    Includes high frequency, unusual amounts, and high failure rates.
    """
    try:
        # Check admin permissions for viewing other users' patterns
        current_user_id = _get_user_id(current_user)
        is_admin = current_user.get("role") == "admin" or current_user.get(
            "is_admin", False
        )

        if not is_admin and user_id and int(user_id) != int(current_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view suspicious patterns for your own account",
            )

        # If not admin, default to current user
        if not is_admin:
            user_id = int(current_user_id)

        # Detect suspicious patterns
        patterns = await transaction_monitor.detect_suspicious_patterns(
            user_id=user_id,
            chain_id=chain_id,
        )

        # Apply pagination
        total = len(patterns)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_patterns = patterns[start_idx:end_idx]

        return [SuspiciousPatternResponse(**pattern) for pattern in paginated_patterns]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting suspicious patterns: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve suspicious patterns",
        )


@router.get(
    "/report", response_model=TransactionReportResponse, tags=["Transaction Monitoring"]
)
async def get_transaction_report(
    start_date: str = Query(..., description="Start date (ISO format)"),
    end_date: str = Query(..., description="End date (ISO format)"),
    chain_id: int | None = Query(None, description="Filter by chain ID"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> TransactionReportResponse:
    """
    Generate comprehensive transaction monitoring report

    Includes statistics, chain breakdown, and suspicious patterns.
    """
    try:
        # Parse dates
        try:
            start_datetime = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end_datetime = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use ISO format (e.g., 2025-12-06T00:00:00Z)",
            )

        # Validate date range
        if start_datetime >= end_datetime:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date must be before end_date",
            )

        if (end_datetime - start_datetime).days > 90:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Date range cannot exceed 90 days",
            )

        # Generate report
        report = await transaction_monitor.generate_report(
            start_date=start_datetime,
            end_date=end_datetime,
            chain_id=chain_id,
        )

        return TransactionReportResponse(**report)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating transaction report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate transaction report",
        )
