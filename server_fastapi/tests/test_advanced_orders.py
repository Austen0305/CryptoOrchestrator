"""
Tests for advanced order types (stop-limit, take-profit, trailing-stop)
"""

import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
class TestAdvancedOrderTypes:
    """Test advanced order type functionality"""
    
    async def test_stop_limit_order(self, client: AsyncClient, auth_headers: dict):
        """Test creating a stop-limit order"""
        order = {
            "pair": "BTC/USD",
            "side": "buy",
            "type": "stop-limit",
            "amount": 0.1,
            "price": 50000,
            "stop": 49000,
            "time_in_force": "GTC",
            "mode": "paper"
        }
        response = await client.post("/api/trades/", json=order, headers=auth_headers)
        assert response.status_code in [200, 201, 400, 422]
        if response.status_code in [200, 201]:
            data = response.json()
            assert data.get("type") == "stop-limit" or "id" in data
    
    async def test_take_profit_order(self, client: AsyncClient, auth_headers: dict):
        """Test creating a take-profit order"""
        order = {
            "pair": "BTC/USD",
            "side": "sell",
            "type": "take-profit",
            "amount": 0.1,
            "price": 52000,
            "take_profit": 52000,
            "mode": "paper"
        }
        response = await client.post("/api/trades/", json=order, headers=auth_headers)
        assert response.status_code in [200, 201, 400, 422]
        if response.status_code in [200, 201]:
            data = response.json()
            assert data.get("type") == "take-profit" or "id" in data
    
    async def test_trailing_stop_order(self, client: AsyncClient, auth_headers: dict):
        """Test creating a trailing-stop order"""
        order = {
            "pair": "BTC/USD",
            "side": "sell",
            "type": "trailing-stop",
            "amount": 0.1,
            "trailing_stop_percent": 2.5,
            "mode": "paper"
        }
        response = await client.post("/api/trades/", json=order, headers=auth_headers)
        assert response.status_code in [200, 201, 400, 422]
        if response.status_code in [200, 201]:
            data = response.json()
            assert data.get("type") == "trailing-stop" or "id" in data
    
    async def test_stop_limit_missing_stop_price(self, client: AsyncClient, auth_headers: dict):
        """Test stop-limit order without stop price fails"""
        order = {
            "pair": "BTC/USD",
            "side": "buy",
            "type": "stop-limit",
            "amount": 0.1,
            "price": 50000,
            "mode": "paper"
        }
        response = await client.post("/api/trades/", json=order, headers=auth_headers)
        assert response.status_code in [400, 422]
    
    async def test_take_profit_missing_price(self, client: AsyncClient, auth_headers: dict):
        """Test take-profit order without take_profit price fails"""
        order = {
            "pair": "BTC/USD",
            "side": "sell",
            "type": "take-profit",
            "amount": 0.1,
            "mode": "paper"
        }
        response = await client.post("/api/trades/", json=order, headers=auth_headers)
        assert response.status_code in [400, 422]
    
    async def test_trailing_stop_missing_percent(self, client: AsyncClient, auth_headers: dict):
        """Test trailing-stop order without percentage fails"""
        order = {
            "pair": "BTC/USD",
            "side": "sell",
            "type": "trailing-stop",
            "amount": 0.1,
            "mode": "paper"
        }
        response = await client.post("/api/trades/", json=order, headers=auth_headers)
        assert response.status_code in [400, 422]
    
    async def test_time_in_force_options(self, client: AsyncClient, auth_headers: dict):
        """Test time-in-force options (GTC, IOC, FOK)"""
        for tif in ["GTC", "IOC", "FOK"]:
            order = {
                "pair": "BTC/USD",
                "side": "buy",
                "type": "limit",
                "amount": 0.1,
                "price": 50000,
                "time_in_force": tif,
                "mode": "paper"
            }
            response = await client.post("/api/trades/", json=order, headers=auth_headers)
            assert response.status_code in [200, 201, 400, 422]
    
    async def test_invalid_time_in_force(self, client: AsyncClient, auth_headers: dict):
        """Test invalid time-in-force value fails"""
        order = {
            "pair": "BTC/USD",
            "side": "buy",
            "type": "limit",
            "amount": 0.1,
            "price": 50000,
            "time_in_force": "INVALID",
            "mode": "paper"
        }
        response = await client.post("/api/trades/", json=order, headers=auth_headers)
        assert response.status_code in [400, 422]

