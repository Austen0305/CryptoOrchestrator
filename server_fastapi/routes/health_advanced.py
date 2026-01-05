"""
Comprehensive Health Check System
Monitors all critical system components
Consolidated from health.py, health_comprehensive.py, and health_wallet.py
"""

from fastapi import APIRouter, Response, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, List, Optional, Any, Annotated
from datetime import datetime
from enum import Enum
import asyncio
import psutil
import logging
import time

from ..database import get_db_context, get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from ..dependencies.auth import get_current_user
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/health", tags=["Health"])


class ComponentHealth(BaseModel):
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: Optional[str] = None
    response_time_ms: Optional[float] = None
    details: Optional[Dict] = None


class HealthResponse(BaseModel):
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    version: str = "1.0.0"  # API version
    uptime_seconds: float
    components: List[ComponentHealth]
    checks: Optional[Dict[str, Dict[str, Any]]] = None  # Backward compatibility
    system_metrics: Dict


class HealthChecker:
    """Centralized health checking for all system components"""

    def __init__(self):
        self.start_time = datetime.now()
        self.checks: Dict[str, callable] = {}

    def register_check(self, name: str, check_func: callable):
        """Register a health check function"""
        self.checks[name] = check_func
        logger.info(f"Registered health check: {name}")

    async def check_component(self, name: str, check_func: callable) -> ComponentHealth:
        """Execute a single health check"""
        start_time = datetime.now()

        try:
            # Use longer timeout for health checks that make external API calls (e.g., DEX aggregators)
            result = await asyncio.wait_for(check_func(), timeout=15.0)
            response_time = (datetime.now() - start_time).total_seconds() * 1000

            if isinstance(result, dict):
                return ComponentHealth(
                    name=name,
                    status=result.get("status", "healthy"),
                    message=result.get("message"),
                    response_time_ms=response_time,
                    details=result.get("details"),
                )
            else:
                return ComponentHealth(
                    name=name,
                    status="healthy" if result else "unhealthy",
                    response_time_ms=response_time,
                )

        except asyncio.TimeoutError:
            return ComponentHealth(
                name=name, status="unhealthy", message="Health check timed out"
            )
        except Exception as e:
            logger.error(f"Health check failed for {name}: {e}")
            return ComponentHealth(name=name, status="unhealthy", message=str(e))

    async def check_all(self) -> HealthResponse:
        """Run all registered health checks"""
        tasks = [
            self.check_component(name, check_func)
            for name, check_func in self.checks.items()
        ]

        component_results = await asyncio.gather(*tasks)

        # Determine overall status
        unhealthy_count = sum(1 for c in component_results if c.status == "unhealthy")
        degraded_count = sum(1 for c in component_results if c.status == "degraded")

        if unhealthy_count > 0:
            overall_status = "unhealthy"
        elif degraded_count > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        # Get system metrics
        system_metrics = self._get_system_metrics()

        uptime = (datetime.now() - self.start_time).total_seconds()

        # Add health check metrics
        system_metrics["health_check_metrics"] = {
            "total_checks": len(component_results),
            "healthy_count": sum(1 for c in component_results if c.status == "healthy"),
            "degraded_count": degraded_count,
            "unhealthy_count": unhealthy_count,
            "average_response_time_ms": (
                sum(c.response_time_ms or 0 for c in component_results)
                / len(component_results)
                if component_results
                else 0
            ),
        }

        # Create checks dictionary for backward compatibility with tests
        checks_dict = {
            comp.name: {
                "status": comp.status,
                "message": comp.message,
                "response_time_ms": comp.response_time_ms,
                "details": comp.details,
            }
            for comp in component_results
        }

        return HealthResponse(
            status=overall_status,
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
            uptime_seconds=uptime,
            components=component_results,
            checks=checks_dict,
            system_metrics=system_metrics,
        )

    def _get_system_metrics(self) -> Dict:
        """Get system resource metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "cpu": {"percent": cpu_percent, "count": psutil.cpu_count()},
                "memory": {
                    "total_mb": round(memory.total / 1024 / 1024, 2),
                    "used_mb": round(memory.used / 1024 / 1024, 2),
                    "percent": memory.percent,
                },
                "disk": {
                    "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
                    "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
                    "percent": disk.percent,
                },
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}


# Global health checker instance
health_checker = HealthChecker()


# Health check endpoints
@router.get("/", response_model=HealthResponse)
async def get_health():
    """
    Comprehensive health check endpoint

    Returns:
    - Overall system status
    - Individual component health (database, Redis, blockchain RPC, DEX aggregators, etc.)
    - Response times
    - System uptime
    - System metrics (CPU, memory, disk)
    """
    return await health_checker.check_all()


@router.get("/aggregated", response_model=HealthResponse, tags=["Health"])
async def get_aggregated_health():
    """
    Aggregated health check with dependency status

    Returns overall health with all component statuses.
    Useful for monitoring and alerting systems.
    """
    health_response = await health_checker.check_all()

    # Add dependency health summary
    critical_components = ["database", "blockchain_rpc"]
    optional_components = ["redis", "dex_aggregators"]

    critical_healthy = all(
        comp.status == "healthy"
        for comp in health_response.components
        if comp.name in critical_components
    )

    optional_healthy_count = sum(
        1
        for comp in health_response.components
        if comp.name in optional_components and comp.status == "healthy"
    )

    # Determine if system is ready for trading
    trading_ready = critical_healthy and any(
        comp.status in ["healthy", "degraded"]
        for comp in health_response.components
        if comp.name == "dex_aggregators"
    )

    health_response.system_metrics["trading_ready"] = trading_ready
    health_response.system_metrics["critical_components_healthy"] = critical_healthy
    health_response.system_metrics["optional_components_healthy"] = (
        optional_healthy_count
    )

    return health_response


@router.get("/live")
async def get_liveness():
    """
    Kubernetes liveness probe endpoint

    Returns 200 if the service is alive
    Returns 503 if the service should be restarted
    """
    try:
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "uptime_seconds": round(time.time() - _app_start_time, 2),
        }
    except Exception as e:
        logger.error(f"Liveness check failed: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Service not alive: {str(e)}")


@router.get("/ready")
async def get_readiness(db: Annotated[AsyncSession, Depends(get_db_session)]):
    """
    Kubernetes readiness probe endpoint

    Returns 200 if the service is ready to accept traffic
    Returns 503 if the service is not ready
    """
    try:
        # Check critical dependencies only
        db_health = await check_database()

        if db_health.get("status") == "healthy":
            return {"status": "ready", "timestamp": datetime.utcnow().isoformat() + "Z"}
        else:
            raise HTTPException(
                status_code=503, detail="Service not ready: database unavailable"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")


@router.get("/startup")
async def get_startup():
    """
    Kubernetes startup probe endpoint

    Returns 200 when the application has finished starting up
    Returns 503 if the service is still starting
    """
    try:
        # Check if critical services are initialized
        # Exchange service deprecated - platform uses DEX-only trading
        # No longer checking exchange service availability

        db_health = await check_database()

        if db_health.get("status") == "healthy":
            return {
                "status": "started",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        else:
            raise HTTPException(status_code=503, detail="Service still starting up")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Startup check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=503, detail=f"Service startup check failed: {str(e)}"
        )


@router.get("/wallet")
async def wallet_health_check(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Dict[str, Any]:
    """Health check for wallet service"""
    try:
        user_id = _get_user_id(current_user)
        wallet_health = await check_wallet(str(user_id), db)
        return {
            "status": wallet_health.get("status", "unknown"),
            "service": "wallet",
            "user_id": user_id,
            **wallet_health.get("details", {}),
        }
    except Exception as e:
        logger.error(f"Wallet health check failed: {e}", exc_info=True)
        return {"status": "unhealthy", "service": "wallet", "error": str(e)}


@router.get("/staking")
async def staking_health_check(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Dict[str, Any]:
    """Health check for staking service"""
    try:
        staking_health = await check_staking(db)
        return {
            "status": staking_health.get("status", "unknown"),
            "service": "staking",
            **staking_health.get("details", {}),
        }
    except Exception as e:
        logger.error(f"Staking health check failed: {e}", exc_info=True)
        return {"status": "unhealthy", "service": "staking", "error": str(e)}


# Track application start time
_app_start_time = time.time()


# Health check functions
async def check_database():
    """Check database connectivity"""
    start_time = time.time()
    try:
        async with get_db_context() as db:
            result = await db.execute(text("SELECT 1"))
            result.scalar()
            response_time = (time.time() - start_time) * 1000
            return {
                "status": "healthy",
                "message": "Database connection successful",
                "response_time_ms": round(response_time, 2),
            }
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.error(f"Database health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
            "response_time_ms": round(response_time, 2),
        }


async def check_redis():
    """Check Redis connectivity (optional)"""
    start_time = time.time()
    try:
        from ..services.cache_service import cache_service

        if cache_service and cache_service.redis_available:
            # Try a simple ping operation
            test_key = "__health_check__"
            await cache_service.set(test_key, "ok", ttl=1)
            value = await cache_service.get(test_key)
            await cache_service.delete(test_key)
            response_time = (time.time() - start_time) * 1000

            if value == "ok":
                return {
                    "status": "healthy",
                    "message": "Redis connection successful",
                    "response_time_ms": round(response_time, 2),
                }
            else:
                return {
                    "status": "degraded",
                    "message": "Redis connection test failed",
                    "response_time_ms": round(response_time, 2),
                }
        else:
            return {
                "status": "degraded",
                "message": "Redis not configured (using memory cache)",
                "response_time_ms": 0,
            }
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.warning(f"Redis health check failed: {e}")
        return {
            "status": "degraded",
            "message": f"Redis unavailable: {str(e)}",
            "response_time_ms": round(response_time, 2),
        }


async def check_exchange_apis():
    """Check exchange API connectivity (DEPRECATED - platform uses DEX-only)"""
    # Exchange service has been removed - platform uses DEX-only trading
    # This endpoint is kept for backward compatibility but always returns deprecated status
    response_time = 0.1  # Minimal response time
    return {
        "status": "deprecated",
        "message": "Exchange API service deprecated (platform uses DEX-only trading via DEX aggregators)",
        "response_time_ms": round(response_time, 2),
        "note": "Use DEX aggregator health checks instead (0x, OKX, Rubic)",
    }


async def check_trading_safety():
    """Check trading safety service"""
    start_time = time.time()
    try:
        from ..services.trading.trading_safety_service import get_trading_safety_service

        service = get_trading_safety_service()
        status_data = service.get_safety_status()
        response_time = (time.time() - start_time) * 1000

        return {
            "status": "healthy",
            "message": f"Trading safety service operational (Kill switch: {status_data['kill_switch_active']})",
            "response_time_ms": round(response_time, 2),
            "details": {
                "kill_switch_active": status_data["kill_switch_active"],
                "trades_today": status_data["trades_today"],
                "daily_pnl": status_data["daily_pnl"],
            },
        }
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.warning(f"Trading safety health check failed: {e}")
        return {
            "status": "degraded",
            "message": f"Trading safety service unavailable: {str(e)}",
            "response_time_ms": round(response_time, 2),
        }


async def check_sl_tp_service():
    """Check stop-loss/take-profit service"""
    start_time = time.time()
    try:
        from ..services.trading.sl_tp_service import get_sl_tp_service

        service = get_sl_tp_service()
        active_orders = service.get_active_orders()
        response_time = (time.time() - start_time) * 1000

        return {
            "status": "healthy",
            "message": f"SL/TP service operational ({len(active_orders)} active orders)",
            "response_time_ms": round(response_time, 2),
            "details": {"active_orders": len(active_orders)},
        }
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.warning(f"SL/TP health check failed: {e}")
        return {
            "status": "degraded",
            "message": f"SL/TP service unavailable: {str(e)}",
            "response_time_ms": round(response_time, 2),
        }


async def check_price_monitor():
    """Check price monitoring service"""
    start_time = time.time()
    try:
        from ..services.trading.price_monitor import get_price_monitor

        monitor = get_price_monitor()
        monitor_status = monitor.get_monitoring_status()
        response_time = (time.time() - start_time) * 1000

        status_val = "healthy" if monitor_status["monitoring"] else "idle"

        return {
            "status": status_val,
            "message": f"Price monitor {'active' if monitor_status['monitoring'] else 'idle'}",
            "response_time_ms": round(response_time, 2),
            "details": monitor_status,
        }
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.warning(f"Price monitor health check failed: {e}")
        return {
            "status": "degraded",
            "message": f"Price monitor unavailable: {str(e)}",
            "response_time_ms": round(response_time, 2),
        }


async def check_wallet(user_id: str, db: AsyncSession):
    """Check wallet service health"""
    start_time = time.time()
    try:
        from ..services.wallet_service import WalletService

        service = WalletService(db)
        balance = await service.get_wallet_balance(user_id, "USD")
        response_time = (time.time() - start_time) * 1000

        return {
            "status": "healthy",
            "message": "Wallet service operational",
            "response_time_ms": round(response_time, 2),
            "details": {
                "wallet_exists": balance.get("wallet_id") is not None,
                "balance": balance.get("balance", 0.0),
            },
        }
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.warning(f"Wallet health check failed: {e}")
        return {
            "status": "degraded",
            "message": f"Wallet service unavailable: {str(e)}",
            "response_time_ms": round(response_time, 2),
        }


async def check_staking(db: AsyncSession):
    """Check staking service health"""
    start_time = time.time()
    try:
        from ..services.staking_service import StakingService

        service = StakingService(db)
        options = await service.get_staking_options()
        response_time = (time.time() - start_time) * 1000

        return {
            "status": "healthy",
            "message": f"Staking service operational ({len(options)} options)",
            "response_time_ms": round(response_time, 2),
            "details": {
                "options_count": len(options),
                "supported_assets": [opt["asset"] for opt in options],
            },
        }
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.warning(f"Staking health check failed: {e}")
        return {
            "status": "degraded",
            "message": f"Staking service unavailable: {str(e)}",
            "response_time_ms": round(response_time, 2),
        }


async def check_blockchain_rpc():
    """Check blockchain RPC endpoint health for all supported chains"""
    start_time = time.time()
    results = {}

    # Supported chains
    chains = [
        {"chain_id": 1, "name": "Ethereum"},
        {"chain_id": 8453, "name": "Base"},
        {"chain_id": 42161, "name": "Arbitrum One"},
        {"chain_id": 137, "name": "Polygon"},
    ]

    try:
        from ..services.blockchain.web3_service import get_web3_service

        web3_service = get_web3_service()
        healthy_chains = 0
        degraded_chains = 0

        for chain in chains:
            try:
                w3 = await web3_service.get_connection(chain["chain_id"])
                if w3:
                    # Try a simple call (get block number)
                    block_number = await w3.eth.block_number
                    results[chain["name"]] = {
                        "status": "healthy",
                        "chain_id": chain["chain_id"],
                        "latest_block": block_number,
                    }
                    healthy_chains += 1
                else:
                    results[chain["name"]] = {
                        "status": "unhealthy",
                        "chain_id": chain["chain_id"],
                        "message": "RPC connection not available",
                    }
                    degraded_chains += 1
            except Exception as e:
                results[chain["name"]] = {
                    "status": "unhealthy",
                    "chain_id": chain["chain_id"],
                    "message": str(e),
                }
                degraded_chains += 1

        response_time = (time.time() - start_time) * 1000

        # Overall status
        if degraded_chains == 0:
            status = "healthy"
            message = f"All blockchain RPC endpoints healthy ({healthy_chains} chains)"
        elif healthy_chains > 0:
            status = "degraded"
            message = (
                f"{healthy_chains} chains healthy, {degraded_chains} chains unhealthy"
            )
        else:
            status = "unhealthy"
            message = "All blockchain RPC endpoints unavailable"

        return {
            "status": status,
            "message": message,
            "response_time_ms": round(response_time, 2),
            "details": {
                "chains": results,
                "healthy_count": healthy_chains,
                "unhealthy_count": degraded_chains,
            },
        }
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.warning(f"Blockchain RPC health check failed: {e}")
        return {
            "status": "degraded",
            "message": f"Blockchain RPC health check error: {str(e)}",
            "response_time_ms": round(response_time, 2),
        }


async def check_dex_aggregators():
    """Check DEX aggregator API health"""
    start_time = time.time()
    results = {}

    aggregators = ["0x", "okx", "rubic"]

    try:
        from ..services.trading.aggregator_router import AggregatorRouter

        router = AggregatorRouter()
        healthy_aggregators = 0
        degraded_aggregators = 0

        for agg_name in aggregators:
            try:
                # Try to get a simple quote (ETH -> USDC on Ethereum)
                quote = await router.get_best_quote(
                    sell_token="ETH",
                    buy_token="USDC",
                    sell_amount="1000000000000000000",  # 1 ETH
                    chain_id=1,
                )

                if quote and quote[0]:  # quote is (aggregator_name, quote_data)
                    results[agg_name] = {
                        "status": "healthy",
                        "message": "Aggregator responding",
                    }
                    healthy_aggregators += 1
                else:
                    results[agg_name] = {
                        "status": "degraded",
                        "message": "No quote available",
                    }
                    degraded_aggregators += 1
            except Exception as e:
                results[agg_name] = {
                    "status": "unhealthy",
                    "message": str(e)[:100],  # Truncate long error messages
                }
                degraded_aggregators += 1

        response_time = (time.time() - start_time) * 1000

        # Overall status
        if degraded_aggregators == 0:
            status = "healthy"
            message = f"All DEX aggregators healthy ({healthy_aggregators} aggregators)"
        elif healthy_aggregators > 0:
            status = "degraded"
            message = f"{healthy_aggregators} aggregators healthy, {degraded_aggregators} aggregators unhealthy"
        else:
            status = "unhealthy"
            message = "All DEX aggregators unavailable"

        return {
            "status": status,
            "message": message,
            "response_time_ms": round(response_time, 2),
            "details": {
                "aggregators": results,
                "healthy_count": healthy_aggregators,
                "unhealthy_count": degraded_aggregators,
            },
        }
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.warning(f"DEX aggregator health check failed: {e}")
        return {
            "status": "degraded",
            "message": f"DEX aggregator health check error: {str(e)}",
            "response_time_ms": round(response_time, 2),
        }


async def check_database_pool():
    """Check database connection pool health"""
    start_time = time.time()
    try:
        from ..database import db_pool

        if db_pool:
            pool_status = await db_pool.get_pool_status()
            response_time = (time.time() - start_time) * 1000

            return {
                "status": "healthy",
                "message": "Database connection pool operational",
                "response_time_ms": round(response_time, 2),
                "details": pool_status,
            }
        else:
            return {
                "status": "degraded",
                "message": "Database pool not initialized",
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
            }
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.warning(f"Database pool health check failed: {e}")
        return {
            "status": "degraded",
            "message": f"Database pool check error: {str(e)}",
            "response_time_ms": round(response_time, 2),
        }


# Register health checks
health_checker.register_check("database", check_database)
health_checker.register_check("database_pool", check_database_pool)
health_checker.register_check("redis", check_redis)
health_checker.register_check("exchange_apis", check_exchange_apis)
health_checker.register_check("blockchain_rpc", check_blockchain_rpc)
health_checker.register_check("dex_aggregators", check_dex_aggregators)
health_checker.register_check("trading_safety", check_trading_safety)
health_checker.register_check("sl_tp_service", check_sl_tp_service)
health_checker.register_check("price_monitor", check_price_monitor)
