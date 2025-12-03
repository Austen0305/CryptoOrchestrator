"""
Tests for Trading Safety Service
"""
import pytest
from datetime import datetime, timedelta
from server_fastapi.services.trading.trading_safety_service import (
    TradingSafetyService,
    get_trading_safety_service
)


@pytest.fixture
def safety_service():
    """Create a fresh safety service for each test."""
    return TradingSafetyService()


@pytest.fixture
def mock_account_state():
    """Mock account state for testing."""
    return {
        'balance': 10000.0,
        'positions': {
            'BTC/USDT': {'value': 1000.0, 'quantity': 0.05},
            'ETH/USDT': {'value': 500.0, 'quantity': 0.3}
        }
    }


class TestTradeValidation:
    """Test trade validation logic."""
    
    def test_valid_trade_passes(self, safety_service, mock_account_state):
        """Test that a valid trade passes validation."""
        result = safety_service.validate_trade(
            symbol='BTC/USDT',
            side='buy',
            quantity=0.01,
            price=50000.0,
            account_balance=mock_account_state['balance'],
            current_positions=mock_account_state['positions']
        )
        
        assert result['valid'] is True
        assert result['adjustments'] is None
    
    def test_position_size_limit_enforced(self, safety_service, mock_account_state):
        """Test that position size limit is enforced."""
        # Try to buy 0.1 BTC at $50k = $5k (50% of account)
        result = safety_service.validate_trade(
            symbol='BTC/USDT',
            side='buy',
            quantity=0.1,
            price=50000.0,
            account_balance=mock_account_state['balance'],
            current_positions=mock_account_state['positions']
        )
        
        # Should be adjusted to max 10% = $1000
        assert result['valid'] is True
        assert result['adjustments'] is not None
        adjusted_qty = result['adjustments']['adjusted_quantity']
        adjusted_value = adjusted_qty * 50000.0
        assert adjusted_value == pytest.approx(1000.0, abs=1.0)
    
    def test_minimum_balance_check(self, safety_service):
        """Test minimum balance check."""
        result = safety_service.validate_trade(
            symbol='BTC/USDT',
            side='buy',
            quantity=0.001,
            price=50000.0,
            account_balance=50.0,  # Below minimum
            current_positions={}
        )
        
        assert result['valid'] is False
        assert 'minimum' in result['reason'].lower()
    
    def test_daily_loss_limit_triggers_kill_switch(self, safety_service, mock_account_state):
        """Test that daily loss limit triggers kill switch."""
        # Record losses to hit daily limit
        safety_service.record_trade_result('trade1', -300.0, 'BTC/USDT', 'buy', 0.01, 50000.0)
        safety_service.record_trade_result('trade2', -250.0, 'BTC/USDT', 'sell', 0.01, 49000.0)
        
        # Daily P&L = -550 (5.5% of $10k, above 5% limit)
        result = safety_service.validate_trade(
            symbol='BTC/USDT',
            side='buy',
            quantity=0.01,
            price=50000.0,
            account_balance=mock_account_state['balance'],
            current_positions=mock_account_state['positions']
        )
        
        assert result['valid'] is False
        assert safety_service.kill_switch_active
        assert 'daily loss' in result['reason'].lower()
    
    def test_consecutive_losses_trigger_kill_switch(self, safety_service, mock_account_state):
        """Test that consecutive losses trigger kill switch."""
        # Record 3 consecutive losses
        safety_service.record_trade_result('trade1', -100.0, 'BTC/USDT', 'buy', 0.01, 50000.0)
        safety_service.record_trade_result('trade2', -100.0, 'ETH/USDT', 'buy', 0.1, 3000.0)
        safety_service.record_trade_result('trade3', -100.0, 'BTC/USDT', 'sell', 0.01, 49000.0)
        
        result = safety_service.validate_trade(
            symbol='BTC/USDT',
            side='buy',
            quantity=0.01,
            price=50000.0,
            account_balance=mock_account_state['balance'],
            current_positions=mock_account_state['positions']
        )
        
        assert result['valid'] is False
        assert safety_service.kill_switch_active
        assert safety_service.consecutive_losses == 3
    
    def test_portfolio_heat_limit(self, safety_service, mock_account_state):
        """Test portfolio heat limit enforcement."""
        # Current exposure: BTC $1000 + ETH $500 = $1500 (15%)
        # Try to add $900 position (9% position size, but 15% + 9% = 24% < 30% should pass)
        # Then add another $900 (24% + 9% = 33% > 30% should fail)
        
        # First trade should pass
        result1 = safety_service.validate_trade(
            symbol='SOL/USDT',
            side='buy',
            quantity=4.5,  # $900 at $200 = 9% position
            price=200.0,
            account_balance=mock_account_state['balance'],
            current_positions=mock_account_state['positions']
        )
        assert result1['valid'] is True
        
        # Add SOL position to mock state
        mock_account_state['positions']['SOL/USDT'] = {'value': 900.0, 'quantity': 4.5}
        
        # Second trade should fail due to portfolio heat
        result2 = safety_service.validate_trade(
            symbol='AVAX/USDT',
            side='buy',
            quantity=9.0,  # $900 at $100 = 9% position, but total becomes 33%
            price=100.0,
            account_balance=mock_account_state['balance'],
            current_positions=mock_account_state['positions']
        )
        
        assert result2['valid'] is False
        assert 'portfolio heat' in result2['reason'].lower()


