"""
Integration tests for Grid Trading Service
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from server_fastapi.services.trading.grid_trading_service import GridTradingService
from server_fastapi.repositories.grid_bot_repository import GridBotRepository
from server_fastapi.models.user import User
import os

# Test database URL
TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")


@pytest.fixture
async def test_db():
    """Create test database session."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Create tables
    from server_fastapi.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
async def test_user(test_db: AsyncSession):
    """Create test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        is_active=True
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_create_grid_bot(test_db: AsyncSession, test_user: User):
    """Test creating a grid trading bot."""
    service = GridTradingService(session=test_db)
    
    bot_id = await service.create_grid_bot(
        user_id=test_user.id,
        name="Test Grid Bot",
        symbol="BTC/USD",
        exchange="binance",
        upper_price=50000.0,
        lower_price=45000.0,
        grid_count=10,
        order_amount=100.0,
        trading_mode="paper"
    )
    
    assert bot_id is not None
    assert bot_id.startswith("grid-")
    
    # Verify bot was created
    repository = GridBotRepository()
    bot = await repository.get_by_user_and_id(test_db, bot_id, test_user.id)
    assert bot is not None
    assert bot.name == "Test Grid Bot"
    assert bot.symbol == "BTC/USD"
    assert bot.upper_price == 50000.0
    assert bot.lower_price == 45000.0
    assert bot.grid_count == 10


@pytest.mark.asyncio
async def test_start_stop_grid_bot(test_db: AsyncSession, test_user: User):
    """Test starting and stopping a grid bot."""
    service = GridTradingService(session=test_db)
    
    # Create bot
    bot_id = await service.create_grid_bot(
        user_id=test_user.id,
        name="Test Grid Bot",
        symbol="BTC/USD",
        exchange="binance",
        upper_price=50000.0,
        lower_price=45000.0,
        grid_count=10,
        order_amount=100.0,
        trading_mode="paper"
    )
    
    # Start bot
    success = await service.start_grid_bot(bot_id, test_user.id)
    assert success is True
    
    # Verify bot is active
    repository = GridBotRepository()
    bot = await repository.get_by_user_and_id(test_db, bot_id, test_user.id)
    assert bot.active is True
    assert bot.status == "running"
    
    # Stop bot
    success = await service.stop_grid_bot(bot_id, test_user.id)
    assert success is True
    
    # Verify bot is stopped
    bot = await repository.get_by_user_and_id(test_db, bot_id, test_user.id)
    assert bot.active is False
    assert bot.status == "stopped"


@pytest.mark.asyncio
async def test_list_user_grid_bots(test_db: AsyncSession, test_user: User):
    """Test listing user's grid bots."""
    service = GridTradingService(session=test_db)
    
    # Create multiple bots
    bot_id1 = await service.create_grid_bot(
        user_id=test_user.id,
        name="Bot 1",
        symbol="BTC/USD",
        exchange="binance",
        upper_price=50000.0,
        lower_price=45000.0,
        grid_count=10,
        order_amount=100.0,
        trading_mode="paper"
    )
    
    bot_id2 = await service.create_grid_bot(
        user_id=test_user.id,
        name="Bot 2",
        symbol="ETH/USD",
        exchange="binance",
        upper_price=3000.0,
        lower_price=2500.0,
        grid_count=8,
        order_amount=50.0,
        trading_mode="paper"
    )
    
    # List bots
    bots = await service.list_user_grid_bots(test_user.id)
    assert len(bots) >= 2
    assert any(bot["id"] == bot_id1 for bot in bots)
    assert any(bot["id"] == bot_id2 for bot in bots)

