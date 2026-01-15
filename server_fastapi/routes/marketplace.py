"""
Marketplace Routes
API endpoints for copy trading marketplace functionality.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies.auth import get_current_user, require_admin
from ..dependencies.copy_trading import get_copy_trading_service
from ..middleware.cache_manager import cached
from ..services.copy_trading_service import CopyTradingService
from ..services.marketplace_service import MarketplaceService
from ..services.marketplace_verification_service import MarketplaceVerificationService
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter()


class ApplySignalProviderRequest(BaseModel):
    profile_description: str | None = None


class RateSignalProviderRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: str | None = None


class UpdateSignalProviderRequest(BaseModel):
    profile_description: str | None = None
    trading_strategy: str | None = None
    risk_level: str | None = None
    subscription_fee: float | None = None
    performance_fee_percentage: float | None = Field(None, ge=0, le=100)
    minimum_subscription_amount: float | None = None


@router.post("/apply")
async def apply_as_signal_provider(
    request: ApplySignalProviderRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Apply to become a signal provider (requires curator approval)"""
    try:
        user_id = _get_user_id(current_user)
        service = MarketplaceService(db)

        result = await service.apply_as_signal_provider(
            user_id=user_id, profile_description=request.profile_description
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error applying as signal provider: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to apply as signal provider"
        )


@router.get("/traders")
@cached(ttl=300, prefix="marketplace_traders")  # 5 min cache
async def get_marketplace_traders(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query(
        "total_return",
        description="Sort field: total_return, sharpe_ratio, win_rate, follower_count, rating",
    ),
    min_rating: float | None = Query(
        None, ge=0, le=5, description="Minimum average rating"
    ),
    min_win_rate: float | None = Query(
        None, ge=0, le=1, description="Minimum win rate (0-1)"
    ),
    min_sharpe: float | None = Query(None, description="Minimum Sharpe ratio"),
):
    """Get list of signal providers for marketplace"""
    try:
        service = MarketplaceService(db)

        result = await service.get_marketplace_traders(
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            min_rating=min_rating,
            min_win_rate=min_win_rate,
            min_sharpe=min_sharpe,
        )

        return result
    except Exception as e:
        logger.error(f"Error getting marketplace traders: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get marketplace traders")


