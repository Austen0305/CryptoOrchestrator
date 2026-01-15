"""
Safe trading system
"""

import logging
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...repositories.safety_repository import SafetyRepository

logger = logging.getLogger(__name__)


class TradingRules(BaseModel):
    max_position_size: float
    max_daily_loss: float
    max_drawdown: float
    required_confirmations: int
    allowed_symbols: list[str]


class SafeTradingSystem:
    """Safe trading system with risk controls (2026 Persistent Standard)"""

    def __init__(
        self,
        db_session: AsyncSession | None = None,
        safety_repo: SafetyRepository | None = None,
    ):
        self.db_session = db_session
        self.safety_repo = safety_repo or SafetyRepository()
        self.rules = TradingRules(
            max_position_size=1000.0,
            max_daily_loss=500.0,
            max_drawdown=0.1,
            required_confirmations=2,
            allowed_symbols=["BTC/USD", "ETH/USD", "ADA/USD", "SOL/USD"],
        )

        logger.info("Safe trading system initialized with persistent safety repository")

    async def validate_trade(
        self, trade_details: dict[str, Any], session: AsyncSession | None = None
    ) -> dict[str, Any]:
        """Validate trade against safety rules (2026 Persistent)"""
        current_session = session or self.db_session
        if not current_session:
            raise ValueError(
                "AsyncSession is required for persistent safety validation"
            )

        try:
            errors = []
            warnings = []

            # Get user_id as int
            user_id_raw = trade_details.get("user_id")
            if not user_id_raw or user_id_raw == "default":
                # For backward compatibility or anonymous tests, use a system user ID if defined, or fail
                errors.append(
                    "Valid Integer user_id is required for 2026 safety standards"
                )
                return {"valid": False, "warnings": warnings, "errors": errors}

            user_id = int(user_id_raw)

            # Fetch persistent stats
            stats = await self.safety_repo.get_safety_stats(current_session, user_id)
            if not stats:
                stats = await self.safety_repo.create_safety_stats(
                    current_session, user_id
                )

            # Check for daily reset (Handled in repository's update_trade_stats logic mostly,
            # but for validation we check here)
            today = datetime.now(UTC).date()
            if stats.last_reset_at.date() < today:
                # Stats are stale, effectively zero for validation
                total_loss = 0.0
                total_trades = 0
                emergency_stop = stats.emergency_stop_active == 1
            else:
                total_loss = stats.daily_loss
                total_trades = stats.total_trades_today
                emergency_stop = stats.emergency_stop_active == 1

            # Check if emergency stop is active
            if emergency_stop:
                errors.append("Emergency stop is active - no trading allowed")
                return {"valid": False, "warnings": warnings, "errors": errors}

            # Validate required fields
            required_fields = ["symbol", "action", "quantity", "price", "bot_id"]
            for field in required_fields:
                if field not in trade_details:
                    errors.append(f"Missing required field: {field}")
                    continue

            if errors:
                return {"valid": False, "warnings": warnings, "errors": errors}

            symbol = trade_details["symbol"]
            action = trade_details["action"]
            quantity = trade_details["quantity"]
            price = trade_details["price"]

            # Validate symbol
            if symbol not in self.rules.allowed_symbols:
                errors.append(f"Symbol {symbol} not in allowed list")

            # Validate action
            if action not in ["buy", "sell"]:
                errors.append(f"Invalid action: {action}")

            # Validate position size
            position_value = quantity * price
            if position_value > self.rules.max_position_size:
                errors.append(
                    f"Position size ${position_value:.2f} exceeds max ${self.rules.max_position_size}"
                )

            # Check daily loss limit
            if total_loss >= self.rules.max_daily_loss:
                errors.append(f"Daily loss limit ${self.rules.max_daily_loss} exceeded")

            # Check current position for the symbol
            # NOTE: Persistent position tracking is handled by Order/Trade repositories
            # Here we just validate against rule-based limits
            current_position = 0.0  # Placeholder: For 2026, we should query current holdings from WalletRepository if needed

            # For sell orders, check if we have enough position
            if action == "sell" and current_position < quantity:
                errors.append(
                    f"Insufficient position: have {current_position}, trying to sell {quantity}"
                )

            # For buy orders, check if adding this would exceed position limit
            if action == "buy":
                new_position_value = (current_position + quantity) * price
                if new_position_value > self.rules.max_position_size:
                    warnings.append(
                        f"New position value ${new_position_value:.2f} approaches max limit"
                    )

            # Validate price (basic sanity check)
            if price <= 0:
                errors.append("Invalid price: must be positive")

            if quantity <= 0:
                errors.append("Invalid quantity: must be positive")

            # Check for high frequency trading (rate limiting)
            if total_trades > 100:  # arbitrary limit
                warnings.append("High trading frequency detected")

            return {
                "valid": len(errors) == 0,
                "warnings": warnings,
                "errors": errors,
                "risk_score": self._calculate_risk_score(
                    trade_details,
                    {"total_loss": total_loss, "total_trades": total_trades},
                ),
                "position_impact": position_value / self.rules.max_position_size,
            }

        except Exception as e:
            logger.error(f"Error validating trade: {str(e)}")
            return {
                "valid": False,
                "warnings": [],
                "errors": [f"Validation error: {str(e)}"],
            }

    async def apply_risk_limits(
        self,
        portfolio: dict[str, Any],
        user_id: int | None = None,
        session: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """Apply risk limits to portfolio (2026 Persistent)"""
        current_session = session or self.db_session
        if not current_session:
            return portfolio  # Graceful fallback if no session

        try:
            if not user_id:
                return portfolio

            # Fetch persistent stats
            stats = await self.safety_repo.get_safety_stats(current_session, user_id)
            total_loss = (
                stats.daily_loss
                if stats and stats.last_reset_at.date() == datetime.now(UTC).date()
                else 0.0
            )

            modified_portfolio = portfolio.copy()

            # Calculate current portfolio value and drawdown
            total_value = sum(
                position.get("value", 0)
                for position in portfolio.get("positions", {}).values()
            )

            # Check drawdown limit
            if "initial_value" in portfolio:
                initial_value = portfolio["initial_value"]
                drawdown = (initial_value - total_value) / initial_value
                if drawdown > self.rules.max_drawdown:
                    logger.warning(
                        f"Drawdown limit exceeded: {drawdown:.2%} > {self.rules.max_drawdown:.2%}"
                    )
                    # Reduce position sizes to bring drawdown within limits
                    reduction_factor = (
                        initial_value * (1 - self.rules.max_drawdown)
                    ) / total_value
                    for symbol, position in modified_portfolio.get(
                        "positions", {}
                    ).items():
                        position["quantity"] *= reduction_factor
                        position["value"] *= reduction_factor

            # Apply position size limits
            positions = modified_portfolio.get("positions", {})
            for symbol, position in positions.items():
                if position.get("value", 0) > self.rules.max_position_size:
                    logger.warning(f"Position size limit exceeded for {symbol}")
                    position["quantity"] *= (
                        self.rules.max_position_size / position["value"]
                    )
                    position["value"] = self.rules.max_position_size

            # Apply daily loss limits
            if total_loss > self.rules.max_daily_loss:
                logger.warning("Daily loss limit exceeded - restricting trading")
                modified_portfolio["trading_restricted"] = True
                modified_portfolio["restriction_reason"] = "daily_loss_limit"

            return modified_portfolio

        except Exception as e:
            logger.error(f"Error applying risk limits: {str(e)}")
            return portfolio

    async def emergency_stop_all(
        self, user_id: int | None = None, session: AsyncSession | None = None
    ) -> bool:
        """Emergency stop all trading activities for a user (2026 Persistent)"""
        current_session = session or self.db_session
        if not current_session:
            logger.error("AsyncSession required for persistent emergency stop")
            return False

        try:
            if not user_id:
                return False

            await self.safety_repo.set_emergency_stop(current_session, user_id, True)

            # In a real implementation, this would:
            # 1. Stop all active bots via BotRunner
            # 2. Cancel all pending orders
            # 3. Close all open positions
            # 4. Notify administrators

            # For now, just set the flag and log
            logger.critical(
                f"Emergency stop: All trading halted for user {user_id_str}"
            )

            return True

        except Exception as e:
            logger.error(f"Error activating emergency stop: {str(e)}")
            return False

    async def get_safety_status(
        self, user_id: int | None = None, session: AsyncSession | None = None
    ) -> dict[str, Any]:
        """Get current safety status for a user (2026 Persistent)"""
        current_session = session or self.db_session
        if not current_session:
            return {"status": "error", "alerts": ["No DB session"]}

        try:
            if not user_id:
                return {"status": "error", "alerts": ["No user ID provided"]}

            stats = await self.safety_repo.get_safety_stats(current_session, user_id)
            if not stats:
                stats = await self.safety_repo.create_safety_stats(
                    current_session, user_id
                )

            today = datetime.now(UTC).date()
            if stats.last_reset_at.date() < today:
                total_loss = 0.0
                total_profit = 0.0
                total_trades = 0
                emergency_stop = stats.emergency_stop_active == 1
                positions_count = 0
            else:
                total_loss = stats.daily_loss
                total_profit = 0.0  # Placeholder: stats model doesn't track daily profit separately yet,
                # but we could add it if needed for a "perfect" system.
                total_trades = stats.total_trades_today
                emergency_stop = stats.emergency_stop_active == 1
                positions_count = 0  # Placeholder: query trade/order repository

            # Calculate safety metrics
            drawdown_pct = (total_loss / max(self.rules.max_daily_loss, 1)) * 100
            position_utilization = 0.0  # Placeholder

            status = "safe"
            alerts = []

            if user_stats.get("emergency_stop_active", False):
                status = "emergency_stop"
                alerts.append("EMERGENCY STOP ACTIVE")
            elif drawdown_pct > 80:
                status = "warning"
                alerts.append(f"Daily loss at {drawdown_pct:.1f}% of limit")
            elif position_utilization > 0.8:
                status = "caution"
                alerts.append(f"Position utilization at {position_utilization:.1f}")

            return {
                "status": status,
                "active_rules": [
                    f"Max position size: ${self.rules.max_position_size}",
                    f"Max daily loss: ${self.rules.max_daily_loss}",
                    f"Max drawdown: {self.rules.max_drawdown:.1%}",
                    f"Required confirmations: {self.rules.required_confirmations}",
                ],
                "current_stats": {
                    "daily_loss": total_loss,
                    "daily_profit": total_profit,
                    "daily_trades": total_trades,
                    "active_positions": positions_count,
                    "emergency_stop": emergency_stop,
                },
                "alerts": alerts,
                "allowed_symbols": self.rules.allowed_symbols,
            }

        except Exception as e:
            logger.error(f"Error getting safety status: {str(e)}")
            return {
                "status": "error",
                "active_rules": [],
                "current_stats": {},
                "alerts": [f"Status check failed: {str(e)}"],
                "allowed_symbols": [],
            }

    def _calculate_risk_score(
        self, trade_details: dict[str, Any], user_stats: dict[str, Any] | None = None
    ) -> float:
        """Calculate risk score for a trade (0-10 scale, higher = riskier)"""
        score = 0.0

        # Get user stats
        user_id = str(trade_details.get("user_id", "default"))
        if user_stats is None:
            user_stats = self.daily_stats.get(
                user_id,
                {
                    "total_loss": 0.0,
                    "total_trades": 0,
                },
            )

        # Position size risk
        position_value = trade_details["quantity"] * trade_details["price"]
        size_ratio = position_value / self.rules.max_position_size
        score += min(size_ratio * 5, 5)  # Max 5 points for size

        # Daily loss risk
        loss_ratio = user_stats.get("total_loss", 0.0) / self.rules.max_daily_loss
        score += min(loss_ratio * 3, 3)  # Max 3 points for daily loss

        # Frequency risk (recent trading activity)
        if user_stats.get("total_trades", 0) > 50:
            score += 2

        return min(score, 10.0)

    async def record_trade_result(
        self,
        trade_details: dict[str, Any],
        pnl: float,
        session: AsyncSession | None = None,
    ):
        """Record trade result for risk monitoring (2026 Persistent)"""
        current_session = session or self.db_session
        if not current_session:
            logger.error("AsyncSession required for persistent trade recording")
            return

        try:
            user_id_raw = trade_details.get("user_id")
            if not user_id_raw or user_id_raw == "default":
                return

            user_id = int(user_id_raw)
            realized_loss = abs(pnl) if pnl < 0 else 0.0
            realized_profit = pnl if pnl > 0 else 0.0
            trade_volume = trade_details.get("quantity", 0) * trade_details.get(
                "price", 0
            )

            # Update persistent stats
            stats = await self.safety_repo.update_trade_stats(
                current_session, user_id, realized_loss, realized_profit, trade_volume
            )

            # Check for emergency stop conditions
            if stats.daily_loss > self.rules.max_daily_loss * 1.2:  # 20% buffer
                logger.warning(
                    f"Daily loss limit exceeded for user {user_id} - triggering emergency stop"
                )
                await self.emergency_stop_all(user_id, current_session)

        except Exception as e:
            logger.error(f"Error recording trade result: {str(e)}")

    async def get_daily_pnl(
        self, user_id: int, session: AsyncSession | None = None
    ) -> float:
        """Get daily P&L for a user (2026 Persistent)"""
        current_session = session or self.db_session
        if not current_session:
            return 0.0

        try:
            stats = await self.safety_repo.get_safety_stats(current_session, user_id)
            if not stats or stats.last_reset_at.date() < datetime.now(UTC).date():
                return 0.0

            return stats.daily_profit - stats.daily_loss

        except Exception as e:
            logger.error(f"Error getting daily P&L: {str(e)}")
            return 0.0
