"""
Stop-Loss and Take-Profit Management Service
Handles automatic order execution for risk management
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class OrderType(str, Enum):
    """Order types for stop-loss/take-profit"""

    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"


class StopLossTakeProfitService:
    """
    Service for managing stop-loss and take-profit orders.

    Features:
    - Automatic stop-loss placement
    - Take-profit targets
    - Trailing stop-loss
    - Position-based triggers
    - Slippage protection
    """

    def __init__(self):
        # Active stop-loss/take-profit orders
        self.active_orders: Dict[str, Dict[str, Any]] = {}

        # Trailing stop state
        self.trailing_stops: Dict[str, Dict[str, Any]] = {}

        logger.info("Stop-Loss/Take-Profit Service initialized")

    def calculate_stop_loss_price(
        self, entry_price: float, side: str, stop_loss_pct: float
    ) -> float:
        """
        Calculate stop-loss price based on entry price and percentage.

        Args:
            entry_price: Entry price of position
            side: Trade side (buy/sell)
            stop_loss_pct: Stop-loss percentage (e.g., 0.02 for 2%)

        Returns:
            Stop-loss trigger price
        """
        if side == "buy":
            # For long positions, stop-loss is below entry
            stop_price = entry_price * (1 - stop_loss_pct)
        else:
            # For short positions, stop-loss is above entry
            stop_price = entry_price * (1 + stop_loss_pct)

        return stop_price

    def calculate_take_profit_price(
        self, entry_price: float, side: str, take_profit_pct: float
    ) -> float:
        """
        Calculate take-profit price based on entry price and percentage.

        Args:
            entry_price: Entry price of position
            side: Trade side (buy/sell)
            take_profit_pct: Take-profit percentage (e.g., 0.05 for 5%)

        Returns:
            Take-profit trigger price
        """
        if side == "buy":
            # For long positions, take-profit is above entry
            target_price = entry_price * (1 + take_profit_pct)
        else:
            # For short positions, take-profit is below entry
            target_price = entry_price * (1 - take_profit_pct)

        return target_price

    def create_stop_loss(
        self,
        position_id: str,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        stop_loss_pct: float,
        user_id: str,
        bot_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a stop-loss order for a position.

        Args:
            position_id: Unique position identifier
            symbol: Trading pair
            side: Original trade side (buy/sell)
            quantity: Position quantity
            entry_price: Entry price
            stop_loss_pct: Stop-loss percentage
            user_id: User identifier
            bot_id: Optional bot identifier

        Returns:
            Dict with stop-loss order details
        """
        stop_price = self.calculate_stop_loss_price(entry_price, side, stop_loss_pct)

        # Determine exit side (opposite of entry)
        exit_side = "sell" if side == "buy" else "buy"

        order = {
            "order_id": f"sl_{position_id}",
            "position_id": position_id,
            "type": OrderType.STOP_LOSS,
            "symbol": symbol,
            "side": exit_side,
            "quantity": quantity,
            "entry_price": entry_price,
            "trigger_price": stop_price,
            "stop_loss_pct": stop_loss_pct,
            "user_id": user_id,
            "bot_id": bot_id,
            "created_at": datetime.now().isoformat(),
            "status": "active",
        }

        self.active_orders[position_id] = order

        logger.info(
            f"Stop-loss created for {symbol} position {position_id}: "
            f"Entry ${entry_price:.2f}, Stop ${stop_price:.2f} ({stop_loss_pct:.1%})"
        )

        return order

    def create_take_profit(
        self,
        position_id: str,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        take_profit_pct: float,
        user_id: str,
        bot_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a take-profit order for a position.

        Args:
            position_id: Unique position identifier
            symbol: Trading pair
            side: Original trade side (buy/sell)
            quantity: Position quantity
            entry_price: Entry price
            take_profit_pct: Take-profit percentage
            user_id: User identifier
            bot_id: Optional bot identifier

        Returns:
            Dict with take-profit order details
        """
        target_price = self.calculate_take_profit_price(
            entry_price, side, take_profit_pct
        )

        # Determine exit side (opposite of entry)
        exit_side = "sell" if side == "buy" else "buy"

        order = {
            "order_id": f"tp_{position_id}",
            "position_id": position_id,
            "type": OrderType.TAKE_PROFIT,
            "symbol": symbol,
            "side": exit_side,
            "quantity": quantity,
            "entry_price": entry_price,
            "trigger_price": target_price,
            "take_profit_pct": take_profit_pct,
            "user_id": user_id,
            "bot_id": bot_id,
            "created_at": datetime.now().isoformat(),
            "status": "active",
        }

        # Store alongside stop-loss (use tp_ prefix)
        tp_key = f"tp_{position_id}"
        self.active_orders[tp_key] = order

        logger.info(
            f"Take-profit created for {symbol} position {position_id}: "
            f"Entry ${entry_price:.2f}, Target ${target_price:.2f} ({take_profit_pct:.1%})"
        )

        return order

    def create_trailing_stop(
        self,
        position_id: str,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        trailing_pct: float,
        user_id: str,
        bot_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a trailing stop-loss order.

        Args:
            position_id: Unique position identifier
            symbol: Trading pair
            side: Original trade side (buy/sell)
            quantity: Position quantity
            entry_price: Entry price
            trailing_pct: Trailing percentage (e.g., 0.03 for 3%)
            user_id: User identifier
            bot_id: Optional bot identifier

        Returns:
            Dict with trailing stop order details
        """
        # Initial stop price
        initial_stop = self.calculate_stop_loss_price(entry_price, side, trailing_pct)

        # Determine exit side
        exit_side = "sell" if side == "buy" else "buy"

        order = {
            "order_id": f"trail_{position_id}",
            "position_id": position_id,
            "type": OrderType.TRAILING_STOP,
            "symbol": symbol,
            "side": exit_side,
            "quantity": quantity,
            "entry_price": entry_price,
            "trigger_price": initial_stop,
            "trailing_pct": trailing_pct,
            "highest_price": entry_price if side == "buy" else None,
            "lowest_price": entry_price if side == "sell" else None,
            "user_id": user_id,
            "bot_id": bot_id,
            "created_at": datetime.now().isoformat(),
            "status": "active",
        }

        self.trailing_stops[position_id] = order

        logger.info(
            f"Trailing stop created for {symbol} position {position_id}: "
            f"Entry ${entry_price:.2f}, Initial stop ${initial_stop:.2f} (trails by {trailing_pct:.1%})"
        )

        return order

    def update_trailing_stop(
        self, position_id: str, current_price: float
    ) -> Optional[Dict[str, Any]]:
        """
        Update trailing stop-loss based on current price.

        Args:
            position_id: Position identifier
            current_price: Current market price

        Returns:
            Updated order if stop was adjusted, None otherwise
        """
        if position_id not in self.trailing_stops:
            return None

        order = self.trailing_stops[position_id]
        side = "buy" if order["side"] == "sell" else "sell"  # Original side
        trailing_pct = order["trailing_pct"]

        updated = False

        if side == "buy":
            # Long position - update if price makes new high
            if current_price > order["highest_price"]:
                order["highest_price"] = current_price
                new_stop = current_price * (1 - trailing_pct)

                if new_stop > order["trigger_price"]:
                    order["trigger_price"] = new_stop
                    updated = True
                    logger.info(
                        f"Trailing stop updated for position {position_id}: "
                        f"New high ${current_price:.2f}, Stop moved to ${new_stop:.2f}"
                    )
        else:
            # Short position - update if price makes new low
            if current_price < order["lowest_price"]:
                order["lowest_price"] = current_price
                new_stop = current_price * (1 + trailing_pct)

                if new_stop < order["trigger_price"]:
                    order["trigger_price"] = new_stop
                    updated = True
                    logger.info(
                        f"Trailing stop updated for position {position_id}: "
                        f"New low ${current_price:.2f}, Stop moved to ${new_stop:.2f}"
                    )

        return order if updated else None

    def check_triggers(self, current_prices: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Check if any stop-loss/take-profit orders should be triggered.

        Args:
            current_prices: Dict mapping symbols to current prices

        Returns:
            List of orders that should be executed
        """
        triggered_orders = []

        # Check regular stop-loss/take-profit orders
        for order_id, order in list(self.active_orders.items()):
            symbol = order["symbol"]
            if symbol not in current_prices:
                continue

            current_price = current_prices[symbol]
            trigger_price = order["trigger_price"]

            triggered = False

            if order["type"] == OrderType.STOP_LOSS:
                # Stop-loss triggers when price crosses below (long) or above (short)
                if order["side"] == "sell":
                    # Long position stop-loss
                    triggered = current_price <= trigger_price
                else:
                    # Short position stop-loss
                    triggered = current_price >= trigger_price

            elif order["type"] == OrderType.TAKE_PROFIT:
                # Take-profit triggers when price crosses above (long) or below (short)
                if order["side"] == "sell":
                    # Long position take-profit
                    triggered = current_price >= trigger_price
                else:
                    # Short position take-profit
                    triggered = current_price <= trigger_price

            if triggered:
                order["triggered_at"] = datetime.now().isoformat()
                order["triggered_price"] = current_price
                order["status"] = "triggered"
                triggered_orders.append(order)

                logger.warning(
                    f"{order['type'].upper()} triggered for {symbol}: "
                    f"Current ${current_price:.2f}, Trigger ${trigger_price:.2f}"
                )

        # Check trailing stops
        for position_id, order in list(self.trailing_stops.items()):
            symbol = order["symbol"]
            if symbol not in current_prices:
                continue

            current_price = current_prices[symbol]

            # Update trailing stop first
            self.update_trailing_stop(position_id, current_price)

            # Check if triggered
            trigger_price = order["trigger_price"]

            if order["side"] == "sell":
                # Long position trailing stop
                triggered = current_price <= trigger_price
            else:
                # Short position trailing stop
                triggered = current_price >= trigger_price

            if triggered:
                order["triggered_at"] = datetime.now().isoformat()
                order["triggered_price"] = current_price
                order["status"] = "triggered"
                triggered_orders.append(order)

                logger.warning(
                    f"TRAILING STOP triggered for {symbol}: "
                    f"Current ${current_price:.2f}, Stop ${trigger_price:.2f}"
                )

        return triggered_orders

    def cancel_order(self, order_id: str) -> bool:
        """Cancel a stop-loss/take-profit order."""
        if order_id in self.active_orders:
            order = self.active_orders.pop(order_id)
            logger.info(f"Cancelled {order['type']} order {order_id}")
            return True

        # Check if it's a position_id for trailing stop
        if order_id in self.trailing_stops:
            order = self.trailing_stops.pop(order_id)
            logger.info(f"Cancelled trailing stop for position {order_id}")
            return True

        return False

    def get_active_orders(
        self, user_id: Optional[str] = None, bot_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all active stop-loss/take-profit orders."""
        orders = list(self.active_orders.values()) + list(self.trailing_stops.values())

        if user_id:
            orders = [o for o in orders if o.get("user_id") == user_id]

        if bot_id:
            orders = [o for o in orders if o.get("bot_id") == bot_id]

        return orders


# Singleton instance
_sl_tp_service_instance = None


def get_sl_tp_service() -> StopLossTakeProfitService:
    """Get or create the stop-loss/take-profit service singleton."""
    global _sl_tp_service_instance
    if _sl_tp_service_instance is None:
        _sl_tp_service_instance = StopLossTakeProfitService()
    return _sl_tp_service_instance
