"""
Business Metrics Service
Tracks business-level metrics: trades/day, revenue, user growth, etc.
Exposes metrics for Prometheus and business intelligence dashboards.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from prometheus_client import Counter, Gauge, Histogram

# OpenTelemetry integration
try:
    from ..observability.opentelemetry_setup import (
        record_metric,
        record_gauge,
        record_histogram,
        get_tracer,
    )

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False

    def record_metric(*args, **kwargs):
        pass

    def record_gauge(*args, **kwargs):
        pass

    def record_histogram(*args, **kwargs):
        pass

    def get_tracer():
        return None


logger = logging.getLogger(__name__)

# Prometheus metrics for business KPIs
trades_per_day = Counter(
    "crypto_trades_per_day_total", "Total trades executed per day", ["mode", "chain_id"]
)

revenue_total = Counter(
    "crypto_revenue_total",
    "Total platform revenue",
    ["revenue_type"],  # subscription, trading_fees, etc.
)

user_growth_total = Gauge("crypto_users_total", "Total number of registered users")

active_users_24h = Gauge(
    "crypto_active_users_24h", "Number of active users in last 24 hours"
)

trading_volume_total = Counter(
    "crypto_trading_volume_total", "Total trading volume", ["mode", "chain_id"]
)

bot_activity_total = Counter(
    "crypto_bot_activity_total",
    "Total bot trading activity",
    ["bot_status", "strategy"],
)

wallet_operations_total = Counter(
    "crypto_wallet_operations_total",
    "Total wallet operations",
    ["operation_type", "chain_id"],
)

dex_swap_success_rate = Histogram(
    "crypto_dex_swap_success_rate", "DEX swap success rate", ["aggregator", "chain_id"]
)

wallet_balance_refresh_duration = Histogram(
    "crypto_wallet_balance_refresh_duration_seconds",
    "Wallet balance refresh duration",
    ["chain_id"],
)

transaction_confirmation_time = Histogram(
    "crypto_transaction_confirmation_time_seconds",
    "Blockchain transaction confirmation time",
    ["chain_id", "status"],
)


class BusinessMetricsService:
    """Service for tracking and exposing business metrics"""

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    async def record_trade(
        self, mode: str, chain_id: Optional[int] = None, amount: Optional[float] = None
    ) -> None:
        """Record a trade for business metrics"""
        trades_per_day.labels(mode=mode, chain_id=chain_id or 0).inc()

        if amount:
            trading_volume_total.labels(mode=mode, chain_id=chain_id or 0).inc(amount)

        # Record in OpenTelemetry
        if OTEL_AVAILABLE:
            record_metric(
                "business.trades.total",
                1.0,
                attributes={"mode": mode, "chain_id": str(chain_id or 0)},
            )
            if amount:
                record_metric(
                    "business.trading_volume.total",
                    amount,
                    attributes={"mode": mode, "chain_id": str(chain_id or 0)},
                )

    async def record_revenue(self, revenue_type: str, amount: float) -> None:
        """Record revenue for business metrics"""
        revenue_total.labels(revenue_type=revenue_type).inc(amount)

        # Record in OpenTelemetry
        if OTEL_AVAILABLE:
            record_metric(
                "business.revenue.total",
                amount,
                attributes={"revenue_type": revenue_type},
            )

    async def update_user_metrics(self, db: AsyncSession) -> Dict[str, Any]:
        """Update user growth and activity metrics"""
        try:
            from ..models.user import User

            # Total users
            total_users_stmt = select(func.count(User.id))
            total_result = await db.execute(total_users_stmt)
            total_users = total_result.scalar() or 0
            user_growth_total.set(total_users)

            # Active users in last 24 hours
            active_cutoff = datetime.utcnow() - timedelta(hours=24)
            active_stmt = select(func.count(User.id)).where(
                User.last_login_at >= active_cutoff
            )
            active_result = await db.execute(active_stmt)
            active_users = active_result.scalar() or 0
            active_users_24h.set(active_users)

            # Record in OpenTelemetry
            if OTEL_AVAILABLE:
                record_gauge("business.users.total", float(total_users))
                record_gauge("business.users.active_24h", float(active_users))

            return {"total_users": total_users, "active_users_24h": active_users}
        except Exception as e:
            logger.error(f"Error updating user metrics: {e}", exc_info=True)
            return {"total_users": 0, "active_users_24h": 0}

    async def get_trades_per_day(
        self, db: AsyncSession, days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get trades per day for the last N days"""
        try:
            from ..models.trade import Trade

            start_date = datetime.utcnow() - timedelta(days=days)

            stmt = (
                select(
                    func.date(Trade.created_at).label("date"),
                    func.count(Trade.id).label("trade_count"),
                    Trade.mode,
                )
                .where(Trade.created_at >= start_date)
                .group_by(func.date(Trade.created_at), Trade.mode)
                .order_by(func.date(Trade.created_at).desc())
            )

            result = await db.execute(stmt)
            rows = result.all()

            return [
                {
                    "date": (
                        row.date.isoformat()
                        if hasattr(row.date, "isoformat")
                        else str(row.date)
                    ),
                    "trade_count": row.trade_count,
                    "mode": row.mode,
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Error getting trades per day: {e}", exc_info=True)
            return []

    async def get_revenue_metrics(
        self,
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get revenue metrics"""
        try:
            from ..services.payments.stripe_service import StripeService

            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()

            # Get subscription revenue
            stripe_service = StripeService()
            subscription_revenue = await stripe_service.get_revenue_in_period(
                start_date, end_date
            )

            # Get trading fee revenue
            from ..models.trading_fee import TradingFee

            fee_stmt = (
                select(func.sum(TradingFee.fee_amount))
                .where(TradingFee.collected_at >= start_date)
                .where(TradingFee.collected_at <= end_date)
                .where(TradingFee.status == "collected")
            )
            fee_result = await db.execute(fee_stmt)
            trading_fee_revenue = float(fee_result.scalar() or 0)

            total_revenue = subscription_revenue + trading_fee_revenue

            return {
                "subscription_revenue": subscription_revenue,
                "trading_fee_revenue": trading_fee_revenue,
                "total_revenue": total_revenue,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }
        except Exception as e:
            logger.error(f"Error getting revenue metrics: {e}", exc_info=True)
            return {
                "subscription_revenue": 0.0,
                "trading_fee_revenue": 0.0,
                "total_revenue": 0.0,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            }

    async def record_wallet_operation(
        self,
        operation_type: str,
        chain_id: int,
        duration_seconds: Optional[float] = None,
    ) -> None:
        """Record wallet operation for metrics"""
        wallet_operations_total.labels(
            operation_type=operation_type, chain_id=chain_id
        ).inc()

        if duration_seconds is not None and operation_type == "balance_refresh":
            wallet_balance_refresh_duration.labels(chain_id=chain_id).observe(
                duration_seconds
            )

    async def record_transaction_confirmation(
        self, chain_id: int, status: str, confirmation_time_seconds: float
    ) -> None:
        """Record transaction confirmation time"""
        transaction_confirmation_time.labels(chain_id=chain_id, status=status).observe(
            confirmation_time_seconds
        )

    async def record_dex_swap(
        self, aggregator: str, chain_id: int, success: bool
    ) -> None:
        """Record DEX swap for success rate tracking"""
        status = "success" if success else "failed"
        dex_swap_success_rate.labels(aggregator=aggregator, chain_id=chain_id).observe(
            1.0 if success else 0.0
        )

    async def record_bot_activity(self, bot_status: str, strategy: str) -> None:
        """Record bot activity"""
        bot_activity_total.labels(bot_status=bot_status, strategy=strategy).inc()

    async def get_all_business_metrics(self, db: AsyncSession) -> Dict[str, Any]:
        """Get all business metrics"""
        user_metrics = await self.update_user_metrics(db)
        trades_per_day_data = await self.get_trades_per_day(db, days=30)
        revenue_metrics = await self.get_revenue_metrics(db)

        return {
            "users": user_metrics,
            "trades_per_day": trades_per_day_data,
            "revenue": revenue_metrics,
            "timestamp": datetime.utcnow().isoformat(),
        }


# Singleton instance
_business_metrics_service: Optional[BusinessMetricsService] = None


def get_business_metrics_service(
    db: Optional[AsyncSession] = None,
) -> BusinessMetricsService:
    """Get business metrics service instance"""
    global _business_metrics_service
    if _business_metrics_service is None:
        _business_metrics_service = BusinessMetricsService(db)
    return _business_metrics_service