@router.get("/traders/{trader_id}")
@cached(ttl=120, prefix="marketplace_trader")
async def get_trader_profile(
    trader_id: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get detailed profile of a signal provider"""
    try:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        from ..models.signal_provider import SignalProvider

        result = await db.execute(
            select(SignalProvider)
            .where(SignalProvider.id == trader_id)
            .options(selectinload(SignalProvider.user))
        )
        signal_provider = result.scalar_one_or_none()

        if not signal_provider:
            raise HTTPException(status_code=404, detail="Signal provider not found")

        user = signal_provider.user

        return {
            "id": signal_provider.id,
            "user_id": signal_provider.user_id,
            "username": user.username or user.email if user else None,
            "profile_description": signal_provider.profile_description,
            "trading_strategy": signal_provider.trading_strategy,
            "risk_level": signal_provider.risk_level,
            "total_return": signal_provider.total_return,
            "sharpe_ratio": signal_provider.sharpe_ratio,
            "win_rate": signal_provider.win_rate,
            "total_trades": signal_provider.total_trades,
            "winning_trades": signal_provider.winning_trades,
            "total_profit": signal_provider.total_profit,
            "max_drawdown": signal_provider.max_drawdown,
            "profit_factor": signal_provider.profit_factor,
            "follower_count": signal_provider.follower_count,
            "average_rating": signal_provider.average_rating,
            "total_ratings": signal_provider.total_ratings,
            "subscription_fee": signal_provider.subscription_fee,
            "performance_fee_percentage": signal_provider.performance_fee_percentage,
            "curator_status": signal_provider.curator_status,
            "last_metrics_update": (
                signal_provider.last_metrics_update.isoformat()
                if signal_provider.last_metrics_update
                else None
            ),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trader profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get trader profile")


@router.post("/traders/{trader_id}/rate")
async def rate_trader(
    trader_id: int,
    request: RateSignalProviderRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Rate a signal provider (1-5 stars)"""
    try:
        user_id = _get_user_id(current_user)
        service = MarketplaceService(db)

        result = await service.rate_signal_provider(
            signal_provider_id=trader_id,
            user_id=user_id,
            rating=request.rating,
            comment=request.comment,
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error rating trader: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to rate trader")


@router.post("/traders/{trader_id}/follow")
async def follow_trader_marketplace(
    trader_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    copy_trading_service: Annotated[
        CopyTradingService, Depends(get_copy_trading_service)
    ],
):
    """Follow a trader from the marketplace"""
    try:
        follower_id = _get_user_id(current_user)

        result = await copy_trading_service.follow_trader(
            follower_id=follower_id,
            trader_id=trader_id,
            allocation_percentage=100.0,  # Default allocation
            max_position_size=None,
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error following trader: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to follow trader")


@router.delete("/traders/{trader_id}/follow")
async def unfollow_trader_marketplace(
    trader_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    copy_trading_service: Annotated[
        CopyTradingService, Depends(get_copy_trading_service)
    ],
):
    """Unfollow a trader from the marketplace"""
    try:
        follower_id = _get_user_id(current_user)

        success = await copy_trading_service.unfollow_trader(follower_id, trader_id)

        if success:
            return {"message": "Successfully unfollowed trader"}
        else:
            raise HTTPException(status_code=404, detail="Follow relationship not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unfollowing trader: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to unfollow trader")


@router.post("/traders/{trader_id}/update-metrics")
async def update_trader_metrics(
    trader_id: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Update performance metrics for a signal provider (admin/curator only)"""
    try:
        service = MarketplaceService(db)

        result = await service.update_performance_metrics(signal_provider_id=trader_id)

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating trader metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update trader metrics")


@router.get("/payouts/calculate")
async def calculate_payout(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    signal_provider_id: int = Query(..., description="Signal provider ID"),
    period_days: int = Query(30, ge=1, le=365, description="Period in days"),
):
    """Calculate payout for a signal provider"""
    try:
        user_id = _get_user_id(current_user)

        # Verify user owns the signal provider
        from sqlalchemy import select

        from ..models.signal_provider import SignalProvider

        result = await db.execute(
            select(SignalProvider).where(SignalProvider.id == signal_provider_id)
        )
        signal_provider = result.scalar_one_or_none()

        if not signal_provider or signal_provider.user_id != user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to view this payout"
            )

        service = MarketplaceService(db)
        period_end = datetime.now(UTC)
        period_start = period_end - timedelta(days=period_days)

        result = await service.calculate_payout(
            signal_provider_id=signal_provider_id,
            period_start=period_start,
            period_end=period_end,
        )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating payout: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to calculate payout")


@router.post("/payouts/create")
async def create_payout(
    signal_provider_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    period_days: int = Query(30, ge=1, le=365, description="Period in days"),
):
    """Create a payout record for a signal provider"""
    try:
        user_id = _get_user_id(current_user)

        # Verify user owns the signal provider
        from sqlalchemy import select

        from ..models.signal_provider import SignalProvider

        result = await db.execute(
            select(SignalProvider).where(SignalProvider.id == signal_provider_id)
        )
        signal_provider = result.scalar_one_or_none()

        if not signal_provider or signal_provider.user_id != user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to create this payout"
            )

        service = MarketplaceService(db)
        period_end = datetime.now(UTC)
        period_start = period_end - timedelta(days=period_days)

        result = await service.create_payout(
            signal_provider_id=signal_provider_id,
            period_start=period_start,
            period_end=period_end,
        )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating payout: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create payout")


@router.post("/traders/{trader_id}/verify")
async def verify_trader_performance(
    trader_id: int,
    current_user: Annotated[dict, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    period_days: int = Query(90, ge=1, le=365, description="Period in days"),
):
    """Verify historical performance of a signal provider (admin only)"""
    try:
        service = MarketplaceVerificationService(db)

        result = await service.verify_provider_performance(
            provider_id=trader_id,
            period_days=period_days,
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error verifying trader performance: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to verify trader performance"
        )


@router.post("/traders/verify-all")
async def verify_all_traders(
    current_user: Annotated[dict, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    period_days: int = Query(90, ge=1, le=365, description="Period in days"),
):
    """Verify all signal providers (admin only)"""
    try:
        service = MarketplaceVerificationService(db)

        result = await service.verify_all_providers(period_days=period_days)

        return result
    except Exception as e:
        logger.error(f"Error verifying all traders: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to verify all traders")


@router.get("/traders/flagged")
async def get_flagged_traders(
    current_user: Annotated[dict, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    threshold_days: int = Query(
        30, ge=1, le=365, description="Days since last verification"
    ),
):
    """Get list of flagged/suspicious signal providers (admin only)"""
    try:
        service = MarketplaceVerificationService(db)

        flagged = await service.flag_suspicious_providers(threshold_days=threshold_days)

        return {
            "flagged_count": len(flagged),
            "flagged_providers": flagged,
        }
    except Exception as e:
        logger.error(f"Error getting flagged traders: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get flagged traders")


@router.get("/analytics/provider/{provider_id}")
async def get_provider_analytics(
    request: Request,
    provider_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get analytics for a specific signal provider (owner only)"""
    try:
        user_id = _get_user_id(current_user)

        # Verify user owns the provider
        from sqlalchemy import select

        from ..models.signal_provider import SignalProvider

        result = await db.execute(
            select(SignalProvider).where(SignalProvider.id == provider_id)
        )
        provider = result.scalar_one_or_none()

        if not provider:
            raise HTTPException(status_code=404, detail="Signal provider not found")

        if provider.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view this provider's analytics",
            )

        from ..services.marketplace_analytics_service import MarketplaceAnalyticsService

        analytics_service = MarketplaceAnalyticsService(db)

        analytics = await analytics_service.get_provider_analytics(
            provider_id=provider_id
        )

        return analytics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting provider analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get provider analytics")


# Analytics Threshold Management Routes


class CreateThresholdRequest(BaseModel):
    threshold_type: str = Field(
        ...,
        description="Type of threshold (copy_trading, indicator_marketplace, provider, developer, marketplace_overview)",
    )
    metric: str = Field(..., description="Metric to monitor")
    operator: str = Field(
        ...,
        description="Comparison operator (gt, lt, eq, gte, lte, percent_change_down, percent_change_up)",
    )
    threshold_value: float = Field(..., description="Threshold value")
    context: dict | None = Field(
        None, description="Context data (e.g., provider_id, developer_id)"
    )
    enabled: bool = Field(True, description="Whether threshold is enabled")
    notification_channels: dict | None = Field(
        None, description="Notification channels configuration"
    )
    cooldown_minutes: int = Field(60, description="Cooldown period in minutes")
    name: str | None = Field(None, description="Threshold name")
    description: str | None = Field(None, description="Threshold description")


class UpdateThresholdRequest(BaseModel):
    enabled: bool | None = None
    threshold_value: float | None = None
    operator: str | None = None
    notification_channels: dict | None = None
    cooldown_minutes: int | None = None
    name: str | None = None
    description: str | None = None


@router.post("/analytics/thresholds")
async def create_analytics_threshold(
    request: CreateThresholdRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Create a new analytics threshold"""
    try:
        user_id = _get_user_id(current_user)

        from ..models.analytics_threshold import (
            AnalyticsThreshold,
            ThresholdMetric,
            ThresholdOperator,
            ThresholdType,
        )

        # Validate threshold type
        valid_types = [t.value for t in ThresholdType]
        if request.threshold_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid threshold_type. Must be one of: {', '.join(valid_types)}",
            )

        # Validate operator
        valid_operators = [op.value for op in ThresholdOperator]
        if request.operator not in valid_operators:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid operator. Must be one of: {', '.join(valid_operators)}",
            )

        # Validate metric (basic check - metric should be a valid ThresholdMetric enum value)
        valid_metrics = [m.value for m in ThresholdMetric]
        if request.metric not in valid_metrics:
            raise HTTPException(
                status_code=400,
                detail="Invalid metric. Must be a valid ThresholdMetric value",
            )

        # Validate cooldown
        if request.cooldown_minutes < 1:
            raise HTTPException(
                status_code=400, detail="cooldown_minutes must be at least 1"
            )

        # Validate context for provider/developer types
        if request.threshold_type in [
            ThresholdType.PROVIDER.value,
            ThresholdType.DEVELOPER.value,
        ]:
            if not request.context:
                raise HTTPException(
                    status_code=400,
                    detail=f"context with {request.threshold_type}_id is required for {request.threshold_type} thresholds",
                )
            context_key = f"{request.threshold_type}_id"
            if context_key not in request.context:
                raise HTTPException(
                    status_code=400, detail=f"context must include {context_key}"
                )

        threshold = AnalyticsThreshold(
            user_id=user_id,
            threshold_type=request.threshold_type,
            metric=request.metric,
            operator=request.operator,
            threshold_value=request.threshold_value,
            context=request.context,
            enabled=request.enabled,
            notification_channels=request.notification_channels
            or {
                "email": True,
                "push": True,
                "in_app": True,
            },
            cooldown_minutes=request.cooldown_minutes,
            name=request.name,
            description=request.description,
        )

        db.add(threshold)
        await db.commit()
        await db.refresh(threshold)

        logger.info(
            f"Created analytics threshold {threshold.id} for user {user_id}",
            extra={
                "threshold_id": threshold.id,
                "user_id": user_id,
                "threshold_type": threshold.threshold_type,
            },
        )

        return {
            "id": threshold.id,
            "threshold_type": threshold.threshold_type,
            "metric": threshold.metric,
            "operator": threshold.operator,
            "threshold_value": threshold.threshold_value,
            "enabled": threshold.enabled,
            "created_at": threshold.created_at.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating threshold: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create threshold")


@router.get("/analytics/thresholds")
async def get_analytics_thresholds(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    threshold_type: str | None = Query(None, description="Filter by threshold type"),
):
    """Get all analytics thresholds for the current user"""
    try:
        user_id = _get_user_id(current_user)

        from sqlalchemy import select

        from ..models.analytics_threshold import AnalyticsThreshold

        query = select(AnalyticsThreshold).where(AnalyticsThreshold.user_id == user_id)

        if threshold_type:
            query = query.where(AnalyticsThreshold.threshold_type == threshold_type)

        result = await db.execute(query)
        thresholds = result.scalars().all()

        return [
            {
                "id": t.id,
                "threshold_type": t.threshold_type,
                "metric": t.metric,
                "operator": t.operator,
                "threshold_value": t.threshold_value,
                "context": t.context,
                "enabled": t.enabled,
                "notification_channels": t.notification_channels,
                "cooldown_minutes": t.cooldown_minutes,
                "last_triggered_at": (
                    t.last_triggered_at.isoformat() if t.last_triggered_at else None
                ),
                "name": t.name,
                "description": t.description,
                "created_at": t.created_at.isoformat(),
            }
            for t in thresholds
        ]
    except Exception as e:
        logger.error(f"Error getting thresholds: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get thresholds")


@router.get("/analytics/thresholds/{threshold_id}")
async def get_analytics_threshold(
    threshold_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get a specific analytics threshold"""
    try:
        user_id = _get_user_id(current_user)

        from sqlalchemy import select

        from ..models.analytics_threshold import AnalyticsThreshold

        result = await db.execute(
            select(AnalyticsThreshold).where(
                AnalyticsThreshold.id == threshold_id,
                AnalyticsThreshold.user_id == user_id,
            )
        )
        threshold = result.scalar_one_or_none()

        if not threshold:
            raise HTTPException(status_code=404, detail="Threshold not found")

        return {
            "id": threshold.id,
            "threshold_type": threshold.threshold_type,
            "metric": threshold.metric,
            "operator": threshold.operator,
            "threshold_value": threshold.threshold_value,
            "context": threshold.context,
            "enabled": threshold.enabled,
            "notification_channels": threshold.notification_channels,
            "cooldown_minutes": threshold.cooldown_minutes,
            "last_triggered_at": (
                threshold.last_triggered_at.isoformat()
                if threshold.last_triggered_at
                else None
            ),
            "name": threshold.name,
            "description": threshold.description,
            "created_at": threshold.created_at.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting threshold: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get threshold")


@router.put("/analytics/thresholds/{threshold_id}")
async def update_analytics_threshold(
    threshold_id: int,
    request: UpdateThresholdRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Update an analytics threshold"""
    try:
        user_id = _get_user_id(current_user)

        from sqlalchemy import select

        from ..models.analytics_threshold import AnalyticsThreshold

        result = await db.execute(
            select(AnalyticsThreshold).where(
                AnalyticsThreshold.id == threshold_id,
                AnalyticsThreshold.user_id == user_id,
            )
        )
        threshold = result.scalar_one_or_none()

        if not threshold:
            raise HTTPException(status_code=404, detail="Threshold not found")

        if request.enabled is not None:
            threshold.enabled = request.enabled
        if request.threshold_value is not None:
            threshold.threshold_value = request.threshold_value
        if request.operator is not None:
            threshold.operator = request.operator
        if request.notification_channels is not None:
            threshold.notification_channels = request.notification_channels
        if request.cooldown_minutes is not None:
            threshold.cooldown_minutes = request.cooldown_minutes
        if request.name is not None:
            threshold.name = request.name
        if request.description is not None:
            threshold.description = request.description

        await db.commit()
        await db.refresh(threshold)

        return {
            "id": threshold.id,
            "threshold_type": threshold.threshold_type,
            "metric": threshold.metric,
            "operator": threshold.operator,
            "threshold_value": threshold.threshold_value,
            "enabled": threshold.enabled,
            "updated_at": threshold.updated_at.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating threshold: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update threshold")


@router.delete("/analytics/thresholds/{threshold_id}")
async def delete_analytics_threshold(
    threshold_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Delete an analytics threshold"""
    try:
        user_id = _get_user_id(current_user)

        from sqlalchemy import select

        from ..models.analytics_threshold import AnalyticsThreshold

        result = await db.execute(
            select(AnalyticsThreshold).where(
                AnalyticsThreshold.id == threshold_id,
                AnalyticsThreshold.user_id == user_id,
            )
        )
        threshold = result.scalar_one_or_none()

        if not threshold:
            raise HTTPException(status_code=404, detail="Threshold not found")

        await db.delete(threshold)
        await db.commit()

        return {"message": "Threshold deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting threshold: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete threshold")


@router.post("/analytics/thresholds/{threshold_id}/test")
async def test_analytics_threshold(
    threshold_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Manually test/trigger a threshold check"""
    try:
        user_id = _get_user_id(current_user)

        from sqlalchemy import select

        from ..models.analytics_threshold import AnalyticsThreshold
        from ..services.marketplace_threshold_service import MarketplaceThresholdService

        result = await db.execute(
            select(AnalyticsThreshold).where(
                AnalyticsThreshold.id == threshold_id,
                AnalyticsThreshold.user_id == user_id,
            )
        )
        threshold = result.scalar_one_or_none()

        if not threshold:
            raise HTTPException(status_code=404, detail="Threshold not found")

        threshold_service = MarketplaceThresholdService(db)
        alert = await threshold_service._check_threshold(threshold)

        if alert:
            return {
                "triggered": True,
                "alert": alert,
            }
        else:
            return {
                "triggered": False,
                "message": "Threshold condition not met",
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing threshold: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to test threshold")
