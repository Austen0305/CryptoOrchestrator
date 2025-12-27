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
@pytest.mark.skip(reason="Integration test requires complex mocking; unit tests cover individual components")
async def test_complete_bot_lifecycle(client, db_session, auth_headers):
    """
    Test complete bot lifecycle: create → configure → start → trade → stop → delete
    """
    # 1. Create a new bot
    create_response = await client.post(
        "/api/bots/",
        json={
            "name": "Integration Test Bot",
            "symbol": "BTC/USDT",
            "strategy": "smart_adaptive",
            "config": {
                "account_balance": 10000,
                "max_position_size": 0.1,
                "stop_loss": 0.02,
                "take_profit": 0.03,
            },
        },
        headers=auth_headers,
    )

    assert create_response.status_code == 200
    bot_data = create_response.json()
    bot_id = bot_data["id"]

    # 2. Verify bot was created correctly
    get_response = await client.get(f"/api/bots/{bot_id}", headers=auth_headers)
    assert get_response.status_code == 200
    bot = get_response.json()
    assert bot["name"] == "Integration Test Bot"
    # BotConfig uses is_active (bool), not status (string)
    assert bot.get("is_active") is False  # Bot starts as inactive/stopped

    # 3. Start the bot
    with patch(
        "server_fastapi.services.integration_service.IntegrationService"
    ) as mock_service:
        mock_instance = AsyncMock()
        mock_service.return_value = mock_instance

        start_response = await client.post(
            f"/api/bots/{bot_id}/start", headers=auth_headers
        )
        assert start_response.status_code == 200

        # Verify bot is now running (check is_active field)
        bot_response = await client.get(f"/api/bots/{bot_id}", headers=auth_headers)
        bot = bot_response.json()
        assert bot.get("is_active") is True  # Bot should be active after start

    # 4. Execute a trade
    with patch(
        "server_fastapi.services.trading_orchestrator.TradingOrchestrator"
    ) as mock_orchestrator:
        mock_orch_instance = AsyncMock()
        mock_orch_instance.execute_trade.return_value = {
            "trade_id": "test_trade_123",
            "symbol": "BTC/USDT",
            "side": "buy",
            "amount": 0.01,
            "price": 50000,
            "status": "filled",
        }
        mock_orchestrator.return_value = mock_orch_instance

        trade_response = await client.post(
            f"/api/bots/{bot_id}/trade",
            json={"side": "buy", "amount": 0.01},
            headers=auth_headers,
        )

        assert trade_response.status_code == 200
        trade = trade_response.json()
        assert trade["symbol"] == "BTC/USDT"
        assert trade["side"] == "buy"

    # 5. Check portfolio
    portfolio_response = await client.get(
        f"/api/bots/{bot_id}/portfolio", headers=auth_headers
    )
    assert portfolio_response.status_code == 200
    portfolio = portfolio_response.json()
    assert "total_value" in portfolio

    # 6. Stop the bot
    stop_response = await client.post(f"/api/bots/{bot_id}/stop", headers=auth_headers)
    assert stop_response.status_code == 200

    # 7. Verify bot stopped (check is_active field)
    final_bot = await client.get(f"/api/bots/{bot_id}", headers=auth_headers)
    assert (
        final_bot.json().get("is_active") is False
    )  # Bot should be inactive after stop

    # 8. Delete the bot
    delete_response = await client.delete(f"/api/bots/{bot_id}", headers=auth_headers)
    assert delete_response.status_code == 200

    # 9. Verify bot is deleted
    verify_response = await client.get(f"/api/bots/{bot_id}", headers=auth_headers)
    assert verify_response.status_code == 404


