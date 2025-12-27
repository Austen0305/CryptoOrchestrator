"""
Integration tests for DCA Trading Service
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import os

# Import User model (always available)
from server_fastapi.models.user import User

# Optional imports - skip tests if services are not available
try:
    from server_fastapi.services.trading.dca_trading_service import DCATradingService
    from server_fastapi.repositories.dca_bot_repository import DCABotRepository

    DCA_TRADING_AVAILABLE = True
except ImportError as e:
    DCA_TRADING_AVAILABLE = False
    pytestmark = pytest.mark.skip(reason=f"DCA trading service not available: {e}")
    # Create dummy classes to prevent NameError
    DCATradingService = None
    DCABotRepository = None

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
async def test_create_dca_bot(test_db: AsyncSession, test_user: User):
    """Test creating a DCA bot."""
    service = DCATradingService(session=test_db)

    bot_id = await service.create_dca_bot(
        user_id=test_user.id,
        name="Test DCA Bot",
        symbol="BTC/USD",
        exchange="binance",
        total_investment=1000.0,
        order_amount=100.0,
        interval_minutes=60,
        trading_mode="paper",
    )

    assert bot_id is not None
    assert bot_id.startswith("dca-")

    # Verify bot was created
    repository = DCABotRepository()
    bot = await repository.get_by_user_and_id(test_db, bot_id, test_user.id)
    assert bot is not None
    assert bot.name == "Test DCA Bot"
    assert bot.total_investment == 1000.0
    assert bot.order_amount == 100.0
    assert bot.interval_minutes == 60


@pytest.mark.asyncio
async def test_dca_bot_with_martingale(test_db: AsyncSession, test_user: User):
    """Test creating DCA bot with martingale strategy."""
    service = DCATradingService(session=test_db)

    bot_id = await service.create_dca_bot(
        user_id=test_user.id,
        name="Martingale DCA Bot",
        symbol="BTC/USD",
        exchange="binance",
        total_investment=1000.0,
        order_amount=100.0,
        interval_minutes=60,
        trading_mode="paper",
        use_martingale=True,
        martingale_multiplier=1.5,
        martingale_max_multiplier=5.0,
    )

    repository = DCABotRepository()
    bot = await repository.get_by_user_and_id(test_db, bot_id, test_user.id)
    assert bot.use_martingale is True
    assert bot.martingale_multiplier == 1.5
    assert bot.martingale_max_multiplier == 5.0
