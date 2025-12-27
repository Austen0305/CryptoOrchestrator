"""
Staking Service Tests
Unit tests for staking service
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from server_fastapi.services.staking_service import StakingService
from server_fastapi.repositories.wallet_repository import WalletRepository


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return MagicMock(spec=AsyncSession)


@pytest.fixture
def mock_wallet_repo():
    """Mock wallet repository"""
    repo = MagicMock(spec=WalletRepository)
    repo.get_user_wallet = AsyncMock(return_value=None)
    repo.create_wallet = AsyncMock(
        return_value=MagicMock(id=1, wallet_address="0x1234")
    )
    return repo


@pytest.fixture
def staking_service(mock_db_session, mock_wallet_repo):
    """Create StakingService instance with mocked dependencies"""
    return StakingService(wallet_repository=mock_wallet_repo, db=mock_db_session)


@pytest.mark.asyncio
async def test_get_staking_options(staking_service):
    """Test getting staking options"""
    options = await staking_service.get_staking_options()

    assert isinstance(options, list)
    # Should return list of staking options with APY, min amount, etc.


@pytest.mark.asyncio
async def test_stake_assets_success(staking_service, mock_wallet_repo):
    """Test successful asset staking"""
    user_id = 1
    asset = "ETH"
    amount = 10.0

    # Mock wallet exists
    mock_wallet_repo.get_user_wallet.return_value = MagicMock(
        id=1, wallet_address="0x1234", chain_id=1
    )

    result = await staking_service.stake_assets(user_id, asset, amount)

    assert "stake_id" in result or "transaction_hash" in result
    assert result.get("amount") == amount


@pytest.mark.asyncio
async def test_calculate_staking_rewards(staking_service):
    """Test staking rewards calculation"""
    user_id = 1
    asset = "ETH"

    result = await staking_service.calculate_staking_rewards(user_id, asset)

    assert "rewards" in result
    assert "apy" in result or "rate" in result
