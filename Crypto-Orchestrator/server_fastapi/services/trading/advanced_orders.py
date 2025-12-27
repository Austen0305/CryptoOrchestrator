"""
Advanced Order Management Service
Handles stop-loss, take-profit, trailing stops, and OCO orders
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.order import Order, OrderType, OrderStatus
from ...repositories.order_repository import OrderRepository

# Exchange services removed - using blockchain/DEX only
# Advanced orders on DEX may require different implementation (smart contracts or position monitoring)

logger = logging.getLogger(__name__)


class AdvancedOrdersService:
    """Service for managing advanced order types"""

    def __init__(
        self,
        db: AsyncSession,
        order_repository: Optional[OrderRepository] = None,
    ):
        # ✅ Repository injected via dependency injection (Service Layer Pattern)
        self.order_repository = order_repository or OrderRepository()
        self.db = db  # Keep db for transaction handling

    async def create_stop_loss_order(
        self,
        user_id: int,
        symbol: str,
        side: str,
        amount: float,
        stop_price: float,
        limit_price: Optional[float] = None,
        chain_id: int = 1,  # Default to Ethereum
        mode: str = "paper",
    ) -> Order:
        """
        Create a stop-loss order

        Args:
            user_id: User ID
            symbol: Trading pair (e.g., "BTC/USD")
            side: "buy" or "sell"
            amount: Order amount
            stop_price: Price at which to trigger the stop
            limit_price: Optional limit price (for stop-limit orders)
            exchange: Exchange name
            mode: Trading mode ("paper" or "real")

        Returns:
            Created Order
        """
        # ✅ Business logic: Determine order type
        order_type = OrderType.STOP_LIMIT if limit_price else OrderType.STOP

        # ✅ Business logic: Create order data
        # ✅ Data access delegated to repository
        order = await self.order_repository.create_order(
            self.db,
            {
                "user_id": user_id,
                "chain_id": chain_id,
                "symbol": symbol,
                "pair": symbol,
                "side": side,
                "order_type": order_type.value,
                "status": OrderStatus.PENDING.value,
                "amount": amount,
                "price": limit_price,
                "stop_price": stop_price,
                "mode": mode,
                "time_in_force": "GTC",
            },
        )

        logger.info(
            f"Created stop-loss order {order.id} for {symbol} at {stop_price}",
            extra={
                "order_id": order.id,
                "user_id": user_id,
                "symbol": symbol,
                "stop_price": stop_price,
            },
        )
        return order

    async def create_take_profit_order(
        self,
        user_id: int,
        symbol: str,
        side: str,
        amount: float,
        take_profit_price: float,
        limit_price: Optional[float] = None,
        chain_id: int = 1,  # Default to Ethereum
        mode: str = "paper",
    ) -> Order:
        """
        Create a take-profit order

        Args:
            user_id: User ID
            symbol: Trading pair
            side: "buy" or "sell"
            amount: Order amount
            take_profit_price: Price at which to take profit
            limit_price: Optional limit price
            exchange: Exchange name
            mode: Trading mode

        Returns:
            Created Order
        """
        # ✅ Business logic: Determine order type
        order_type = (
            OrderType.TAKE_PROFIT_LIMIT if limit_price else OrderType.TAKE_PROFIT
        )

        # ✅ Business logic: Create order data
        # ✅ Data access delegated to repository
        order = await self.order_repository.create_order(
            self.db,
            {
                "user_id": user_id,
                "chain_id": chain_id,
                "symbol": symbol,
                "pair": symbol,
                "side": side,
                "order_type": order_type.value,
                "status": OrderStatus.PENDING.value,
                "amount": amount,
                "price": limit_price,
                "take_profit_price": take_profit_price,
                "mode": mode,
                "time_in_force": "GTC",
            },
        )

        logger.info(
            f"Created take-profit order {order.id} for {symbol} at {take_profit_price}",
            extra={
                "order_id": order.id,
                "user_id": user_id,
                "symbol": symbol,
                "take_profit_price": take_profit_price,
            },
        )
        return order

    async def create_trailing_stop_order(
        self,
        user_id: int,
        symbol: str,
        side: str,
        amount: float,
        trailing_stop_percent: Optional[float] = None,
        trailing_stop_amount: Optional[float] = None,
        chain_id: int = 1,  # Default to Ethereum
        mode: str = "paper",
    ) -> Order:
        """
        Create a trailing stop order

        Args:
            user_id: User ID
            symbol: Trading pair
            side: "buy" or "sell"
            amount: Order amount
            trailing_stop_percent: Trailing stop as percentage (e.g., 2.0 for 2%)
            trailing_stop_amount: Trailing stop as fixed amount
            exchange: Exchange name
            mode: Trading mode

        Returns:
            Created Order
        """
        # ✅ Business logic: Validate trailing stop parameters
        if not trailing_stop_percent and not trailing_stop_amount:
            raise ValueError(
                "Either trailing_stop_percent or trailing_stop_amount must be provided"
            )

        # ✅ Business logic: Create order data
        # ✅ Data access delegated to repository
        order = await self.order_repository.create_order(
            self.db,
            {
                "user_id": user_id,
                "chain_id": chain_id,
                "symbol": symbol,
                "pair": symbol,
                "side": side,
                "order_type": OrderType.TRAILING_STOP.value,
                "status": OrderStatus.PENDING.value,
                "amount": amount,
                "trailing_stop_percent": trailing_stop_percent,
                "trailing_stop_amount": trailing_stop_amount,
                "mode": mode,
                "time_in_force": "GTC",
            },
        )

        logger.info(
            f"Created trailing stop order {order.id} for {symbol}",
            extra={"order_id": order.id, "user_id": user_id, "symbol": symbol},
        )
        return order

    async def create_oco_order(
        self,
        user_id: int,
        symbol: str,
        side: str,
        amount: float,
        stop_price: float,
        take_profit_price: float,
        chain_id: int = 1,  # Default to Ethereum
        mode: str = "paper",
    ) -> List[Order]:
        """
        Create an OCO (One-Cancels-Other) order
        Combines stop-loss and take-profit orders

        Returns:
            List of two orders (stop-loss and take-profit)
        """
        # Create stop-loss order
        stop_order = await self.create_stop_loss_order(
            user_id=user_id,
            symbol=symbol,
            side=side,
            amount=amount,
            stop_price=stop_price,
            chain_id=chain_id,
            mode=mode,
        )

        # Create take-profit order
        take_profit_order = await self.create_take_profit_order(
            user_id=user_id,
            symbol=symbol,
            side=side,
            amount=amount,
            take_profit_price=take_profit_price,
            chain_id=chain_id,
            mode=mode,
        )

        # ✅ Business logic: Link orders (store reference in bot_id field)
        # ✅ Data access delegated to repository
        await self.order_repository.update_order(
            self.db, stop_order.id, {"bot_id": f"oco_{take_profit_order.id}"}
        )
        await self.order_repository.update_order(
            self.db, take_profit_order.id, {"bot_id": f"oco_{stop_order.id}"}
        )

        # Refresh orders to get updated bot_id
        stop_order = await self.order_repository.get_by_id(self.db, stop_order.id)
        take_profit_order = await self.order_repository.get_by_id(
            self.db, take_profit_order.id
        )

        logger.info(
            f"Created OCO order pair: stop={stop_order.id}, take_profit={take_profit_order.id}",
            extra={
                "stop_order_id": stop_order.id,
                "take_profit_order_id": take_profit_order.id,
                "user_id": user_id,
            },
        )
        return [stop_order, take_profit_order]

    async def update_trailing_stop(
        self,
        order_id: int,
        current_price: float,
    ) -> Optional[Order]:
        """
        Update trailing stop order based on current price

        Args:
            order_id: Order ID
            current_price: Current market price

        Returns:
            Updated Order or None if order should be executed
        """
        # ✅ Data access delegated to repository
        order = await self.order_repository.get_by_id(self.db, order_id)

        if not order or order.order_type != OrderType.TRAILING_STOP.value:
            return None

        if order.status != OrderStatus.OPEN.value:
            return order

        # ✅ Business logic: Update highest/lowest price and calculate stop price
        update_data = {}

        if order.side == "sell":
            # For sell orders, track highest price
            if order.highest_price is None or current_price > order.highest_price:
                update_data["highest_price"] = current_price

                # ✅ Business logic: Calculate stop price
                if order.trailing_stop_percent:
                    stop_price = current_price * (1 - order.trailing_stop_percent / 100)
                elif order.trailing_stop_amount:
                    stop_price = current_price - order.trailing_stop_amount
                else:
                    return order

                update_data["stop_price"] = stop_price

                # ✅ Business logic: Check if stop should trigger
                if current_price <= stop_price:
                    update_data["status"] = (
                        OrderStatus.PENDING.value
                    )  # Trigger execution
                    logger.info(
                        f"Trailing stop {order_id} triggered at {current_price}",
                        extra={
                            "order_id": order_id,
                            "current_price": current_price,
                            "stop_price": stop_price,
                        },
                    )
        else:
            # For buy orders, track lowest price
            if order.lowest_price is None or current_price < order.lowest_price:
                update_data["lowest_price"] = current_price

                # ✅ Business logic: Calculate stop price
                if order.trailing_stop_percent:
                    stop_price = current_price * (1 + order.trailing_stop_percent / 100)
                elif order.trailing_stop_amount:
                    stop_price = current_price + order.trailing_stop_amount
                else:
                    return order

                update_data["stop_price"] = stop_price

                # ✅ Business logic: Check if stop should trigger
                if current_price >= stop_price:
                    update_data["status"] = (
                        OrderStatus.PENDING.value
                    )  # Trigger execution
                    logger.info(
                        f"Trailing stop {order_id} triggered at {current_price}",
                        extra={
                            "order_id": order_id,
                            "current_price": current_price,
                            "stop_price": stop_price,
                        },
                    )

        if update_data:
            # ✅ Data access delegated to repository
            order = await self.order_repository.update_order(
                self.db, order_id, update_data
            )

        return order

    async def check_and_execute_advanced_orders(
        self,
        symbol: str,
        current_price: float,
        chain_id: int = 1,  # Blockchain chain ID
    ) -> List[Order]:
        """
        Check all pending advanced orders and execute if conditions are met

        Args:
            symbol: Trading pair to check
            current_price: Current market price
            chain_id: Blockchain chain ID for DEX execution

        Returns:
            List of executed orders
        """
        from ...services.trading.dex_trading_service import DEXTradingService

        dex_service = DEXTradingService()

        # ✅ Data access delegated to repository
        orders = await self.order_repository.get_by_symbol_and_status(
            self.db,
            symbol,
            [OrderStatus.PENDING.value, OrderStatus.OPEN.value],
            order_types=[
                OrderType.STOP.value,
                OrderType.STOP_LIMIT.value,
                OrderType.TAKE_PROFIT.value,
                OrderType.TAKE_PROFIT_LIMIT.value,
                OrderType.TRAILING_STOP.value,
            ],
            chain_id=chain_id,
        )

        executed_orders = []

        for order in orders:
            should_execute = False

            # Check stop-loss orders
            if order.order_type in [OrderType.STOP.value, OrderType.STOP_LIMIT.value]:
                if (
                    order.side == "sell"
                    and order.stop_price
                    and current_price <= order.stop_price
                ):
                    should_execute = True
                elif (
                    order.side == "buy"
                    and order.stop_price
                    and current_price >= order.stop_price
                ):
                    should_execute = True

            # Check take-profit orders
            elif order.order_type in [
                OrderType.TAKE_PROFIT.value,
                OrderType.TAKE_PROFIT_LIMIT.value,
            ]:
                if (
                    order.side == "sell"
                    and order.take_profit_price
                    and current_price >= order.take_profit_price
                ):
                    should_execute = True
                elif (
                    order.side == "buy"
                    and order.take_profit_price
                    and current_price <= order.take_profit_price
                ):
                    should_execute = True

            # Update trailing stops
            elif order.order_type == OrderType.TRAILING_STOP.value:
                updated_order = await self.update_trailing_stop(order.id, current_price)
                if updated_order and updated_order.status == OrderStatus.PENDING.value:
                    should_execute = True
                    order = updated_order

            if should_execute:
                try:
                    # ✅ Business logic: Execute the order
                    transaction_hash = None

                    if order.mode == "paper":
                        # Paper trading - simulate execution
                        status = OrderStatus.FILLED.value
                    else:
                        # Real trading - execute via DEX
                        # Note: Advanced orders on DEX may require smart contracts or position monitoring
                        # For now, execute as a market order via DEX
                        try:
                            # Convert symbol to token addresses
                            sell_token = (
                                symbol.split("/")[0] if "/" in symbol else symbol
                            )
                            buy_token = (
                                symbol.split("/")[1] if "/" in symbol else "USDC"
                            )

                            # Execute DEX swap (simplified - in production, handle order types properly)
                            swap_result = await dex_service.execute_custodial_swap(
                                user_id=order.user_id,
                                sell_token=(
                                    sell_token if order.side == "sell" else buy_token
                                ),
                                buy_token=(
                                    buy_token if order.side == "sell" else sell_token
                                ),
                                sell_amount=str(
                                    int(order.amount * 1e18)
                                ),  # Convert to wei
                                chain_id=order.chain_id,
                                slippage_percentage=0.5,
                                user_tier="free",  # Get from user profile
                                db=self.db,
                            )

                            if swap_result and swap_result.get("success"):
                                status = OrderStatus.FILLED.value
                                transaction_hash = swap_result.get("transaction_hash")
                            else:
                                status = OrderStatus.REJECTED.value
                        except Exception as dex_error:
                            logger.error(
                                f"DEX execution failed for order {order.id}: {dex_error}",
                                exc_info=True,
                                extra={
                                    "order_id": order.id,
                                    "symbol": symbol,
                                    "user_id": order.user_id,
                                },
                            )
                            status = OrderStatus.REJECTED.value

                    # ✅ Data access delegated to repository
                    await self.order_repository.update_status(
                        self.db,
                        order.id,
                        status,
                        filled_amount=(
                            order.amount if status == OrderStatus.FILLED.value else None
                        ),
                        average_fill_price=(
                            current_price
                            if status == OrderStatus.FILLED.value
                            else None
                        ),
                        transaction_hash=transaction_hash,
                    )

                    # Refresh order to get updated status
                    order = await self.order_repository.get_by_id(self.db, order.id)
                    executed_orders.append(order)

                    logger.info(
                        f"Executed advanced order {order.id} for {symbol} at {current_price}",
                        extra={
                            "order_id": order.id,
                            "symbol": symbol,
                            "current_price": current_price,
                            "status": status,
                        },
                    )

                    # ✅ Business logic: If this is part of an OCO, cancel the other order
                    if order.bot_id and order.bot_id.startswith("oco_"):
                        other_order_id = int(order.bot_id.split("_")[1])
                        # ✅ Data access delegated to repository
                        other_order = await self.order_repository.get_by_id(
                            self.db, other_order_id
                        )
                        if other_order and other_order.status in [
                            OrderStatus.PENDING.value,
                            OrderStatus.OPEN.value,
                        ]:
                            await self.order_repository.update_status(
                                self.db, other_order_id, OrderStatus.CANCELLED.value
                            )
                            logger.info(
                                f"Cancelled OCO partner order {other_order_id}",
                                extra={
                                    "order_id": order.id,
                                    "other_order_id": other_order_id,
                                },
                            )

                except Exception as e:
                    logger.error(
                        f"Error executing advanced order {order.id}: {e}",
                        exc_info=True,
                        extra={"order_id": order.id, "symbol": symbol},
                    )
                    # ✅ Data access delegated to repository
                    await self.order_repository.update_status(
                        self.db, order.id, OrderStatus.REJECTED.value
                    )

        return executed_orders
