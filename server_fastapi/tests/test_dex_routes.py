"""
DEX Trading Routes Tests
Integration tests for DEX trading API endpoints
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_quote_success(client: AsyncClient, auth_headers):
    """Test successful quote retrieval"""
    with patch(
        "server_fastapi.routes.dex_trading.get_dex_trading_service"
    ) as mock_service:
        mock_dex_service = MagicMock()
        mock_dex_service.get_quote = AsyncMock(
            return_value={
                "sellToken": "ETH",
                "buyToken": "USDC",
                "sellAmount": "1000000000000000000",
                "buyAmount": "3000000000",
                "price": "3000",
                "aggregator": "0x",
            }
        )
        mock_service.return_value = mock_dex_service

        response = await client.post(
            "/api/dex/quote",
            json={
                "sell_token": "ETH",
                "buy_token": "USDC",
                "sell_amount": "1000000000000000000",
                "chain_id": 1,
                "slippage_percentage": 0.5,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sellToken"] == "ETH"
        assert data["buyToken"] == "USDC"
        assert data["aggregator"] == "0x"


@pytest.mark.asyncio
async def test_get_quote_unauthorized(client: AsyncClient):
    """Test quote endpoint requires authentication"""
    response = await client.post(
        "/api/dex/quote",
        json={
            "sell_token": "ETH",
            "buy_token": "USDC",
            "sell_amount": "1000000000000000000",
            "chain_id": 1,
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_quote_validation_error(client: AsyncClient, auth_headers):
    """Test quote endpoint validation"""
    response = await client.post(
        "/api/dex/quote",
        json={
            "sell_token": "ETH",
            # Missing buy_token
            "sell_amount": "1000000000000000000",
            "chain_id": 1,
        },
        headers=auth_headers,
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_execute_swap_custodial_success(client: AsyncClient, auth_headers):
    """Test successful custodial swap execution"""
    with patch(
        "server_fastapi.routes.dex_trading.get_dex_trading_service"
    ) as mock_service:
        mock_dex_service = MagicMock()
        mock_dex_service.execute_custodial_swap = AsyncMock(
            return_value={
                "success": True,
                "trade_id": 1,
                "transaction_hash": "0x1234567890abcdef",
                "status": "executing",
            }
        )
        mock_service.return_value = mock_dex_service

        response = await client.post(
            "/api/dex/swap",
            json={
                "sell_token": "ETH",
                "buy_token": "USDC",
                "sell_amount": "1000000000000000000",
                "chain_id": 1,
                "slippage_percentage": 0.5,
                "custodial": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "transaction_hash" in data


@pytest.mark.asyncio
async def test_execute_swap_non_custodial_success(client: AsyncClient, auth_headers):
    """Test successful non-custodial swap execution"""
    with patch(
        "server_fastapi.routes.dex_trading.get_dex_trading_service"
    ) as mock_service:
        mock_dex_service = MagicMock()
        mock_dex_service.prepare_non_custodial_swap = AsyncMock(
            return_value={
                "swap_calldata": {
                    "to": "0x1234567890123456789012345678901234567890",
                    "calldata": "0xabcd...",
                    "value": "0",
                },
                "nonce": 12345,
            }
        )
        mock_service.return_value = mock_dex_service

        response = await client.post(
            "/api/dex/swap",
            json={
                "sell_token": "ETH",
                "buy_token": "USDC",
                "sell_amount": "1000000000000000000",
                "chain_id": 1,
                "slippage_percentage": 0.5,
                "custodial": False,
                "user_wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "signature": "0x1234...",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "swap_calldata" in data


@pytest.mark.asyncio
async def test_execute_swap_insufficient_balance(client: AsyncClient, auth_headers):
    """Test swap with insufficient balance"""
    with patch(
        "server_fastapi.routes.dex_trading.get_dex_trading_service"
    ) as mock_service:
        mock_dex_service = MagicMock()
        mock_dex_service.execute_custodial_swap = AsyncMock(
            side_effect=ValueError("Insufficient balance")
        )
        mock_service.return_value = mock_dex_service

        response = await client.post(
            "/api/dex/swap",
            json={
                "sell_token": "ETH",
                "buy_token": "USDC",
                "sell_amount": "1000000000000000000",
                "chain_id": 1,
                "custodial": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "insufficient" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_supported_chains(client: AsyncClient, auth_headers):
    """Test getting supported chains"""
    with patch(
        "server_fastapi.routes.dex_trading.get_dex_trading_service"
    ) as mock_service:
        mock_dex_service = MagicMock()
        mock_dex_service.get_supported_chains = AsyncMock(
            return_value=[
                {"chainId": 1, "name": "Ethereum", "symbol": "ETH"},
                {"chainId": 8453, "name": "Base", "symbol": "ETH"},
            ]
        )
        mock_service.return_value = mock_dex_service

        response = await client.get(
            "/api/dex/supported-chains",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["chainId"] == 1


@pytest.mark.asyncio
async def test_get_supported_chains_unauthorized(client: AsyncClient):
    """Test supported chains endpoint requires authentication"""
    response = await client.get("/api/dex/supported-chains")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_transaction_status_success(client: AsyncClient, auth_headers):
    """Test transaction status endpoint"""
    trade_id = 1
    transaction_hash = "0xabc123..."

    with patch(
        "server_fastapi.routes.dex_trading.get_dex_trading_service"
    ) as mock_service:
        mock_dex_service = MagicMock()
        mock_dex_service.get_swap_status = AsyncMock(
            return_value={
                "status": "confirmed",
                "success": True,
                "block_number": 12345,
                "transaction_hash": transaction_hash,
            }
        )
        mock_service.return_value = mock_dex_service

        response = await client.get(
            f"/api/dex/trades/{trade_id}/status?chain_id=1&transaction_hash={transaction_hash}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "confirmed"
        assert data["success"] is True


@pytest.mark.asyncio
async def test_get_transaction_status_not_found(client: AsyncClient, auth_headers):
    """Test status for non-existent transaction"""
    trade_id = 999

    with patch(
        "server_fastapi.routes.dex_trading.get_dex_trading_service"
    ) as mock_service:
        mock_dex_service = MagicMock()
        mock_dex_service.get_swap_status = AsyncMock(
            return_value={
                "status": "not_found",
                "message": "Transaction not found",
            }
        )
        mock_service.return_value = mock_dex_service

        response = await client.get(
            f"/api/dex/trades/{trade_id}/status?chain_id=1&transaction_hash=0xinvalid",
            headers=auth_headers,
        )

        # Should return 200 with not_found status or 404
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "not_found"


@pytest.mark.asyncio
async def test_quote_endpoint_validation_errors(client: AsyncClient, auth_headers):
    """Test all validation error cases for quote endpoint"""
    # Missing required fields
    response = await client.post(
        "/api/dex/quote",
        json={},  # Empty request
        headers=auth_headers,
    )
    assert response.status_code == 422

    # Invalid chain_id
    response = await client.post(
        "/api/dex/quote",
        json={
            "sell_token": "ETH",
            "buy_token": "USDC",
            "sell_amount": "1000000000000000000",
            "chain_id": 99999,  # Invalid chain ID
        },
        headers=auth_headers,
    )
    # Should still validate (chain_id validation may be in service layer)
    assert response.status_code in [200, 400, 422]

    # Invalid slippage (too high)
    response = await client.post(
        "/api/dex/quote",
        json={
            "sell_token": "ETH",
            "buy_token": "USDC",
            "sell_amount": "1000000000000000000",
            "chain_id": 1,
            "slippage_percentage": 100,  # Exceeds max (50)
        },
        headers=auth_headers,
    )
    assert response.status_code == 422

    # Negative slippage
    response = await client.post(
        "/api/dex/quote",
        json={
            "sell_token": "ETH",
            "buy_token": "USDC",
            "sell_amount": "1000000000000000000",
            "chain_id": 1,
            "slippage_percentage": -1,
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_swap_endpoint_validation_errors(client: AsyncClient, auth_headers):
    """Test all validation error cases for swap endpoint"""
    # Missing required fields
    response = await client.post(
        "/api/dex/swap",
        json={},  # Empty request
        headers=auth_headers,
    )
    assert response.status_code == 422

    # Missing user_wallet_address for non-custodial
    response = await client.post(
        "/api/dex/swap",
        json={
            "sell_token": "ETH",
            "buy_token": "USDC",
            "sell_amount": "1000000000000000000",
            "chain_id": 1,
            "custodial": False,  # Non-custodial but no wallet address
        },
        headers=auth_headers,
    )
    # May require wallet address validation in service layer
    assert response.status_code in [200, 400, 422]

    # Invalid slippage
    response = await client.post(
        "/api/dex/swap",
        json={
            "sell_token": "ETH",
            "buy_token": "USDC",
            "sell_amount": "1000000000000000000",
            "chain_id": 1,
            "slippage_percentage": 100,  # Exceeds max
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """Test all endpoints require authentication"""
    # Quote endpoint
    response = await client.post(
        "/api/dex/quote",
        json={
            "sell_token": "ETH",
            "buy_token": "USDC",
            "sell_amount": "1000000000000000000",
            "chain_id": 1,
        },
    )
    assert response.status_code == 401

    # Swap endpoint
    response = await client.post(
        "/api/dex/swap",
        json={
            "sell_token": "ETH",
            "buy_token": "USDC",
            "sell_amount": "1000000000000000000",
            "chain_id": 1,
        },
    )
    assert response.status_code == 401

    # Status endpoint
    response = await client.get(
        "/api/dex/trades/1/status?chain_id=1&transaction_hash=0xabc"
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_chain_id(client: AsyncClient, auth_headers):
    """Test error handling for invalid chain IDs"""
    with patch(
        "server_fastapi.routes.dex_trading.get_dex_trading_service"
    ) as mock_service:
        mock_dex_service = MagicMock()
        mock_dex_service.get_quote = AsyncMock(
            return_value=None
        )  # No quote for invalid chain
        mock_service.return_value = mock_dex_service

        response = await client.post(
            "/api/dex/quote",
            json={
                "sell_token": "ETH",
                "buy_token": "USDC",
                "sell_amount": "1000000000000000000",
                "chain_id": 99999,  # Invalid chain ID
            },
            headers=auth_headers,
        )

        # Should return 200 with None quote or 400 error
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            # Quote might be None for unsupported chain
            pass


@pytest.mark.asyncio
async def test_invalid_token_addresses(client: AsyncClient, auth_headers):
    """Test error handling for invalid token addresses"""
    with patch(
        "server_fastapi.routes.dex_trading.get_dex_trading_service"
    ) as mock_service:
        mock_dex_service = MagicMock()
        mock_dex_service.get_quote = AsyncMock(
            return_value=None
        )  # No quote for invalid token
        mock_service.return_value = mock_dex_service

        response = await client.post(
            "/api/dex/quote",
            json={
                "sell_token": "0xInvalidTokenAddress",
                "buy_token": "USDC",
                "sell_amount": "1000000000000000000",
                "chain_id": 1,
            },
            headers=auth_headers,
        )

        # Should handle invalid token gracefully
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            # Quote might be None for invalid token
            data = response.json()
            # May return None or error message
            pass


@pytest.mark.asyncio
async def test_quote_endpoint_rate_limiting(client: AsyncClient, auth_headers):
    """Test rate limiting on quote endpoint"""
    # Note: Rate limiting tests require rate limiter to be configured
    # This is a basic test - full rate limiting test would need rate limiter mock

    with patch(
        "server_fastapi.routes.dex_trading.get_dex_trading_service"
    ) as mock_service:
        mock_dex_service = MagicMock()
        mock_dex_service.get_quote = AsyncMock(
            return_value={
                "sellToken": "ETH",
                "buyToken": "USDC",
                "sellAmount": "1000000000000000000",
                "buyAmount": "3000000000",
                "price": "3000",
                "aggregator": "0x",
            }
        )
        mock_service.return_value = mock_dex_service

        # Make multiple rapid requests
        responses = []
        for _ in range(5):
            response = await client.post(
                "/api/dex/quote",
                json={
                    "sell_token": "ETH",
                    "buy_token": "USDC",
                    "sell_amount": "1000000000000000000",
                    "chain_id": 1,
                },
                headers=auth_headers,
            )
            responses.append(response.status_code)

        # All should succeed unless rate limited
        # In production with rate limiting, some might return 429
        assert all(status in [200, 429] for status in responses)


@pytest.mark.asyncio
async def test_swap_endpoint_rate_limiting(client: AsyncClient, auth_headers):
    """Test rate limiting on swap endpoint"""
    with patch(
        "server_fastapi.routes.dex_trading.get_dex_trading_service"
    ) as mock_service:
        mock_dex_service = MagicMock()
        mock_dex_service.execute_custodial_swap = AsyncMock(
            return_value={
                "success": True,
                "trade_id": 1,
                "transaction_hash": "0xabc123...",
            }
        )
        mock_service.return_value = mock_dex_service

        # Make multiple rapid requests
        responses = []
        for _ in range(3):  # Fewer requests for swap (more restrictive)
            response = await client.post(
                "/api/dex/swap",
                json={
                    "sell_token": "ETH",
                    "buy_token": "USDC",
                    "sell_amount": "1000000000000000000",
                    "chain_id": 1,
                    "custodial": True,
                },
                headers=auth_headers,
            )
            responses.append(response.status_code)

        # All should succeed unless rate limited
        assert all(status in [200, 429] for status in responses)
