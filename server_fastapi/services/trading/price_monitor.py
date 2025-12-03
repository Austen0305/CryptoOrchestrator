"""
Price Monitoring Service
Continuously monitors market prices and triggers stop-loss/take-profit orders
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PriceMonitoringService:
    """
    Service that continuously monitors market prices and triggers SL/TP orders.
    
    Features:
    - Real-time price monitoring
    - Automatic trigger detection
    - Order execution on triggers
    - Configurable monitoring interval
    - Support for multiple symbols
    """
    
    def __init__(self):
        self.monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.monitored_symbols: set = set()
        self.check_interval = 5  # Check every 5 seconds
        
        logger.info("Price Monitoring Service initialized")
    
    async def start_monitoring(self, check_interval: int = 5):
        """
        Start the price monitoring loop.
        
        Args:
            check_interval: How often to check prices (in seconds)
        """
        if self.monitoring:
            logger.warning("Price monitoring already running")
            return
        
        self.check_interval = check_interval
        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info(f"Price monitoring started (checking every {check_interval}s)")
    
    async def stop_monitoring(self):
        """Stop the price monitoring loop."""
        if not self.monitoring:
            return
        
        self.monitoring = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Price monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop that checks prices and triggers orders."""
        logger.info("Price monitoring loop started")
        
        while self.monitoring:
            try:
                await self._check_all_triggers()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                # Continue monitoring despite errors
                await asyncio.sleep(self.check_interval)
    
    async def _check_all_triggers(self):
        """Check all active orders for triggers."""
        try:
            from .sl_tp_service import get_sl_tp_service
            sl_tp_service = get_sl_tp_service()
            
            # Get all active orders
            active_orders = sl_tp_service.get_active_orders()
            
            if not active_orders:
                return
            
            # Get unique symbols from active orders
            symbols = set(order['symbol'] for order in active_orders)
            
            # Fetch current prices for all symbols
            current_prices = await self._fetch_current_prices(symbols)
            
            if not current_prices:
                logger.warning("No prices fetched, skipping trigger check")
                return
            
            # Check for triggers
            triggered_orders = sl_tp_service.check_triggers(current_prices)
            
            if triggered_orders:
                logger.info(f"Found {len(triggered_orders)} triggered orders")
                
                # Execute triggered orders
                for order in triggered_orders:
                    await self._execute_triggered_order(order)
            
        except Exception as e:
            logger.error(f"Error checking triggers: {e}", exc_info=True)
    
    async def _fetch_current_prices(self, symbols: set) -> Dict[str, float]:
        """
        Fetch current market prices for all symbols.
        
        Args:
            symbols: Set of symbols to fetch prices for
            
        Returns:
            Dict mapping symbols to current prices
        """
        prices = {}
        
        try:
            # Import exchange service
            from ...services.exchange_service import ExchangeService
            
            # For now, use a mock exchange (in production, use real exchange)
            exchange = ExchangeService(name='binance', use_mock=True)
            
            for symbol in symbols:
                try:
                    price = await exchange.get_market_price(symbol)
                    if price:
                        prices[symbol] = price
                except Exception as e:
                    logger.warning(f"Failed to fetch price for {symbol}: {e}")
            
            if prices:
                logger.debug(f"Fetched prices for {len(prices)} symbols")
            
        except Exception as e:
            logger.error(f"Error fetching prices: {e}")
        
        return prices
    
    async def _execute_triggered_order(self, order: Dict[str, Any]):
        """
        Execute an order that has been triggered.
        
        Args:
            order: Triggered order details
        """
        try:
            order_id = order['order_id']
            symbol = order['symbol']
            side = order['side']
            quantity = order['quantity']
            triggered_price = order['triggered_price']
            order_type = order['type']
            
            logger.info(
                f"Executing triggered {order_type}: {side} {quantity} {symbol} "
                f"at ${triggered_price:.2f}"
            )
            
            # Import real money trading service
            from .real_money_service import real_money_trading_service
            from .sl_tp_service import get_sl_tp_service
            
            # Execute the order
            try:
                result = await real_money_trading_service.execute_real_money_trade(
                    user_id=order['user_id'],
                    exchange='binance',  # TODO: Get from order or user preference
                    pair=symbol,
                    side=side,
                    order_type='market',  # Use market order for immediate execution
                    amount=quantity,
                    price=None,  # Market order
                    bot_id=order.get('bot_id')
                )
                
                if result.get('success'):
                    logger.info(
                        f"Successfully executed {order_type} for {symbol}: "
                        f"Order ID {result.get('order_id')}"
                    )
                    
                    # Remove the order from active orders
                    sl_tp_service = get_sl_tp_service()
                    sl_tp_service.cancel_order(order_id)
                    
                    # If this was a stop-loss or take-profit, also cancel the counterpart
                    position_id = order['position_id']
                    if order_type == 'stop_loss':
                        # Cancel take-profit
                        sl_tp_service.cancel_order(f"tp_{position_id}")
                    elif order_type == 'take_profit':
                        # Cancel stop-loss
                        sl_tp_service.cancel_order(position_id)
                    
                else:
                    logger.error(
                        f"Failed to execute {order_type} for {symbol}: "
                        f"{result.get('error', 'Unknown error')}"
                    )
                    
            except Exception as e:
                logger.error(f"Error executing triggered order: {e}", exc_info=True)
            
        except Exception as e:
            logger.error(f"Error processing triggered order: {e}", exc_info=True)
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        return {
            'monitoring': self.monitoring,
            'check_interval': self.check_interval,
            'monitored_symbols': list(self.monitored_symbols)
        }


# Singleton instance
_price_monitor_instance = None


def get_price_monitor() -> PriceMonitoringService:
    """Get or create the price monitoring service singleton."""
    global _price_monitor_instance
    if _price_monitor_instance is None:
        _price_monitor_instance = PriceMonitoringService()
    return _price_monitor_instance
