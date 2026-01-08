"""
Unit tests for BotService
Tests individual service methods in isolation with mocked dependencies
"""

from unittest.mock import AsyncMock, patch

import pytest

from server_fastapi.services.trading.bot_service import BotService
from server_fastapi.tests.utils.test_helpers import create_mock_db_session


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return create_mock_db_session()


@pytest.fixture
def bot_service(mock_db_session):
    """Create BotService instance with mocked database"""
    return BotService(db_session=mock_db_session)


@pytest.mark.asyncio
async def test_create_bot_success(bot_service, mock_db_session):
    """Test successful bot creation"""
    user_id = 1
    name = "Test Bot"
    symbol = "BTC/USDT"
    strategy = "simple_ma"
    parameters = {"max_position_size": 0.1}

    # Mock the creation service
    with patch.object(
        bot_service.creation, "create_bot", new_callable=AsyncMock
    ) as mock_create:
        mock_create.return_value = "bot-123"

        bot_id = await bot_service.create_bot(
            user_id=user_id,
            name=name,
            symbol=symbol,
            strategy=strategy,
            parameters=parameters,
        )

        assert bot_id == "bot-123"
        mock_create.assert_called_once_with(user_id, name, symbol, strategy, parameters)


@pytest.mark.asyncio
async def test_update_bot_success(bot_service):
    """Test successful bot update"""
    bot_id = "bot-123"
    user_id = 1
    updates = {"name": "Updated Bot Name"}

    with patch.object(
        bot_service.creation, "update_bot", new_callable=AsyncMock
    ) as mock_update:
        mock_update.return_value = {
            "id": bot_id,
            "name": "Updated Bot",
            "user_id": user_id,
        }

        result = await bot_service.update_bot(bot_id, user_id, updates)

        assert result is not None
        assert isinstance(result, dict)
        mock_update.assert_called_once_with(bot_id, user_id, updates)


@pytest.mark.asyncio
async def test_delete_bot_success(bot_service):
    """Test successful bot deletion"""
    bot_id = "bot-123"
    user_id = 1

    with patch.object(
        bot_service.creation, "delete_bot", new_callable=AsyncMock
    ) as mock_delete:
        mock_delete.return_value = True

        result = await bot_service.delete_bot(bot_id, user_id)

        assert result is True
        mock_delete.assert_called_once_with(bot_id, user_id)