class TestSlippageProtection:
    """Test slippage protection logic."""
    
    def test_acceptable_slippage_buy(self, safety_service):
        """Test acceptable slippage on buy order."""
        result = safety_service.check_slippage(
            expected_price=50000.0,
            actual_price=50100.0,  # 0.2% slippage
            side='buy'
        )
        
        assert result['acceptable'] is True
        assert result['slippage_pct'] < 0.005
    
    def test_acceptable_slippage_sell(self, safety_service):
        """Test acceptable slippage on sell order."""
        result = safety_service.check_slippage(
            expected_price=50000.0,
            actual_price=49900.0,  # 0.2% slippage
            side='sell'
        )
        
        assert result['acceptable'] is True
        assert result['slippage_pct'] < 0.005
    
    def test_excessive_slippage_rejected(self, safety_service):
        """Test that excessive slippage is rejected."""
        result = safety_service.check_slippage(
            expected_price=50000.0,
            actual_price=51000.0,  # 2% slippage (too high)
            side='buy'
        )
        
        assert result['acceptable'] is False
        assert result['slippage_pct'] > 0.005


class TestTradeRecording:
    """Test trade result recording."""
    
    def test_profit_resets_consecutive_losses(self, safety_service):
        """Test that a profitable trade resets consecutive losses."""
        # Record 2 losses
        safety_service.record_trade_result('trade1', -100.0, 'BTC/USDT', 'buy', 0.01, 50000.0)
        safety_service.record_trade_result('trade2', -100.0, 'ETH/USDT', 'buy', 0.1, 3000.0)
        assert safety_service.consecutive_losses == 2
        
        # Record a profit
        safety_service.record_trade_result('trade3', 150.0, 'BTC/USDT', 'sell', 0.01, 51500.0)
        assert safety_service.consecutive_losses == 0
    
    def test_daily_pnl_accumulates(self, safety_service):
        """Test that daily P&L accumulates correctly."""
        safety_service.record_trade_result('trade1', 100.0, 'BTC/USDT', 'buy', 0.01, 50000.0)
        safety_service.record_trade_result('trade2', -50.0, 'ETH/USDT', 'buy', 0.1, 3000.0)
        safety_service.record_trade_result('trade3', 75.0, 'BTC/USDT', 'sell', 0.01, 50750.0)
        
        assert safety_service.daily_pnl == pytest.approx(125.0)
        assert len(safety_service.trades_today) == 3


