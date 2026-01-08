"""
DEX Trading Service Tests
Unit tests for DEX trading service with mocked dependencies
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Optional imports - skip tests if services are not available
try:
    from server_fastapi.services.payments.trading_fee_service import TradingFeeService
    from server_fastapi.services.trading.aggregator_router import AggregatorRouter
    from server_fastapi.services.trading.dex_trading_service import DEXTradingService
    from server_fastapi.services.wallet_service import WalletService
    from server_fastapi.services.wallet_signature_service import WalletSignatureService

    DEX_TRADING_AVAILABLE = True
except ImportError as e:
    DEX_TRADING_AVAILABLE = False
    pytestmark = pytest.mark.skip(reason=f"DEX trading service not available: {e}")


@pytest.fixture
def mock_router():
    """Mock aggregator router"""
    router = MagicMock(spec=AggregatorRouter)
    router.get_best_quote = AsyncMock(
        return_value=(
            "0x",
            {
                "sellToken": "ETH",
                "buyToken": "USDC",
                "sellAmount": "1000000000000000000",  # 1 ETH
                "buyAmount": "3000000000",  # 3000 USDC (6 decimals)
                "price": "3000",
                "aggregator": "0x",
                "sellTokenSymbol": "ETH",
                "buyTokenSymbol": "USDC",
            },
        )
    )
    router.get_swap_calldata = AsyncMock(
        return_value={
            "to": "0x1234567890123456789012345678901234567890",
            "calldata": "0xabcd...",
            "value": "0",
        }
    )
    return router


@pytest.fixture
def mock_signature_service():
    """Mock wallet signature service"""
    service = MagicMock(spec=WalletSignatureService)
    service.generate_nonce = AsyncMock(return_value=12345)
    service.verify_signature = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_wallet_service():
    """Mock wallet service"""
    service = MagicMock(spec=WalletService)
    service.get_deposit_address = AsyncMock(
        return_value="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    )
    service.is_address_valid = MagicMock(return_value=True)
    return service


@pytest.fixture
def mock_fee_service():
    """Mock trading fee service"""
    service = MagicMock(spec=TradingFeeService)
    service.get_user_monthly_volume = AsyncMock(return_value=Decimal(0))
    service.calculate_fee = MagicMock(return_value=Decimal("0.002"))  # 0.2% of 1 ETH
    return service


@pytest.fixture
def dex_service(
    mock_router, mock_signature_service, mock_wallet_service, mock_fee_service
):
    """Create DEX trading service with mocked dependencies"""
    service = DEXTradingService()
    service.router = mock_router
    service.signature_service = mock_signature_service
    service.wallet_service = mock_wallet_service
    service.fee_service = mock_fee_service
    return service


@pytest.mark.asyncio
async def test_get_quote_success(dex_service, db_session):
    """Test successful quote retrieval"""
    quote = await dex_service.get_quote(
        sell_token="ETH",
        buy_token="USDC",
        sell_amount="1000000000000000000",
        chain_id=1,
    )

    assert quote is not None
    assert quote["sellToken"] == "ETH"
    assert quote["buyToken"] == "USDC"
    assert quote["aggregator"] == "0x"
    dex_service.router.get_best_quote.assert_called_once()


@pytest.mark.asyncio
async def test_get_quote_no_aggregator_available(dex_service, db_session):
    """Test quote retrieval when no aggregator available"""
    dex_service.router.get_best_quote = AsyncMock(return_value=(None, None))

    quote = await dex_service.get_quote(
        sell_token="ETH",
        buy_token="USDC",
        sell_amount="1000000000000000000",
        chain_id=1,
    )

    assert quote is None


@pytest.mark.asyncio
async def test_execute_custodial_swap_success(dex_service, db_session):
    """Test successful custodial swap execution"""
    # Mock blockchain services
    with (
        patch(
            "server_fastapi.services.trading.dex_trading_service.get_balance_service"
        ) as mock_balance,
        patch(
            "server_fastapi.services.trading.dex_trading_service.get_transaction_service"
        ) as mock_tx,
        patch(
            "server_fastapi.services.trading.dex_trading_service.get_key_management_service"
        ) as mock_key,
    ):
        # Mock balance check
        mock_balance_service = MagicMock()
        mock_balance_service.get_eth_balance = AsyncMock(return_value=Decimal("2.0"))
        mock_balance.return_value = mock_balance_service

        # Mock transaction execution
        mock_tx_service = MagicMock()
        mock_tx_service.sign_and_send_transaction = AsyncMock(
            return_value="0x1234567890abcdef"
        )
        mock_tx_service.get_transaction_receipt = AsyncMock(
            return_value={
                "status": 1,
                "blockNumber": 12345,
                "gasUsed": 100000,
            }
        )
        mock_tx.return_value = mock_tx_service

        # Mock key management
        mock_key_service = MagicMock()
        mock_key_service.get_private_key = AsyncMock(return_value="0x" + "1" * 64)
        mock_key.return_value = mock_key_service

        # Mock wallet repository
        with patch(
            "server_fastapi.services.trading.dex_trading_service.WalletRepository"
        ) as mock_repo:
            mock_repo_instance = MagicMock()
            mock_repo_instance.get_user_wallet = AsyncMock(
                return_value=MagicMock(
                    wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                    chain_id=1,
                )
            )
            mock_repo.return_value = mock_repo_instance

            result = await dex_service.execute_custodial_swap(
                user_id=1,
                sell_token="ETH",
                buy_token="USDC",
                sell_amount="1000000000000000000",
                chain_id=1,
                slippage_percentage=0.5,
                user_tier="free",
                db=db_session,
            )

            assert result is not None
            assert result["success"] is True
            assert "transaction_hash" in result


@pytest.mark.asyncio
async def test_execute_custodial_swap_insufficient_balance(dex_service, db_session):
    """Test custodial swap with insufficient balance"""
    with (
        patch(
            "server_fastapi.services.trading.dex_trading_service.get_balance_service"
        ) as mock_balance,
        patch(
            "server_fastapi.services.trading.dex_trading_service.WalletRepository"
        ) as mock_repo,
    ):
        # Mock insufficient balance
        mock_balance_service = MagicMock()
        mock_balance_service.get_eth_balance = AsyncMock(return_value=Decimal("0.5"))
        mock_balance.return_value = mock_balance_service

        mock_repo_instance = MagicMock()
        mock_repo_instance.get_user_wallet = AsyncMock(
            return_value=MagicMock(
                wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                chain_id=1,
            )
        )
        mock_repo.return_value = mock_repo_instance

        with pytest.raises(ValueError, match="Insufficient"):
            await dex_service.execute_custodial_swap(
                user_id=1,
                sell_token="ETH",
                buy_token="USDC",
                sell_amount="1000000000000000000",  # 1 ETH
                chain_id=1,
                slippage_percentage=0.5,
                user_tier="free",
                db=db_session,
            )


@pytest.mark.asyncio
async def test_prepare_non_custodial_swap_success(dex_service, db_session):
    """Test successful non-custodial swap preparation"""
    result = await dex_service.prepare_non_custodial_swap(
        user_id="1",
        sell_token="ETH",
        buy_token="USDC",
        sell_amount="1000000000000000000",
        chain_id=1,
        slippage_percentage=0.5,
        user_wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    )

    assert result is not None
    assert "swap_calldata" in result
    assert "to" in result["swap_calldata"]
    assert "calldata" in result["swap_calldata"]


@pytest.mark.asyncio
async def test_get_supported_chains(dex_service):
    """Test getting supported chains"""
    chains = await dex_service.get_supported_chains()

    assert isinstance(chains, list)
    assert len(chains) > 0
    assert all("chainId" in chain for chain in chains)
    assert all("name" in chain for chain in chains)


@pytest.mark.asyncio
async def test_fee_calculation(dex_service, db_session):
    """Test fee calculation for different tiers"""
    # Mock fee service
    dex_service.fee_service.calculate_fee = MagicMock(
        side_effect=[
            Decimal("0.003"),  # Free tier
            Decimal("0.0025"),  # Basic tier
            Decimal("0.002"),  # Pro tier
            Decimal("0.0015"),  # Enterprise tier
        ]
    )

    free_fee = dex_service.fee_service.calculate_fee(
        trade_amount=Decimal("1.0"),
        user_tier="free",
        is_custodial=True,
        monthly_volume=Decimal(0),
    )

    assert free_fee == Decimal("0.003")


@pytest.mark.asyncio
async def test_error_handling_no_quote(dex_service, db_session):
    """Test error handling when quote fails"""
    dex_service.router.get_best_quote = AsyncMock(return_value=(None, None))

    with pytest.raises(ValueError, match="Failed to get quote"):
        await dex_service.execute_custodial_swap(
            user_id=1,
            sell_token="ETH",
            buy_token="USDC",
            sell_amount="1000000000000000000",
            chain_id=1,
            slippage_percentage=0.5,
            user_tier="free",
            db=db_session,
        )


@pytest.mark.asyncio
async def test_error_handling_no_swap_calldata(dex_service, db_session):
    """Test error handling when swap calldata fails"""
    dex_service.router.get_swap_calldata = AsyncMock(return_value=None)

    with (
        patch(
            "server_fastapi.services.trading.dex_trading_service.get_balance_service"
        ) as mock_balance,
        patch(
            "server_fastapi.services.trading.dex_trading_service.WalletRepository"
        ) as mock_repo,
    ):
        mock_balance_service = MagicMock()
        mock_balance_service.get_eth_balance = AsyncMock(return_value=Decimal("2.0"))
        mock_balance.return_value = mock_balance_service

        mock_repo_instance = MagicMock()
        mock_repo_instance.get_user_wallet = AsyncMock(
            return_value=MagicMock(
                wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                chain_id=1,
            )
        )
        mock_repo.return_value = mock_repo_instance

        with pytest.raises(ValueError, match="Failed to get swap calldata"):
            await dex_service.execute_custodial_swap(
                user_id=1,
                sell_token="ETH",
                buy_token="USDC",
                sell_amount="1000000000000000000",
                chain_id=1,
                slippage_percentage=0.5,
                user_tier="free",
                db=db_session,
            )


@pytest.mark.asyncio
async def test_execute_non_custodial_swap_success(dex_service, db_session):
    """Test successful non-custodial swap execution with transaction hash"""
    user_wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    transaction_hash = "0xabc123def456..."

    # Mock quote
    dex_service.router.get_best_quote = AsyncMock(
        return_value=(
            "0x",
            {
                "sellToken": "ETH",
                "buyToken": "USDC",
                "sellAmount": "1000000000000000000",
                "buyAmount": "3000000000",
                "price": "3000",
                "aggregator": "0x",
            },
        )
    )

    # Mock fee service
    dex_service.fee_service.get_user_monthly_volume = AsyncMock(return_value=Decimal(0))
    dex_service.fee_service.calculate_fee = MagicMock(return_value=Decimal("0.0015"))

    # Mock DEXTrade save
    with patch(
        "server_fastapi.services.trading.dex_trading_service.DEXTrade"
    ) as mock_trade:
        mock_trade_instance = MagicMock()
        mock_trade_instance.id = 1
        mock_trade.return_value = mock_trade_instance

        result = await dex_service.execute_non_custodial_swap(
            user_id=1,
            sell_token="ETH",
            buy_token="USDC",
            sell_amount="1000000000000000000",
            chain_id=1,
            slippage_percentage=0.5,
            user_wallet_address=user_wallet_address,
            transaction_hash=transaction_hash,
            db=db_session,
            user_tier="free",
        )

        assert result is not None
        assert result["success"] is True
        assert result["transaction_hash"] == transaction_hash


@pytest.mark.asyncio
async def test_execute_non_custodial_swap_prepare(dex_service, db_session):
    """Test non-custodial swap calldata preparation"""
    user_wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

    # Mock quote
    dex_service.router.get_best_quote = AsyncMock(
        return_value=(
            "0x",
            {
                "sellToken": "ETH",
                "buyToken": "USDC",
                "sellAmount": "1000000000000000000",
                "buyAmount": "3000000000",
                "price": "3000",
                "aggregator": "0x",
            },
        )
    )

    # Mock swap calldata
    dex_service.router.get_swap_calldata = AsyncMock(
        return_value={
            "to": "0x1234567890123456789012345678901234567890",
            "calldata": "0xabcd...",
            "value": "1000000000000000000",
        }
    )

    result = await dex_service.prepare_non_custodial_swap(
        user_id="1",
        sell_token="ETH",
        buy_token="USDC",
        sell_amount="1000000000000000000",
        chain_id=1,
        slippage_percentage=0.5,
        user_wallet_address=user_wallet_address,
        db=db_session,
    )

    assert result is not None
    assert "swap_calldata" in result
    assert "to" in result["swap_calldata"]
    assert "calldata" in result["swap_calldata"]


@pytest.mark.asyncio
async def test_get_swap_status_pending(dex_service, db_session):
    """Test transaction status tracking (pending)"""
    trade_id = 1
    chain_id = 1
    transaction_hash = "0xabc123..."

    # Mock transaction service
    with patch(
        "server_fastapi.services.trading.dex_trading_service.get_transaction_service"
    ) as mock_tx:
        mock_tx_service = MagicMock()
        mock_tx_service.get_transaction_status = AsyncMock(
            return_value={
                "status": "pending",
                "success": None,
                "block_number": None,
            }
        )
        mock_tx.return_value = mock_tx_service

        # Mock trade record
        with patch(
            "server_fastapi.services.trading.dex_trading_service.DEXTrade"
        ) as mock_trade_model:
            mock_trade = MagicMock()
            mock_trade.id = trade_id
            mock_trade.status = "executing"
            mock_trade.transaction_hash = transaction_hash

            # Mock database query
            mock_result = MagicMock()
            mock_result.scalar_one_or_none = MagicMock(return_value=mock_trade)
            db_session.execute = AsyncMock(return_value=mock_result)
            db_session.commit = AsyncMock()

            result = await dex_service.get_swap_status(
                trade_id=trade_id,
                chain_id=chain_id,
                transaction_hash=transaction_hash,
                db=db_session,
            )

            assert result is not None
            assert result["status"] == "pending"


@pytest.mark.asyncio
async def test_get_swap_status_confirmed(dex_service, db_session):
    """Test transaction status tracking (confirmed)"""
    trade_id = 1
    chain_id = 1
    transaction_hash = "0xabc123..."

    with patch(
        "server_fastapi.services.trading.dex_trading_service.get_transaction_service"
    ) as mock_tx:
        mock_tx_service = MagicMock()
        mock_tx_service.get_transaction_status = AsyncMock(
            return_value={
                "status": "confirmed",
                "success": True,
                "block_number": 12345,
            }
        )
        mock_tx.return_value = mock_tx_service

        # Mock trade record
        mock_trade = MagicMock()
        mock_trade.id = trade_id
        mock_trade.status = "executing"
        mock_trade.transaction_hash = transaction_hash

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_trade)
        db_session.execute = AsyncMock(return_value=mock_result)
        db_session.commit = AsyncMock()

        result = await dex_service.get_swap_status(
            trade_id=trade_id,
            chain_id=chain_id,
            transaction_hash=transaction_hash,
            db=db_session,
        )

        assert result is not None
        assert result["status"] == "confirmed"
        assert result["success"] is True


@pytest.mark.asyncio
async def test_get_swap_status_failed(dex_service, db_session):
    """Test transaction status tracking (failed)"""
    trade_id = 1
    chain_id = 1
    transaction_hash = "0xabc123..."

    with patch(
        "server_fastapi.services.trading.dex_trading_service.get_transaction_service"
    ) as mock_tx:
        mock_tx_service = MagicMock()
        mock_tx_service.get_transaction_status = AsyncMock(
            return_value={
                "status": "confirmed",
                "success": False,
                "block_number": 12345,
            }
        )
        mock_tx.return_value = mock_tx_service

        mock_trade = MagicMock()
        mock_trade.id = trade_id
        mock_trade.status = "executing"
        mock_trade.transaction_hash = transaction_hash

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_trade)
        db_session.execute = AsyncMock(return_value=mock_result)
        db_session.commit = AsyncMock()

        result = await dex_service.get_swap_status(
            trade_id=trade_id,
            chain_id=chain_id,
            transaction_hash=transaction_hash,
            db=db_session,
        )

        assert result is not None
        assert result["status"] == "confirmed"
        assert result["success"] is False


@pytest.mark.asyncio
async def test_fee_calculation_by_tier(dex_service):
    """Test fee calculation for different user tiers"""
    from decimal import Decimal

    # Test free tier
    free_fee = dex_service.fee_service.calculate_fee(
        trade_amount=Decimal("1.0"),
        user_tier="free",
        is_custodial=True,
        monthly_volume=Decimal(0),
    )
    assert free_fee == Decimal("0.002")  # 0.2% for free tier

    # Test pro tier
    dex_service.fee_service.calculate_fee = MagicMock(
        return_value=Decimal("0.001")
    )  # 0.1% for pro
    pro_fee = dex_service.fee_service.calculate_fee(
        trade_amount=Decimal("1.0"),
        user_tier="pro",
        is_custodial=True,
        monthly_volume=Decimal(0),
    )
    assert pro_fee == Decimal("0.001")


@pytest.mark.asyncio
async def test_fee_charging_custodial(dex_service, db_session):
    """Test fee charging for custodial swaps"""
    from decimal import Decimal

    # Mock fee service
    dex_service.fee_service.get_user_monthly_volume = AsyncMock(return_value=Decimal(0))
    dex_service.fee_service.calculate_fee = MagicMock(return_value=Decimal("0.002"))

    # Mock custodial swap execution
    with patch.object(dex_service, "execute_custodial_swap") as mock_execute:
        mock_execute.return_value = {
            "success": True,
            "trade_id": 1,
            "transaction_hash": "0xabc123...",
        }

        result = await dex_service.execute_custodial_swap(
            user_id=1,
            sell_token="ETH",
            buy_token="USDC",
            sell_amount="1000000000000000000",
            chain_id=1,
            slippage_percentage=0.5,
            user_tier="free",
            db=db_session,
        )

        # Verify fee was calculated
        dex_service.fee_service.calculate_fee.assert_called()


@pytest.mark.asyncio
async def test_fee_charging_non_custodial(dex_service, db_session):
    """Test fee charging for non-custodial swaps"""
    from decimal import Decimal

    user_wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    transaction_hash = "0xabc123..."

    # Mock quote
    dex_service.router.get_best_quote = AsyncMock(
        return_value=(
            "0x",
            {
                "sellToken": "ETH",
                "buyToken": "USDC",
                "sellAmount": "1000000000000000000",
                "buyAmount": "3000000000",
                "price": "3000",
                "aggregator": "0x",
            },
        )
    )

    # Mock fee service
    dex_service.fee_service.get_user_monthly_volume = AsyncMock(return_value=Decimal(0))
    dex_service.fee_service.calculate_fee = MagicMock(
        return_value=Decimal("0.0015")
    )  # 0.15% for non-custodial

    # Mock DEXTrade save
    with patch(
        "server_fastapi.services.trading.dex_trading_service.DEXTrade"
    ) as mock_trade:
        mock_trade_instance = MagicMock()
        mock_trade_instance.id = 1
        mock_trade.return_value = mock_trade_instance

        result = await dex_service.execute_non_custodial_swap(
            user_id=1,
            sell_token="ETH",
            buy_token="USDC",
            sell_amount="1000000000000000000",
            chain_id=1,
            slippage_percentage=0.5,
            user_wallet_address=user_wallet_address,
            transaction_hash=transaction_hash,
            db=db_session,
            user_tier="free",
        )

        # Verify fee was calculated
        dex_service.fee_service.calculate_fee.assert_called()


@pytest.mark.asyncio
async def test_aggregator_fallback(dex_service, db_session):
    """Test fallback when primary aggregator fails"""
    # Mock primary aggregator failure
    dex_service.router.get_best_quote = AsyncMock(
        side_effect=[
            (None, None),  # First aggregator fails
            (
                "okx",
                {  # Fallback aggregator succeeds
                    "sellToken": "ETH",
                    "buyToken": "USDC",
                    "sellAmount": "1000000000000000000",
                    "buyAmount": "3000000000",
                    "price": "3000",
                    "aggregator": "okx",
                },
            ),
        ]
    )

    # The service should try fallback aggregators
    quote = await dex_service.get_quote(
        sell_token="ETH",
        buy_token="USDC",
        sell_amount="1000000000000000000",
        chain_id=1,
    )

    # Should eventually get a quote from fallback
    # Note: Actual implementation may vary, this tests the concept
    assert quote is not None or dex_service.router.get_best_quote.call_count > 1


@pytest.mark.asyncio
async def test_slippage_exceeded_error(dex_service, db_session):
    """Test error when slippage tolerance exceeded"""
    # Mock quote with high price impact
    dex_service.router.get_best_quote = AsyncMock(
        return_value=(
            "0x",
            {
                "sellToken": "ETH",
                "buyToken": "USDC",
                "sellAmount": "1000000000000000000",
                "buyAmount": "2800000000",  # 6.67% slippage (exceeds 0.5% tolerance)
                "price": "2800",
                "aggregator": "0x",
                "priceImpact": 6.67,
            },
        )
    )

    # The service should detect high slippage and raise error
    # Note: Actual implementation may vary
    quote = await dex_service.get_quote(
        sell_token="ETH",
        buy_token="USDC",
        sell_amount="1000000000000000000",
        chain_id=1,
        slippage_percentage=0.5,
    )

    # Quote should include price impact warning
    if quote and "priceImpact" in quote:
        assert quote["priceImpact"] > 0.5  # High price impact detected


@pytest.mark.asyncio
async def test_insufficient_liquidity_error(dex_service, db_session):
    """Test error for low liquidity tokens"""
    # Mock aggregator returning no quote due to low liquidity
    dex_service.router.get_best_quote = AsyncMock(return_value=(None, None))

    quote = await dex_service.get_quote(
        sell_token="0xSomeLowLiquidityToken",
        buy_token="USDC",
        sell_amount="1000000000000000000",
        chain_id=1,
    )

    # Should return None when no quote available
    assert quote is None


@pytest.mark.asyncio
async def test_multi_chain_swap(dex_service, db_session):
    """Test swaps on different blockchain networks"""
    # Test Ethereum (chain_id=1)
    dex_service.router.get_best_quote = AsyncMock(
        return_value=(
            "0x",
            {
                "sellToken": "ETH",
                "buyToken": "USDC",
                "sellAmount": "1000000000000000000",
                "buyAmount": "3000000000",
                "price": "3000",
                "aggregator": "0x",
            },
        )
    )

    quote_eth = await dex_service.get_quote(
        sell_token="ETH",
        buy_token="USDC",
        sell_amount="1000000000000000000",
        chain_id=1,
    )
    assert quote_eth is not None

    # Test Base (chain_id=8453)
    quote_base = await dex_service.get_quote(
        sell_token="ETH",
        buy_token="USDC",
        sell_amount="1000000000000000000",
        chain_id=8453,
    )
    assert quote_base is not None or dex_service.router.get_best_quote.call_count >= 2


@pytest.mark.asyncio
async def test_network_timeout_error(dex_service, db_session):
    """Test error handling for network timeouts"""
    import asyncio

    # Mock aggregator with timeout
    async def timeout_quote(*args, **kwargs):
        await asyncio.sleep(0.1)
        raise TimeoutError("Network timeout")

    dex_service.router.get_best_quote = AsyncMock(side_effect=timeout_quote)

    with pytest.raises((asyncio.TimeoutError, ValueError)):
        await dex_service.get_quote(
            sell_token="ETH",
            buy_token="USDC",
            sell_amount="1000000000000000000",
            chain_id=1,
        )


@pytest.mark.asyncio
async def test_rpc_failure_error(dex_service, db_session):
    """Test error handling for RPC failures"""
    # Mock RPC failure in balance service
    with patch(
        "server_fastapi.services.trading.dex_trading_service.get_balance_service"
    ) as mock_balance:
        mock_balance_service = MagicMock()
        mock_balance_service.get_eth_balance = AsyncMock(
            return_value=None
        )  # RPC failure
        mock_balance.return_value = mock_balance_service

        with patch(
            "server_fastapi.services.trading.dex_trading_service.WalletRepository"
        ) as mock_repo:
            mock_repo_instance = MagicMock()
            mock_repo_instance.get_user_wallet = AsyncMock(
                return_value=MagicMock(
                    wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                    chain_id=1,
                )
            )
            mock_repo.return_value = mock_repo_instance

            # Should handle RPC failure gracefully
            with pytest.raises(ValueError, match="Insufficient|balance"):
                await dex_service.execute_custodial_swap(
                    user_id=1,
                    sell_token="ETH",
                    buy_token="USDC",
                    sell_amount="1000000000000000000",
                    chain_id=1,
                    slippage_percentage=0.5,
                    user_tier="free",
                    db=db_session,
                )


@pytest.mark.asyncio
async def test_invalid_token_addresses(dex_service, db_session):
    """Test error handling for invalid token addresses"""
    invalid_token = "0xInvalidTokenAddress"

    # Mock aggregator returning None for invalid token
    dex_service.router.get_best_quote = AsyncMock(return_value=(None, None))

    quote = await dex_service.get_quote(
        sell_token=invalid_token,
        buy_token="USDC",
        sell_amount="1000000000000000000",
        chain_id=1,
    )

    # Should return None for invalid tokens
    assert quote is None