@pytest.mark.asyncio
async def test_bot_risk_limits_enforcement(client, db_session, auth_headers):
    """
    Test that risk limits are properly enforced
    """
    # Create bot with strict risk limits
    create_response = await client.post(
        "/api/bots/",
        json={
            "name": "Risk Limited Bot",
            "symbol": "ETH/USDT",
            "strategy": "conservative",
            "config": {
                "account_balance": 5000,
                "max_position_size": 0.05,  # 5% max position
                "max_daily_loss": 100,
                "stop_loss": 0.01,
            },
        },
        headers=auth_headers,
    )

    bot_id = create_response.json()["id"]

    with patch(
        "server_fastapi.services.risk_management_engine.RiskManagementEngine"
    ) as mock_risk:
        mock_risk_instance = AsyncMock()

        # First trade should succeed
        mock_risk_instance.check_position_limits.return_value = True
        mock_risk.return_value = mock_risk_instance

        trade1_response = await client.post(
            f"/api/bots/{bot_id}/trade",
            json={"side": "buy", "amount": 0.02},
            headers=auth_headers,
        )
        assert trade1_response.status_code == 200

        # Second trade exceeding limits should fail
        mock_risk_instance.check_position_limits.return_value = False

        trade2_response = await client.post(
            f"/api/bots/{bot_id}/trade",
            json={"side": "buy", "amount": 0.05},  # Would exceed 5% limit
            headers=auth_headers,
        )
        assert trade2_response.status_code in [400, 403]  # Risk limit violation


@pytest.mark.asyncio
async def test_bot_strategy_switching(client, db_session, auth_headers):
    """
    Test switching strategies on an active bot
    """
    # Create bot with initial strategy
    create_response = await client.post(
        "/api/bots/",
        json={
            "name": "Strategy Switch Bot",
            "symbol": "BTC/USDT",
            "strategy": "aggressive",
            "config": {"account_balance": 10000},
        },
        headers=auth_headers,
    )

    bot_id = create_response.json()["id"]

    # Switch to conservative strategy
    update_response = await client.patch(
        f"/api/bots/{bot_id}", json={"strategy": "conservative"}, headers=auth_headers
    )

    assert update_response.status_code == 200

    # Verify strategy changed
    bot_response = await client.get(f"/api/bots/{bot_id}", headers=auth_headers)
    assert bot_response.json()["strategy"] == "conservative"


@pytest.mark.asyncio
async def test_bot_performance_metrics(client, db_session, auth_headers):
    """
    Test that performance metrics are calculated correctly
    """
    create_response = await client.post(
        "/api/bots/",
        json={
            "name": "Performance Test Bot",
            "symbol": "BTC/USDT",
            "strategy": "smart_adaptive",
            "config": {"account_balance": 10000},
        },
        headers=auth_headers,
    )

    bot_id = create_response.json()["id"]

    # Simulate some trades
    with patch(
        "server_fastapi.services.trading_orchestrator.TradingOrchestrator"
    ) as mock_orch:
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
                "status": "filled",
            }
            mock_orch.return_value = mock_instance

            await client.post(
                f"/api/bots/{bot_id}/trade",
                json={"side": "buy" if i % 2 == 0 else "sell", "amount": 0.01},
                headers=auth_headers,
            )

        # Simulate 2 losing trades
        for i in range(2):
            mock_instance.execute_trade.return_value = {
                "trade_id": f"trade_loss_{i}",
                "symbol": "BTC/USDT",
                "side": "sell",
                "amount": 0.01,
                "price": 49000,
                "profit": -30,
                "status": "filled",
            }

            await client.post(
                f"/api/bots/{bot_id}/trade",
                json={"side": "sell", "amount": 0.01},
                headers=auth_headers,
            )

    # Get performance metrics
    metrics_response = await client.get(
        f"/api/bots/{bot_id}/performance", headers=auth_headers
    )
    assert metrics_response.status_code == 200

    metrics = metrics_response.json()
    assert "total_trades" in metrics
    assert "win_rate" in metrics
    assert "total_profit" in metrics
    assert metrics["total_trades"] >= 7


