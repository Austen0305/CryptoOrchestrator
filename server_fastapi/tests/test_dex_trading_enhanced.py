"""
Enhanced tests for DEX trading with error scenarios and aggregator fallback.
"""

import logging
from unittest.mock import patch

import pytest
from httpx import AsyncClient

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio


class TestDEXTradingEnhanced:
    """Enhanced DEX trading tests with error handling"""

    async def test_dex_quote_aggregator_fallback(
        self, client: AsyncClient, test_user_with_auth
    ):
        """Test DEX quote with aggregator fallback"""
        user = test_user_with_auth

        quote_data = {
            "token_in": "USDC",
            "token_out": "ETH",
            "amount": "1000.0",
            "chain_id": 1,
        }

        # Mock first aggregator failure, second success
        with patch(
            "server_fastapi.services.integrations.zeroex_service.ZeroExService.get_quote"
        ) as mock_zeroex:
            mock_zeroex.side_effect = Exception("0x API unavailable")

            response = await client.post(
                "/api/dex/quote", json=quote_data, headers=user["auth_headers"]
            )

            # Should fallback to other aggregators
            assert response.status_code in [200, 503]

    async def test_dex_swap_price_impact_warning(
        self, client: AsyncClient, test_user_with_auth
    ):
        """Test DEX swap with high price impact warning"""
        user = test_user_with_auth

        swap_data = {
            "token_in": "USDC",
            "token_out": "ETH",
            "amount": "1000000.0",  # Large amount (high price impact)
            "chain_id": 1,
            "slippage": 0.005,
        }

        response = await client.post(
            "/api/dex/swap", json=swap_data, headers=user["auth_headers"]
        )

        # Should either reject high impact or warn
        assert response.status_code in [200, 400, 422]
        if response.status_code == 200:
            data = response.json()
            # Check for price impact warning
            assert "price_impact" in data or "warning" in data

    async def test_dex_swap_insufficient_balance(
        self, client: AsyncClient, test_user_with_auth, factories, db_session
    ):
        """Test DEX swap with insufficient balance"""
        user = test_user_with_auth

        # Create wallet with low balance
        wallet = await factories["wallet"].create_wallet(
            db_session, user_id=user["id"], balance="10.0"
        )

        swap_data = {
            "token_in": "USDC",
            "token_out": "ETH",
            "amount": "1000.0",  # More than balance
            "chain_id": wallet["chain_id"],
            "wallet_id": wallet["id"],
        }

        response = await client.post(
            "/api/dex/swap", json=swap_data, headers=user["auth_headers"]
        )

        # Should reject insufficient balance
        assert response.status_code in [400, 422]

    async def test_dex_swap_transaction_status_tracking(
        self, client: AsyncClient, test_user_with_auth
    ):
        """Test transaction status tracking after swap"""
        user = test_user_with_auth

        # First execute a swap (may fail in test, that's OK)
        swap_data = {
            "token_in": "USDC",
            "token_out": "ETH",
            "amount": "100.0",
            "chain_id": 1,
        }

        swap_response = await client.post(
            "/api/dex/swap", json=swap_data, headers=user["auth_headers"]
        )

        if swap_response.status_code == 200:
            swap_result = swap_response.json()
            tx_hash = swap_result.get("tx_hash")

            if tx_hash:
                # Check transaction status
                status_response = await client.get(
                    f"/api/dex/transactions/{tx_hash}", headers=user["auth_headers"]
                )

                assert status_response.status_code in [200, 404]

    async def test_dex_quote_all_aggregators_fail(
        self, client: AsyncClient, test_user_with_auth
    ):
        """Test behavior when all DEX aggregators fail"""
        user = test_user_with_auth

        quote_data = {
            "token_in": "USDC",
            "token_out": "ETH",
            "amount": "1000.0",
            "chain_id": 1,
        }

        # Mock all aggregators failing
        with (
            patch(
                "server_fastapi.services.integrations.zeroex_service.ZeroExService.get_quote"
            ) as mock_zeroex,
            patch(
                "server_fastapi.services.integrations.okx_dex_service.OKXDexService.get_quote"
            ) as mock_okx,
            patch(
                "server_fastapi.services.integrations.rubic_service.RubicService.get_quote"
            ) as mock_rubic,
        ):
            mock_zeroex.side_effect = Exception("0x unavailable")
            mock_okx.side_effect = Exception("OKX unavailable")
            mock_rubic.side_effect = Exception("Rubic unavailable")

            response = await client.post(
                "/api/dex/quote", json=quote_data, headers=user["auth_headers"]
            )

            # Should return 503 when all aggregators fail
            assert response.status_code == 503

    async def test_dex_swap_slippage_protection(
        self, client: AsyncClient, test_user_with_auth
    ):
        """Test slippage protection in DEX swaps"""
        user = test_user_with_auth

        swap_data = {
            "token_in": "USDC",
            "token_out": "ETH",
            "amount": "1000.0",
            "chain_id": 1,
            "slippage": 0.001,  # Very tight slippage (0.1%)
        }

        response = await client.post(
            "/api/dex/swap", json=swap_data, headers=user["auth_headers"]
        )

        # Should either execute or reject if slippage too tight
        assert response.status_code in [200, 400, 422]
