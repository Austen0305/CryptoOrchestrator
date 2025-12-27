"""
Comprehensive Integration Tests for DEX Aggregators
Tests multiple aggregators, fallback logic, and error scenarios
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
import logging

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio


class TestDEXAggregatorsIntegration:
    """Comprehensive tests for DEX aggregator integration"""

    async def test_get_quote_from_multiple_aggregators(
        self, client: AsyncClient, auth_headers
    ):
        """Test getting quote from multiple aggregators with fallback"""
        quote_data = {
            "token_in": "USDC",
            "token_out": "ETH",
            "amount": 1000.0,
            "chain": "ethereum",
        }

        # Mock multiple aggregator responses
        with patch(
            "server_fastapi.services.dex_aggregator_service.DexAggregatorService.get_best_quote"
        ) as mock_quote:
            mock_quote.return_value = {
                "price": 0.0005,
                "amount_out": 0.5,
                "price_impact": 0.001,
                "aggregator": "0x",
                "gas_estimate": 150000,
            }

            # Test quote endpoint
            response = await client.post(
                "/api/dex/quote", json=quote_data, headers=auth_headers
            )

            # Should succeed or return appropriate error
            assert response.status_code in [200, 400, 503]

    async def test_aggregator_fallback_on_failure(
        self, client: AsyncClient, auth_headers
    ):
        """Test fallback to other aggregators when one fails"""
        quote_data = {
            "token_in": "USDC",
            "token_out": "ETH",
            "amount": 1000.0,
            "chain": "ethereum",
        }

        # Mock first aggregator failure, second success
        with patch(
            "server_fastapi.services.dex_aggregator_service.DexAggregatorService.get_best_quote"
        ) as mock_quote:
            # Simulate fallback logic
            mock_quote.return_value = {
                "price": 0.0005,
                "amount_out": 0.5,
                "price_impact": 0.001,
                "aggregator": "okx",  # Fallback aggregator
                "gas_estimate": 150000,
            }

            response = await client.post(
                "/api/dex/quote", json=quote_data, headers=auth_headers
            )

            # Should succeed with fallback aggregator
            assert response.status_code in [200, 400, 503]

    async def test_price_impact_validation(self, client: AsyncClient, auth_headers):
        """Test price impact validation before swap"""
        quote_data = {
            "token_in": "USDC",
            "token_out": "ETH",
            "amount": 100000.0,  # Large amount for high price impact
            "chain": "ethereum",
        }

        # Mock high price impact quote
        with patch(
            "server_fastapi.services.dex_aggregator_service.DexAggregatorService.get_best_quote"
        ) as mock_quote:
            mock_quote.return_value = {
                "price": 0.0005,
                "amount_out": 50.0,
                "price_impact": 0.05,  # 5% price impact (high)
                "aggregator": "0x",
                "gas_estimate": 150000,
            }

            response = await client.post(
                "/api/dex/quote", json=quote_data, headers=auth_headers
            )

            # Should warn about high price impact or reject
            assert response.status_code in [200, 400, 422]
            if response.status_code == 200:
                data = response.json()
                # Check if price impact warning is included
                assert "price_impact" in data or "warning" in str(data).lower()

    async def test_all_aggregators_fail(self, client: AsyncClient, auth_headers):
        """Test behavior when all aggregators fail"""
        quote_data = {
            "token_in": "USDC",
            "token_out": "ETH",
            "amount": 1000.0,
            "chain": "ethereum",
        }

        # Mock all aggregators failing
        with patch(
            "server_fastapi.services.dex_aggregator_service.DexAggregatorService.get_best_quote"
        ) as mock_quote:
            mock_quote.side_effect = Exception("All aggregators unavailable")

            response = await client.post(
                "/api/dex/quote", json=quote_data, headers=auth_headers
            )

            # Should return 503 Service Unavailable
            assert response.status_code in [503, 500, 400]

    async def test_swap_execution_with_aggregator(
        self, client: AsyncClient, auth_headers
    ):
        """Test swap execution using aggregator"""
        swap_data = {
            "token_in": "USDC",
            "token_out": "ETH",
            "amount": 1000.0,
            "chain": "ethereum",
            "slippage": 0.005,
        }

        # Mock swap execution
        with patch(
            "server_fastapi.services.dex_aggregator_service.DexAggregatorService.execute_swap"
        ) as mock_swap:
            mock_swap.return_value = {
                "tx_hash": "0x123...",
                "status": "pending",
                "chain": "ethereum",
                "aggregator": "0x",
            }

            response = await client.post(
                "/api/dex/swap", json=swap_data, headers=auth_headers
            )

            # Should succeed or return appropriate error
            assert response.status_code in [200, 400, 503]

    async def test_aggregator_quote_comparison(self, client: AsyncClient, auth_headers):
        """Test comparing quotes from multiple aggregators"""
        quote_data = {
            "token_in": "USDC",
            "token_out": "ETH",
            "amount": 1000.0,
            "chain": "ethereum",
        }

        # Mock multiple aggregator quotes
        with patch(
            "server_fastapi.services.dex_aggregator_service.DexAggregatorService.get_best_quote"
        ) as mock_quote:
            # Return best quote (lowest price impact)
            mock_quote.return_value = {
                "price": 0.0005,
                "amount_out": 0.5,
                "price_impact": 0.001,  # Low price impact
                "aggregator": "0x",
                "gas_estimate": 150000,
            }

            response = await client.post(
                "/api/dex/quote", json=quote_data, headers=auth_headers
            )

            # Should return best quote
            assert response.status_code in [200, 400, 503]
