"""
System Metrics and Performance Monitoring
Comprehensive observability for the trading platform
"""

import logging
from datetime import datetime, timedelta
from typing import Annotated, Any

import psutil
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..middleware.cache_manager import cached
from ..services.monitoring.business_metrics import get_business_metrics_service
from ..services.monitoring.dex_metrics import get_dex_metrics_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/metrics", tags=["Metrics & Monitoring"])


class SystemMetrics(BaseModel):
    """System resource metrics"""

    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_sent_mb: float
    network_recv_mb: float


class ApplicationMetrics(BaseModel):
    """Application-level metrics"""

    uptime_seconds: float
    active_bots: int
    total_requests: int
    active_websocket_connections: int
    cache_hit_rate: float
    average_response_time_ms: float


class PerformanceMetrics(BaseModel):
    """Performance and health metrics"""

    system: SystemMetrics
    application: ApplicationMetrics
    circuit_breakers: dict[str, dict]
    database: dict[str, Any]
    timestamp: str


class AlertThreshold(BaseModel):
    """Alerting threshold configuration"""

    metric: str
    threshold: float
    operator: str  # "gt", "lt", "eq"
    severity: str  # "low", "medium", "high", "critical"


class MetricsAlert(BaseModel):
    """Active metric alert"""

    id: str
    metric: str
    current_value: float
    threshold: float
    severity: str
    message: str
    timestamp: str


