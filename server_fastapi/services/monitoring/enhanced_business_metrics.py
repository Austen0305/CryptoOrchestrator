"""
Enhanced Business Metrics Service
Extends business metrics with OpenTelemetry integration and advanced analytics
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..observability.opentelemetry_setup import (
    OTEL_AVAILABLE,
    get_meter,
    get_tracer,
    record_gauge,
)
from .business_metrics import BusinessMetricsService

logger = logging.getLogger(__name__)


class EnhancedBusinessMetricsService(BusinessMetricsService):
    """
    Enhanced business metrics service with OpenTelemetry integration

    Features:
    - Automatic OpenTelemetry metric recording
    - Distributed tracing for business operations
    - Advanced analytics and aggregations
    - Real-time metric updates
    """

    def __init__(self, db: AsyncSession | None = None):
        super().__init__(db)
        self.tracer = get_tracer() if OTEL_AVAILABLE else None
        self.meter = get_meter() if OTEL_AVAILABLE else None

    async def get_business_kpis(
        self, db: AsyncSession, period_days: int = 30
    ) -> dict[str, Any]:
        """
        Get comprehensive business KPIs

        Returns:
            Dict with key performance indicators
        """
        try:
            tracer = self.tracer
            with tracer.start_as_current_span("get_business_kpis") if tracer else None:
                # Get all metrics
                user_metrics = await self.update_user_metrics(db)
                revenue_metrics = await self.get_revenue_metrics(db)
                trades_per_day = await self.get_trades_per_day(db, days=period_days)

                # Calculate growth rates
                if len(trades_per_day) >= 2:
                    recent_trades = sum(t["trade_count"] for t in trades_per_day[:7])
                    previous_trades = (
                        sum(t["trade_count"] for t in trades_per_day[7:14])
                        if len(trades_per_day) >= 14
                        else recent_trades
                    )
                    trade_growth = (
                        ((recent_trades - previous_trades) / previous_trades * 100)
                        if previous_trades > 0
                        else 0
                    )
                else:
                    trade_growth = 0

                # Calculate revenue growth
                revenue_growth = 0.0
                if revenue_metrics.get("total_revenue", 0) > 0:
                    # Would need historical data for accurate growth calculation
                    pass

                kpis = {
                    "users": {
                        **user_metrics,
                        "growth_rate": 0.0,  # Would calculate from historical data
                    },
                    "revenue": {**revenue_metrics, "growth_rate": revenue_growth},
                    "trades": {
                        "total_last_30_days": sum(
                            t["trade_count"] for t in trades_per_day
                        ),
                        "average_per_day": (
                            sum(t["trade_count"] for t in trades_per_day)
                            / len(trades_per_day)
                            if trades_per_day
                            else 0
                        ),
                        "growth_rate": trade_growth,
                        "daily_breakdown": trades_per_day,
                    },
                    "timestamp": datetime.now(UTC).isoformat(),
                }

                # Record KPIs in OpenTelemetry
                if OTEL_AVAILABLE:
                    record_gauge(
                        "business.kpi.total_users",
                        float(user_metrics.get("total_users", 0)),
                    )
                    record_gauge(
                        "business.kpi.active_users_24h",
                        float(user_metrics.get("active_users_24h", 0)),
                    )
                    record_gauge(
                        "business.kpi.total_revenue",
                        float(revenue_metrics.get("total_revenue", 0)),
                    )
                    record_gauge("business.kpi.trade_growth_rate", trade_growth)

                return kpis

        except Exception as e:
            logger.error(f"Error getting business KPIs: {e}", exc_info=True)
            return {"error": str(e), "timestamp": datetime.now(UTC).isoformat()}

    async def get_user_acquisition_metrics(
        self, db: AsyncSession, days: int = 30
    ) -> dict[str, Any]:
        """Get user acquisition metrics"""
        try:
            from ..models.user import User

            start_date = datetime.now(UTC) - timedelta(days=days)

            # Daily user registrations
            daily_registrations_stmt = (
                select(
                    func.date(User.created_at).label("date"),
                    func.count(User.id).label("count"),
                )
                .where(User.created_at >= start_date)
                .group_by(func.date(User.created_at))
                .order_by(func.date(User.created_at).desc())
            )

            result = await db.execute(daily_registrations_stmt)
            daily_registrations = [
                {
                    "date": (
                        row.date.isoformat()
                        if hasattr(row.date, "isoformat")
                        else str(row.date)
                    ),
                    "count": row.count,
                }
                for row in result
            ]

            # Total new users
            total_new_users = sum(r["count"] for r in daily_registrations)

            return {
                "period_days": days,
                "total_new_users": total_new_users,
                "daily_registrations": daily_registrations,
                "average_per_day": total_new_users / days if days > 0 else 0,
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting user acquisition metrics: {e}", exc_info=True)
            return {"error": str(e), "timestamp": datetime.now(UTC).isoformat()}

    async def get_trading_activity_metrics(
        self, db: AsyncSession, days: int = 30
    ) -> dict[str, Any]:
        """Get comprehensive trading activity metrics"""
        try:
            from ..models.trade import Trade

            start_date = datetime.now(UTC) - timedelta(days=days)

            # Trading activity by mode
            activity_by_mode_stmt = (
                select(
                    Trade.mode,
                    func.count(Trade.id).label("count"),
                    func.sum(Trade.amount * Trade.price).label("volume"),
                )
                .where(Trade.created_at >= start_date)
                .group_by(Trade.mode)
            )

            result = await db.execute(activity_by_mode_stmt)
            activity_by_mode = {
                row.mode: {"count": row.count, "volume": float(row.volume or 0)}
                for row in result
            }

            # Trading activity by chain
            activity_by_chain_stmt = (
                select(
                    Trade.chain_id,
                    func.count(Trade.id).label("count"),
                    func.sum(Trade.amount * Trade.price).label("volume"),
                )
                .where(Trade.created_at >= start_date)
                .group_by(Trade.chain_id)
            )

            result = await db.execute(activity_by_chain_stmt)
            activity_by_chain = {
                str(row.chain_id): {
                    "count": row.count,
                    "volume": float(row.volume or 0),
                }
                for row in result
            }

            return {
                "period_days": days,
                "activity_by_mode": activity_by_mode,
                "activity_by_chain": activity_by_chain,
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting trading activity metrics: {e}", exc_info=True)
            return {"error": str(e), "timestamp": datetime.now(UTC).isoformat()}

    async def calculate_user_acquisition_cost(
        self, db: AsyncSession, days: int = 30
    ) -> dict[str, Any]:
        """Calculate user acquisition cost (CAC)"""
        try:
            from ..models.user import User

            start_date = datetime.now(UTC) - timedelta(days=days)

            # Get new users in period
            new_users_stmt = select(func.count(User.id)).where(
                User.created_at >= start_date
            )
            result = await db.execute(new_users_stmt)
            new_users = result.scalar() or 0

            # Note: Marketing spend would come from marketing campaigns table when implemented
            # This is a placeholder for future marketing analytics integration
            marketing_spend = (
                0.0  # Future: Query marketing_campaigns table for total spend
            )

            cac = marketing_spend / new_users if new_users > 0 else 0.0

            return {
                "period_days": days,
                "new_users": new_users,
                "marketing_spend": marketing_spend,
                "cac": cac,
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error calculating CAC: {e}", exc_info=True)
            return {"error": str(e), "timestamp": datetime.now(UTC).isoformat()}

    async def calculate_lifetime_value(
        self, db: AsyncSession, days: int = 90
    ) -> dict[str, Any]:
        """Calculate customer lifetime value (LTV)"""
        try:
            from ..models.trade import Trade
            from ..models.trading_fee import TradingFee

            # Get average revenue per user
            start_date = datetime.now(UTC) - timedelta(days=days)

            # Get total revenue from trading fees
            fee_stmt = (
                select(func.sum(TradingFee.fee_amount))
                .where(TradingFee.collected_at >= start_date)
                .where(TradingFee.status == "collected")
            )
            fee_result = await db.execute(fee_stmt)
            total_fees = float(fee_result.scalar() or 0)

            # Get active users in period
            active_users_stmt = select(func.count(func.distinct(Trade.user_id))).where(
                Trade.created_at >= start_date
            )
            active_result = await db.execute(active_users_stmt)
            active_users = active_result.scalar() or 0

            # Average revenue per user (ARPU)
            arpu = total_fees / active_users if active_users > 0 else 0.0

            # Average customer lifespan (in days) - simplified calculation
            # Would ideally track from first to last activity
            avg_lifespan_days = days  # Placeholder

            # LTV = ARPU * Average Lifespan (in months)
            ltv = arpu * (avg_lifespan_days / 30)

            # Get CAC for LTV/CAC ratio
            cac_data = await self.calculate_user_acquisition_cost(db, days)
            cac = cac_data.get("cac", 0)
            ltv_cac_ratio = (ltv / cac) if cac > 0 else 0

            return {
                "period_days": days,
                "active_users": active_users,
                "total_revenue": total_fees,
                "arpu": arpu,
                "avg_lifespan_days": avg_lifespan_days,
                "ltv": ltv,
                "ltv_cac_ratio": ltv_cac_ratio,
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error calculating LTV: {e}", exc_info=True)
            return {"error": str(e), "timestamp": datetime.now(UTC).isoformat()}

    async def analyze_churn(self, db: AsyncSession, days: int = 30) -> dict[str, Any]:
        """Analyze user churn"""
        try:
            from ..models.trade import Trade

            # Users who were active before period but not during
            period_start = datetime.now(UTC) - timedelta(days=days)
            before_period = period_start - timedelta(days=days)

            # Users active before period
            active_before_stmt = select(func.count(func.distinct(Trade.user_id))).where(
                and_(
                    Trade.created_at >= before_period,
                    Trade.created_at < period_start,
                )
            )
            before_result = await db.execute(active_before_stmt)
            active_before = before_result.scalar() or 0

            # Users active during period
            active_during_stmt = select(func.count(func.distinct(Trade.user_id))).where(
                Trade.created_at >= period_start
            )
            during_result = await db.execute(active_during_stmt)
            active_during = during_result.scalar() or 0

            # Churned users (were active before but not during)
            churned_users = max(0, active_before - active_during)
            churn_rate = (
                (churned_users / active_before * 100) if active_before > 0 else 0.0
            )

            return {
                "period_days": days,
                "active_before_period": active_before,
                "active_during_period": active_during,
                "churned_users": churned_users,
                "churn_rate_percent": round(churn_rate, 2),
                "retention_rate_percent": round(100 - churn_rate, 2),
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error analyzing churn: {e}", exc_info=True)
            return {"error": str(e), "timestamp": datetime.now(UTC).isoformat()}

    async def get_detailed_trading_metrics(
        self, db: AsyncSession, days: int = 30
    ) -> dict[str, Any]:
        """Get detailed trading metrics: volume, avg size, pairs, success rates"""
        try:
            from ..models.trade import Trade

            start_date = datetime.now(UTC) - timedelta(days=days)

            # Total trading volume
            volume_stmt = (
                select(
                    func.sum(Trade.amount * Trade.price).label("total_volume"),
                    func.count(Trade.id).label("trade_count"),
                    func.avg(Trade.amount * Trade.price).label("avg_trade_size"),
                )
                .where(Trade.created_at >= start_date)
                .where(Trade.status == "completed")
            )
            volume_result = await db.execute(volume_stmt)
            volume_row = volume_result.first()

            # Most traded pairs
            pairs_stmt = (
                select(
                    Trade.symbol,
                    func.count(Trade.id).label("count"),
                    func.sum(Trade.amount * Trade.price).label("volume"),
                )
                .where(Trade.created_at >= start_date)
                .where(Trade.status == "completed")
                .group_by(Trade.symbol)
                .order_by(func.count(Trade.id).desc())
                .limit(10)
            )
            pairs_result = await db.execute(pairs_stmt)
            most_traded_pairs = [
                {
                    "symbol": row.symbol,
                    "trade_count": row.count,
                    "volume": float(row.volume or 0),
                }
                for row in pairs_result
            ]

            # Success rates
            success_stmt = select(
                func.count(Trade.id).label("total"),
                func.sum(func.case((Trade.status == "completed", 1), else_=0)).label(
                    "successful"
                ),
            ).where(Trade.created_at >= start_date)
            success_result = await db.execute(success_stmt)
            success_row = success_result.first()

            total_trades = success_row.total or 0
            successful_trades = success_row.successful or 0
            success_rate = (
                (successful_trades / total_trades * 100) if total_trades > 0 else 0.0
            )

            return {
                "period_days": days,
                "total_trading_volume": float(volume_row.total_volume or 0),
                "total_trades": int(volume_row.trade_count or 0),
                "average_trade_size": float(volume_row.avg_trade_size or 0),
                "most_traded_pairs": most_traded_pairs,
                "success_rate_percent": round(success_rate, 2),
                "successful_trades": successful_trades,
                "failed_trades": total_trades - successful_trades,
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting detailed trading metrics: {e}", exc_info=True)
            return {"error": str(e), "timestamp": datetime.now(UTC).isoformat()}


# Enhanced instance
_enhanced_business_metrics_service: EnhancedBusinessMetricsService | None = None


def get_enhanced_business_metrics_service(
    db: AsyncSession | None = None,
) -> EnhancedBusinessMetricsService:
    """Get enhanced business metrics service instance"""
    global _enhanced_business_metrics_service
    if _enhanced_business_metrics_service is None:
        _enhanced_business_metrics_service = EnhancedBusinessMetricsService(db)
    return _enhanced_business_metrics_service
