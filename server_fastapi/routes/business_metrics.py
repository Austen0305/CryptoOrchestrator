"""
Business Metrics API Endpoints
Exposes business KPIs: revenue, user growth, trading volume, etc.
"""

import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies.auth import require_permission
from ..services.monitoring.business_metrics import get_business_metrics_service
from ..services.monitoring.enhanced_business_metrics import (
    get_enhanced_business_metrics_service,
)
from ..services.observability.opentelemetry_setup import (
    get_tracer,
    record_metric,
)
from ..services.platform_revenue import platform_revenue_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/summary")
async def get_business_metrics_summary(
    current_user: Annotated[dict, Depends(require_permission("admin:metrics"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get comprehensive business metrics summary (admin only)"""
    try:
        tracer = get_tracer()
        with (
            tracer.start_as_current_span("get_business_metrics_summary")
            if tracer
            else None
        ):
            metrics_service = get_business_metrics_service(db)
            all_metrics = await metrics_service.get_all_business_metrics(db)

            # Record metric in OpenTelemetry
            record_metric("business_metrics_requested", 1.0)

            return all_metrics
    except Exception as e:
        logger.error(f"Error getting business metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get business metrics: {str(e)}"
        )


@router.get("/revenue")
async def get_revenue_metrics(
    current_user: Annotated[dict, Depends(require_permission("admin:metrics"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    start_date: datetime | None = Query(None, description="Start date"),
    end_date: datetime | None = Query(None, description="End date"),
):
    """Get revenue metrics (admin only)"""
    try:
        metrics_service = get_business_metrics_service(db)
        revenue = await metrics_service.get_revenue_metrics(
            db=db, start_date=start_date, end_date=end_date
        )

        # Also get from platform revenue service
        platform_revenue = await platform_revenue_service.get_total_revenue(
            start_date=start_date, end_date=end_date, db=db
        )

        return {**revenue, "platform_revenue": platform_revenue}
    except Exception as e:
        logger.error(f"Error getting revenue metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get revenue metrics: {str(e)}"
        )


@router.get("/revenue/daily")
async def get_daily_revenue(
    current_user: Annotated[dict, Depends(require_permission("admin:metrics"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    days: int = Query(30, ge=1, le=365, description="Number of days"),
):
    """Get daily revenue breakdown (admin only)"""
    try:
        daily_revenue = await platform_revenue_service.get_daily_revenue(
            days=days, db=db
        )

        return {
            "daily_revenue": daily_revenue,
            "days": days,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting daily revenue: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get daily revenue: {str(e)}"
        )


@router.get("/users")
async def get_user_metrics(
    current_user: Annotated[dict, Depends(require_permission("admin:metrics"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get user growth and activity metrics (admin only)"""
    try:
        metrics_service = get_business_metrics_service(db)
        user_metrics = await metrics_service.update_user_metrics(db)

        return {**user_metrics, "timestamp": datetime.now(UTC).isoformat()}
    except Exception as e:
        logger.error(f"Error getting user metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get user metrics: {str(e)}"
        )


@router.get("/trades")
async def get_trade_metrics(
    current_user: Annotated[dict, Depends(require_permission("admin:metrics"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    days: int = Query(30, ge=1, le=365, description="Number of days"),
):
    """Get trading metrics (admin only)"""
    try:
        metrics_service = get_business_metrics_service(db)
        trades_per_day = await metrics_service.get_trades_per_day(db, days=days)

        return {
            "trades_per_day": trades_per_day,
            "days": days,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting trade metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get trade metrics: {str(e)}"
        )


@router.get("/dashboard")
async def get_business_dashboard(
    current_user: Annotated[dict, Depends(require_permission("admin:metrics"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get comprehensive business dashboard data (admin only)"""
    try:
        tracer = get_tracer()
        with tracer.start_as_current_span("get_business_dashboard") if tracer else None:
            metrics_service = get_business_metrics_service(db)
            enhanced_service = get_enhanced_business_metrics_service(db)

            # Get all metrics in parallel
            user_metrics = await metrics_service.update_user_metrics(db)
            revenue_metrics = await metrics_service.get_revenue_metrics(db)
            trades_per_day = await metrics_service.get_trades_per_day(db, days=30)

            # Get platform revenue
            platform_revenue = await platform_revenue_service.get_total_revenue(db=db)
            daily_revenue = await platform_revenue_service.get_daily_revenue(
                days=30, db=db
            )

            # Get enhanced KPIs
            kpis = await enhanced_service.get_business_kpis(db, period_days=30)
            user_acquisition = await enhanced_service.get_user_acquisition_metrics(
                db, days=30
            )
            trading_activity = await enhanced_service.get_trading_activity_metrics(
                db, days=30
            )

            return {
                "users": user_metrics,
                "revenue": {
                    **revenue_metrics,
                    "platform_revenue": platform_revenue,
                    "daily_revenue": daily_revenue,
                },
                "trades": {"trades_per_day": trades_per_day},
                "kpis": kpis,
                "user_acquisition": user_acquisition,
                "trading_activity": trading_activity,
                "timestamp": datetime.now(UTC).isoformat(),
            }
    except Exception as e:
        logger.error(f"Error getting business dashboard: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get business dashboard: {str(e)}"
        )


@router.get("/kpis")
async def get_business_kpis(
    current_user: Annotated[dict, Depends(require_permission("admin:metrics"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    period_days: int = Query(30, ge=1, le=365, description="Period in days"),
):
    """Get business KPIs with growth rates (admin only)"""
    try:
        enhanced_service = get_enhanced_business_metrics_service(db)
        kpis = await enhanced_service.get_business_kpis(db, period_days=period_days)
        return kpis
    except Exception as e:
        logger.error(f"Error getting business KPIs: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get business KPIs: {str(e)}"
        )


@router.get("/user-acquisition")
async def get_user_acquisition(
    current_user: Annotated[dict, Depends(require_permission("admin:metrics"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    days: int = Query(30, ge=1, le=365, description="Number of days"),
):
    """Get user acquisition metrics (admin only)"""
    try:
        enhanced_service = get_enhanced_business_metrics_service(db)
        metrics = await enhanced_service.get_user_acquisition_metrics(db, days=days)
        return metrics
    except Exception as e:
        logger.error(f"Error getting user acquisition metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get user acquisition metrics: {str(e)}"
        )


@router.get("/trading-activity")
async def get_trading_activity(
    current_user: Annotated[dict, Depends(require_permission("admin:metrics"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    days: int = Query(30, ge=1, le=365, description="Number of days"),
):
    """Get trading activity metrics by mode and chain (admin only)"""
    try:
        enhanced_service = get_enhanced_business_metrics_service(db)
        metrics = await enhanced_service.get_trading_activity_metrics(db, days=days)
        return metrics
    except Exception as e:
        logger.error(f"Error getting trading activity metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get trading activity metrics: {str(e)}"
        )


@router.get("/user-acquisition-cost")
async def get_user_acquisition_cost(
    current_user: Annotated[dict, Depends(require_permission("admin:metrics"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    days: int = Query(30, ge=1, le=365, description="Number of days"),
):
    """Get user acquisition cost (CAC) metrics (admin only)"""
    try:
        enhanced_service = get_enhanced_business_metrics_service(db)
        metrics = await enhanced_service.calculate_user_acquisition_cost(db, days=days)
        return metrics
    except Exception as e:
        logger.error(f"Error getting CAC metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get CAC metrics: {str(e)}"
        )


@router.get("/lifetime-value")
async def get_lifetime_value(
    current_user: Annotated[dict, Depends(require_permission("admin:metrics"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    days: int = Query(90, ge=1, le=365, description="Number of days"),
):
    """Get customer lifetime value (LTV) metrics (admin only)"""
    try:
        enhanced_service = get_enhanced_business_metrics_service(db)
        metrics = await enhanced_service.calculate_lifetime_value(db, days=days)
        return metrics
    except Exception as e:
        logger.error(f"Error getting LTV metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get LTV metrics: {str(e)}"
        )


@router.get("/churn")
async def get_churn_analysis(
    current_user: Annotated[dict, Depends(require_permission("admin:metrics"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    days: int = Query(30, ge=1, le=365, description="Number of days"),
):
    """Get user churn analysis (admin only)"""
    try:
        enhanced_service = get_enhanced_business_metrics_service(db)
        metrics = await enhanced_service.analyze_churn(db, days=days)
        return metrics
    except Exception as e:
        logger.error(f"Error getting churn analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get churn analysis: {str(e)}"
        )


@router.get("/trading/detailed")
async def get_detailed_trading_metrics(
    current_user: Annotated[dict, Depends(require_permission("admin:metrics"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    days: int = Query(30, ge=1, le=365, description="Number of days"),
):
    """Get detailed trading metrics: volume, avg size, pairs, success rates (admin only)"""
    try:
        enhanced_service = get_enhanced_business_metrics_service(db)
        metrics = await enhanced_service.get_detailed_trading_metrics(db, days=days)
        return metrics
    except Exception as e:
        logger.error(f"Error getting detailed trading metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get detailed trading metrics: {str(e)}"
        )
