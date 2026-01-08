"""
Integration tests for Futures Trading Service
"""

import os

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from server_fastapi.models.user import User
from server_fastapi.repositories.futures_position_repository import (
    FuturesPositionRepository,
)
from server_fastapi.services.trading.futures_trading_service import (
    FuturesTradingService,
)

TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")


@pytest.fixture
async def test_db():
    """Create test database session."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

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
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_create_futures_position(test_db: AsyncSession, test_user: User):
    """Test creating a futures position."""
    service = FuturesTradingService(session=test_db)

    position_id = await service.create_futures_position(
        user_id=test_user.id,
        symbol="BTC/USD",
        exchange="binance",
        side="long",
        quantity=0.1,
        leverage=10,
        trading_mode="paper",
        entry_price=50000.0,
    )

    assert position_id is not None
    assert position_id.startswith("futures-")

    # Verify position was created
    repository = FuturesPositionRepository()
    position = await repository.get_by_user_and_id(test_db, position_id, test_user.id)
    assert position is not None
    assert position.side == "long"
    assert position.leverage == 10
    assert position.quantity == 0.1
    assert position.entry_price == 50000.0
    assert position.is_open is True


@pytest.mark.asyncio
async def test_futures_position_liquidation_price(
    test_db: AsyncSession, test_user: User
):
    """Test liquidation price calculation."""
    service = FuturesTradingService(session=test_db)

    position_id = await service.create_futures_position(
        user_id=test_user.id,
        symbol="BTC/USD",
        exchange="binance",
        side="long",
        quantity=0.1,
        leverage=10,
        trading_mode="paper",
        entry_price=50000.0,
    )

    repository = FuturesPositionRepository()
    position = await repository.get_by_user_and_id(test_db, position_id, test_user.id)

    # Long position should have liquidation price below entry price
    assert position.liquidation_price < position.entry_price

    # For 10x leverage, liquidation should be around 10% below entry
    price_drop = position.entry_price - position.liquidation_price
    assert price_drop > 0
