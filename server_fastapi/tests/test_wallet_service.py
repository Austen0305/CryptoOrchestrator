"""
Wallet Service Tests
Unit tests for wallet management service
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Optional dependency for blockchain features
try:
    from eth_account import Account

    ETH_ACCOUNT_AVAILABLE = True
except ImportError:
    ETH_ACCOUNT_AVAILABLE = False
    Account = None

from server_fastapi.repositories.wallet_repository import WalletRepository
from server_fastapi.services.wallet_service import WalletService


@pytest.fixture
def mock_repository():
    """Mock wallet repository"""
    repo = MagicMock(spec=WalletRepository)
    repo.get_user_wallet = AsyncMock(return_value=None)
    repo.get_user_wallets = AsyncMock(return_value=[])
    repo.create_wallet = AsyncMock(
        return_value=MagicMock(
            id=1,
            wallet_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Valid 42-char address
            chain_id=1,
            wallet_type="custodial",
        )
    )
    return repo


@pytest.fixture
def wallet_service(mock_repository):
    """Create wallet service with mocked repository"""
    service = WalletService()
    service.repository = mock_repository
    return service


@pytest.mark.asyncio
async def test_generate_wallet_address(wallet_service):
    """Test wallet address generation"""
    result = wallet_service.generate_wallet_address()

    assert result is not None
    assert "address" in result
    assert "private_key" in result
    assert result["address"].startswith("0x")
    assert len(result["address"]) == 42  # Ethereum address length


@pytest.mark.asyncio
async def test_is_address_valid(wallet_service):
    """Test address validation"""
    # Generate a valid address if eth-account is available, otherwise use a known valid address
    if ETH_ACCOUNT_AVAILABLE:
        account = Account.create()
        valid_address = account.address
    else:
        # Use a known valid 42-character Ethereum address (Vitalik's address as example)
        valid_address = (
            "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Valid 42-char address
        )
    invalid_address = "0xinvalid"

    assert wallet_service.is_address_valid(valid_address) is True
    assert wallet_service.is_address_valid(invalid_address) is False


@pytest.mark.asyncio
async def test_create_custodial_wallet(wallet_service, db_session, mock_repository):
    """Test creating a custodial wallet"""
    with patch(
        "server_fastapi.services.wallet_service.WalletRepository",
        return_value=mock_repository,
    ):
        result = await wallet_service.create_custodial_wallet(
            user_id=1,
            chain_id=1,
            label="Test Wallet",
            db=db_session,
        )

        assert result is not None
        assert "wallet_id" in result
        assert result["wallet_type"] == "custodial"
        mock_repository.create_wallet.assert_called_once()


@pytest.mark.asyncio
async def test_register_external_wallet(wallet_service, db_session, mock_repository):
    """Test registering an external wallet"""
    # Use a valid 42-character Ethereum address
    if ETH_ACCOUNT_AVAILABLE:
        account = Account.create()
        address = account.address
    else:
        address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Valid 42-char address

    # Update mock to return external wallet type
    mock_repository.create_wallet = AsyncMock(
        return_value=MagicMock(
            id=1,
            wallet_address=address,
            chain_id=1,
            wallet_type="external",
        )
    )
    mock_repository.get_user_wallet = AsyncMock(return_value=None)  # No existing wallet

    with patch(
        "server_fastapi.services.wallet_service.WalletRepository",
        return_value=mock_repository,
    ):
        result = await wallet_service.register_external_wallet(
            user_id=1,
            wallet_address=address,
            chain_id=1,
            label="My MetaMask",
            db=db_session,
        )

        assert result is not None
        assert result["wallet_type"] == "external"
        assert result["address"] == address
        mock_repository.create_wallet.assert_called_once()


@pytest.mark.asyncio
async def test_register_external_wallet_invalid_address(wallet_service, db_session):
    """Test registering external wallet with invalid address"""
    # The service returns None for invalid addresses instead of raising ValueError
    result = await wallet_service.register_external_wallet(
        user_id=1,
        wallet_address="invalid",
        chain_id=1,
        db=db_session,
    )

    # Service returns None for invalid addresses
    assert result is None


@pytest.mark.asyncio
async def test_get_deposit_address_existing(
    wallet_service, db_session, mock_repository
):
    """Test getting existing deposit address"""
    # Use a valid 42-character Ethereum address
    valid_address = (
        "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Valid 42-char address
    )
    mock_repository.get_user_wallet = AsyncMock(
        return_value=MagicMock(
            wallet_address=valid_address,
            chain_id=1,
        )
    )

    with patch(
        "server_fastapi.services.wallet_service.WalletRepository",
        return_value=mock_repository,
    ):
        address = await wallet_service.get_deposit_address(
            user_id=1,
            chain_id=1,
            db=db_session,
        )

        assert address == valid_address


@pytest.mark.asyncio
async def test_get_deposit_address_create_new(
    wallet_service, db_session, mock_repository
):
    """Test creating new deposit address if none exists"""
    # Use a valid 42-character Ethereum address
    valid_address = (
        "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Valid 42-char address
    )
    mock_repository.get_user_wallet = AsyncMock(return_value=None)
    mock_repository.create_wallet = AsyncMock(
        return_value=MagicMock(
            wallet_address=valid_address,
        )
    )

    with patch(
        "server_fastapi.services.wallet_service.WalletRepository",
        return_value=mock_repository,
    ):
        # Mock generate_wallet_address to return a valid address
        with patch.object(
            wallet_service,
            "generate_wallet_address",
            return_value={"address": valid_address},
        ):
            address = await wallet_service.get_deposit_address(
                user_id=1,
                chain_id=1,
                db=db_session,
            )

            assert address is not None
            assert address.startswith("0x")
            mock_repository.create_wallet.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_wallets(wallet_service, db_session, mock_repository):
    """Test getting user wallets"""
    valid_address = (
        "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Valid 42-char address
    )
    mock_wallet = MagicMock(
        id=1,
        wallet_address=valid_address,
        chain_id=1,
        wallet_type="custodial",
        label="Test Wallet",
        is_verified=True,
    )
    mock_wallet.to_dict = lambda: {
        "wallet_id": 1,
        "address": valid_address,
        "chain_id": 1,
        "wallet_type": "custodial",
        "label": "Test Wallet",
        "is_verified": True,
    }

    mock_repository.get_user_wallets = AsyncMock(return_value=[mock_wallet])

    with patch(
        "server_fastapi.services.wallet_service.WalletRepository",
        return_value=mock_repository,
    ):
        wallets = await wallet_service.get_user_wallets(
            user_id=1,
            db=db_session,
        )

        assert isinstance(wallets, list)
        assert len(wallets) > 0
        assert wallets[0]["wallet_type"] == "custodial"


@pytest.mark.asyncio
async def test_get_wallet_balance_eth(wallet_service, db_session):
    """Test ETH balance fetching"""
    from decimal import Decimal
    from unittest.mock import patch

    wallet_id = 1
    chain_id = 1
    address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Valid address

    with (
        patch("server_fastapi.services.wallet_service.BLOCKCHAIN_AVAILABLE", True),
        patch(
            "server_fastapi.services.wallet_service.get_balance_service"
        ) as mock_balance_service,
    ):
        mock_service = MagicMock()
        mock_service.get_eth_balance = AsyncMock(return_value=Decimal("1.5"))
        mock_balance_service.return_value = mock_service

        result = await wallet_service.get_wallet_balance(
            wallet_id=wallet_id,
            chain_id=chain_id,
            address=address,
            db=db_session,
        )

        assert result is not None
        assert "balance" in result
        assert result["balance"] == "1.5"
        assert result["token"] == "ETH"
        assert result["chain_id"] == chain_id
        mock_service.get_eth_balance.assert_called_once()


@pytest.mark.asyncio
async def test_get_wallet_balance_erc20(wallet_service, db_session):
    """Test ERC-20 token balance fetching"""
    from decimal import Decimal
    from unittest.mock import patch

    wallet_id = 1
    chain_id = 1
    address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Valid address
    token_address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"  # USDC

    with (
        patch("server_fastapi.services.wallet_service.BLOCKCHAIN_AVAILABLE", True),
        patch(
            "server_fastapi.services.wallet_service.get_balance_service"
        ) as mock_balance_service,
    ):
        mock_service = MagicMock()
        mock_service.get_token_balance = AsyncMock(return_value=Decimal("1000.0"))
        mock_balance_service.return_value = mock_service

        result = await wallet_service.get_wallet_balance(
            wallet_id=wallet_id,
            chain_id=chain_id,
            address=address,
            token_address=token_address,
            db=db_session,
        )

        assert result is not None
        assert "balance" in result
        assert result["balance"] == "1000.0"
        assert result["token"] == "TOKEN"
        mock_service.get_token_balance.assert_called_once_with(
            chain_id=chain_id,
            address=address,
            token_address=token_address,
            use_cache=True,
        )


@pytest.mark.asyncio
async def test_get_wallet_balance_multi_chain(wallet_service, db_session):
    """Test balance fetching on different chains"""
    from decimal import Decimal
    from unittest.mock import patch

    valid_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Valid address

    # Test Ethereum (chain_id=1)
    with (
        patch("server_fastapi.services.wallet_service.BLOCKCHAIN_AVAILABLE", True),
        patch(
            "server_fastapi.services.wallet_service.get_balance_service"
        ) as mock_balance_service,
    ):
        mock_service = MagicMock()
        mock_service.get_eth_balance = AsyncMock(return_value=Decimal("1.0"))
        mock_balance_service.return_value = mock_service

        result_eth = await wallet_service.get_wallet_balance(
            wallet_id=1,
            chain_id=1,
            address=valid_address,
            db=db_session,
        )
        assert result_eth is not None
        assert result_eth["chain_id"] == 1

    # Test Base (chain_id=8453)
    with (
        patch("server_fastapi.services.wallet_service.BLOCKCHAIN_AVAILABLE", True),
        patch(
            "server_fastapi.services.wallet_service.get_balance_service"
        ) as mock_balance_service,
    ):
        mock_service = MagicMock()
        mock_service.get_eth_balance = AsyncMock(return_value=Decimal("2.0"))
        mock_balance_service.return_value = mock_service

        result_base = await wallet_service.get_wallet_balance(
            wallet_id=2,
            chain_id=8453,
            address=valid_address,
            db=db_session,
        )
        assert result_base is not None
        assert result_base["chain_id"] == 8453


@pytest.mark.asyncio
async def test_get_wallet_balance_network_failure(wallet_service, db_session):
    """Test balance fetching with network failure"""
    from unittest.mock import patch

    with patch(
        "server_fastapi.services.wallet_service.get_balance_service"
    ) as mock_balance_service:
        mock_service = MagicMock()
        mock_service.get_eth_balance = AsyncMock(return_value=None)  # Network failure
        mock_balance_service.return_value = mock_service

        result = await wallet_service.get_wallet_balance(
            wallet_id=1,
            chain_id=1,
            address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            db=db_session,
        )

        assert result is None


@pytest.mark.asyncio
async def test_refresh_wallet_balances(wallet_service, db_session, mock_repository):
    """Test refreshing balances for all user wallets"""
    from decimal import Decimal
    from unittest.mock import patch

    user_id = 1
    valid_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Valid address

    # Mock repository to return multiple wallets
    mock_wallet1 = MagicMock(id=1, wallet_address=valid_address, chain_id=1, balance={})
    mock_wallet2 = MagicMock(
        id=2, wallet_address=valid_address, chain_id=8453, balance={}
    )
    mock_repository.get_user_wallets = AsyncMock(
        return_value=[mock_wallet1, mock_wallet2]
    )
    mock_repository.update_wallet_balance = AsyncMock()

    with (
        patch(
            "server_fastapi.services.wallet_service.WalletRepository",
            return_value=mock_repository,
        ),
        patch("server_fastapi.services.wallet_service.BLOCKCHAIN_AVAILABLE", True),
        patch(
            "server_fastapi.services.wallet_service.get_balance_service"
        ) as mock_balance_service,
    ):
        mock_service = MagicMock()
        mock_service.get_eth_balance = AsyncMock(return_value=Decimal("1.0"))
        mock_balance_service.return_value = mock_service

        results = await wallet_service.refresh_wallet_balances(
            user_id=user_id,
            db=db_session,
        )

        assert isinstance(results, dict)
        assert len(results) == 2
        assert results[1] is True  # Success
        assert results[2] is True  # Success
        assert mock_service.get_eth_balance.call_count == 2


@pytest.mark.asyncio
async def test_refresh_wallet_balances_partial_failure(
    wallet_service, db_session, mock_repository
):
    """Test refresh with some wallets failing"""
    from decimal import Decimal
    from unittest.mock import patch

    user_id = 1
    valid_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Valid address

    mock_wallet1 = MagicMock(id=1, wallet_address=valid_address, chain_id=1, balance={})
    mock_wallet2 = MagicMock(
        id=2, wallet_address=valid_address, chain_id=8453, balance={}
    )
    mock_repository.get_user_wallets = AsyncMock(
        return_value=[mock_wallet1, mock_wallet2]
    )
    mock_repository.update_wallet_balance = AsyncMock()

    with (
        patch(
            "server_fastapi.services.wallet_service.WalletRepository",
            return_value=mock_repository,
        ),
        patch("server_fastapi.services.wallet_service.BLOCKCHAIN_AVAILABLE", True),
        patch(
            "server_fastapi.services.wallet_service.get_balance_service"
        ) as mock_balance_service,
    ):
        mock_service = MagicMock()
        # First call succeeds, second raises exception (network failure)
        mock_service.get_eth_balance = AsyncMock(
            side_effect=[
                Decimal("1.0"),
                Exception("Network error"),  # Network failure - raises exception
            ]
        )
        mock_balance_service.return_value = mock_service

        results = await wallet_service.refresh_wallet_balances(
            user_id=user_id,
            db=db_session,
        )

        assert isinstance(results, dict)
        assert results[1] is True  # Success
        assert results[2] is False  # Failure


@pytest.mark.asyncio
async def test_process_withdrawal_success(wallet_service, db_session, mock_repository):
    """Test successful withdrawal processing"""
    from decimal import Decimal
    from unittest.mock import patch

    wallet_id = 1
    user_id = 1
    to_address = "0x1234567890123456789012345678901234567890"
    amount = Decimal("0.5")
    chain_id = 1

    # Mock wallet repository
    mock_repository.get_user_wallet = AsyncMock(
        return_value=MagicMock(
            id=wallet_id,
            user_id=user_id,
            wallet_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Valid address
            chain_id=chain_id,
            wallet_type="custodial",
            balance={"ETH": "1.0"},
        )
    )

    with (
        patch(
            "server_fastapi.services.wallet_service.WalletRepository",
            return_value=mock_repository,
        ),
        patch.object(
            wallet_service, "get_wallet_balance", new_callable=AsyncMock
        ) as mock_get_balance,
        patch("server_fastapi.services.wallet_service.BLOCKCHAIN_AVAILABLE", True),
        patch(
            "server_fastapi.services.wallet_service.get_transaction_service"
        ) as mock_tx,
    ):
        # Mock balance check
        mock_get_balance.return_value = {
            "balance": "1.0",
            "token_address": None,
            "chain_id": chain_id,
        }

        # Mock transaction execution
        mock_tx_service = MagicMock()
        mock_tx_service.sign_and_send_transaction = AsyncMock(
            return_value="0xabc123..."
        )
        mock_tx.return_value = mock_tx_service

        result = await wallet_service.process_withdrawal(
            wallet_id=wallet_id,
            user_id=user_id,
            to_address=to_address,
            amount=amount,
            chain_id=chain_id,
            db=db_session,
        )

        assert result is not None
        assert "status" in result or "transaction_hash" in result


@pytest.mark.asyncio
async def test_process_withdrawal_insufficient_balance(
    wallet_service, db_session, mock_repository
):
    """Test withdrawal with insufficient balance"""
    from decimal import Decimal
    from unittest.mock import patch

    wallet_id = 1
    user_id = 1
    to_address = "0x1234567890123456789012345678901234567890"
    amount = Decimal("2.0")  # More than available
    chain_id = 1

    mock_repository.get_user_wallet = AsyncMock(
        return_value=MagicMock(
            id=wallet_id,
            user_id=user_id,
            wallet_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Valid address
            chain_id=chain_id,
            wallet_type="custodial",
            balance={"ETH": "1.0"},
        )
    )

    with (
        patch(
            "server_fastapi.services.wallet_service.WalletRepository",
            return_value=mock_repository,
        ),
        patch.object(
            wallet_service, "get_wallet_balance", new_callable=AsyncMock
        ) as mock_get_balance,
    ):
        # Mock get_wallet_balance to return balance info
        mock_get_balance.return_value = {
            "balance": "1.0",
            "token_address": None,
            "chain_id": chain_id,
        }

        with pytest.raises(ValueError, match="Insufficient"):
            await wallet_service.process_withdrawal(
                wallet_id=wallet_id,
                user_id=user_id,
                to_address=to_address,
                amount=amount,
                chain_id=chain_id,
                db=db_session,
            )


@pytest.mark.asyncio
async def test_process_withdrawal_invalid_address(wallet_service, db_session):
    """Test withdrawal to invalid address"""
    from decimal import Decimal

    wallet_id = 1
    user_id = 1
    to_address = "invalid_address"
    amount = Decimal("0.5")
    chain_id = 1

    # No need to mock repository - validation happens before repository access
    with pytest.raises(ValueError, match="Invalid"):
        await wallet_service.process_withdrawal(
            wallet_id=wallet_id,
            user_id=user_id,
            to_address=to_address,
            amount=amount,
            chain_id=chain_id,
            db=db_session,
        )


@pytest.mark.asyncio
async def test_process_withdrawal_wallet_not_found(
    wallet_service, db_session, mock_repository
):
    """Test withdrawal when wallet not found"""
    from decimal import Decimal

    wallet_id = 999
    user_id = 1
    to_address = "0x1234567890123456789012345678901234567890"
    amount = Decimal("0.5")
    chain_id = 1

    mock_repository.get_user_wallet = AsyncMock(return_value=None)

    with patch(
        "server_fastapi.services.wallet_service.WalletRepository",
        return_value=mock_repository,
    ):
        with pytest.raises(ValueError, match="Wallet not found"):
            await wallet_service.process_withdrawal(
                wallet_id=wallet_id,
                user_id=user_id,
                to_address=to_address,
                amount=amount,
                chain_id=chain_id,
                db=db_session,
            )


@pytest.mark.asyncio
async def test_get_wallet_balance_zero_balance(wallet_service, db_session):
    """Test balance fetching with zero balance"""
    from decimal import Decimal
    from unittest.mock import patch

    wallet_id = 1
    chain_id = 1
    address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Valid address

    with (
        patch("server_fastapi.services.wallet_service.BLOCKCHAIN_AVAILABLE", True),
        patch(
            "server_fastapi.services.wallet_service.get_balance_service"
        ) as mock_balance_service,
    ):
        mock_service = MagicMock()
        mock_service.get_eth_balance = AsyncMock(return_value=Decimal("0"))
        mock_balance_service.return_value = mock_service

        result = await wallet_service.get_wallet_balance(
            wallet_id=wallet_id,
            chain_id=chain_id,
            address=address,
            db=db_session,
        )

        assert result is not None
        assert result["balance"] == "0"


@pytest.mark.asyncio
async def test_get_wallet_balance_invalid_chain_id(wallet_service, db_session):
    """Test balance fetching with invalid chain ID"""
    from unittest.mock import patch

    wallet_id = 1
    chain_id = 99999  # Invalid chain ID
    address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

    with patch(
        "server_fastapi.services.wallet_service.get_balance_service"
    ) as mock_balance_service:
        mock_service = MagicMock()
        mock_service.get_eth_balance = AsyncMock(return_value=None)  # RPC error
        mock_balance_service.return_value = mock_service

        wallet_service.repository.get_user_wallet = AsyncMock(
            return_value=MagicMock(
                id=wallet_id,
                wallet_address=address,
                chain_id=chain_id,
                balance={},
            )
        )

        result = await wallet_service.get_wallet_balance(
            wallet_id=wallet_id,
            chain_id=chain_id,
            address=address,
            db=db_session,
        )

        # Should return None on error
        assert result is None


@pytest.mark.asyncio
async def test_get_deposit_address_new_wallet(wallet_service, db_session):
    """Test deposit address for new wallet (creates wallet)"""
    wallet_service.repository.get_user_wallet = AsyncMock(return_value=None)
    wallet_service.repository.create_wallet = AsyncMock(
        return_value=MagicMock(
            wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        )
    )

    # Mock create_custodial_wallet to return wallet info
    with patch.object(wallet_service, "create_custodial_wallet") as mock_create:
        mock_create.return_value = {
            "wallet_id": 1,
            "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            "chain_id": 1,
            "wallet_type": "custodial",
        }

        address = await wallet_service.get_deposit_address(
            user_id=1,
            chain_id=1,
            db=db_session,
        )

        assert address is not None
        assert address == "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_get_deposit_address_existing_wallet(wallet_service, db_session):
    """Test deposit address for existing wallet"""
    existing_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

    # Mock create_custodial_wallet to return existing wallet
    with patch.object(wallet_service, "create_custodial_wallet") as mock_create:
        mock_create.return_value = {
            "wallet_id": 1,
            "address": existing_address,
            "chain_id": 1,
            "wallet_type": "custodial",
        }

        address = await wallet_service.get_deposit_address(
            user_id=1,
            chain_id=1,
            db=db_session,
        )

        assert address == existing_address
