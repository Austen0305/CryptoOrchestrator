"""
Additional test fixtures for bot integration tests
Extends existing conftest.py with bot-specific fixtures
"""

import pytest
import pytest_asyncio
from datetime import datetime
from typing import Dict, Any


@pytest_asyncio.fixture
async def test_bot_data() -> Dict[str, Any]:
    """Provide sample bot data for testing"""
    return {
        "name": "Test Bot",
        "exchange": "kraken",
        "symbol": "BTC/USD",
        "strategy": "ml_adaptive",
        "config": {
            "risk_level": "medium",
            "position_size": 0.1,
            "stop_loss": 0.02,
            "take_profit": 0.05
        }
    }


@pytest_asyncio.fixture
async def created_bot(db_session, test_bot_data):
    """Create a test bot in the database"""
    from server_fastapi.models.bot import Bot
    
    bot = Bot(
        user_id="test_user_123",
        **test_bot_data,
        status="inactive"
    )
    db_session.add(bot)
    await db_session.commit()
    await db_session.refresh(bot)
    
    yield bot
    
    # Cleanup
    await db_session.delete(bot)
    await db_session.commit()


@pytest_asyncio.fixture
async def test_portfolio(db_session):
    """Create a test portfolio"""
    from server_fastapi.models.portfolio import Portfolio
    
    portfolio = Portfolio(
        user_id="test_user_123",
        exchange="kraken",
        balances={"BTC": 1.5, "USD": 10000.0},
        total_value_usd=50000.0
    )
    db_session.add(portfolio)
    await db_session.commit()
    await db_session.refresh(portfolio)
    
    yield portfolio
    
    # Cleanup
    await db_session.delete(portfolio)
    await db_session.commit()


@pytest_asyncio.fixture
async def test_trades(db_session):
    """Create sample trades for testing"""
    from server_fastapi.models.trade import Trade
    
    trades = [
        Trade(
            user_id="test_user_123",
            exchange="kraken",
            symbol="BTC/USD",
            side="buy",
            amount=0.5,
            price=40000.0,
            cost=20000.0,
            fee=20.0,
            executed_at=datetime.utcnow()
        ),
        Trade(
            user_id="test_user_123",
            exchange="kraken",
            symbol="BTC/USD",
            side="buy",
            amount=1.0,
            price=42000.0,
            cost=42000.0,
            fee=42.0,
            executed_at=datetime.utcnow()
        ),
    ]
    
    for trade in trades:
        db_session.add(trade)
    
    await db_session.commit()
    
    yield trades
    
    # Cleanup
    for trade in trades:
        await db_session.delete(trade)
    await db_session.commit()


@pytest.fixture
def mock_exchange_client():
    """Mock exchange client for testing"""
    class MockExchange:
        def __init__(self):
            self.name = "kraken"
            self.orders = {}
        
        async def fetch_ticker(self, symbol: str):
            return {
                "symbol": symbol,
                "last": 45000.0,
                "bid": 44990.0,
                "ask": 45010.0,
                "high": 46000.0,
                "low": 44000.0,
                "volume": 1000.0
            }
        
        async def create_order(self, symbol: str, type: str, side: str, amount: float, price: float = None):
            order_id = f"order_{len(self.orders) + 1}"
            order = {
                "id": order_id,
                "symbol": symbol,
                "type": type,
                "side": side,
                "amount": amount,
                "price": price or 45000.0,
                "status": "open",
                "filled": 0.0
            }
            self.orders[order_id] = order
            return order
        
        async def fetch_balance(self):
            return {
                "BTC": {"free": 1.5, "used": 0.0, "total": 1.5},
                "USD": {"free": 10000.0, "used": 0.0, "total": 10000.0}
            }
    
    return MockExchange()
