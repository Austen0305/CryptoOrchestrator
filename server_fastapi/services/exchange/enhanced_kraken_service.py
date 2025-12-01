"""
Enhanced Kraken service with additional safety and monitoring features
Migrated from TypeScript enhancedKrakenService.ts
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .kraken_service import KrakenService, MarketData, TradingPair, KrakenFee
from ..monitoring.safety_monitor import SafetyMonitor
from ..logger_service import LoggerService

logger = LoggerService()


@dataclass
class RateLimitInfo:
    remaining: int
    reset: int


class EnhancedKrakenService(KrakenService):
    """Enhanced Kraken service with advanced features and safety monitoring"""

    def __init__(self):
        super().__init__()
        self.rate_limit_info = RateLimitInfo(remaining=100, reset=int(asyncio.get_event_loop().time() * 1000) + 3600000)
        self.last_order_check = {}
        self.ORDER_CHECK_TIMEOUT = 30000  # 30 seconds
        self.safety_monitor = SafetyMonitor()
        self.setup_rate_limit_tracking()

    def setup_rate_limit_tracking(self) -> None:
        """Track rate limits after each API call"""
        if self.exchange and hasattr(self.exchange, 'request'):
            original_request = self.exchange.request
            async def tracked_request(*args, **kwargs):
                try:
                    response = await original_request(*args, **kwargs)
                    self.update_rate_limits(response.headers if hasattr(response, 'headers') else {})
                    return response
                except Exception as error:
                    self.handle_api_error(error)
                    raise error

            self.exchange.request = tracked_request

    def update_rate_limits(self, headers: Dict[str, Any]) -> None:
        """Update rate limit information from response headers"""
        remaining = int(headers.get('x-ratelimit-remaining', '100'))
        reset = int(headers.get('x-ratelimit-reset', str(int(asyncio.get_event_loop().time() * 1000) + 3600000)))

        self.rate_limit_info = RateLimitInfo(remaining=remaining, reset=reset)

        if remaining < 10:
            logger.warning(f"API rate limit low: {remaining} calls remaining")
            self.safety_monitor.emit('lowApiQuota', remaining)

    def handle_api_error(self, error: Exception) -> None:
        """Handle API errors with appropriate logging and safety measures"""
        error_message = str(error)
        logger.error(f"Kraken API error: {error_message}")

        if self.is_rate_limit_error(error):
            self.safety_monitor.activate_emergency_stop('Rate limit exceeded')
        elif self.is_connection_error(error):
            self.safety_monitor.emit('connectionError', error_message)

    def is_rate_limit_error(self, error: Exception) -> bool:
        """Check if error is a rate limit error"""
        error_str = str(error).lower()
        return 'rate limit exceeded' in error_str or 'eapi_rate_limit' in error_str

    def is_connection_error(self, error: Exception) -> bool:
        """Check if error is a connection error"""
        error_str = str(error).lower()
        return any(code in error_str for code in ['etimedout', 'econnreset', 'econnrefused'])

    async def validate_order_parameters(self, order: Dict[str, Any]) -> bool:
        """Validate order parameters before execution"""
        try:
            symbol = order.get('symbol')
            order_type = order.get('type')
            side = order.get('side')
            amount = order.get('amount')
            price = order.get('price')

            if not all([symbol, order_type, side, amount]):
                raise ValueError("Missing required order parameters")

            # Check minimum order size
            if self.exchange:
                market = await self.exchange.loadMarket(symbol)
                if amount < market['limits']['amount']['min']:
                    raise ValueError(f"Order amount {amount} below minimum {market['limits']['amount']['min']}")

                # Check price precision
                if price and market.get('precision', {}).get('price'):
                    correct_price = self.exchange.priceToPrecision(symbol, price)
                    if str(correct_price) != str(price):
                        raise ValueError(f"Invalid price precision. Use {correct_price}")

                # Check available balance
                balance = await self.exchange.fetchBalance()
                required_currency = market['quote'] if side == 'buy' else market['base']
                available = balance.get(required_currency, {}).get('free', 0)

                if side == 'buy' and price and available < price * amount:
                    raise ValueError(f"Insufficient {required_currency} balance")
                elif side == 'sell' and available < amount:
                    raise ValueError(f"Insufficient {required_currency} balance")

            return True
        except Exception as error:
            logger.error(f"Order validation failed: {str(error)}")
            return False

    async def execute_order_with_safety(self, order_params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute order with safety checks"""
        if not self.is_connected():
            raise ValueError('Exchange connection not established')

        if not self.safety_monitor.is_system_healthy():
            raise ValueError('System health check failed')

        is_valid = await self.validate_order_parameters(order_params)
        if not is_valid:
            raise ValueError('Order validation failed')

        try:
            if not self.exchange:
                raise ValueError('Exchange client not initialized')

            order = await self.exchange.createOrder(
                order_params['symbol'],
                order_params['type'],
                order_params['side'],
                order_params['amount'],
                order_params.get('price')
            )

            # Start monitoring the order
            self.monitor_order(order['id'])

            return {
                'success': True,
                'orderId': order['id'],
                'executedPrice': order.get('price'),
                'executedAmount': order.get('amount'),
                'status': order.get('status'),
            }
        except Exception as error:
            logger.error(f"Order execution failed: {str(error)}")
            raise error

    def monitor_order(self, order_id: str) -> None:
        """Monitor order status asynchronously"""
        async def check_order():
            try:
                if not self.exchange:
                    return

                order = await self.exchange.fetchOrder(order_id)

                if order['status'] == 'closed':
                    self.last_order_check.pop(order_id, None)
                    logger.info(f"Order {order_id} completed successfully")
                elif order['status'] in ['canceled', 'expired']:
                    self.last_order_check.pop(order_id, None)
                    logger.warning(f"Order {order_id} {order['status']}")
                else:
                    last_check = self.last_order_check.get(order_id, int(asyncio.get_event_loop().time() * 1000))

                    if int(asyncio.get_event_loop().time() * 1000) - last_check > self.ORDER_CHECK_TIMEOUT:
                        logger.warning(f"Order {order_id} pending for too long")
                        self.safety_monitor.emit('orderTimeout', order_id)

                    self.last_order_check[order_id] = int(asyncio.get_event_loop().time() * 1000)
                    # Schedule next check in 5 seconds
                    asyncio.get_event_loop().call_later(5, lambda: asyncio.create_task(check_order()))
            except Exception as error:
                logger.error(f"Order monitoring failed: {str(error)}")
                self.safety_monitor.emit('orderMonitoringError', {'orderId': order_id, 'error': str(error)})

        # Start monitoring
        asyncio.create_task(check_order())

    async def get_api_quota(self) -> RateLimitInfo:
        """Get current API quota information"""
        return RateLimitInfo(remaining=self.rate_limit_info.remaining, reset=self.rate_limit_info.reset)

    async def get_advanced_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get advanced market data including indicators"""
        # Implementation would include technical indicators, volume analysis, etc.
        # For now, return basic market data
        market_data = await self.get_market_price(symbol)
        return {'symbol': symbol, 'price': market_data} if market_data else None

    async def execute_smart_order(self, symbol: str, side: str, quantity: float) -> bool:
        """Execute smart order with optimal timing"""
        # Implementation would include slippage protection, optimal entry timing, etc.
        # For now, execute as market order
        try:
            await self.place_order(symbol, side, 'market', quantity)
            return True
        except Exception:
            return False

    async def get_portfolio_analysis(self) -> Dict[str, Any]:
        """Get portfolio analysis data"""
        balance = await self.get_balance()
        # Implementation would include P&L analysis, risk metrics, etc.
        return {'balance': balance}

    async def risk_adjusted_positioning(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Calculate risk-adjusted position sizing"""
        # Implementation would include volatility-based sizing, risk limits, etc.
        # For now, return basic position size
        balance = await self.get_balance()
        usd_balance = balance.get('USD', 0)
        if usd_balance > 0:
            risk_amount = usd_balance * 0.01  # 1% risk
            current_price = await self.get_market_price(symbol)
            if current_price:
                position_size = risk_amount / current_price
                return {'position_size': position_size, 'risk_amount': risk_amount}
        return None


# Create singleton instance
enhanced_kraken_service = EnhancedKrakenService()