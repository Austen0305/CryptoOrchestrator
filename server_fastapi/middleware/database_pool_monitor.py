"""
Database Connection Pool Monitor
Monitors and optimizes database connection pool usage
"""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PoolMetrics:
    """Database pool metrics"""
    timestamp: datetime
    pool_size: int
    active_connections: int
    idle_connections: int
    wait_count: int
    timeout_count: int
    checkout_time_ms: float = 0.0


class DatabasePoolMonitor:
    """
    Monitors database connection pool health and performance
    
    Features:
    - Real-time pool metrics
    - Connection leak detection
    - Performance tracking
    - Health alerts
    """

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.checkout_times: deque = deque(maxlen=100)
        self.leak_detection: Dict[str, datetime] = {}
        self.alerts: deque = deque(maxlen=100)

    def record_checkout(self, connection_id: str):
        """Record connection checkout"""
        self.leak_detection[connection_id] = datetime.utcnow()

    def record_checkin(self, connection_id: str, checkout_duration_ms: float):
        """Record connection checkin"""
        if connection_id in self.leak_detection:
            del self.leak_detection[connection_id]
        
        self.checkout_times.append(checkout_duration_ms)

    def record_metrics(
        self,
        pool_size: int,
        active: int,
        idle: int,
        wait_count: int = 0,
        timeout_count: int = 0,
    ):
        """Record pool metrics"""
        metric = PoolMetrics(
            timestamp=datetime.utcnow(),
            pool_size=pool_size,
            active_connections=active,
            idle_connections=idle,
            wait_count=wait_count,
            timeout_count=timeout_count,
            checkout_time_ms=sum(self.checkout_times) / len(self.checkout_times) if self.checkout_times else 0,
        )
        self.metrics_history.append(metric)
        
        # Check for issues
        self._check_health(metric)

    def _check_health(self, metric: PoolMetrics):
        """Check pool health and generate alerts"""
        # Check for connection leaks
        leak_threshold = timedelta(minutes=5)
        now = datetime.utcnow()
        leaks = [
            conn_id for conn_id, checkout_time in self.leak_detection.items()
            if (now - checkout_time) > leak_threshold
        ]
        
        if leaks:
            self.alerts.append({
                "type": "connection_leak",
                "message": f"Detected {len(leaks)} potential connection leaks",
                "timestamp": now.isoformat(),
            })
            logger.warning(f"Connection leak detected: {len(leaks)} connections")

        # Check pool exhaustion
        if metric.active_connections >= metric.pool_size * 0.9:
            self.alerts.append({
                "type": "pool_exhaustion",
                "message": f"Pool nearly exhausted: {metric.active_connections}/{metric.pool_size}",
                "timestamp": metric.timestamp.isoformat(),
            })
            logger.warning("Database pool nearly exhausted")

        # Check for timeouts
        if metric.timeout_count > 0:
            self.alerts.append({
                "type": "timeout",
                "message": f"Connection timeouts detected: {metric.timeout_count}",
                "timestamp": metric.timestamp.isoformat(),
            })

        # Check checkout time
        if metric.checkout_time_ms > 100:  # > 100ms is slow
            self.alerts.append({
                "type": "slow_checkout",
                "message": f"Slow connection checkout: {metric.checkout_time_ms:.2f}ms",
                "timestamp": metric.timestamp.isoformat(),
            })

    def get_current_metrics(self) -> Optional[PoolMetrics]:
        """Get most recent metrics"""
        return self.metrics_history[-1] if self.metrics_history else None

    def get_stats(self, window_minutes: int = 5) -> Dict[str, Any]:
        """Get statistics for the last N minutes"""
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp > cutoff
        ]
        
        if not recent_metrics:
            return {
                "pool_size": 0,
                "avg_active": 0,
                "max_active": 0,
                "avg_idle": 0,
                "avg_checkout_time_ms": 0,
                "total_wait_count": 0,
                "total_timeout_count": 0,
                "leak_count": len(self.leak_detection),
            }
        
        return {
            "pool_size": recent_metrics[-1].pool_size,
            "avg_active": sum(m.active_connections for m in recent_metrics) / len(recent_metrics),
            "max_active": max(m.active_connections for m in recent_metrics),
            "avg_idle": sum(m.idle_connections for m in recent_metrics) / len(recent_metrics),
            "avg_checkout_time_ms": sum(m.checkout_time_ms for m in recent_metrics) / len(recent_metrics),
            "total_wait_count": sum(m.wait_count for m in recent_metrics),
            "total_timeout_count": sum(m.timeout_count for m in recent_metrics),
            "leak_count": len(self.leak_detection),
            "recent_alerts": list(self.alerts)[-10:],  # Last 10 alerts
        }

    def get_leaks(self) -> Dict[str, datetime]:
        """Get current connection leaks"""
        return self.leak_detection.copy()


# Global pool monitor instance
pool_monitor = DatabasePoolMonitor()

