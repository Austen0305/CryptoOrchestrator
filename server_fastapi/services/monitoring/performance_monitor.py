"""
Performance monitoring service - migrated from TypeScript
"""

import asyncio
import math
import time
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import logging
import psutil

logger = logging.getLogger(__name__)

class PerformanceMetrics(BaseModel):
    """Trading performance metrics"""
    win_rate: float
    profit_factor: float
    average_win: float
    average_loss: float
    successful_trades: int
    failed_trades: int
    total_trades: int
    consecutive_losses: int
    max_drawdown: float
    sharpe_ratio: float

class TradeMetrics(BaseModel):
    """Individual trade metrics"""
    profit: float
    duration: int
    entry_price: float
    exit_price: float
    timestamp: int

class SystemMetrics(BaseModel):
    """System performance metrics"""
    timestamp: int
    cpu_usage: float
    memory_usage: float
    response_time: float
    error_rate: float
    active_connections: int

class PerformanceMonitor:
    """Performance monitoring service with trading metrics and system monitoring"""

    def __init__(self):
        self.metrics = PerformanceMetrics(
            win_rate=0.0,
            profit_factor=0.0,
            average_win=0.0,
            average_loss=0.0,
            successful_trades=0,
            failed_trades=0,
            total_trades=0,
            consecutive_losses=0,
            max_drawdown=0.0,
            sharpe_ratio=0.0
        )
        self.recent_trades: List[TradeMetrics] = []
        self.system_metrics: List[SystemMetrics] = []
        self.max_trades_history = 1000
        self.alert_thresholds = {
            'min_win_rate': 0.4,        # 40% minimum win rate
            'min_profit_factor': 1.2,   # 1.2 minimum profit factor
            'max_consecutive_losses': 5, # Maximum consecutive losses
            'max_drawdown': 0.15,       # 15% maximum drawdown
            'min_sharpe_ratio': 0.5     # Minimum Sharpe ratio
        }
        self._update_task: Optional[asyncio.Task] = None
        # Don't start async task in __init__ to avoid event loop issues
        # Will be started when needed in FastAPI startup

    def _start_metrics_update(self):
        """Start periodic metrics update"""
        self._update_task = asyncio.create_task(self._periodic_update())

    async def _periodic_update(self):
        """Periodic metrics update"""
        while True:
            try:
                await self._update_metrics()
                await asyncio.sleep(60)  # Update every minute
            except Exception as e:
                logger.error(f"Error in periodic metrics update: {e}")
                await asyncio.sleep(60)

    async def record_trade(self, trade: TradeMetrics) -> None:
        """Record a completed trade"""
        self.recent_trades.append(trade)
        if len(self.recent_trades) > self.max_trades_history:
            self.recent_trades.pop(0)

        # Update consecutive losses
        if trade.profit < 0:
            self.metrics.consecutive_losses += 1
            if self.metrics.consecutive_losses >= self.alert_thresholds['max_consecutive_losses']:
                logger.warning(f"Consecutive losses alert: {self.metrics.consecutive_losses} losses in a row")
                # Emit alert event (would be handled by event system)
        else:
            self.metrics.consecutive_losses = 0

        await self._update_metrics()

    async def _update_metrics(self) -> None:
        """Update trading performance metrics"""
        if not self.recent_trades:
            return

        winning_trades = [t for t in self.recent_trades if t.profit > 0]
        losing_trades = [t for t in self.recent_trades if t.profit < 0]

        self.metrics.successful_trades = len(winning_trades)
        self.metrics.failed_trades = len(losing_trades)
        self.metrics.total_trades = len(self.recent_trades)
        self.metrics.win_rate = len(winning_trades) / len(self.recent_trades) if self.recent_trades else 0

        # Calculate average win/loss
        self.metrics.average_win = (
            sum(t.profit for t in winning_trades) / len(winning_trades)
            if winning_trades else 0
        )
        self.metrics.average_loss = (
            abs(sum(t.profit for t in losing_trades) / len(losing_trades))
            if losing_trades else 0
        )

        # Calculate profit factor
        total_profit = sum(t.profit for t in winning_trades)
        total_loss = abs(sum(t.profit for t in losing_trades))
        self.metrics.profit_factor = total_profit / total_loss if total_loss > 0 else (float('inf') if total_profit > 0 else 0)

        # Calculate Sharpe ratio
        returns = [t.profit for t in self.recent_trades]
        if returns:
            avg_return = sum(returns) / len(returns)
            std_dev = math.sqrt(sum((r - avg_return) ** 2 for r in returns) / len(returns))
            self.metrics.sharpe_ratio = (avg_return / std_dev * math.sqrt(252)) if std_dev > 0 else 0

        # Check performance alerts
        await self._check_performance_alerts()

        logger.info("Performance metrics updated", extra={'metrics': self.metrics.dict()})

    async def _check_performance_alerts(self) -> None:
        """Check for performance alerts"""
        alerts = []

        if self.metrics.win_rate < self.alert_thresholds['min_win_rate']:
            alerts.append(f"Low win rate: {self.metrics.win_rate:.2%}")
            logger.warning(f"Low win rate alert: {self.metrics.win_rate:.2%}")

        if self.metrics.profit_factor < self.alert_thresholds['min_profit_factor']:
            alerts.append(f"Low profit factor: {self.metrics.profit_factor:.2f}")
            logger.warning(f"Low profit factor alert: {self.metrics.profit_factor:.2f}")

        if self.metrics.max_drawdown > self.alert_thresholds['max_drawdown']:
            alerts.append(f"High drawdown: {self.metrics.max_drawdown:.2%}")
            logger.warning(f"High drawdown alert: {self.metrics.max_drawdown:.2%}")

        if self.metrics.sharpe_ratio < self.alert_thresholds['min_sharpe_ratio']:
            alerts.append(f"Low Sharpe ratio: {self.metrics.sharpe_ratio:.2f}")
            logger.warning(f"Low Sharpe ratio alert: {self.metrics.sharpe_ratio:.2f}")

        # Multiple poor indicators trigger emergency
        poor_indicators = sum([
            self.metrics.win_rate < self.alert_thresholds['min_win_rate'],
            self.metrics.profit_factor < self.alert_thresholds['min_profit_factor'],
            self.metrics.max_drawdown > self.alert_thresholds['max_drawdown'],
            self.metrics.sharpe_ratio < self.alert_thresholds['min_sharpe_ratio']
        ])

        if poor_indicators >= 2:
            logger.error("Multiple poor performance indicators detected")
            # Would trigger emergency stop via safety monitor

    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system performance metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Calculate error rate from recent logs (simplified)
            error_rate = 0.0  # Would need log analysis implementation

            metrics = SystemMetrics(
                timestamp=int(time.time()),
                cpu_usage=cpu_percent,
                memory_usage=memory_percent,
                response_time=0.0,  # Would need actual response time tracking
                error_rate=error_rate,
                active_connections=0  # Would need connection tracking
            )

            self.system_metrics.append(metrics)
            if len(self.system_metrics) > 1000:  # Keep last 1000 entries
                self.system_metrics.pop(0)

            return metrics
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(
                timestamp=int(time.time()),
                cpu_usage=0.0,
                memory_usage=0.0,
                response_time=0.0,
                error_rate=0.0,
                active_connections=0
            )

    async def get_metrics_history(self, hours: int = 24) -> List[SystemMetrics]:
        """Get system metrics history"""
        cutoff_time = time.time() - (hours * 3600)
        return [m for m in self.system_metrics if m.timestamp >= cutoff_time]

    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            # Simple health checks
            cpu_ok = psutil.cpu_percent() < 90
            memory_ok = psutil.virtual_memory().percent < 90

            status = "healthy" if cpu_ok and memory_ok else "degraded"

            return {
                "status": status,
                "uptime": time.time() - psutil.boot_time(),
                "cpu_ok": cpu_ok,
                "memory_ok": memory_ok
            }
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {"status": "unknown", "uptime": 0}

    async def alert_on_thresholds(self, thresholds: Dict[str, float]) -> List[str]:
        """Check metrics against custom thresholds and return alerts"""
        alerts = []
        current_metrics = await self.collect_system_metrics()

        if current_metrics.cpu_usage > thresholds.get('cpu', 90):
            alerts.append(f"High CPU usage: {current_metrics.cpu_usage:.1f}%")

        if current_metrics.memory_usage > thresholds.get('memory', 90):
            alerts.append(f"High memory usage: {current_metrics.memory_usage:.1f}%")

        if current_metrics.error_rate > thresholds.get('error_rate', 0.05):
            alerts.append(f"High error rate: {current_metrics.error_rate:.2%}")

        return alerts

    def adjust_risk_thresholds(self, conditions: Dict[str, Any]) -> None:
        """Adjust risk thresholds based on market conditions"""
        # Placeholder for dynamic threshold adjustment
        logger.debug("Risk thresholds adjustment requested", extra=conditions)

    def get_trading_metrics(self) -> PerformanceMetrics:
        """Get current trading performance metrics"""
        return self.metrics

    async def reset(self) -> None:
        """Reset all metrics"""
        self.recent_trades.clear()
        self.metrics = PerformanceMetrics(
            win_rate=0.0,
            profit_factor=0.0,
            average_win=0.0,
            average_loss=0.0,
            successful_trades=0,
            failed_trades=0,
            total_trades=0,
            consecutive_losses=0,
            max_drawdown=0.0,
            sharpe_ratio=0.0
        )
        logger.info("Performance monitor reset")

    async def close(self) -> None:
        """Cleanup resources"""
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

# Export singleton instance
performance_monitor = PerformanceMonitor()