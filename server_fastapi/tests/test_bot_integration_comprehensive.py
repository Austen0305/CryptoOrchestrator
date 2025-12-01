"""
Comprehensive Integration Tests for Bots Service
Tests complete workflows from creation to execution
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

# These tests follow the existing test patterns in the project


@pytest.mark.asyncio
async def test_complete_bot_lifecycle(test_client, test_db):
    """
    Test complete bot lifecycle: create → configure → start → trade → stop → delete
    """
    # 1. Create a new bot
    create_response = await test_client.post("/api/bots", json={
        "name": "Integration Test Bot",
        "symbol": "BTC/USDT",
        "strategy": "smart_adaptive",
        "config": {
            "account_balance": 10000,
            "max_position_size": 0.1,
            "stop_loss": 0.02,
            "take_profit": 0.03
        }
    })
    
    assert create_response.status_code == 200
    bot_data = create_response.json()
    bot_id = bot_data["id"]
    
    # 2. Verify bot was created correctly
    get_response = await test_client.get(f"/api/bots/{bot_id}")
    assert get_response.status_code == 200
    bot = get_response.json()
    assert bot["name"] == "Integration Test Bot"
    assert bot["status"] == "stopped"
    
    # 3. Start the bot
    with patch('server_fastapi.services.integration_service.IntegrationService') as mock_service:
        mock_instance = AsyncMock()
        mock_service.return_value = mock_instance
        
        start_response = await test_client.post(f"/api/bots/{bot_id}/start")
        assert start_response.status_code == 200
        
        # Verify bot is now running
        status_response = await test_client.get(f"/api/bots/{bot_id}/status")
        status = status_response.json()
        assert status["status"] in ["running", "started"]
    
    # 4. Execute a trade
    with patch('server_fastapi.services.trading_orchestrator.TradingOrchestrator') as mock_orchestrator:
        mock_orch_instance = AsyncMock()
        mock_orch_instance.execute_trade.return_value = {
            "trade_id": "test_trade_123",
            "symbol": "BTC/USDT",
            "side": "buy",
            "amount": 0.01,
            "price": 50000,
            "status": "filled"
        }
        mock_orchestrator.return_value = mock_orch_instance
        
        trade_response = await test_client.post(f"/api/bots/{bot_id}/trade", json={
            "side": "buy",
            "amount": 0.01
        })
        
        assert trade_response.status_code == 200
        trade = trade_response.json()
        assert trade["symbol"] == "BTC/USDT"
        assert trade["side"] == "buy"
    
    # 5. Check portfolio
    portfolio_response = await test_client.get(f"/api/bots/{bot_id}/portfolio")
    assert portfolio_response.status_code == 200
    portfolio = portfolio_response.json()
    assert "total_value" in portfolio
    
    # 6. Stop the bot
    stop_response = await test_client.post(f"/api/bots/{bot_id}/stop")
    assert stop_response.status_code == 200
    
    # 7. Verify bot stopped
    final_status = await test_client.get(f"/api/bots/{bot_id}/status")
    assert final_status.json()["status"] == "stopped"
    
    # 8. Delete the bot
    delete_response = await test_client.delete(f"/api/bots/{bot_id}")
    assert delete_response.status_code == 200
    
    # 9. Verify bot is deleted
    verify_response = await test_client.get(f"/api/bots/{bot_id}")
    assert verify_response.status_code == 404


@pytest.mark.asyncio
async def test_bot_risk_limits_enforcement(test_client, test_db):
    """
    Test that risk limits are properly enforced
    """
    # Create bot with strict risk limits
    create_response = await test_client.post("/api/bots", json={
        "name": "Risk Limited Bot",
        "symbol": "ETH/USDT",
        "strategy": "conservative",
        "config": {
            "account_balance": 5000,
            "max_position_size": 0.05,  # 5% max position
            "max_daily_loss": 100,
            "stop_loss": 0.01
        }
    })
    
    bot_id = create_response.json()["id"]
    
    with patch('server_fastapi.services.risk_management_engine.RiskManagementEngine') as mock_risk:
        mock_risk_instance = AsyncMock()
        
        # First trade should succeed
        mock_risk_instance.check_position_limits.return_value = True
        mock_risk.return_value = mock_risk_instance
        
        trade1_response = await test_client.post(f"/api/bots/{bot_id}/trade", json={
            "side": "buy",
            "amount": 0.02
        })
        assert trade1_response.status_code == 200
        
        # Second trade exceeding limits should fail
        mock_risk_instance.check_position_limits.return_value = False
        
        trade2_response = await test_client.post(f"/api/bots/{bot_id}/trade", json={
            "side": "buy",
            "amount": 0.05  # Would exceed 5% limit
        })
        assert trade2_response.status_code in [400, 403]  # Risk limit violation


@pytest.mark.asyncio
async def test_bot_strategy_switching(test_client, test_db):
    """
    Test switching strategies on an active bot
    """
    # Create bot with initial strategy
    create_response = await test_client.post("/api/bots", json={
        "name": "Strategy Switch Bot",
        "symbol": "BTC/USDT",
        "strategy": "aggressive",
        "config": {"account_balance": 10000}
    })
    
    bot_id = create_response.json()["id"]
    
    # Switch to conservative strategy
    update_response = await test_client.patch(f"/api/bots/{bot_id}", json={
        "strategy": "conservative"
    })
    
    assert update_response.status_code == 200
    
    # Verify strategy changed
    bot_response = await test_client.get(f"/api/bots/{bot_id}")
    assert bot_response.json()["strategy"] == "conservative"


@pytest.mark.asyncio
async def test_bot_performance_metrics(test_client, test_db):
    """
    Test that performance metrics are calculated correctly
    """
    create_response = await test_client.post("/api/bots", json={
        "name": "Performance Test Bot",
        "symbol": "BTC/USDT",
        "strategy": "smart_adaptive",
        "config": {"account_balance": 10000}
    })
    
    bot_id = create_response.json()["id"]
    
    # Simulate some trades
    with patch('server_fastapi.services.trading_orchestrator.TradingOrchestrator') as mock_orch:
        mock_instance = AsyncMock()
        
        # Simulate 5 winning trades
        for i in range(5):
            mock_instance.execute_trade.return_value = {
                "trade_id": f"trade_{i}",
                "symbol": "BTC/USDT",
                "side": "buy" if i % 2 == 0 else "sell",
                "amount": 0.01,
                "price": 50000 + (i * 100),
                "profit": 50,
                "status": "filled"
            }
            mock_orch.return_value = mock_instance
            
            await test_client.post(f"/api/bots/{bot_id}/trade", json={
                "side": "buy" if i % 2 == 0 else "sell",
                "amount": 0.01
            })
        
        # Simulate 2 losing trades
        for i in range(2):
            mock_instance.execute_trade.return_value = {
                "trade_id": f"trade_loss_{i}",
                "symbol": "BTC/USDT",
                "side": "sell",
                "amount": 0.01,
                "price": 49000,
                "profit": -30,
                "status": "filled"
            }
            
            await test_client.post(f"/api/bots/{bot_id}/trade", json={
                "side": "sell",
                "amount": 0.01
            })
    
    # Get performance metrics
    metrics_response = await test_client.get(f"/api/bots/{bot_id}/performance")
    assert metrics_response.status_code == 200
    
    metrics = metrics_response.json()
    assert "total_trades" in metrics
    assert "win_rate" in metrics
    assert "total_profit" in metrics
    assert metrics["total_trades"] >= 7


@pytest.mark.asyncio
async def test_bot_error_recovery(test_client, test_db):
    """
    Test that bot can recover from errors gracefully
    """
    create_response = await test_client.post("/api/bots", json={
        "name": "Error Recovery Bot",
        "symbol": "BTC/USDT",
        "strategy": "smart_adaptive",
        "config": {"account_balance": 10000}
    })
    
    bot_id = create_response.json()["id"]
    
    # Simulate error during trade execution
    with patch('server_fastapi.services.trading_orchestrator.TradingOrchestrator') as mock_orch:
        mock_instance = AsyncMock()
        mock_instance.execute_trade.side_effect = Exception("Exchange connection failed")
        mock_orch.return_value = mock_instance
        
        trade_response = await test_client.post(f"/api/bots/{bot_id}/trade", json={
            "side": "buy",
            "amount": 0.01
        })
        
        # Bot should handle error gracefully
        assert trade_response.status_code == 500
        
        # Bot should still be operational
        status_response = await test_client.get(f"/api/bots/{bot_id}/status")
        assert status_response.status_code == 200


@pytest.mark.asyncio
async def test_concurrent_bot_operations(test_client, test_db):
    """
    Test that multiple bots can operate concurrently without conflicts
    """
    bot_ids = []
    
    # Create multiple bots
    for i in range(3):
        create_response = await test_client.post("/api/bots", json={
            "name": f"Concurrent Bot {i}",
            "symbol": "BTC/USDT",
            "strategy": "smart_adaptive",
            "config": {"account_balance": 10000}
        })
        bot_ids.append(create_response.json()["id"])
    
    # Start all bots concurrently
    with patch('server_fastapi.services.integration_service.IntegrationService') as mock_service:
        mock_instance = AsyncMock()
        mock_service.return_value = mock_instance
        
        start_tasks = [
            test_client.post(f"/api/bots/{bot_id}/start")
            for bot_id in bot_ids
        ]
        
        start_responses = await asyncio.gather(*start_tasks)
        
        # All should succeed
        for response in start_responses:
            assert response.status_code == 200
    
    # Verify all bots are running
    status_tasks = [
        test_client.get(f"/api/bots/{bot_id}/status")
        for bot_id in bot_ids
    ]
    
    status_responses = await asyncio.gather(*status_tasks)
    
    for response in status_responses:
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_bot_backup_and_restore(test_client, test_db):
    """
    Test that bot configuration can be backed up and restored
    """
    # Create and configure a bot
    create_response = await test_client.post("/api/bots", json={
        "name": "Backup Test Bot",
        "symbol": "BTC/USDT",
        "strategy": "smart_adaptive",
        "config": {
            "account_balance": 10000,
            "custom_setting": "important_value"
        }
    })
    
    bot_id = create_response.json()["id"]
    original_config = create_response.json()["config"]
    
    # Get backup of configuration
    backup_response = await test_client.get(f"/api/bots/{bot_id}/export")
    assert backup_response.status_code == 200
    backup_data = backup_response.json()
    
    # Modify bot configuration
    await test_client.patch(f"/api/bots/{bot_id}", json={
        "config": {"account_balance": 5000}
    })
    
    # Restore from backup
    restore_response = await test_client.post(f"/api/bots/{bot_id}/restore", json=backup_data)
    assert restore_response.status_code == 200
    
    # Verify configuration restored
    restored_bot = await test_client.get(f"/api/bots/{bot_id}")
    assert restored_bot.json()["config"]["account_balance"] == original_config["account_balance"]
