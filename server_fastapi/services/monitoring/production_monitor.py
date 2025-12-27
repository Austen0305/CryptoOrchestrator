"""
Production Monitoring Service
Monitors system health, exchange connectivity, and trading operations for SaaS production
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class SystemHealth(str, Enum):
    """System health status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


class ExchangeStatus(str, Enum):
    """Exchange connection status"""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    DEGRADED = "degraded"
    ERROR = "error"


class ProductionMonitor:
    """Monitor production system health and exchange connectivity"""

    def __init__(self):
        self.exchange_status: Dict[str, ExchangeStatus] = {}
        self.last_health_check: Optional[datetime] = None
        self.health_history: List[Dict[str, Any]] = []
        self.exchange_errors: Dict[str, List[datetime]] = (
            {}
        )  # Track errors per exchange
        self.trading_metrics: Dict[str, Any] = {
            "total_trades_24h": 0,
            "successful_trades_24h": 0,
            "failed_trades_24h": 0,
            "total_volume_24h": 0.0,
            "average_execution_time_ms": 0.0,
        }

    async def check_exchange_health(self, exchange_name: str) -> ExchangeStatus:
        """Check health of a specific exchange"""
        try:
            from ..exchange_service import ExchangeService

            exchange = ExchangeService(name=exchange_name, use_mock=False)
            await exchange.connect()

            if exchange.is_connected():
                # Test a simple API call
                try:
                    await exchange.get_market_price("BTC/USDT")  # Test call
                    status = ExchangeStatus.CONNECTED
                except Exception as e:
                    logger.warning(
                        f"Exchange {exchange_name} connected but API call failed: {e}"
                    )
                    status = ExchangeStatus.DEGRADED
            else:
                status = ExchangeStatus.DISCONNECTED

            self.exchange_status[exchange_name] = status
            return status

        except Exception as e:
            logger.error(f"Error checking exchange {exchange_name} health: {e}")
            self.exchange_status[exchange_name] = ExchangeStatus.ERROR
            self._record_exchange_error(exchange_name)
            return ExchangeStatus.ERROR

    async def check_all_exchanges(self) -> Dict[str, ExchangeStatus]:
        """Check health of all supported exchanges"""
        supported_exchanges = ["binance", "kraken", "coinbasepro", "kucoin", "bybit"]

        tasks = [
            self.check_exchange_health(exchange) for exchange in supported_exchanges
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        return self.exchange_status.copy()

    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            # Check all exchanges
            exchange_statuses = await self.check_all_exchanges()

            # Count healthy exchanges
            healthy_count = sum(
                1 for s in exchange_statuses.values() if s == ExchangeStatus.CONNECTED
            )
            total_count = len(exchange_statuses)

            # Determine overall health
            if healthy_count == total_count and total_count > 0:
                overall_health = SystemHealth.HEALTHY
            elif healthy_count >= total_count * 0.5:
                overall_health = SystemHealth.DEGRADED
            elif healthy_count > 0:
                overall_health = SystemHealth.UNHEALTHY
            else:
                overall_health = SystemHealth.CRITICAL

            # Check for recent errors
            recent_errors = self._count_recent_errors(minutes=5)
            if recent_errors > 10:
                overall_health = SystemHealth.CRITICAL
            elif recent_errors > 5:
                overall_health = SystemHealth.UNHEALTHY

            self.last_health_check = datetime.now()

            health_data = {
                "status": overall_health.value,
                "timestamp": datetime.now().isoformat(),
                "exchanges": {
                    name: status.value for name, status in exchange_statuses.items()
                },
                "exchange_health": {
                    "healthy": healthy_count,
                    "total": total_count,
                    "percentage": (
                        (healthy_count / total_count * 100) if total_count > 0 else 0
                    ),
                },
                "recent_errors": recent_errors,
                "trading_metrics": self.trading_metrics.copy(),
                "production_mode": True,  # Always true for this service
            }

            # Store in history (keep last 100)
            self.health_history.append(health_data)
            if len(self.health_history) > 100:
                self.health_history = self.health_history[-100:]

            return health_data

        except Exception as e:
            logger.error(f"Error getting system health: {e}", exc_info=True)
            return {
                "status": SystemHealth.CRITICAL.value,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            }

    def record_trade_execution(
        self, success: bool, execution_time_ms: float, volume_usd: float, exchange: str
    ):
        """Record trade execution metrics"""
        self.trading_metrics["total_trades_24h"] += 1
        if success:
            self.trading_metrics["successful_trades_24h"] += 1
        else:
            self.trading_metrics["failed_trades_24h"] += 1

        self.trading_metrics["total_volume_24h"] += volume_usd

        # Update average execution time (simple moving average)
        current_avg = self.trading_metrics["average_execution_time_ms"]
        total_trades = self.trading_metrics["total_trades_24h"]
        self.trading_metrics["average_execution_time_ms"] = (
            current_avg * (total_trades - 1) + execution_time_ms
        ) / total_trades

        # Reset daily metrics at midnight
        if datetime.now().hour == 0 and datetime.now().minute == 0:
            self._reset_daily_metrics()

    def _record_exchange_error(self, exchange_name: str):
        """Record an error for an exchange"""
        if exchange_name not in self.exchange_errors:
            self.exchange_errors[exchange_name] = []

        self.exchange_errors[exchange_name].append(datetime.now())

        # Keep only last 100 errors per exchange
        if len(self.exchange_errors[exchange_name]) > 100:
            self.exchange_errors[exchange_name] = self.exchange_errors[exchange_name][
                -100:
            ]

    def _count_recent_errors(self, minutes: int = 5) -> int:
        """Count errors in the last N minutes"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        total_errors = 0

        for errors in self.exchange_errors.values():
            total_errors += sum(1 for error_time in errors if error_time > cutoff)

        return total_errors

    def _reset_daily_metrics(self):
        """Reset daily trading metrics"""
        self.trading_metrics = {
            "total_trades_24h": 0,
            "successful_trades_24h": 0,
            "failed_trades_24h": 0,
            "total_volume_24h": 0.0,
            "average_execution_time_ms": 0.0,
        }

    async def get_exchange_status(self, exchange_name: str) -> Dict[str, Any]:
        """Get detailed status for a specific exchange"""
        status = await self.check_exchange_health(exchange_name)

        recent_errors = sum(
            1
            for error_time in self.exchange_errors.get(exchange_name, [])
            if error_time > datetime.now() - timedelta(minutes=5)
        )

        return {
            "exchange": exchange_name,
            "status": status.value,
            "recent_errors_5m": recent_errors,
            "total_errors_24h": len(
                [
                    e
                    for e in self.exchange_errors.get(exchange_name, [])
                    if e > datetime.now() - timedelta(hours=24)
                ]
            ),
            "last_check": datetime.now().isoformat(),
        }

    async def get_alerts(self) -> List[Dict[str, Any]]:
        """Get production alerts for issues requiring attention"""
        alerts = []

        # Check exchange health
        exchange_statuses = await self.check_all_exchanges()
        for exchange, status in exchange_statuses.items():
            if status == ExchangeStatus.ERROR:
                alerts.append(
                    {
                        "level": "critical",
                        "type": "exchange_error",
                        "exchange": exchange,
                        "message": f"Exchange {exchange} is in error state",
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            elif status == ExchangeStatus.DISCONNECTED:
                alerts.append(
                    {
                        "level": "warning",
                        "type": "exchange_disconnected",
                        "exchange": exchange,
                        "message": f"Exchange {exchange} is disconnected",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        # Check error rates
        recent_errors = self._count_recent_errors(minutes=5)
        if recent_errors > 20:
            alerts.append(
                {
                    "level": "critical",
                    "type": "high_error_rate",
                    "message": f"High error rate detected: {recent_errors} errors in last 5 minutes",
                    "timestamp": datetime.now().isoformat(),
                }
            )
        elif recent_errors > 10:
            alerts.append(
                {
                    "level": "warning",
                    "type": "elevated_error_rate",
                    "message": f"Elevated error rate: {recent_errors} errors in last 5 minutes",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Check trading metrics
        if self.trading_metrics["failed_trades_24h"] > 0:
            failure_rate = (
                self.trading_metrics["failed_trades_24h"]
                / self.trading_metrics["total_trades_24h"]
                if self.trading_metrics["total_trades_24h"] > 0
                else 0
            )

            if failure_rate > 0.1:  # More than 10% failure rate
                alerts.append(
                    {
                        "level": "warning",
                        "type": "high_trade_failure_rate",
                        "message": f"High trade failure rate: {failure_rate:.1%}",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return alerts


# Global instance
production_monitor = ProductionMonitor()
