import pytest
import json
from sqlalchemy.ext.asyncio import AsyncSession
from server_fastapi.repositories.bot_repository import BotRepository
from server_fastapi.models.bot import Bot

@pytest.mark.asyncio
class TestBotRepository:
    """Test cases for BotRepository"""

    async def test_create_bot(self, db_session: AsyncSession):
        """Test creating a new bot"""
        repo = BotRepository()

        # Test data
        bot_data = {
            "id": "test_bot_1",
            "user_id": 1,
            "name": "Test Bot",
            "symbol": "BTC/USDT",
            "strategy": "SMA",
            "parameters": {"period": 20},
            "active": False,
            "status": "stopped"
        }

        bot = await repo.create(db_session, bot_data)

        assert bot.id == "test_bot_1"
        assert bot.user_id == 1
        assert bot.name == "Test Bot"
        assert bot.symbol == "BTC/USDT"
        assert bot.strategy == "SMA"
        assert json.loads(bot.parameters) == {"period": 20}
        assert bot.active == False
        assert bot.status == "stopped"

    async def test_get_by_user_and_id(self, db_session: AsyncSession):
        """Test getting bot by ID and user ID"""
        repo = BotRepository()

        # Create test bot
        bot_data = {
            "id": "test_bot_1",
            "user_id": 1,
            "name": "Test Bot",
            "symbol": "BTC/USDT",
            "strategy": "SMA",
            "parameters": {"period": 20},
            "active": False,
            "status": "stopped"
        }
        await repo.create(db_session, bot_data)

        # Retrieve bot
        bot = await repo.get_by_user_and_id(db_session, "test_bot_1", 1)

        assert bot is not None
        assert bot.id == "test_bot_1"
        assert bot.user_id == 1

    async def test_get_by_user_and_id_not_found(self, db_session: AsyncSession):
        """Test getting non-existent bot by ID and user ID"""
        repo = BotRepository()

        bot = await repo.get_by_user_and_id(db_session, "nonexistent", 1)

        assert bot is None

    async def test_get_user_bots(self, db_session: AsyncSession):
        """Test getting all bots for a user"""
        repo = BotRepository()

        # Create multiple bots for user 1
        for i in range(3):
            bot_data = {
                "id": f"test_bot_{i}",
                "user_id": 1,
                "name": f"Test Bot {i}",
                "symbol": "BTC/USDT",
                "strategy": "SMA",
                "parameters": {"period": 20},
                "active": False,
                "status": "stopped"
            }
            await repo.create(db_session, bot_data)

        # Create bot for different user
        bot_data = {
            "id": "other_user_bot",
            "user_id": 2,
            "name": "Other User Bot",
            "symbol": "ETH/USDT",
            "strategy": "EMA",
            "parameters": {"period": 10},
            "active": False,
            "status": "stopped"
        }
        await repo.create(db_session, bot_data)

        # Get bots for user 1
        user_bots = await repo.get_user_bots(db_session, 1)

        assert len(user_bots) == 3
        assert all(bot.user_id == 1 for bot in user_bots)

    async def test_update_bot_status(self, db_session: AsyncSession):
        """Test updating bot status"""
        repo = BotRepository()

        # Create test bot
        bot_data = {
            "id": "test_bot_1",
            "user_id": 1,
            "name": "Test Bot",
            "symbol": "BTC/USDT",
            "strategy": "SMA",
            "parameters": {"period": 20},
            "active": False,
            "status": "stopped"
        }
        await repo.create(db_session, bot_data)

        # Update status to running
        updated_bot = await repo.update_bot_status(db_session, "test_bot_1", 1, True, "running")

        assert updated_bot is not None
        assert updated_bot.active == True
        assert updated_bot.status == "running"
        assert updated_bot.last_started_at is not None

        # Update status to stopped
        updated_bot = await repo.update_bot_status(db_session, "test_bot_1", 1, False, "stopped")

        assert updated_bot is not None
        assert updated_bot.active == False
        assert updated_bot.status == "stopped"
        assert updated_bot.last_stopped_at is not None

    async def test_update_performance_data(self, db_session: AsyncSession):
        """Test updating bot performance data"""
        repo = BotRepository()

        # Create test bot
        bot_data = {
            "id": "test_bot_1",
            "user_id": 1,
            "name": "Test Bot",
            "symbol": "BTC/USDT",
            "strategy": "SMA",
            "parameters": {"period": 20},
            "active": False,
            "status": "stopped"
        }
        await repo.create(db_session, bot_data)

        # Update performance data
        performance_data = {
            "total_trades": 100,
            "winning_trades": 60,
            "losing_trades": 40,
            "profit_loss": 1500.50,
            "win_rate": 0.6
        }

        success = await repo.update_performance_data(db_session, "test_bot_1", 1, performance_data)

        assert success == True

        # Verify data was updated
        bot = await repo.get_by_user_and_id(db_session, "test_bot_1", 1)
        assert bot is not None
        assert json.loads(bot.performance_data) == performance_data

    async def test_create_bot_method(self, db_session: AsyncSession):
        """Test the create_bot method"""
        repo = BotRepository()

        parameters = {"period": 20, "threshold": 0.5}

        bot = await repo.create_bot(
            session=db_session,
            bot_id="test_bot_1",
            user_id=1,
            name="Test Bot",
            symbol="BTC/USDT",
            strategy="SMA",
            parameters=parameters
        )

        assert bot.id == "test_bot_1"
        assert bot.user_id == 1
        assert bot.name == "Test Bot"
        assert bot.symbol == "BTC/USDT"
        assert bot.strategy == "SMA"
        assert json.loads(bot.parameters) == parameters
        assert bot.active == False
        assert bot.status == "stopped"