class TestKillSwitch:
    """Test kill switch functionality."""
    
    def test_kill_switch_blocks_all_trades(self, safety_service, mock_account_state):
        """Test that active kill switch blocks all trades."""
        safety_service._activate_kill_switch("Test reason")
        
        result = safety_service.validate_trade(
            symbol='BTC/USDT',
            side='buy',
            quantity=0.001,
            price=50000.0,
            account_balance=mock_account_state['balance'],
            current_positions={}
        )
        
        assert result['valid'] is False
        assert 'kill switch' in result['reason'].lower()
    
    def test_kill_switch_reset_requires_override(self, safety_service):
        """Test that kill switch reset requires admin override."""
        safety_service._activate_kill_switch("Test reason")
        
        # Try to reset without override (same day)
        result = safety_service.reset_kill_switch(admin_override=False)
        assert result['success'] is False
        assert safety_service.kill_switch_active
        
        # Reset with admin override
        result = safety_service.reset_kill_switch(admin_override=True)
        assert result['success'] is True
        assert not safety_service.kill_switch_active
    
    def test_kill_switch_auto_resets_new_day(self, safety_service):
        """Test that kill switch auto-resets on new day."""
        safety_service._activate_kill_switch("Test reason")
        
        # Simulate new day by manipulating last_reset
        safety_service.last_reset = datetime.now() - timedelta(days=1)
        
        # Check daily reset
        safety_service._check_daily_reset()
        
        assert not safety_service.kill_switch_active


class TestConfiguration:
    """Test configuration management."""
    
    def test_configuration_update(self, safety_service):
        """Test updating safety configuration."""
        new_config = {
            'max_position_size_pct': 0.15,
            'daily_loss_limit_pct': 0.08,
            'max_consecutive_losses': 5
        }
        
        result = safety_service.update_configuration(new_config)
        
        assert result['success'] is True
        assert len(result['updated_fields']) == 3
        assert safety_service.max_position_size_pct == 0.15
        assert safety_service.daily_loss_limit_pct == 0.08
        assert safety_service.max_consecutive_losses == 5
    
    def test_get_safety_status(self, safety_service):
        """Test getting safety status."""
        status = safety_service.get_safety_status()
        
        assert 'kill_switch_active' in status
        assert 'daily_pnl' in status
        assert 'configuration' in status
        assert 'max_position_size_pct' in status['configuration']


class TestSingleton:
    """Test singleton pattern."""
    
    def test_singleton_returns_same_instance(self):
        """Test that get_trading_safety_service returns same instance."""
        service1 = get_trading_safety_service()
        service2 = get_trading_safety_service()
        
        assert service1 is service2


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_zero_balance_rejected(self, safety_service):
        """Test that zero balance is rejected."""
        result = safety_service.validate_trade(
            symbol='BTC/USDT',
            side='buy',
            quantity=0.001,
            price=50000.0,
            account_balance=0.0,
            current_positions={}
        )
        
        assert result['valid'] is False
    
    def test_negative_quantity_handled(self, safety_service):
        """Test handling of negative quantity (should be caught by caller)."""
        # This tests that the service doesn't crash with invalid input
        result = safety_service.validate_trade(
            symbol='BTC/USDT',
            side='buy',
            quantity=-0.001,
            price=50000.0,
            account_balance=10000.0,
            current_positions={}
        )
        
        # Negative value should be validated (result depends on implementation)
        assert 'valid' in result
    
    def test_very_small_trade_allowed(self, safety_service):
        """Test that very small trades are allowed."""
        result = safety_service.validate_trade(
            symbol='BTC/USDT',
            side='buy',
            quantity=0.0001,  # Very small
            price=50000.0,
            account_balance=10000.0,
            current_positions={}
        )
        
        assert result['valid'] is True
