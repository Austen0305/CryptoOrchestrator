from __future__ import annotations

"""
Bot monitoring service integrating safety and monitoring
"""

import logging
from typing import Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..monitoring.safety_monitor import SafetyMonitor
from ..trading.safe_trading_system import SafeTradingSystem
from .bot_control_service import BotControlService

logger = logging.getLogger(__name__)


class MonitoringAlert(BaseModel):
    bot_id: str
    type: str
    severity: str
    message: str
    timestamp: int


class BotMonitoringService:
    """Service for bot monitoring, safety checks, and alerts"""

    def __init__(self, session: AsyncSession | None = None):
        self.control_service = BotControlService(session=session)
        self.safety_monitor = SafetyMonitor()
        self.safe_trading_system = SafeTradingSystem()
        self.session = session

    async def check_bot_health(self, bot_id: str, user_id: int) -> dict[str, Any]:
        """Check overall health of a bot"""
        try:
            # Get bot status
            bot_status = await self.control_service.get_bot_status(bot_id, user_id)
            if not bot_status:
                return {"healthy": False, "status": "not_found"}

            # Check if bot should be active but isn't responding
            is_active = bot_status.get("active", False)
            last_update = bot_status.get("updated_at")

            # Get safety status
            safety_status = await self.safe_trading_system.get_safety_status()

            # Get active alerts for this bot
            alerts = await self.get_bot_alerts(bot_id, user_id)

            # Determine health based on various factors
            health_issues = []

            if safety_status["status"] == "emergency_stop":
                health_issues.append("system_emergency_stop")
            elif safety_status["status"] == "warning":
                health_issues.append("system_warnings")

            if len(alerts) > 0:
                critical_alerts = [a for a in alerts if a.severity == "critical"]
                if critical_alerts:
                    health_issues.append("critical_alerts")

            # Check for stale bot status (if active but no recent updates)
            if is_active and last_update:
                # This would need actual timestamp comparison logic
                pass

            healthy = len(health_issues) == 0

            return {
                "healthy": healthy,
                "status": bot_status.get("status", "unknown"),
                "issues": health_issues,
                "alerts_count": len(alerts),
                "safety_status": safety_status["status"],
            }

        except Exception as e:
            logger.error(f"Error checking bot health for {bot_id}: {str(e)}")
            return {"healthy": False, "status": "error", "error": str(e)}

    async def get_bot_alerts(self, bot_id: str, user_id: int) -> list[MonitoringAlert]:
        """Get alerts specific to a bot"""
        try:
            # Get system-wide alerts
            system_alerts = await self.safety_monitor.get_active_alerts()

            # Filter alerts related to this bot
            bot_alerts = []
            for alert in system_alerts:
                # This is a simplified filtering - in reality you'd need bot-specific alert types
                if bot_id in alert.message or "bot" in alert.type.lower():
                    bot_alerts.append(
                        MonitoringAlert(
                            bot_id=bot_id,
                            type=alert.type,
                            severity=alert.severity,
                            message=alert.message,
                            timestamp=alert.timestamp,
                        )
                    )

            return bot_alerts

        except Exception as e:
            logger.error(f"Error getting alerts for bot {bot_id}: {str(e)}")
            return []

    async def validate_bot_start_conditions(
        self, bot_id: str, user_id: int
    ) -> dict[str, Any]:
        """Validate conditions before starting a bot"""
        try:
            # Check safety status
            safety_status = await self.safe_trading_system.get_safety_status()

            validation_result = {"can_start": True, "warnings": [], "blockers": []}

            if safety_status["status"] == "emergency_stop":
                validation_result["can_start"] = False
                validation_result["blockers"].append("System emergency stop is active")

            if safety_status["status"] == "warning":
                validation_result["warnings"].extend(safety_status.get("alerts", []))

            # Check bot health
            health = await self.check_bot_health(bot_id, user_id)
            if not health["healthy"]:
                validation_result["warnings"].extend(health.get("issues", []))

            # Check for critical alerts
            alerts = await self.get_bot_alerts(bot_id, user_id)
            critical_alerts = [a for a in alerts if a.severity == "critical"]
            if critical_alerts:
                validation_result["can_start"] = False
                validation_result["blockers"].append(
                    f"Critical alerts: {len(critical_alerts)}"
                )

            return validation_result

        except Exception as e:
            logger.error(
                f"Error validating start conditions for bot {bot_id}: {str(e)}"
            )
            return {
                "can_start": False,
                "warnings": [],
                "blockers": [f"Validation error: {str(e)}"],
            }

    async def monitor_active_bots(self, user_id: int) -> dict[str, Any]:
        """Monitor all active bots for a user"""
        try:
            from .bot_creation_service import BotCreationService

            creation_service = BotCreationService()

            user_bots = await creation_service.list_user_bots(user_id)
            active_bots = [bot for bot in user_bots if bot.active]

            monitoring_results = {
                "total_active": len(active_bots),
                "healthy_count": 0,
                "unhealthy_count": 0,
                "bot_health": {},
            }

            for bot in active_bots:
                health = await self.check_bot_health(bot.id, user_id)
                monitoring_results["bot_health"][bot.id] = health

                if health["healthy"]:
                    monitoring_results["healthy_count"] += 1
                else:
                    monitoring_results["unhealthy_count"] += 1

            return monitoring_results

        except Exception as e:
            logger.error(f"Error monitoring active bots for user {user_id}: {str(e)}")
            return {"error": str(e)}

    async def emergency_stop_bot(
        self, bot_id: str, user_id: int, reason: str = "manual_emergency"
    ) -> bool:
        """Emergency stop a specific bot"""
        try:
            logger.warning(
                f"Emergency stop triggered for bot {bot_id}, reason: {reason}"
            )

            # Stop the bot
            success = await self.control_service.stop_bot(bot_id, user_id)

            # Log emergency stop event
            if success:
                # This could integrate with a more comprehensive logging system
                logger.critical(f"Emergency stop successful for bot {bot_id}: {reason}")

            return success

        except Exception as e:
            logger.error(f"Error during emergency stop for bot {bot_id}: {str(e)}")
            return False

    async def emergency_stop_all_user_bots(
        self, user_id: int, reason: str = "system_emergency"
    ) -> int:
        """Emergency stop all active bots for a user"""
        try:
            logger.warning(
                f"Emergency stop all bots for user {user_id}, reason: {reason}"
            )

            stopped_count = await self.control_service.bulk_stop_user_bots(user_id)

            logger.critical(
                f"Emergency stopped {stopped_count} bots for user {user_id}: {reason}"
            )
            return stopped_count

        except Exception as e:
            logger.error(
                f"Error during emergency stop all for user {user_id}: {str(e)}"
            )
            return 0

    async def get_system_safety_status(self) -> dict[str, Any]:
        """Get overall system safety status"""
        try:
            return await self.safe_trading_system.get_safety_status()
        except Exception as e:
            logger.error(f"Error getting system safety status: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def get_bot_performance(self, bot_id: str, user_id: int) -> dict[str, Any]:
        """Get performance metrics for a bot"""
        try:
            from ..database import get_db_context
            from ..repositories.trade_repository import TradeRepository

            async def _calculate_performance(session):
                """Helper to calculate performance with a session"""
                trade_repo = TradeRepository()
                trades = await trade_repo.get_by_bot(
                    session, bot_id, skip=0, limit=10000
                )
                # Filter by user_id if needed
                trades = [t for t in trades if str(t.user_id) == str(user_id)]

                if not trades:
                    # Return empty performance if no trades
                    return {
                        "total_trades": 0,
                        "winning_trades": 0,
                        "losing_trades": 0,
                        "win_rate": 0.0,
                        "total_pnl": 0.0,
                        "max_drawdown": 0.0,
                        "sharpe_ratio": 0.0,
                        "current_balance": 0.0,
                    }

                # Calculate real performance metrics
                total_trades = len(trades)
                winning_trades = sum(1 for t in trades if t.pnl and t.pnl > 0)
                losing_trades = total_trades - winning_trades
                win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
                total_pnl = sum((t.pnl or 0.0) for t in trades)

                # Calculate max drawdown (simplified)
                pnl_values = [(t.pnl or 0.0) for t in trades]
                if pnl_values:
                    cumulative = []
                    running_sum = 0.0
                    for pnl in pnl_values:
                        running_sum += pnl
                        cumulative.append(running_sum)
                    peak = max(cumulative) if cumulative else 0.0
                    max_drawdown = abs(min(cumulative) - peak) if cumulative else 0.0
                else:
                    max_drawdown = 0.0

                # Calculate Sharpe ratio (simplified - would need risk-free rate)
                if len(pnl_values) > 1:
                    import statistics

                    mean_return = statistics.mean(pnl_values)
                    std_return = (
                        statistics.stdev(pnl_values) if len(pnl_values) > 1 else 0.0
                    )
                    sharpe_ratio = (mean_return / std_return) if std_return > 0 else 0.0
                else:
                    sharpe_ratio = 0.0

                # Calculate current balance from trades (sum of all PnL + initial balance estimate)
                # Note: For accurate balance, use portfolio service via API endpoint
                # This is an approximation based on trade PnL
                initial_balance_estimate = 1000.0  # Default starting balance
                current_balance = initial_balance_estimate + total_pnl

                return {
                    "total_trades": total_trades,
                    "winning_trades": winning_trades,
                    "losing_trades": losing_trades,
                    "win_rate": win_rate,
                    "total_pnl": total_pnl,
                    "max_drawdown": max_drawdown,
                    "sharpe_ratio": sharpe_ratio,
                    "current_balance": current_balance,
                }

            # Use provided session or get new one
            if self.session:
                return await _calculate_performance(self.session)
            else:
                async with get_db_context() as session:
                    return await _calculate_performance(session)
        except Exception as e:
            logger.error(
                f"Error getting bot performance for {bot_id}: {str(e)}", exc_info=True
            )
            # Return empty performance on error
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "current_balance": 0.0,
            }
