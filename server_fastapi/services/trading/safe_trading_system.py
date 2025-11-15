"""
Safe trading system
"""

import logging
from typing import Dict, Optional, List, Any
from pydantic import BaseModel
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TradingRules(BaseModel):
    max_position_size: float
    max_daily_loss: float
    max_drawdown: float
    required_confirmations: int
    allowed_symbols: List[str]


class SafeTradingSystem:
    """Safe trading system with risk controls"""

    def __init__(self):
        self.rules = TradingRules(
            max_position_size=1000.0,
            max_daily_loss=500.0,
            max_drawdown=0.1,
            required_confirmations=2,
            allowed_symbols=["BTC/USD", "ETH/USD", "ADA/USD", "SOL/USD"]
        )

        # Track daily trading activity
        self.daily_stats = {
            "date": datetime.now().date(),
            "total_loss": 0.0,
            "total_trades": 0,
            "positions": {},
            "emergency_stop_active": False
        }

        logger.info("Safe trading system initialized")

    async def validate_trade(self, trade_details: Dict[str, Any]) -> Dict[str, Any]:
        """Validate trade against safety rules"""
        try:
            errors = []
            warnings = []

            # Check if emergency stop is active
            if self.daily_stats["emergency_stop_active"]:
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
                errors.append(f"Position size ${position_value:.2f} exceeds max ${self.rules.max_position_size}")

            # Check daily loss limit
            if self.daily_stats["total_loss"] >= self.rules.max_daily_loss:
                errors.append(f"Daily loss limit ${self.rules.max_daily_loss} exceeded")

            # Check current position for the symbol
            current_position = self.daily_stats["positions"].get(symbol, 0)

            # For sell orders, check if we have enough position
            if action == "sell" and current_position < quantity:
                errors.append(f"Insufficient position: have {current_position}, trying to sell {quantity}")

            # For buy orders, check if adding this would exceed position limit
            if action == "buy":
                new_position_value = (current_position + quantity) * price
                if new_position_value > self.rules.max_position_size:
                    warnings.append(f"New position value ${new_position_value:.2f} approaches max limit")

            # Validate price (basic sanity check)
            if price <= 0:
                errors.append("Invalid price: must be positive")

            if quantity <= 0:
                errors.append("Invalid quantity: must be positive")

            # Check for high frequency trading (rate limiting)
            if self.daily_stats["total_trades"] > 100:  # arbitrary limit
                warnings.append("High trading frequency detected")

            return {
                "valid": len(errors) == 0,
                "warnings": warnings,
                "errors": errors,
                "risk_score": self._calculate_risk_score(trade_details),
                "position_impact": position_value / self.rules.max_position_size
            }

        except Exception as e:
            logger.error(f"Error validating trade: {str(e)}")
            return {"valid": False, "warnings": [], "errors": [f"Validation error: {str(e)}"]}

    async def apply_risk_limits(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """Apply risk limits to portfolio"""
        try:
            modified_portfolio = portfolio.copy()

            # Calculate current portfolio value and drawdown
            total_value = sum(position.get("value", 0) for position in portfolio.get("positions", {}).values())

            # Check drawdown limit
            if "initial_value" in portfolio:
                initial_value = portfolio["initial_value"]
                drawdown = (initial_value - total_value) / initial_value
                if drawdown > self.rules.max_drawdown:
                    logger.warning(f"Drawdown limit exceeded: {drawdown:.2%} > {self.rules.max_drawdown:.2%}")
                    # Reduce position sizes to bring drawdown within limits
                    reduction_factor = (initial_value * (1 - self.rules.max_drawdown)) / total_value
                    for symbol, position in modified_portfolio.get("positions", {}).items():
                        position["quantity"] *= reduction_factor
                        position["value"] *= reduction_factor

            # Apply position size limits
            positions = modified_portfolio.get("positions", {})
            for symbol, position in positions.items():
                if position.get("value", 0) > self.rules.max_position_size:
                    logger.warning(f"Position size limit exceeded for {symbol}")
                    position["quantity"] *= self.rules.max_position_size / position["value"]
                    position["value"] = self.rules.max_position_size

            # Apply daily loss limits
            if self.daily_stats["total_loss"] > self.rules.max_daily_loss:
                logger.warning("Daily loss limit exceeded - restricting trading")
                modified_portfolio["trading_restricted"] = True
                modified_portfolio["restriction_reason"] = "daily_loss_limit"

            return modified_portfolio

        except Exception as e:
            logger.error(f"Error applying risk limits: {str(e)}")
            return portfolio

    async def emergency_stop_all(self) -> bool:
        """Emergency stop all trading activities"""
        try:
            logger.warning("EMERGENCY STOP ACTIVATED - Stopping all trading activities")

            self.daily_stats["emergency_stop_active"] = True

            # In a real implementation, this would:
            # 1. Stop all active bots via BotRunner
            # 2. Cancel all pending orders
            # 3. Close all open positions
            # 4. Notify administrators

            # For now, just set the flag and log
            logger.critical("Emergency stop: All trading halted")

            return True

        except Exception as e:
            logger.error(f"Error activating emergency stop: {str(e)}")
            return False

    async def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety status"""
        try:
            # Reset daily stats if it's a new day
            today = datetime.now().date()
            if self.daily_stats["date"] != today:
                self.daily_stats = {
                    "date": today,
                    "total_loss": 0.0,
                    "total_trades": 0,
                    "positions": {},
                    "emergency_stop_active": False
                }

            # Calculate safety metrics
            drawdown_pct = (self.daily_stats["total_loss"] / max(self.rules.max_daily_loss, 1)) * 100
            position_utilization = sum(self.daily_stats["positions"].values()) / max(self.rules.max_position_size, 1)

            status = "safe"
            alerts = []

            if self.daily_stats["emergency_stop_active"]:
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
                    f"Required confirmations: {self.rules.required_confirmations}"
                ],
                "current_stats": {
                    "daily_loss": self.daily_stats["total_loss"],
                    "daily_trades": self.daily_stats["total_trades"],
                    "active_positions": len(self.daily_stats["positions"]),
                    "emergency_stop": self.daily_stats["emergency_stop_active"]
                },
                "alerts": alerts,
                "allowed_symbols": self.rules.allowed_symbols
            }

        except Exception as e:
            logger.error(f"Error getting safety status: {str(e)}")
            return {
                "status": "error",
                "active_rules": [],
                "current_stats": {},
                "alerts": [f"Status check failed: {str(e)}"],
                "allowed_symbols": []
            }

    def _calculate_risk_score(self, trade_details: Dict[str, Any]) -> float:
        """Calculate risk score for a trade (0-10 scale, higher = riskier)"""
        score = 0.0

        # Position size risk
        position_value = trade_details["quantity"] * trade_details["price"]
        size_ratio = position_value / self.rules.max_position_size
        score += min(size_ratio * 5, 5)  # Max 5 points for size

        # Daily loss risk
        loss_ratio = self.daily_stats["total_loss"] / self.rules.max_daily_loss
        score += min(loss_ratio * 3, 3)  # Max 3 points for daily loss

        # Frequency risk (recent trading activity)
        if self.daily_stats["total_trades"] > 50:
            score += 2

        return min(score, 10.0)

    async def record_trade_result(self, trade_details: Dict[str, Any], pnl: float):
        """Record trade result for risk monitoring"""
        try:
            symbol = trade_details.get("symbol", "unknown")

            # Update daily stats
            self.daily_stats["total_trades"] += 1

            if pnl < 0:
                self.daily_stats["total_loss"] += abs(pnl)

            # Update position tracking
            action = trade_details.get("action")
            quantity = trade_details.get("quantity", 0)

            if action == "buy":
                self.daily_stats["positions"][symbol] = self.daily_stats["positions"].get(symbol, 0) + quantity
            elif action == "sell":
                self.daily_stats["positions"][symbol] = max(0, self.daily_stats["positions"].get(symbol, 0) - quantity)

            # Check for emergency stop conditions
            if self.daily_stats["total_loss"] > self.rules.max_daily_loss * 1.2:  # 20% buffer
                logger.warning("Daily loss limit exceeded - triggering emergency stop")
                await self.emergency_stop_all()

        except Exception as e:
            logger.error(f"Error recording trade result: {str(e)}")