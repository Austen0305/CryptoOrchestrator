"""
Trading Safety Service
Implements critical safety features to prevent catastrophic losses and maximize profitability.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class TradingSafetyService:
    """
    Comprehensive trading safety system with multiple layers of protection.

    Features:
    - Position size limits
    - Daily loss limits (kill switch)
    - Consecutive loss protection
    - Minimum balance checks
    - Trade size validation
    - Slippage protection
    - Portfolio heat monitoring
    """

    def __init__(self):
        # Configuration
        self.max_position_size_pct = 0.10  # Max 10% per trade
        self.daily_loss_limit_pct = 0.05  # Kill switch at -5% daily loss
        self.max_consecutive_losses = 3  # Stop after 3 consecutive losses
        self.min_account_balance = 100.0  # Minimum balance in USD
        self.max_slippage_pct = 0.005  # Max 0.5% slippage
        self.max_portfolio_heat = 0.30  # Max 30% of portfolio at risk

        # State tracking
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.trades_today = []
        self.last_reset = datetime.now()
        self.kill_switch_active = False
        self.kill_switch_reason = None

        logger.info("Trading Safety Service initialized")

    def validate_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        account_balance: float,
        current_positions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Comprehensive trade validation before execution.

        Args:
            symbol: Trading pair (e.g., BTC/USDT)
            side: buy or sell
            quantity: Trade quantity
            price: Expected price
            account_balance: Current account balance in USD
            current_positions: Dict of current open positions

        Returns:
            Dict with 'valid' (bool), 'reason' (str), and 'adjustments' (dict)
        """
        # Reset daily tracking if new day
        self._check_daily_reset()

        # 1. Check kill switch
        if self.kill_switch_active:
            return {
                "valid": False,
                "reason": f"Kill switch active: {self.kill_switch_reason}",
                "adjustments": None,
            }

        # 2. Check minimum balance
        if account_balance < self.min_account_balance:
            return {
                "valid": False,
                "reason": f"Account balance ${account_balance:.2f} below minimum ${self.min_account_balance:.2f}",
                "adjustments": None,
            }

        # 3. Check position size limit
        trade_value = quantity * price
        position_size_pct = trade_value / account_balance

        if position_size_pct > self.max_position_size_pct:
            # Auto-adjust quantity to max allowed
            max_trade_value = account_balance * self.max_position_size_pct
            adjusted_quantity = max_trade_value / price

            logger.warning(
                f"Position size {position_size_pct:.2%} exceeds max {self.max_position_size_pct:.2%}. "
                f"Adjusting quantity from {quantity:.6f} to {adjusted_quantity:.6f}"
            )

            return {
                "valid": True,
                "reason": "Position size adjusted to stay within limits",
                "adjustments": {
                    "original_quantity": quantity,
                    "adjusted_quantity": adjusted_quantity,
                    "reason": f"Reduced to max {self.max_position_size_pct:.1%} position size",
                },
            }

        # 4. Check daily loss limit
        if self.daily_pnl < 0:
            daily_loss_pct = abs(self.daily_pnl) / account_balance
            if daily_loss_pct >= self.daily_loss_limit_pct:
                self._activate_kill_switch(
                    f"Daily loss limit reached: {daily_loss_pct:.2%} (limit: {self.daily_loss_limit_pct:.2%})"
                )
                return {
                    "valid": False,
                    "reason": f"Daily loss limit reached: {daily_loss_pct:.2%}",
                    "adjustments": None,
                }

        # 5. Check consecutive losses
        if self.consecutive_losses >= self.max_consecutive_losses:
            self._activate_kill_switch(
                f"Too many consecutive losses: {self.consecutive_losses}"
            )
            return {
                "valid": False,
                "reason": f"Consecutive loss limit reached: {self.consecutive_losses} losses",
                "adjustments": None,
            }

        # 6. Check portfolio heat (total exposure)
        current_exposure = self._calculate_portfolio_exposure(
            current_positions, account_balance
        )
        new_exposure = current_exposure + position_size_pct

        if new_exposure > self.max_portfolio_heat:
            return {
                "valid": False,
                "reason": f"Portfolio heat too high: {new_exposure:.2%} (max: {self.max_portfolio_heat:.2%})",
                "adjustments": None,
            }

        # All checks passed
        return {"valid": True, "reason": "Trade validation passed", "adjustments": None}

    def check_slippage(
        self, expected_price: float, actual_price: float, side: str
    ) -> Dict[str, Any]:
        """
        Check if slippage is within acceptable limits.

        Args:
            expected_price: Expected execution price
            actual_price: Actual execution price
            side: buy or sell

        Returns:
            Dict with 'acceptable' (bool), 'slippage_pct' (float), 'reason' (str)
        """
        if side == "buy":
            # For buys, higher actual price is bad
            slippage = (actual_price - expected_price) / expected_price
        else:
            # For sells, lower actual price is bad
            slippage = (expected_price - actual_price) / expected_price

        slippage_pct = abs(slippage)
        acceptable = slippage_pct <= self.max_slippage_pct

        if not acceptable:
            logger.warning(
                f"Slippage {slippage_pct:.2%} exceeds max {self.max_slippage_pct:.2%} "
                f"(expected: {expected_price:.2f}, actual: {actual_price:.2f})"
            )

        return {
            "acceptable": acceptable,
            "slippage_pct": slippage_pct,
            "slippage_value": slippage,
            "reason": (
                "Acceptable" if acceptable else f"Slippage {slippage_pct:.2%} too high"
            ),
        }

    def record_trade_result(
        self,
        trade_id: str,
        pnl: float,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
    ):
        """
        Record trade result and update safety tracking.

        Args:
            trade_id: Unique trade identifier
            pnl: Profit/loss from the trade
            symbol: Trading pair
            side: buy or sell
            quantity: Trade quantity
            price: Execution price
        """
        trade_record = {
            "trade_id": trade_id,
            "timestamp": datetime.now(),
            "pnl": pnl,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
        }

        self.trades_today.append(trade_record)
        self.daily_pnl += pnl

        # Update consecutive losses
        if pnl < 0:
            self.consecutive_losses += 1
            logger.warning(
                f"Loss recorded. Consecutive losses: {self.consecutive_losses}"
            )
        else:
            self.consecutive_losses = 0

        # Log daily stats
        logger.info(
            f"Trade result recorded: PnL ${pnl:.2f}, Daily PnL: ${self.daily_pnl:.2f}, "
            f"Consecutive losses: {self.consecutive_losses}, Trades today: {len(self.trades_today)}"
        )

    def get_safety_status(self) -> Dict[str, Any]:
        """
        Get current safety system status.

        Returns:
            Dict with safety metrics and status
        """
        return {
            "kill_switch_active": self.kill_switch_active,
            "kill_switch_reason": self.kill_switch_reason,
            "daily_pnl": self.daily_pnl,
            "trades_today": len(self.trades_today),
            "consecutive_losses": self.consecutive_losses,
            "last_reset": self.last_reset.isoformat(),
            "configuration": {
                "max_position_size_pct": self.max_position_size_pct,
                "daily_loss_limit_pct": self.daily_loss_limit_pct,
                "max_consecutive_losses": self.max_consecutive_losses,
                "min_account_balance": self.min_account_balance,
                "max_slippage_pct": self.max_slippage_pct,
                "max_portfolio_heat": self.max_portfolio_heat,
            },
        }

    def get_status(self) -> Dict[str, Any]:
        """
        Alias for get_safety_status() for API compatibility.

        Returns:
            Dict with safety metrics and status
        """
        return self.get_safety_status()

    def reset_kill_switch(self, admin_override: bool = False) -> Dict[str, Any]:
        """
        Reset the kill switch (requires admin override or new day).

        Args:
            admin_override: Whether this is an admin manual override

        Returns:
            Dict with reset status
        """
        if not admin_override:
            # Check if it's a new day
            if datetime.now().date() == self.last_reset.date():
                return {
                    "success": False,
                    "reason": "Can only reset kill switch on new day or with admin override",
                }

        old_reason = self.kill_switch_reason
        self.kill_switch_active = False
        self.kill_switch_reason = None

        logger.warning(
            f"Kill switch reset {'(admin override)' if admin_override else '(new day)'}: "
            f"Previous reason: {old_reason}"
        )

        return {
            "success": True,
            "previous_reason": old_reason,
            "reset_type": "admin_override" if admin_override else "new_day",
        }

    def update_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update safety configuration.

        Args:
            config: Dict of configuration parameters to update

        Returns:
            Dict with update status
        """
        updated = []

        if "max_position_size_pct" in config:
            self.max_position_size_pct = float(config["max_position_size_pct"])
            updated.append("max_position_size_pct")

        if "daily_loss_limit_pct" in config:
            self.daily_loss_limit_pct = float(config["daily_loss_limit_pct"])
            updated.append("daily_loss_limit_pct")

        if "max_consecutive_losses" in config:
            self.max_consecutive_losses = int(config["max_consecutive_losses"])
            updated.append("max_consecutive_losses")

        if "min_account_balance" in config:
            self.min_account_balance = float(config["min_account_balance"])
            updated.append("min_account_balance")

        if "max_slippage_pct" in config:
            self.max_slippage_pct = float(config["max_slippage_pct"])
            updated.append("max_slippage_pct")

        if "max_portfolio_heat" in config:
            self.max_portfolio_heat = float(config["max_portfolio_heat"])
            updated.append("max_portfolio_heat")

        logger.info(f"Safety configuration updated: {', '.join(updated)}")

        return {
            "success": True,
            "updated_fields": updated,
            "current_config": self.get_safety_status()["configuration"],
        }

    def _check_daily_reset(self):
        """Reset daily tracking if new day."""
        now = datetime.now()
        if now.date() > self.last_reset.date():
            logger.info(
                f"Daily reset: PnL ${self.daily_pnl:.2f}, Trades: {len(self.trades_today)}, "
                f"Consecutive losses: {self.consecutive_losses}"
            )
            self.daily_pnl = 0.0
            self.consecutive_losses = 0
            self.trades_today = []
            self.last_reset = now

            # Auto-reset kill switch on new day
            if self.kill_switch_active:
                old_reason = self.kill_switch_reason
                self.kill_switch_active = False
                self.kill_switch_reason = None
                logger.warning(
                    f"Kill switch auto-reset (new day): Previous reason: {old_reason}"
                )

    def _activate_kill_switch(self, reason: str):
        """Activate the kill switch."""
        self.kill_switch_active = True
        self.kill_switch_reason = reason
        logger.error(f"🚨 KILL SWITCH ACTIVATED: {reason}")

    def _calculate_portfolio_exposure(
        self, positions: Dict[str, Any], account_balance: float
    ) -> float:
        """
        Calculate total portfolio exposure as percentage of account balance.

        Args:
            positions: Dict of current positions
            account_balance: Total account balance

        Returns:
            Float representing total exposure as decimal (e.g., 0.25 = 25%)
        """
        total_exposure = 0.0

        for symbol, position in positions.items():
            if "value" in position:
                exposure = position["value"] / account_balance
                total_exposure += exposure

        return total_exposure


# Singleton instance
_safety_service_instance = None


def get_trading_safety_service() -> TradingSafetyService:
    """Get or create the trading safety service singleton."""
    global _safety_service_instance
    if _safety_service_instance is None:
        _safety_service_instance = TradingSafetyService()
    return _safety_service_instance