@pytest.mark.asyncio
async def test_get_bot_config_success(bot_service):
    """Test getting bot configuration"""
    bot_id = "bot-123"
    user_id = 1
    expected_config = {
        "id": bot_id,
        "name": "Test Bot",
        "symbol": "BTC/USDT",
        "strategy": "simple_ma",
    }

    with patch.object(
        bot_service.creation, "get_bot_config", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = expected_config

        config = await bot_service.get_bot_config(bot_id, user_id)

        assert config == expected_config
        mock_get.assert_called_once_with(bot_id, user_id)


@pytest.mark.asyncio
async def test_list_user_bots_success(bot_service):
    """Test listing user bots"""
    user_id = 1
    expected_bots = [{"id": "bot-1", "name": "Bot 1"}, {"id": "bot-2", "name": "Bot 2"}]

    with patch.object(
        bot_service.creation, "list_user_bots", new_callable=AsyncMock
    ) as mock_list:
        mock_list.return_value = expected_bots

        bots = await bot_service.list_user_bots(user_id)

        assert bots == expected_bots
        assert len(bots) == 2
        mock_list.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_validate_bot_config_success(bot_service):
    """Test bot configuration validation"""
    strategy = "simple_ma"
    config = {"max_position_size": 0.1}

    with patch.object(
        bot_service.creation, "validate_bot_config", new_callable=AsyncMock
    ) as mock_validate:
        mock_validate.return_value = True

        result = await bot_service.validate_bot_config(strategy, config)

        assert result is True
        mock_validate.assert_called_once_with(strategy, config)


@pytest.mark.asyncio
async def test_start_bot_success(bot_service):
    """Test starting a bot"""
    bot_id = "bot-123"
    user_id = 1

    with patch.object(
        bot_service.control, "start_bot", new_callable=AsyncMock
    ) as mock_start:
        mock_start.return_value = True

        result = await bot_service.start_bot(bot_id, user_id)

        assert result is True
        mock_start.assert_called_once_with(bot_id, user_id)


@pytest.mark.asyncio
async def test_stop_bot_success(bot_service):
    """Test stopping a bot"""
    bot_id = "bot-123"
    user_id = 1

    with patch.object(
        bot_service.control, "stop_bot", new_callable=AsyncMock
    ) as mock_stop:
        mock_stop.return_value = True

        result = await bot_service.stop_bot(bot_id, user_id)

        assert result is True
        mock_stop.assert_called_once_with(bot_id, user_id)


@pytest.mark.asyncio
async def test_get_bot_status_success(bot_service):
    """Test getting bot status"""
    bot_id = "bot-123"
    user_id = 1
    expected_status = {"id": bot_id, "status": "active", "is_active": True}

    with patch.object(
        bot_service.control, "get_bot_status", new_callable=AsyncMock
    ) as mock_status:
        mock_status.return_value = expected_status

        status = await bot_service.get_bot_status(bot_id, user_id)

        assert status == expected_status
        mock_status.assert_called_once_with(bot_id, user_id)


@pytest.mark.asyncio
async def test_is_bot_active_success(bot_service):
    """Test checking if bot is active"""
    bot_id = "bot-123"
    user_id = 1

    with patch.object(
        bot_service.control, "is_bot_active", new_callable=AsyncMock
    ) as mock_active:
        mock_active.return_value = True

        result = await bot_service.is_bot_active(bot_id, user_id)

        assert result is True
        mock_active.assert_called_once_with(bot_id, user_id)


@pytest.mark.asyncio
async def test_check_bot_health_success(bot_service):
    """Test checking bot health"""
    bot_id = "bot-123"
    user_id = 1
    expected_health = {"status": "healthy", "last_cycle": "2024-01-01T00:00:00Z"}

    with patch.object(
        bot_service.monitoring, "check_bot_health", new_callable=AsyncMock
    ) as mock_health:
        mock_health.return_value = expected_health

        health = await bot_service.check_bot_health(bot_id, user_id)

        assert health == expected_health
        mock_health.assert_called_once_with(bot_id, user_id)


@pytest.mark.asyncio
async def test_get_bot_performance_success(bot_service):
    """Test getting bot performance"""
    bot_id = "bot-123"
    user_id = 1
    expected_performance = {
        "total_trades": 10,
        "winning_trades": 7,
        "losing_trades": 3,
        "win_rate": 0.7,
        "total_pnl": 1000.0,
        "max_drawdown": 50.0,
        "sharpe_ratio": 1.5,
        "current_balance": 2000.0,
    }

    # get_bot_performance is now implemented in BotMonitoringService
    with patch.object(
        bot_service.monitoring, "get_bot_performance", new_callable=AsyncMock
    ) as mock_perf:
        mock_perf.return_value = expected_performance

        performance = await bot_service.get_bot_performance(bot_id, user_id)

        assert performance == expected_performance
        mock_perf.assert_called_once_with(bot_id, user_id)


@pytest.mark.asyncio
async def test_create_bot_validation_error(bot_service):
    """Test bot creation with invalid parameters"""
    with patch.object(
        bot_service.creation, "create_bot", new_callable=AsyncMock
    ) as mock_create:
        mock_create.return_value = None

        bot_id = await bot_service.create_bot(
            user_id=1, name="", symbol="BTC/USDT", strategy="simple_ma", parameters={}
        )

        # Should return None on validation error
        assert bot_id is None or bot_id == ""


@pytest.mark.asyncio
async def test_get_bot_config_not_found(bot_service):
    """Test getting config for non-existent bot"""
    with patch.object(
        bot_service.creation, "get_bot_config", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = None

        config = await bot_service.get_bot_config("nonexistent", 1)

        assert config is None