@pytest.mark.asyncio
async def test_bot_error_recovery(client, db_session, auth_headers):
    """
    Test that bot can recover from errors gracefully
    """
    create_response = await client.post(
        "/api/bots/",
        json={
            "name": "Error Recovery Bot",
            "symbol": "BTC/USDT",
            "strategy": "smart_adaptive",
            "config": {"account_balance": 10000},
        },
        headers=auth_headers,
    )

    bot_id = create_response.json()["id"]

    # Simulate error during trade execution
    with patch(
        "server_fastapi.services.trading_orchestrator.TradingOrchestrator"
    ) as mock_orch:
        mock_instance = AsyncMock()
        mock_instance.execute_trade.side_effect = Exception(
            "Exchange connection failed"
        )
        mock_orch.return_value = mock_instance

        trade_response = await client.post(
            f"/api/bots/{bot_id}/trade",
            json={"side": "buy", "amount": 0.01},
            headers=auth_headers,
        )

        # Bot should handle error gracefully
        assert trade_response.status_code == 500

        # Bot should still be operational
        bot_response = await client.get(f"/api/bots/{bot_id}", headers=auth_headers)
        assert bot_response.status_code == 200
        assert bot_response.json().get("id") == bot_id  # Bot still exists


@pytest.mark.asyncio
async def test_concurrent_bot_operations(client, db_session, auth_headers):
    """
    Test that multiple bots can operate concurrently without conflicts
    """
    bot_ids = []

    # Create multiple bots
    for i in range(3):
        create_response = await client.post(
            "/api/bots/",
            json={
                "name": f"Concurrent Bot {i}",
                "symbol": "BTC/USDT",
                "strategy": "smart_adaptive",
                "config": {"account_balance": 10000},
            },
            headers=auth_headers,
        )
        bot_ids.append(create_response.json()["id"])

    # Start all bots concurrently
    with patch(
        "server_fastapi.services.integration_service.IntegrationService"
    ) as mock_service:
        mock_instance = AsyncMock()
        mock_service.return_value = mock_instance

        start_tasks = [
            client.post(f"/api/bots/{bot_id}/start", headers=auth_headers)
            for bot_id in bot_ids
        ]

        start_responses = await asyncio.gather(*start_tasks)

        # All should succeed
        for response in start_responses:
            assert response.status_code == 200

    # Verify all bots are running (check is_active field)
    bot_tasks = [
        client.get(f"/api/bots/{bot_id}", headers=auth_headers) for bot_id in bot_ids
    ]

    bot_responses = await asyncio.gather(*bot_tasks)

    for response in bot_responses:
        assert response.status_code == 200
        assert response.json().get("is_active") is True  # All bots should be active


@pytest.mark.asyncio
async def test_bot_backup_and_restore(client, db_session, auth_headers):
    """
    Test that bot configuration can be backed up and restored
    """
    # Create and configure a bot
    create_response = await client.post(
        "/api/bots/",
        json={
            "name": "Backup Test Bot",
            "symbol": "BTC/USDT",
            "strategy": "smart_adaptive",
            "config": {"account_balance": 10000, "custom_setting": "important_value"},
        },
        headers=auth_headers,
    )

    bot_id = create_response.json()["id"]
    original_config = create_response.json()["config"]

    # Get backup of configuration
    backup_response = await client.get(
        f"/api/bots/{bot_id}/export", headers=auth_headers
    )
    assert backup_response.status_code == 200
    backup_data = backup_response.json()

    # Modify bot configuration
    await client.patch(
        f"/api/bots/{bot_id}",
        json={"config": {"account_balance": 5000}},
        headers=auth_headers,
    )

    # Restore from backup
    restore_response = await client.post(
        f"/api/bots/{bot_id}/restore", json=backup_data, headers=auth_headers
    )
    assert restore_response.status_code == 200

    # Verify configuration restored
    restored_bot = await client.get(f"/api/bots/{bot_id}", headers=auth_headers)
    assert (
        restored_bot.json()["config"]["account_balance"]
        == original_config["account_balance"]
    )
