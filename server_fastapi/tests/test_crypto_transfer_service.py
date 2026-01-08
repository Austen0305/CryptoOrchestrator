"""
Crypto Transfer Service Tests
Unit tests for crypto transfer service
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from server_fastapi.repositories.transaction_repository import TransactionRepository
from server_fastapi.repositories.wallet_balance_repository import (
    WalletBalanceRepository,
)
from server_fastapi.services.crypto_transfer_service import CryptoTransferService


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return MagicMock(spec=AsyncSession)


@pytest.fixture
def mock_wallet_repo():
    """Mock wallet balance repository"""
    repo = MagicMock(spec=WalletBalanceRepository)
    mock_wallet = MagicMock()
    mock_wallet.id = 1
    mock_wallet.available_balance = 100.0
    mock_wallet.locked_balance = 0.0
    mock_wallet.currency = "ETH"
    repo.get_or_create_wallet = AsyncMock(return_value=mock_wallet)
    repo.get_by_id = AsyncMock(return_value=mock_wallet)
    repo.update_balance = AsyncMock(return_value=mock_wallet)
    return repo


@pytest.fixture
def mock_transaction_repo():
    """Mock transaction repository"""
    repo = MagicMock(spec=TransactionRepository)
    repo.create_transaction = AsyncMock(
        return_value=MagicMock(id=1, tx_hash="0xabcd", status="pending")
    )
    return repo


@pytest.fixture
def crypto_transfer_service(mock_db_session, mock_wallet_repo, mock_transaction_repo):
    """Create CryptoTransferService instance with mocked dependencies"""
    return CryptoTransferService(
        db=mock_db_session,
        wallet_repository=mock_wallet_repo,
        transaction_repository=mock_transaction_repo,
    )


@pytest.mark.asyncio
async def test_initiate_crypto_transfer_success(
    crypto_transfer_service, mock_wallet_repo, mock_transaction_repo
):
    """Test successful crypto transfer initiation"""
    user_id = 1
    currency = "ETH"
    amount = 100.0
    source_platform = "external_wallet"

    result = await crypto_transfer_service.initiate_crypto_transfer(
        user_id=user_id,
        currency=currency,
        amount=amount,
        source_platform=source_platform,
    )

    assert "transaction_id" in result
    assert result["status"] == "pending"
    assert result["amount"] == amount
    mock_transaction_repo.create_transaction.assert_called_once()


@pytest.mark.asyncio
async def test_withdraw_crypto_success(
    crypto_transfer_service, mock_wallet_repo, mock_transaction_repo
):
    """Test successful crypto withdrawal"""
    user_id = 1
    currency = "ETH"
    amount = 50.0
    destination_address = "0x5678"

    # Mock wallet with sufficient balance
    mock_wallet = MagicMock()
    mock_wallet.id = 1
    mock_wallet.available_balance = 100.0
    mock_wallet.locked_balance = 0.0
    mock_wallet_repo.get_or_create_wallet.return_value = mock_wallet

    result = await crypto_transfer_service.withdraw_crypto(
        user_id=user_id,
        currency=currency,
        amount=amount,
        destination_address=destination_address,
    )

    assert "transaction_id" in result
    assert result["status"] == "processing"
    assert result["amount"] == amount
    mock_transaction_repo.create_transaction.assert_called_once()