# Global metrics storage
class MetricsCollector:
    """Collect and aggregate system metrics"""

    def __init__(self):
        self.start_time = datetime.now()
        self.request_count = 0
        self.response_times: list[float] = []
        self.alerts: list[MetricsAlert] = []

        # Alert thresholds
        self.thresholds: list[AlertThreshold] = [
            AlertThreshold(
                metric="cpu_percent", threshold=80.0, operator="gt", severity="high"
            ),
            AlertThreshold(
                metric="memory_percent",
                threshold=90.0,
                operator="gt",
                severity="critical",
            ),
            AlertThreshold(
                metric="disk_usage_percent",
                threshold=85.0,
                operator="gt",
                severity="medium",
            ),
        ]

    def record_request(self, response_time_ms: float):
        """Record a request and its response time"""
        self.request_count += 1
        self.response_times.append(response_time_ms)

        # Keep only last 1000 response times
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]

    def get_uptime(self) -> float:
        """Get application uptime in seconds"""
        return (datetime.now() - self.start_time).total_seconds()

    def get_average_response_time(self) -> float:
        """Calculate average response time"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect system resource metrics"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Memory
            memory = psutil.virtual_memory()
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)

            # Disk
            disk = psutil.disk_usage("/")
            disk_free_gb = disk.free / (1024 * 1024 * 1024)

            # Network
            network = psutil.net_io_counters()
            network_sent_mb = network.bytes_sent / (1024 * 1024)
            network_recv_mb = network.bytes_recv / (1024 * 1024)

            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=round(memory_used_mb, 2),
                memory_available_mb=round(memory_available_mb, 2),
                disk_usage_percent=disk.percent,
                disk_free_gb=round(disk_free_gb, 2),
                network_sent_mb=round(network_sent_mb, 2),
                network_recv_mb=round(network_recv_mb, 2),
            )
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            raise

    async def collect_application_metrics(self) -> ApplicationMetrics:
        """Collect application-level metrics"""
        try:
            # Get active bots count
            active_bots = 0
            try:
                # This would query the actual bot service
                pass
            except:
                pass

            # Get WebSocket connections
            ws_connections = 0
            try:
                from ..services.websocket_manager import connection_manager

                ws_connections = len(connection_manager.connections)
            except:
                pass

            # Get cache hit rate
            cache_hit_rate = 0.0
            try:
                from ..middleware.cache_manager import cache_stats

                stats = cache_stats.get_stats()
                cache_hit_rate = stats.get("hit_rate_percentage", 0.0)
            except:
                pass

            return ApplicationMetrics(
                uptime_seconds=self.get_uptime(),
                active_bots=active_bots,
                total_requests=self.request_count,
                active_websocket_connections=ws_connections,
                cache_hit_rate=cache_hit_rate,
                average_response_time_ms=round(self.get_average_response_time(), 2),
            )
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
            raise

    async def check_alerts(self, system_metrics: SystemMetrics):
        """Check if any metrics exceed thresholds"""
        new_alerts = []

        for threshold in self.thresholds:
            metric_value = getattr(system_metrics, threshold.metric, None)

            if metric_value is None:
                continue

            triggered = False
            if (
                threshold.operator == "gt"
                and metric_value > threshold.threshold
                or threshold.operator == "lt"
                and metric_value < threshold.threshold
                or threshold.operator == "eq"
                and metric_value == threshold.threshold
            ):
                triggered = True

            if triggered:
                alert = MetricsAlert(
                    id=f"alert_{threshold.metric}_{datetime.now().timestamp()}",
                    metric=threshold.metric,
                    current_value=metric_value,
                    threshold=threshold.threshold,
                    severity=threshold.severity,
                    message=f"{threshold.metric} is {metric_value:.1f} (threshold: {threshold.threshold})",
                    timestamp=datetime.now().isoformat(),
                )
                new_alerts.append(alert)

        # Keep only recent alerts (last hour)
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.alerts = [
            a for a in self.alerts if datetime.fromisoformat(a.timestamp) > cutoff_time
        ]

        # Add new alerts
        self.alerts.extend(new_alerts)

        return new_alerts


# Global metrics collector
metrics_collector = MetricsCollector()


@router.get("/current", response_model=PerformanceMetrics)
@cached(ttl=30, prefix="current_metrics")  # 30s TTL for current metrics (real-time)
async def get_current_metrics():
    """
    Get comprehensive current system metrics

    Includes:
    - System resources (CPU, memory, disk, network)
    - Application metrics (uptime, requests, cache)
    - Circuit breaker status
    - Database health
    """
    try:
        # Collect system metrics
        system_metrics = await metrics_collector.collect_system_metrics()

        # Collect application metrics
        app_metrics = await metrics_collector.collect_application_metrics()

        # Get circuit breaker stats
        cb_stats = {}
        try:
            from ..middleware.circuit_breaker import (
                database_breaker,
                exchange_breaker,
                ml_service_breaker,
            )

            cb_stats = {
                "exchange": exchange_breaker.get_stats(),
                "database": database_breaker.get_stats(),
                "ml_service": ml_service_breaker.get_stats(),
            }
        except:
            pass

        # Get database stats
        db_stats = {"status": "unknown"}
        try:
            from ..database.connection_pool import db_pool

            if db_pool:
                db_stats = {
                    "status": "healthy",
                    "pool_size": getattr(db_pool, "size", 0),
                    "active_connections": getattr(db_pool, "active", 0),
                }
        except:
            pass

        # Check for alerts
        await metrics_collector.check_alerts(system_metrics)

        return PerformanceMetrics(
            system=system_metrics,
            application=app_metrics,
            circuit_breakers=cb_stats,
            database=db_stats,
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error(f"Error collecting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to collect metrics")


@router.get("/alerts", response_model=list[MetricsAlert])
@cached(ttl=60, prefix="metrics_alerts")  # 60s TTL for metrics alerts
async def get_active_alerts():
    """Get list of active metric alerts"""
    return metrics_collector.alerts


@router.get("/alerts/thresholds", response_model=list[AlertThreshold])
async def get_alert_thresholds():
    """Get configured alert thresholds"""
    return metrics_collector.thresholds


@router.post("/alerts/thresholds")
async def add_alert_threshold(threshold: AlertThreshold):
    """Add a new alert threshold"""
    metrics_collector.thresholds.append(threshold)
    return {"success": True, "threshold": threshold}


@router.delete("/alerts/thresholds/{metric}")
async def remove_alert_threshold(metric: str):
    """Remove an alert threshold"""
    metrics_collector.thresholds = [
        t for t in metrics_collector.thresholds if t.metric != metric
    ]
    return {"success": True}


@router.get("/health-score")
async def get_health_score():
    """
    Calculate overall system health score (0-100)

    Based on:
    - System resource usage
    - Application performance
    - Circuit breaker status
    - Error rates
    """
    try:
        system_metrics = await metrics_collector.collect_system_metrics()
        app_metrics = await metrics_collector.collect_application_metrics()

        # Calculate component scores (0-100)
        cpu_score = max(0, 100 - system_metrics.cpu_percent)
        memory_score = max(0, 100 - system_metrics.memory_percent)
        disk_score = max(0, 100 - system_metrics.disk_usage_percent)

        # Cache performance score
        cache_score = app_metrics.cache_hit_rate

        # Response time score (target <100ms)
        response_score = max(0, 100 - (app_metrics.average_response_time_ms / 10))

        # Weighted overall score
        overall_score = (
            cpu_score * 0.2
            + memory_score * 0.2
            + disk_score * 0.1
            + cache_score * 0.2
            + response_score * 0.3
        )

        return {
            "overall_health_score": round(overall_score, 2),
            "components": {
                "cpu": round(cpu_score, 2),
                "memory": round(memory_score, 2),
                "disk": round(disk_score, 2),
                "cache": round(cache_score, 2),
                "response_time": round(response_score, 2),
            },
            "status": (
                "healthy"
                if overall_score >= 80
                else "degraded"
                if overall_score >= 50
                else "unhealthy"
            ),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error calculating health score: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate health score")


# DEX Trading Metrics Endpoints
@router.get("/dex/volume")
@cached(ttl=120, prefix="dex_volume")  # 120s TTL for DEX volume metrics
async def get_dex_volume(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    start_date: str | None = None,
    end_date: str | None = None,
    chain_id: int | None = None,
    aggregator: str | None = None,
):
    """
    Get DEX trade volume metrics

    Query parameters:
    - start_date: ISO format date (default: 30 days ago)
    - end_date: ISO format date (default: now)
    - chain_id: Optional chain ID filter
    - aggregator: Optional aggregator filter
    """
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        service = get_dex_metrics_service()
        volume = await service.get_trade_volume(db, start, end, chain_id, aggregator)
        return volume
    except Exception as e:
        logger.error(f"Error getting DEX volume: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get DEX volume metrics")


@router.get("/dex/fees")
async def get_dex_fees(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    start_date: str | None = None,
    end_date: str | None = None,
):
    """Get platform fee collection metrics"""
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        service = get_dex_metrics_service()
        fees = await service.get_fee_collection(db, start, end)
        return fees
    except Exception as e:
        logger.error(f"Error getting DEX fees: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get DEX fee metrics")


@router.get("/dex/aggregators")
@cached(ttl=120, prefix="dex_aggregators")  # 120s TTL for aggregator performance
async def get_aggregator_performance(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    start_date: str | None = None,
    end_date: str | None = None,
):
    """Get performance metrics for each aggregator"""
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        service = get_dex_metrics_service()
        aggregators = await service.get_aggregator_performance(db, start, end)
        return {"aggregators": aggregators}
    except Exception as e:
        logger.error(f"Error getting aggregator performance: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to get aggregator performance"
        )


@router.get("/dex/errors")
async def get_dex_error_rates(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    start_date: str | None = None,
    end_date: str | None = None,
):
    """Get error rate metrics for DEX trades"""
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        service = get_dex_metrics_service()
        errors = await service.get_error_rates(db, start, end)
        return errors
    except Exception as e:
        logger.error(f"Error getting DEX error rates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get DEX error rates")


@router.get("/dex/chains")
@cached(ttl=120, prefix="dex_chains")  # 120s TTL for chain volume metrics
async def get_chain_volume(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    start_date: str | None = None,
    end_date: str | None = None,
):
    """Get volume metrics by blockchain chain"""
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        service = get_dex_metrics_service()
        chains = await service.get_chain_volume(db, start, end)
        return {"chains": chains}
    except Exception as e:
        logger.error(f"Error getting chain volume: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to get chain volume metrics"
        )


@router.get("/dex/all")
async def get_all_dex_metrics(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    start_date: str | None = None,
    end_date: str | None = None,
):
    """
    Get all DEX trading metrics in one call

    Includes:
    - Trade volume
    - Fee collection
    - Aggregator performance
    - Error rates
    - Chain volume
    """
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        service = get_dex_metrics_service()
        all_metrics = await service.get_all_metrics(db, start, end)
        return all_metrics
    except Exception as e:
        logger.error(f"Error getting all DEX metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get DEX metrics")


@router.get("/wallets", tags=["Metrics & Monitoring"])
@cached(ttl=120, prefix="wallet_metrics")  # 120s TTL for wallet metrics
async def get_wallet_metrics(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    start_date: str | None = None,
    end_date: str | None = None,
    chain_id: int | None = None,
) -> dict[str, Any]:
    """
    Get wallet operation metrics

    Returns wallet creations, deposits, withdrawals per day, total balances, etc.
    """
    try:
        from collections import defaultdict

        from sqlalchemy import select

        from ..models.user_wallet import UserWallet

        # Parse dates
        if start_date:
            start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        else:
            start = datetime.utcnow() - timedelta(days=7)

        if end_date:
            end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        else:
            end = datetime.utcnow()

        # Build query
        query = select(UserWallet).where(
            UserWallet.created_at >= start,
            UserWallet.created_at <= end,
        )

        if chain_id:
            query = query.where(UserWallet.chain_id == chain_id)

        result = await db.execute(query)
        wallets = result.scalars().all()

        # Calculate metrics
        total_wallets = len(wallets)
        custodial_count = len([w for w in wallets if w.wallet_type == "custodial"])
        external_count = len([w for w in wallets if w.wallet_type == "external"])

        # Per-day breakdown
        daily_creations: dict[str, int] = defaultdict(int)
        for wallet in wallets:
            day = wallet.created_at.date().isoformat()
            daily_creations[day] += 1

        # Chain breakdown
        chain_breakdown: dict[int, int] = defaultdict(int)
        for wallet in wallets:
            chain_breakdown[wallet.chain_id] += 1

        return {
            "period": {
                "start": start.isoformat(),
                "end": end.isoformat(),
            },
            "total_wallets": total_wallets,
            "custodial_wallets": custodial_count,
            "external_wallets": external_count,
            "daily_creations": dict(daily_creations),
            "chain_breakdown": {str(k): v for k, v in chain_breakdown.items()},
        }

    except Exception as e:
        logger.error(f"Error getting wallet metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get wallet metrics")


@router.get("/blockchain", tags=["Metrics & Monitoring"])
async def get_blockchain_metrics(
    chain_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """
    Get blockchain metrics

    Returns transaction counts per chain, gas costs, RPC call statistics.
    """
    try:
        from ..services.monitoring.transaction_monitor import transaction_monitor

        # Parse dates
        if start_date:
            start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        else:
            start = datetime.utcnow() - timedelta(days=7)

        if end_date:
            end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        else:
            end = datetime.utcnow()

        # Get transaction stats
        stats = await transaction_monitor.get_transaction_stats(
            chain_id=chain_id,
            start_date=start,
            end_date=end,
        )

        # Chain-specific metrics
        chain_metrics = {}
        for chain in [1, 8453, 42161, 137]:  # Ethereum, Base, Arbitrum, Polygon
            if chain_id and chain != chain_id:
                continue

            chain_stats = await transaction_monitor.get_transaction_stats(
                chain_id=chain,
                start_date=start,
                end_date=end,
            )
            chain_metrics[str(chain)] = chain_stats

        return {
            "period": {
                "start": start.isoformat(),
                "end": end.isoformat(),
            },
            "overall": stats,
            "per_chain": chain_metrics,
        }

    except Exception as e:
        logger.error(f"Error getting blockchain metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get blockchain metrics")


@router.get("/user-activity", tags=["Metrics & Monitoring"])
@cached(ttl=120, prefix="user_activity_metrics")  # 120s TTL for user activity metrics
async def get_user_activity_metrics(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """
    Get user activity metrics

    Returns active users, trading volume, login counts, etc.
    """
    try:
        from collections import defaultdict

        from sqlalchemy import func, select

        from ..models.dex_trade import DEXTrade
        from ..models.user import User

        # Parse dates
        if start_date:
            start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        else:
            start = datetime.utcnow() - timedelta(days=7)

        if end_date:
            end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        else:
            end = datetime.utcnow()

        # Active users (users who made trades)
        active_users_query = select(func.count(func.distinct(DEXTrade.user_id))).where(
            DEXTrade.created_at >= start,
            DEXTrade.created_at <= end,
        )
        result = await db.execute(active_users_query)
        active_users = result.scalar() or 0

        # Total users
        total_users_query = select(func.count(User.id))
        result = await db.execute(total_users_query)
        total_users = result.scalar() or 0

        # Trading volume
        volume_query = select(func.sum(DEXTrade.sell_amount_decimal)).where(
            DEXTrade.created_at >= start,
            DEXTrade.created_at <= end,
            DEXTrade.status == "completed",
        )
        result = await db.execute(volume_query)
        total_volume = float(result.scalar() or 0)

        # Daily active users
        daily_active: dict[str, int] = defaultdict(int)
        daily_trades_query = (
            select(
                func.date(DEXTrade.created_at).label("date"),
                func.count(func.distinct(DEXTrade.user_id)).label("active_users"),
            )
            .where(
                DEXTrade.created_at >= start,
                DEXTrade.created_at <= end,
            )
            .group_by(func.date(DEXTrade.created_at))
        )

        result = await db.execute(daily_trades_query)
        for row in result:
            daily_active[row.date.isoformat()] = row.active_users

        return {
            "period": {
                "start": start.isoformat(),
                "end": end.isoformat(),
            },
            "total_users": total_users,
            "active_users": active_users,
            "total_trading_volume": total_volume,
            "daily_active_users": dict(daily_active),
        }

    except Exception as e:
        logger.error(f"Error getting user activity metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to get user activity metrics"
        )


@router.get("/performance", tags=["Metrics & Monitoring"])
async def get_performance_metrics() -> dict[str, Any]:
    """
    Get performance metrics

    Returns API response times, database query times, cache hit rates.
    """
    try:
        from ..services.monitoring.performance_profiler import get_performance_profiler
        from ..services.monitoring.transaction_monitor import transaction_monitor

        # Get transaction latency metrics
        stats = await transaction_monitor.get_transaction_stats()

        # Get system metrics
        system_metrics = await metrics_collector.collect_system_metrics()
        app_metrics = await metrics_collector.collect_application_metrics()

        # Get slow queries and endpoints
        profiler = get_performance_profiler()
        slow_queries = profiler.get_slow_queries(limit=10)
        slow_endpoints = profiler.get_slow_endpoints(limit=10)

        return {
            "system": system_metrics.dict(),
            "application": app_metrics.dict(),
            "transaction_latency": {
                "avg_seconds": stats.get("avg_latency_seconds", 0),
            },
            "slow_queries": slow_queries,
            "slow_endpoints": slow_endpoints,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")


@router.get("/business", tags=["Metrics & Monitoring"])
@cached(ttl=120, prefix="business_metrics")  # 120s TTL for business metrics
async def get_business_metrics(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    """
    Get business metrics (trades/day, revenue, user growth)

    Returns:
    - Trades per day
    - Revenue metrics (subscription + trading fees)
    - User growth metrics (total users, active users 24h)
    """
    try:
        service = get_business_metrics_service(db)
        metrics = await service.get_all_business_metrics(db)
        return metrics
    except Exception as e:
        logger.error(f"Error getting business metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get business metrics")


@router.get("/business/trades-per-day", tags=["Metrics & Monitoring"])
async def get_trades_per_day(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    days: int = 30,
) -> dict[str, Any]:
    """Get trades per day for the last N days"""
    try:
        service = get_business_metrics_service(db)
        trades_data = await service.get_trades_per_day(db, days=days)
        return {
            "trades_per_day": trades_data,
            "period_days": days,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting trades per day: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get trades per day")


@router.get("/business/revenue", tags=["Metrics & Monitoring"])
async def get_revenue_metrics(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Get revenue metrics (subscription + trading fees)"""
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        service = get_business_metrics_service(db)
        revenue = await service.get_revenue_metrics(db, start_date=start, end_date=end)
        return revenue
    except Exception as e:
        logger.error(f"Error getting revenue metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get revenue metrics")


@router.get("/business/users", tags=["Metrics & Monitoring"])
async def get_user_metrics(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    """Get user growth metrics (total users, active users 24h)"""
    try:
        service = get_business_metrics_service(db)
        user_metrics = await service.update_user_metrics(db)
        return user_metrics
    except Exception as e:
        logger.error(f"Error getting user metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get user metrics")
