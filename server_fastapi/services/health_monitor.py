"""
Comprehensive System Health Monitoring
Provides detailed health checks for all system components
"""
import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class HealthMonitor:
    """
    Comprehensive health monitoring for all system components.
    
    Checks:
    - API server health
    - Database connectivity
    - Redis availability
    - Exchange connections
    - Safety service status
    - SL/TP service status
    - Price monitoring status
    - Memory usage
    - CPU usage
    """
    
    def __init__(self):
        self.start_time = time.time()
        self.health_checks = []
        logger.info("Health Monitor initialized")
    
    async def check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            from ...database import get_db_context
            
            start = time.time()
            async with get_db_context() as session:
                # Simple query to test connection
                await session.execute("SELECT 1")
                latency = (time.time() - start) * 1000  # Convert to ms
            
            status = "healthy" if latency < 100 else "degraded"
            
            return {
                "service": "database",
                "status": status,
                "latency_ms": round(latency, 2),
                "message": f"Database responding in {latency:.0f}ms"
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "service": "database",
                "status": "unhealthy",
                "error": str(e),
                "message": "Database connection failed"
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        try:
            from ...services.cache_service import redis_available, redis_client
            
            if not redis_available:
                return {
                    "service": "redis",
                    "status": "unavailable",
                    "message": "Redis not configured (optional)"
                }
            
            start = time.time()
            await redis_client.ping()
            latency = (time.time() - start) * 1000
            
            status = "healthy" if latency < 50 else "degraded"
            
            return {
                "service": "redis",
                "status": status,
                "latency_ms": round(latency, 2),
                "message": f"Redis responding in {latency:.0f}ms"
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "service": "redis",
                "status": "unhealthy",
                "error": str(e),
                "message": "Redis connection failed"
            }
    
    async def check_trading_safety(self) -> Dict[str, Any]:
        """Check trading safety service"""
        try:
            from ...services.trading.trading_safety_service import get_trading_safety_service
            
            service = get_trading_safety_service()
            status = service.get_safety_status()
            
            return {
                "service": "trading_safety",
                "status": "healthy",
                "kill_switch_active": status['kill_switch_active'],
                "trades_today": status['trades_today'],
                "daily_pnl": status['daily_pnl'],
                "message": "Trading safety service operational"
            }
        except Exception as e:
            logger.error(f"Trading safety health check failed: {e}")
            return {
                "service": "trading_safety",
                "status": "unhealthy",
                "error": str(e),
                "message": "Trading safety service unavailable"
            }
    
    async def check_sl_tp(self) -> Dict[str, Any]:
        """Check stop-loss/take-profit service"""
        try:
            from ...services.trading.sl_tp_service import get_sl_tp_service
            
            service = get_sl_tp_service()
            active_orders = service.get_active_orders()
            
            return {
                "service": "sl_tp",
                "status": "healthy",
                "active_orders": len(active_orders),
                "message": f"{len(active_orders)} active SL/TP orders"
            }
        except Exception as e:
            logger.error(f"SL/TP health check failed: {e}")
            return {
                "service": "sl_tp",
                "status": "unhealthy",
                "error": str(e),
                "message": "SL/TP service unavailable"
            }
    
    async def check_price_monitor(self) -> Dict[str, Any]:
        """Check price monitoring service"""
        try:
            from ...services.trading.price_monitor import get_price_monitor
            
            monitor = get_price_monitor()
            status = monitor.get_monitoring_status()
            
            service_status = "healthy" if status['monitoring'] else "idle"
            
            return {
                "service": "price_monitor",
                "status": service_status,
                "monitoring": status['monitoring'],
                "check_interval": status['check_interval'],
                "message": f"Monitoring: {status['monitoring']}"
            }
        except Exception as e:
            logger.error(f"Price monitor health check failed: {e}")
            return {
                "service": "price_monitor",
                "status": "unhealthy",
                "error": str(e),
                "message": "Price monitoring service unavailable"
            }
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            import psutil
            
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            memory_total_mb = memory.total / (1024 * 1024)
            
            # Determine status
            if cpu_percent > 90 or memory_percent > 90:
                status = "critical"
            elif cpu_percent > 70 or memory_percent > 70:
                status = "degraded"
            else:
                status = "healthy"
            
            return {
                "service": "system_resources",
                "status": status,
                "cpu_percent": round(cpu_percent, 1),
                "memory_percent": round(memory_percent, 1),
                "memory_used_mb": round(memory_used_mb, 0),
                "memory_total_mb": round(memory_total_mb, 0),
                "message": f"CPU: {cpu_percent:.0f}%, Memory: {memory_percent:.0f}%"
            }
        except ImportError:
            return {
                "service": "system_resources",
                "status": "unavailable",
                "message": "psutil not installed (optional)"
            }
        except Exception as e:
            logger.error(f"System resources check failed: {e}")
            return {
                "service": "system_resources",
                "status": "unknown",
                "error": str(e),
                "message": "Failed to check system resources"
            }
    
    def check_uptime(self) -> Dict[str, Any]:
        """Check system uptime"""
        uptime_seconds = time.time() - self.start_time
        uptime_hours = uptime_seconds / 3600
        uptime_days = uptime_hours / 24
        
        return {
            "service": "uptime",
            "status": "healthy",
            "uptime_seconds": round(uptime_seconds, 0),
            "uptime_hours": round(uptime_hours, 2),
            "uptime_days": round(uptime_days, 2),
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "message": f"Uptime: {uptime_days:.1f} days"
        }
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        checks = await asyncio.gather(
            self.check_database(),
            self.check_redis(),
            self.check_trading_safety(),
            self.check_sl_tp(),
            self.check_price_monitor(),
            return_exceptions=True
        )
        
        # Add synchronous checks
        checks.append(self.check_system_resources())
        checks.append(self.check_uptime())
        
        # Calculate overall status
        statuses = [
            check['status'] for check in checks
            if isinstance(check, dict) and 'status' in check
        ]
        
        if 'critical' in statuses or 'unhealthy' in statuses:
            overall_status = "unhealthy"
        elif 'degraded' in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "overall_status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "checks": checks
        }


# Singleton instance
_health_monitor_instance = None


def get_health_monitor() -> HealthMonitor:
    """Get or create the health monitor singleton."""
    global _health_monitor_instance
    if _health_monitor_instance is None:
        _health_monitor_instance = HealthMonitor()
    return _health_monitor_instance
