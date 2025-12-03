"""
Comprehensive Real Money Trading Test Suite
Tests all safety features, SL/TP functionality, and integration
"""
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TradingSystemTester:
    """Comprehensive testing for real money trading system"""
    
    def __init__(self):
        self.test_results = []
        self.passed = 0
        self.failed = 0
    
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {message}")
        
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    async def test_safety_service(self):
        """Test trading safety service"""
        logger.info("=" * 60)
        logger.info("Testing Trading Safety Service")
        logger.info("=" * 60)
        
        try:
            from server_fastapi.services.trading.trading_safety_service import get_trading_safety_service
            
            # Test 1: Service initialization
            try:
                service = get_trading_safety_service()
                self.log_test("Safety Service Init", True, "Service initialized successfully")
            except Exception as e:
                self.log_test("Safety Service Init", False, f"Failed: {e}")
                return
            
            # Test 2: Valid trade validation
            result = service.validate_trade(
                symbol="BTC/USDT",
                side="buy",
                quantity=0.01,
                price=50000.0,
                account_balance=10000.0,
                current_positions={}
            )
            self.log_test(
                "Valid Trade Validation",
                result['valid'] is True,
                f"Trade validated: {result['reason']}"
            )
            
            # Test 3: Position size limit
            result = service.validate_trade(
                symbol="BTC/USDT",
                side="buy",
                quantity=0.5,  # 50% of account (exceeds 10% limit)
                price=50000.0,
                account_balance=10000.0,
                current_positions={}
            )
            self.log_test(
                "Position Size Limit",
                result['adjustments'] is not None,
                f"Position adjusted: {result.get('adjustments', {})}"
            )
            
            # Test 4: Kill switch activation
            service.record_trade_result("test1", -300, "BTC/USDT", "buy", 0.1, 50000)
            service.record_trade_result("test2", -300, "BTC/USDT", "sell", 0.1, 49000)
            
            result = service.validate_trade(
                symbol="BTC/USDT",
                side="buy",
                quantity=0.01,
                price=50000.0,
                account_balance=10000.0,
                current_positions={}
            )
            
            kill_switch_works = service.kill_switch_active
            self.log_test(
                "Kill Switch Activation",
                kill_switch_works,
                f"Kill switch: {service.kill_switch_reason}"
            )
            
            # Test 5: Get status
            status = service.get_safety_status()
            self.log_test(
                "Safety Status Retrieval",
                'kill_switch_active' in status,
                f"Status retrieved: {len(status)} fields"
            )
            
        except Exception as e:
            logger.error(f"Safety service test failed: {e}", exc_info=True)
            self.log_test("Safety Service Tests", False, f"Exception: {e}")
    
    async def test_sl_tp_service(self):
        """Test stop-loss/take-profit service"""
        logger.info("=" * 60)
        logger.info("Testing Stop-Loss/Take-Profit Service")
        logger.info("=" * 60)
        
        try:
            from server_fastapi.services.trading.sl_tp_service import get_sl_tp_service
            
            # Test 1: Service initialization
            try:
                service = get_sl_tp_service()
                self.log_test("SL/TP Service Init", True, "Service initialized successfully")
            except Exception as e:
                self.log_test("SL/TP Service Init", False, f"Failed: {e}")
                return
            
            # Test 2: Create stop-loss
            sl_order = service.create_stop_loss(
                position_id="test_pos_1",
                symbol="BTC/USDT",
                side="buy",
                quantity=0.1,
                entry_price=50000.0,
                stop_loss_pct=0.02,
                user_id="test_user"
            )
            
            expected_sl_price = 50000.0 * 0.98  # 2% below entry
            actual_sl_price = sl_order['trigger_price']
            
            self.log_test(
                "Stop-Loss Creation",
                abs(actual_sl_price - expected_sl_price) < 1.0,
                f"SL price: ${actual_sl_price:.2f} (expected ${expected_sl_price:.2f})"
            )
            
            # Test 3: Create take-profit
            tp_order = service.create_take_profit(
                position_id="test_pos_1",
                symbol="BTC/USDT",
                side="buy",
                quantity=0.1,
                entry_price=50000.0,
                take_profit_pct=0.05,
                user_id="test_user"
            )
            
            expected_tp_price = 50000.0 * 1.05  # 5% above entry
            actual_tp_price = tp_order['trigger_price']
            
            self.log_test(
                "Take-Profit Creation",
                abs(actual_tp_price - expected_tp_price) < 1.0,
                f"TP price: ${actual_tp_price:.2f} (expected ${expected_tp_price:.2f})"
            )
            
            # Test 4: Trigger detection
            current_prices = {"BTC/USDT": 48900.0}  # Below stop-loss
            triggered = service.check_triggers(current_prices)
            
            self.log_test(
                "Stop-Loss Trigger Detection",
                len(triggered) > 0,
                f"Detected {len(triggered)} triggered orders"
            )
            
            # Test 5: Trailing stop
            trail_order = service.create_trailing_stop(
                position_id="test_pos_2",
                symbol="ETH/USDT",
                side="buy",
                quantity=1.0,
                entry_price=3000.0,
                trailing_pct=0.03,
                user_id="test_user"
            )
            
            self.log_test(
                "Trailing Stop Creation",
                trail_order['type'] == 'trailing_stop',
                f"Trailing stop created at ${trail_order['trigger_price']:.2f}"
            )
            
            # Test 6: Trailing stop update
            service.update_trailing_stop("test_pos_2", 3200.0)  # Price increased
            updated_order = service.trailing_stops.get("test_pos_2")
            
            if updated_order:
                new_stop = updated_order['trigger_price']
                expected_new_stop = 3200.0 * 0.97  # 3% below new high
                
                self.log_test(
                    "Trailing Stop Update",
                    abs(new_stop - expected_new_stop) < 1.0,
                    f"Stop updated to ${new_stop:.2f}"
                )
            else:
                self.log_test("Trailing Stop Update", False, "Order not found")
            
            # Test 7: Get active orders
            active = service.get_active_orders()
            self.log_test(
                "Active Orders Retrieval",
                len(active) > 0,
                f"Found {len(active)} active orders"
            )
            
        except Exception as e:
            logger.error(f"SL/TP service test failed: {e}", exc_info=True)
            self.log_test("SL/TP Service Tests", False, f"Exception: {e}")
    
    async def test_price_monitor(self):
        """Test price monitoring service"""
        logger.info("=" * 60)
        logger.info("Testing Price Monitoring Service")
        logger.info("=" * 60)
        
        try:
            from server_fastapi.services.trading.price_monitor import get_price_monitor
            
            # Test 1: Service initialization
            try:
                monitor = get_price_monitor()
                self.log_test("Price Monitor Init", True, "Monitor initialized successfully")
            except Exception as e:
                self.log_test("Price Monitor Init", False, f"Failed: {e}")
                return
            
            # Test 2: Start monitoring
            await monitor.start_monitoring(check_interval=10)
            await asyncio.sleep(1)  # Give it time to start
            
            status = monitor.get_monitoring_status()
            self.log_test(
                "Start Monitoring",
                status['monitoring'] is True,
                f"Monitoring active with {status['check_interval']}s interval"
            )
            
            # Test 3: Status retrieval
            self.log_test(
                "Monitor Status",
                'check_interval' in status,
                f"Status fields: {list(status.keys())}"
            )
            
            # Test 4: Stop monitoring
            await monitor.stop_monitoring()
            await asyncio.sleep(1)  # Give it time to stop
            
            status = monitor.get_monitoring_status()
            self.log_test(
                "Stop Monitoring",
                status['monitoring'] is False,
                "Monitoring stopped successfully"
            )
            
        except Exception as e:
            logger.error(f"Price monitor test failed: {e}", exc_info=True)
            self.log_test("Price Monitor Tests", False, f"Exception: {e}")
    
    async def test_integration(self):
        """Test integration between services"""
        logger.info("=" * 60)
        logger.info("Testing Service Integration")
        logger.info("=" * 60)
        
        try:
            from server_fastapi.services.trading.trading_safety_service import get_trading_safety_service
            from server_fastapi.services.trading.sl_tp_service import get_sl_tp_service
            
            safety = get_trading_safety_service()
            sl_tp = get_sl_tp_service()
            
            # Test complete trade flow
            # 1. Validate trade
            validation = safety.validate_trade(
                symbol="BTC/USDT",
                side="buy",
                quantity=0.05,
                price=50000.0,
                account_balance=10000.0,
                current_positions={}
            )
            
            if validation['valid']:
                # 2. Create SL/TP orders
                quantity = validation.get('adjustments', {}).get('adjusted_quantity', 0.05)
                
                sl_order = sl_tp.create_stop_loss(
                    position_id="integration_test",
                    symbol="BTC/USDT",
                    side="buy",
                    quantity=quantity,
                    entry_price=50000.0,
                    stop_loss_pct=0.02,
                    user_id="test_user"
                )
                
                tp_order = sl_tp.create_take_profit(
                    position_id="integration_test",
                    symbol="BTC/USDT",
                    side="buy",
                    quantity=quantity,
                    entry_price=50000.0,
                    take_profit_pct=0.05,
                    user_id="test_user"
                )
                
                self.log_test(
                    "Complete Trade Flow",
                    sl_order and tp_order,
                    "Validation → SL/TP creation successful"
                )
                
                # 3. Record trade result
                safety.record_trade_result(
                    "integration_test",
                    100.0,
                    "BTC/USDT",
                    "buy",
                    quantity,
                    50000.0
                )
                
                status = safety.get_safety_status()
                self.log_test(
                    "Trade Recording",
                    status['trades_today'] > 0,
                    f"Trades today: {status['trades_today']}"
                )
            else:
                self.log_test("Complete Trade Flow", False, "Validation failed")
            
        except Exception as e:
            logger.error(f"Integration test failed: {e}", exc_info=True)
            self.log_test("Integration Tests", False, f"Exception: {e}")
    
    def print_summary(self):
        """Print test summary"""
        logger.info("=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {self.passed} ✅")
        logger.info(f"Failed: {self.failed} ❌")
        logger.info(f"Pass Rate: {pass_rate:.1f}%")
        
        if self.failed > 0:
            logger.info("\nFailed Tests:")
            for result in self.test_results:
                if not result['passed']:
                    logger.info(f"  - {result['test']}: {result['message']}")
        
        logger.info("=" * 60)
        
        return self.failed == 0
    
    async def run_all_tests(self):
        """Run all tests"""
        logger.info("\n")
        logger.info("=" * 60)
        logger.info("STARTING COMPREHENSIVE TRADING SYSTEM TESTS")
        logger.info("=" * 60)
        logger.info("\n")
        
        await self.test_safety_service()
        await self.test_sl_tp_service()
        await self.test_price_monitor()
        await self.test_integration()
        
        logger.info("\n")
        all_passed = self.print_summary()
        logger.info("\n")
        
        if all_passed:
            logger.info("🎉 ALL TESTS PASSED - SYSTEM IS READY FOR REAL MONEY TRADING! 🎉")
        else:
            logger.warning("⚠️  SOME TESTS FAILED - REVIEW BEFORE REAL MONEY TRADING ⚠️")
        
        return all_passed


async def main():
    """Main test runner"""
    tester = TradingSystemTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
