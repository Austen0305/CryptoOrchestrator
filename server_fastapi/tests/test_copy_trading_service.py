"""
Copy Trading Service Tests
Unit tests for copy trading service
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from server_fastapi.repositories.copy_trading_repository import CopyTradingRepository
from server_fastapi.repositories.trade_repository import TradeRepository
from server_fastapi.services.copy_trading_service import CopyTradingService


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return MagicMock(spec=AsyncSession)


@pytest.fixture
def mock_copy_trading_repo():
    """Mock copy trading repository"""
    repo = MagicMock(spec=CopyTradingRepository)
    repo.follow_trader = AsyncMock(return_value=True)
    repo.unfollow_trader = AsyncMock(return_value=True)
    repo.get_followed_traders = AsyncMock(return_value=[])
    repo.get_copy_trades = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_trade_repo():
    """Mock trade repository"""
    repo = MagicMock(spec=TradeRepository)
    repo.get_user_trades = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def copy_trading_service(mock_db_session, mock_copy_trading_repo, mock_trade_repo):
    """Create CopyTradingService instance with mocked dependencies"""
    return CopyTradingService(
        copy_trading_repo=mock_copy_trading_repo,
        trade_repo=mock_trade_repo,
        db=mock_db_session,
    )


@pytest.mark.asyncio
async def test_follow_trader_success(copy_trading_service, mock_copy_trading_repo):
    """Test successful trader follow"""
    follower_id = 1
    trader_id = 2

    result = await copy_trading_service.follow_trader(follower_id, trader_id)

    assert result is True
    mock_copy_trading_repo.follow_trader.assert_called_once_with(follower_id, trader_id)


@pytest.mark.asyncio
async def test_unfollow_trader_success(copy_trading_service, mock_copy_trading_repo):
    """Test successful trader unfollow"""
    follower_id = 1
    trader_id = 2

    result = await copy_trading_service.unfollow_trader(follower_id, trader_id)

    assert result is True
    mock_copy_trading_repo.unfollow_trader.assert_called_once_with(
        follower_id, trader_id
    )


@pytest.mark.asyncio
async def test_get_followed_traders(copy_trading_service, mock_copy_trading_repo):
    """Test getting followed traders list"""
    follower_id = 1
    mock_copy_trading_repo.get_followed_traders.return_value = [
        {"trader_id": 2, "username": "trader1"},
        {"trader_id": 3, "username": "trader2"},
    ]

    result = await copy_trading_service.get_followed_traders(follower_id)

    assert len(result) == 2
    assert result[0]["trader_id"] == 2
    mock_copy_trading_repo.get_followed_traders.assert_called_once_with(follower_id)
