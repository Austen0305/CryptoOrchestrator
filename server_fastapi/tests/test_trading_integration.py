"""
Comprehensive integration tests for trading workflows.
Tests the full trading pipeline from bot creation to trade execution.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from datetime import datetime
from typing import Dict, Any
import uuid


@pytest.mark.asyncio
class TestTradingWorkflow:
    """Integration tests for complete trading workflows"""
    
    async def test_create_and_start_bot_workflow(self, client: AsyncClient, auth_headers: Dict[str, str]):
        """Test complete workflow: create bot -> start bot -> check status"""
        # Step 1: Create a bot
        bot_data = {
            "name": f"Integration Test Bot {uuid.uuid4().hex[:8]}",
            "symbol": "BTC/USD",
            "strategy": "simple_ma",
            "config": {
                "max_position_size": 0.1,
                "stop_loss": 0.02,
                "take_profit": 0.05,
                "risk_per_trade": 0.01
            }
        }
        
        create_response = await client.post("/api/bots/", json=bot_data, headers=auth_headers)
        assert create_response.status_code == 200
        created_bot = create_response.json()
        bot_id = created_bot["id"]
        assert created_bot["name"] == bot_data["name"]
        assert created_bot["status"] in ["inactive", "stopped"]
        
        # Step 2: Start the bot
        start_response = await client.post(f"/api/bots/{bot_id}/start", headers=auth_headers)
        assert start_response.status_code == 200
        start_result = start_response.json()
        assert "started successfully" in start_result["message"].lower()
        
        # Step 3: Verify bot is active
        status_response = await client.get(f"/api/bots/{bot_id}", headers=auth_headers)
        assert status_response.status_code == 200
        bot_status = status_response.json()
        assert bot_status["status"] in ["active", "running", "started"]
        
        # Step 4: Check bot performance (should return metrics even if no trades yet)
        perf_response = await client.get(f"/api/bots/{bot_id}/performance", headers=auth_headers)
        assert perf_response.status_code == 200
        performance = perf_response.json()
        assert "total_trades" in performance
        assert "win_rate" in performance
        assert "total_pnl" in performance
    
    async def test_paper_trading_workflow(self, client: AsyncClient, auth_headers: Dict[str, str]):
        """Test paper trading workflow: create trade -> execute -> verify"""
        # Create a bot first
        bot_data = {
            "name": f"Paper Trading Bot {uuid.uuid4().hex[:8]}",
            "symbol": "BTC/USD",
            "strategy": "simple_ma",
            "config": {"mode": "paper"}
        }
        
        create_response = await client.post("/api/bots/", json=bot_data, headers=auth_headers)
        bot_id = create_response.json()["id"]
        
        # Create a paper trade
        trade_data = {
            "pair": "BTC/USD",
            "side": "buy",
            "amount": 0.01,
            "price": 45000.0,
            "botId": bot_id,
            "mode": "paper"
        }
        
        trade_response = await client.post("/api/trades/", json=trade_data, headers=auth_headers)
        assert trade_response.status_code == 200
        trade = trade_response.json()
        assert trade["pair"] == trade_data["pair"]
        assert trade["side"] == trade_data["side"]
        assert trade["mode"] == "paper"
        assert trade["status"] in ["pending", "executed", "filled"]
        
        # Verify trade appears in trades list
        trades_response = await client.get(
            f"/api/trades/?botId={bot_id}",
            headers=auth_headers
        )
        assert trades_response.status_code == 200
        trades = trades_response.json()
        assert isinstance(trades, list)
        assert any(t["id"] == trade["id"] for t in trades)
    
    async def test_bot_update_and_stop_workflow(self, client: AsyncClient, auth_headers: Dict[str, str]):
        """Test workflow: create -> start -> update -> stop"""
        # Create and start bot
        bot_data = {
            "name": f"Update Test Bot {uuid.uuid4().hex[:8]}",
            "symbol": "ETH/USD",
            "strategy": "simple_ma",
            "config": {"max_position_size": 0.1}
        }
        
        create_response = await client.post("/api/bots/", json=bot_data, headers=auth_headers)
        bot_id = create_response.json()["id"]
        
        # Start bot
        await client.post(f"/api/bots/{bot_id}/start", headers=auth_headers)
        
        # Update bot configuration
        update_data = {
            "name": "Updated Bot Name",
            "config": {
                "max_position_size": 0.2,
                "stop_loss": 0.03,
                "take_profit": 0.06
            }
        }
        
        update_response = await client.patch(
            f"/api/bots/{bot_id}",
            json=update_data,
            headers=auth_headers
        )
        assert update_response.status_code == 200
        updated_bot = update_response.json()
        assert updated_bot["name"] == update_data["name"]
        assert updated_bot["config"]["max_position_size"] == 0.2
        
        # Stop bot
        stop_response = await client.post(f"/api/bots/{bot_id}/stop", headers=auth_headers)
        assert stop_response.status_code == 200
        
        # Verify bot is stopped
        status_response = await client.get(f"/api/bots/{bot_id}", headers=auth_headers)
        assert status_response.json()["status"] in ["stopped", "inactive"]
    
    async def test_portfolio_tracking_workflow(self, client: AsyncClient, auth_headers: Dict[str, str]):
        """Test portfolio tracking after trades"""
        # Get portfolio
        portfolio_response = await client.get("/api/portfolio/", headers=auth_headers)
        assert portfolio_response.status_code == 200
        portfolio = portfolio_response.json()
        
        # Portfolio should have structure
        assert isinstance(portfolio, dict)
        # May be empty for new users, but structure should be valid
    
    async def test_risk_management_integration(self, client: AsyncClient, auth_headers: Dict[str, str]):
        """Test risk management integration with trades"""
        # Get risk status
        risk_response = await client.get("/api/risk-management/status", headers=auth_headers)
        assert risk_response.status_code == 200
        risk_status = risk_response.json()
        
        # Should return risk metrics
        assert isinstance(risk_status, dict)
    
    async def test_analytics_integration(self, client: AsyncClient, auth_headers: Dict[str, str]):
        """Test analytics integration"""
        # Get analytics
        analytics_response = await client.get("/api/analytics/", headers=auth_headers)
        assert analytics_response.status_code == 200
        analytics = analytics_response.json()
        
        # Should return analytics data
        assert isinstance(analytics, dict)


@pytest.mark.asyncio
class TestExchangeIntegration:
    """Integration tests for exchange connectivity"""
    
    async def test_market_data_endpoints(self, client: AsyncClient, auth_headers: Dict[str, str]):
        """Test market data retrieval"""
        # Get markets
        markets_response = await client.get("/api/markets/", headers=auth_headers)
        assert markets_response.status_code == 200
        markets = markets_response.json()
        assert isinstance(markets, list)
        
        # If markets exist, test getting specific market
        if markets:
            market_id = markets[0].get("symbol") or markets[0].get("id")
            if market_id:
                market_response = await client.get(
                    f"/api/markets/{market_id}",
                    headers=auth_headers
                )
                # May return 404 if market doesn't exist, or 200 if it does
                assert market_response.status_code in [200, 404]


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling in trading workflows"""
    
    async def test_invalid_bot_creation(self, client: AsyncClient, auth_headers: Dict[str, str]):
        """Test bot creation with invalid data"""
        # Missing required fields
        invalid_bot = {"name": "Invalid Bot"}
        response = await client.post("/api/bots/", json=invalid_bot, headers=auth_headers)
        assert response.status_code in [400, 422]
    
    async def test_invalid_trade_creation(self, client: AsyncClient, auth_headers: Dict[str, str]):
        """Test trade creation with invalid data"""
        invalid_trade = {
            "pair": "INVALID/PAIR",
            "side": "invalid_side",
            "amount": -1.0  # Negative amount
        }
        response = await client.post("/api/trades/", json=invalid_trade, headers=auth_headers)
        assert response.status_code in [400, 422]
    
    async def test_nonexistent_bot_operations(self, client: AsyncClient, auth_headers: Dict[str, str]):
        """Test operations on non-existent bot"""
        fake_bot_id = f"bot_{uuid.uuid4().hex}"
        
        # Try to get non-existent bot
        response = await client.get(f"/api/bots/{fake_bot_id}", headers=auth_headers)
        assert response.status_code == 404
        
        # Try to start non-existent bot
        response = await client.post(f"/api/bots/{fake_bot_id}/start", headers=auth_headers)
        assert response.status_code == 404
        
        # Try to delete non-existent bot
        response = await client.delete(f"/api/bots/{fake_bot_id}", headers=auth_headers)
        assert response.status_code == 404


@pytest.mark.asyncio
class TestAuthentication:
    """Test authentication and authorization"""
    
    async def test_unauthenticated_access(self, client: AsyncClient):
        """Test that unauthenticated requests are rejected"""
        # Try to access protected endpoints without auth
        response = await client.get("/api/bots/")
        assert response.status_code == 403  # Forbidden
        
        response = await client.post("/api/bots/", json={"name": "Test"})
        assert response.status_code == 403
    
    async def test_invalid_token(self, client: AsyncClient):
        """Test that invalid tokens are rejected"""
        invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
        response = await client.get("/api/bots/", headers=invalid_headers)
        assert response.status_code in [401, 403]  # Unauthorized or Forbidden

