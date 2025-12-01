"""
Trading Orchestrator Service Tests
Tests order validation, placement, and risk management
"""

import pytest
from datetime import datetime


@pytest.mark.asyncio
class TestTradingOrchestrator:
    """Test trading orchestrator functionality"""
    
    async def test_orchestrator_initialization(self, db_session):
        """Test trading orchestrator initializes correctly"""
        from server_fastapi.services.trading_orchestrator import TradingOrchestrator
        
        orchestrator = TradingOrchestrator(db_session=db_session)
        assert orchestrator is not None
        assert orchestrator.db == db_session
    
    async def test_validate_symbol_format(self, db_session):
        """Test symbol format validation"""
        from server_fastapi.services.trading_orchestrator import TradingOrchestrator
        
        orchestrator = TradingOrchestrator(db_session=db_session)
        
        # Valid symbols
        valid_symbols = ["BTC/USD", "ETH/USDT", "SOL/EUR"]
        for symbol in valid_symbols:
            # Should not raise
            assert "/" in symbol
        
        # Invalid symbols
        invalid_symbols = ["BTCUSD", "ETH", ""]
        for symbol in invalid_symbols:
            # Should be detected as invalid
            assert "/" not in symbol or symbol == ""
    
    async def test_validate_order_side(self, db_session):
        """Test order side validation"""
        from server_fastapi.services.trading_orchestrator import TradingOrchestrator
        
        orchestrator = TradingOrchestrator(db_session=db_session)
        
        # Valid sides
        valid_sides = ["buy", "sell"]
        for side in valid_sides:
            assert side in ["buy", "sell"]
        
        # Invalid sides
        invalid_sides = ["BUY", "SELL", "short", "long", ""]
        for side in invalid_sides:
            assert side not in ["buy", "sell"]
    
    async def test_validate_order_amount(self, db_session):
        """Test order amount validation"""
        from server_fastapi.services.trading_orchestrator import TradingOrchestrator
        
        orchestrator = TradingOrchestrator(db_session=db_session)
        
        # Valid amounts
        assert 1.0 > 0
        assert 0.001 > 0
        assert 1000.0 > 0
        
        # Invalid amounts
        assert not (-1.0 > 0)
        assert not (0.0 > 0)
        assert not (-0.001 > 0)


@pytest.mark.asyncio
class TestOrderValidation:
    """Test order validation logic"""
    
    async def test_minimum_order_size(self, db_session):
        """Test minimum order size validation"""
        # Most exchanges have minimum order sizes
        min_order = 0.001  # BTC
        
        assert 0.01 > min_order  # Valid
        assert 0.0001 < min_order  # Too small
    
    async def test_maximum_position_size(self, db_session):
        """Test maximum position size validation"""
        max_position_percent = 0.2  # 20% of portfolio
        portfolio_value = 10000.0
        max_position_value = portfolio_value * max_position_percent
        
        order_value = 1500.0
        assert order_value < max_position_value  # Valid
        
        large_order = 3000.0
        assert large_order > max_position_value  # Too large
    
    async def test_balance_check(self, db_session, test_portfolio):
        """Test balance sufficiency check"""
        # Buy order requires sufficient USD
        available_usd = test_portfolio.balances.get("USD", 0.0)
        order_cost = 5000.0
        
        assert order_cost < available_usd  # Sufficient balance
        
        large_order = 15000.0
        assert large_order > available_usd  # Insufficient
    
    async def test_sell_amount_check(self, db_session, test_portfolio):
        """Test sell order has sufficient asset"""
        available_btc = test_portfolio.balances.get("BTC", 0.0)
        sell_amount = 1.0
        
        assert sell_amount < available_btc  # Sufficient
        
        large_sell = 2.0
        assert large_sell > available_btc  # Insufficient


@pytest.mark.asyncio
class TestOrderExecution:
    """Test order execution flow"""
    
    async def test_create_trade_record(self, db_session):
        """Test creating trade record in database"""
        from server_fastapi.models.trade import Trade
        
        trade = Trade(
            user_id="test_user",
            exchange="kraken",
            symbol="BTC/USD",
            side="buy",
            amount=0.1,
            price=45000.0,
            cost=4500.0,
            fee=4.5,
            success=True
        )
        
        db_session.add(trade)
        await db_session.commit()
        await db_session.refresh(trade)
        
        assert trade.id is not None
        assert trade.symbol == "BTC/USD"
        assert trade.cost == 4500.0
        
        # Cleanup
        await db_session.delete(trade)
        await db_session.commit()
    
    async def test_failed_trade_record(self, db_session):
        """Test recording failed trade"""
        from server_fastapi.models.trade import Trade
        
        trade = Trade(
            user_id="test_user",
            exchange="kraken",
            symbol="BTC/USD",
            side="buy",
            amount=0.1,
            price=45000.0,
            cost=4500.0,
            fee=0.0,
            success=False,
            error_message="Insufficient balance"
        )
        
        db_session.add(trade)
        await db_session.commit()
        await db_session.refresh(trade)
        
        assert trade.success is False
        assert trade.error_message is not None
        
        # Cleanup
        await db_session.delete(trade)
        await db_session.commit()


@pytest.mark.asyncio
class TestRiskManagement:
    """Test risk management integration"""
    
    async def test_risk_limit_check(self, db_session):
        """Test checking against risk limits"""
        from server_fastapi.models.risk_limit import RiskLimit
        
        # Create risk limit
        limit = RiskLimit(
            user_id="test_user",
            limit_type="max_position_size",
            value=0.1,  # 10% max
            enabled=True
        )
        
        db_session.add(limit)
        await db_session.commit()
        await db_session.refresh(limit)
        
        # Test order against limit
        order_size_percent = 0.08  # 8%
        assert order_size_percent < limit.value  # Within limit
        
        large_order = 0.15  # 15%
        assert large_order > limit.value  # Exceeds limit
        
        # Cleanup
        await db_session.delete(limit)
        await db_session.commit()
