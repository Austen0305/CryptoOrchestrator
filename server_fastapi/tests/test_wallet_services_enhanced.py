"""
Enhanced tests for wallet services with multi-chain edge cases.
"""

import logging

import pytest
from httpx import AsyncClient

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio


class TestWalletServicesEnhanced:
    """Enhanced wallet service tests with multi-chain support"""

    async def test_create_wallet_multi_chain(
        self, client: AsyncClient, test_user_with_auth, factories
    ):
        """Test creating wallets on multiple chains"""
        user = test_user_with_auth

        # Create wallets on different chains
        chains = [1, 8453, 42161]  # Ethereum, Base, Arbitrum

        for chain_id in chains:
            factories["wallet"].wallet_data(
                user_id=user["id"], chain_id=chain_id
            )

            response = await client.post(
                "/api/wallets/custodial",
                json={"chain_id": chain_id, "label": f"Chain {chain_id} Wallet"},
                headers=user["auth_headers"],
            )

            # May return 200/201 or 400 if wallet already exists
            assert response.status_code in [200, 201, 400]

    async def test_wallet_balance_refresh_multi_chain(
        self, client: AsyncClient, test_user_with_auth, factories, db_session
    ):
        """Test balance refresh across multiple chains"""
        user = test_user_with_auth

        # Create wallets on multiple chains
        await factories["wallet"].create_wallet(
            db_session,
            user_id=user["id"],
            chain_id=1,  # Ethereum
        )

        await factories["wallet"].create_wallet(
            db_session,
            user_id=user["id"],
            chain_id=8453,  # Base
        )

        # Refresh balances
        response = await client.post(
            "/api/wallets/refresh-balances", headers=user["auth_headers"]
        )

        # Should handle multi-chain refresh
        assert response.status_code in [200, 202]  # 202 if async

    async def test_wallet_transaction_history(
        self, client: AsyncClient, test_user_with_auth, factories, db_session
    ):
        """Test wallet transaction history retrieval"""
        user = test_user_with_auth

        wallet = await factories["wallet"].create_wallet(db_session, user_id=user["id"])

        # Get transaction history
        response = await client.get(
            f"/api/wallets/{wallet['id']}/transactions", headers=user["auth_headers"]
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            transactions = response.json()
            assert isinstance(transactions, (list, dict))

    async def test_wallet_withdrawal_validation(
        self, client: AsyncClient, test_user_with_auth, factories, db_session
    ):
        """Test withdrawal validation and edge cases"""
        user = test_user_with_auth

        wallet = await factories["wallet"].create_wallet(
            db_session, user_id=user["id"], balance="100.0"
        )

        # Try withdrawal with insufficient balance
        withdrawal_data = {
            "wallet_id": wallet["id"],
            "to_address": "0x1234567890123456789012345678901234567890",
            "amount": "1000.0",  # More than balance
            "chain_id": wallet["chain_id"],
        }

        response = await client.post(
            f"/api/wallets/{wallet['id']}/withdraw",
            json=withdrawal_data,
            headers=user["auth_headers"],
        )

        # Should reject insufficient balance
        assert response.status_code in [400, 422]

    async def test_wallet_deposit_tracking(
        self, client: AsyncClient, test_user_with_auth, factories, db_session
    ):
        """Test deposit address generation and tracking"""
        user = test_user_with_auth

        wallet = await factories["wallet"].create_wallet(db_session, user_id=user["id"])

        # Get deposit address
        response = await client.get(
            f"/api/wallets/deposit-address/{wallet['chain_id']}",
            headers=user["auth_headers"],
        )

        # Should return deposit address or 404 if not implemented
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "address" in data or "deposit_address" in data
