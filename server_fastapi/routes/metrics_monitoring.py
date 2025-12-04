"""
System Metrics and Performance Monitoring
Comprehensive observability for the trading platform
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import psutil
import logging
import asyncio

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
    circuit_breakers: Dict[str, dict]
    database: Dict[str, Any]
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
        self.response_times: List[float] = []
        self.alerts: List[MetricsAlert] = []

        # Alert thresholds
        self.thresholds: List[AlertThreshold] = [
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
            if threshold.operator == "gt" and metric_value > threshold.threshold:
                triggered = True
            elif threshold.operator == "lt" and metric_value < threshold.threshold:
                triggered = True
            elif threshold.operator == "eq" and metric_value == threshold.threshold:
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
                exchange_breaker,
                database_breaker,
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


@router.get("/alerts", response_model=List[MetricsAlert])
async def get_active_alerts():
    """Get list of active metric alerts"""
    return metrics_collector.alerts


@router.get("/alerts/thresholds", response_model=List[AlertThreshold])
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
                else "degraded" if overall_score >= 50 else "unhealthy"
            ),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error calculating health score: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate health score")
