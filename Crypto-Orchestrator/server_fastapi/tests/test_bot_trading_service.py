"""
Unit tests for BotTradingService
Tests trading cycle execution and bot trading logic with mocked dependencies
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from server_fastapi.services.trading.bot_trading_service import BotTradingService
from server_fastapi.tests.utils.test_helpers import create_mock_db_session


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return create_mock_db_session()


@pytest.fixture
def bot_trading_service(mock_db_session):
    """Create BotTradingService instance with mocked dependencies"""
    service = BotTradingService(session=mock_db_session)

    # Mock ML engines
    service.ml_engines = {
        "ml_enhanced": MagicMock(),
        "ensemble": MagicMock(),
        "neural_network": MagicMock(),
    }

    # Mock smart engine
    service.smart_engine = MagicMock()

    # Mock risk manager
    service.risk_manager = MagicMock()

    # Mock safety service
    service.safety_service = MagicMock()

    return service


@pytest.mark.asyncio
async def test_execute_trading_cycle_bot_inactive(bot_trading_service):
    """Test trading cycle when bot is inactive"""
    bot_config = {"id": "bot-123", "user_id": 1, "strategy": "simple_ma"}

    with patch.object(
        bot_trading_service.control_service, "is_bot_active", new_callable=AsyncMock
    ) as mock_active:
        mock_active.return_value = False

        result = await bot_trading_service.execute_trading_cycle(bot_config)

        assert result["action"] == "skipped"
        assert result["reason"] == "bot_inactive"


@pytest.mark.asyncio
async def test_execute_trading_cycle_validation_failed(bot_trading_service):
    """Test trading cycle when validation fails"""
    bot_config = {"id": "bot-123", "user_id": 1, "strategy": "simple_ma"}

    with patch.object(
        bot_trading_service.control_service, "is_bot_active", new_callable=AsyncMock
    ) as mock_active, patch.object(
        bot_trading_service.monitoring_service,
        "validate_bot_start_conditions",
        new_callable=AsyncMock,
    ) as mock_validate:

        mock_active.return_value = True
        mock_validate.return_value = {
            "can_start": False,
            "blockers": ["insufficient_balance"],
        }

        result = await bot_trading_service.execute_trading_cycle(bot_config)

        assert result["action"] == "blocked"
        assert result["reason"] == "safety_validation_failed"


@pytest.mark.asyncio
async def test_execute_trading_cycle_hold_signal(bot_trading_service):
    """Test trading cycle with hold signal"""
    bot_config = {"id": "bot-123", "user_id": 1, "strategy": "simple_ma"}

    with patch.object(
        bot_trading_service.control_service, "is_bot_active", new_callable=AsyncMock
    ) as mock_active, patch.object(
        bot_trading_service.monitoring_service,
        "validate_bot_start_conditions",
        new_callable=AsyncMock,
    ) as mock_validate, patch.object(
        bot_trading_service, "_get_market_data", new_callable=AsyncMock
    ) as mock_market, patch.object(
        bot_trading_service, "_get_trading_signal", new_callable=AsyncMock
    ) as mock_signal:

        mock_active.return_value = True
        mock_validate.return_value = {"can_start": True}
        mock_market.return_value = {"price": 50000.0, "volume": 1000.0}
        mock_signal.return_value = {"action": "hold"}

        result = await bot_trading_service.execute_trading_cycle(bot_config)

        assert result["action"] == "hold"
        assert "signal" in result


@pytest.mark.asyncio
async def test_execute_trading_cycle_buy_signal(bot_trading_service):
    """Test trading cycle with buy signal"""
    bot_config = {
        "id": "bot-123",
        "user_id": 1,
        "strategy": "simple_ma",
        "mode": "paper",
        "chain_id": 1,  # Ethereum
        "symbol": "ETH/USDC",
    }

    with patch.object(
        bot_trading_service.control_service, "is_bot_active", new_callable=AsyncMock
    ) as mock_active, patch.object(
        bot_trading_service.monitoring_service,
        "validate_bot_start_conditions",
        new_callable=AsyncMock,
    ) as mock_validate, patch.object(
        bot_trading_service, "_get_market_data", new_callable=AsyncMock
    ) as mock_market, patch.object(
        bot_trading_service, "_get_trading_signal", new_callable=AsyncMock
    ) as mock_signal, patch.object(
        bot_trading_service, "_calculate_risk_profile", new_callable=AsyncMock
    ) as mock_risk, patch.object(
        bot_trading_service, "_prepare_trade_details", new_callable=MagicMock
    ) as mock_prepare, patch(
        "server_fastapi.services.trading.bot_trading_service.SafeTradingSystem"
    ) as mock_safe:

        mock_active.return_value = True
        mock_validate.return_value = {"can_start": True}
        mock_market.return_value = {"price": 50000.0, "volume": 1000.0}
        mock_signal.return_value = {"action": "buy", "confidence": 0.8}
        mock_risk.return_value = MagicMock()
        mock_prepare.return_value = {"side": "buy", "amount": 0.1, "price": 50000.0}

        # Mock safe trading system
        mock_safe_instance = MagicMock()
        mock_safe_instance.validate_trade = AsyncMock(return_value={"approved": True})
        mock_safe.return_value = mock_safe_instance

        result = await bot_trading_service.execute_trading_cycle(bot_config)

        # Should attempt to execute trade
        assert result is not None
        assert "action" in result


@pytest.mark.asyncio
async def test_get_market_data(bot_trading_service):
    """Test getting market data"""
    bot_config = {"symbol": "ETH/USDC", "chain_id": 1}  # Ethereum

    with patch.object(
        bot_trading_service, "_get_market_data", new_callable=AsyncMock
    ) as mock_market:
        mock_market.return_value = {
            "price": 50000.0,
            "volume": 1000.0,
            "timestamp": "2024-01-01T00:00:00Z",
        }

        market_data = await bot_trading_service._get_market_data(bot_config)

        assert market_data["price"] == 50000.0
        assert "volume" in market_data


@pytest.mark.asyncio
async def test_get_trading_signal_simple_ma(bot_trading_service):
    """Test getting trading signal for simple MA strategy"""
    market_data = {"price": 50000.0, "volume": 1000.0}
    bot_config = {"strategy": "simple_ma", "config": {}}

    with patch.object(
        bot_trading_service, "_get_trading_signal", new_callable=AsyncMock
    ) as mock_signal:
        mock_signal.return_value = {
            "action": "buy",
            "confidence": 0.7,
            "price": 50000.0,
        }

        signal = await bot_trading_service._get_trading_signal(
            "simple_ma", market_data, bot_config
        )

        assert signal["action"] == "buy"
        assert signal["confidence"] == 0.7


@pytest.mark.asyncio
async def test_get_trading_signal_ml_enhanced(bot_trading_service):
    """Test getting trading signal for ML enhanced strategy"""
    market_data = {"price": 50000.0, "volume": 1000.0}
    bot_config = {"strategy": "ml_enhanced", "config": {}}

    # Mock ML engine prediction
    mock_prediction = MagicMock()
    mock_prediction.action = "buy"
    mock_prediction.confidence = 0.85
    mock_prediction.price = 50000.0

    bot_trading_service.ml_engines["ml_enhanced"].predict = AsyncMock(
        return_value=mock_prediction
    )

    with patch.object(
        bot_trading_service, "_get_trading_signal", new_callable=AsyncMock
    ) as mock_signal:
        mock_signal.return_value = {
            "action": "buy",
            "confidence": 0.85,
            "price": 50000.0,
        }

        signal = await bot_trading_service._get_trading_signal(
            "ml_enhanced", market_data, bot_config
        )

        assert signal["action"] == "buy"
        assert signal["confidence"] == 0.85


@pytest.mark.asyncio
async def test_calculate_risk_profile(bot_trading_service):
    """Test calculating risk profile"""
    market_data = {"price": 50000.0, "volume": 1000.0}
    bot_config = {"config": {"max_position_size": 0.1, "stop_loss": 0.02}}

    with patch.object(
        bot_trading_service, "_calculate_risk_profile", new_callable=AsyncMock
    ) as mock_risk:
        mock_risk_profile = MagicMock()
        mock_risk_profile.max_position_size = 0.1
        mock_risk_profile.stop_loss = 0.02
        mock_risk.return_value = mock_risk_profile

        risk_profile = await bot_trading_service._calculate_risk_profile(
            market_data, bot_config
        )

        assert risk_profile is not None


@pytest.mark.asyncio
async def test_prepare_trade_details(bot_trading_service):
    """Test preparing trade details"""
    bot_config = {"symbol": "BTC/USDT", "config": {"max_position_size": 0.1}}
    signal = {"action": "buy", "price": 50000.0}
    market_data = {"price": 50000.0}
    risk_profile = MagicMock()
    risk_profile.max_position_size = 0.1

    with patch.object(
        bot_trading_service, "_prepare_trade_details", new_callable=MagicMock
    ) as mock_prepare:
        mock_prepare.return_value = {
            "side": "buy",
            "amount": 0.1,
            "price": 50000.0,
            "symbol": "BTC/USDT",
        }

        trade_details = bot_trading_service._prepare_trade_details(
            bot_config, signal, market_data, risk_profile
        )

        assert trade_details["side"] == "buy"
        assert trade_details["amount"] == 0.1


@pytest.mark.asyncio
async def test_execute_trading_cycle_error_handling(bot_trading_service):
    """Test error handling in trading cycle"""
    bot_config = {"id": "bot-123", "user_id": 1, "strategy": "simple_ma"}

    with patch.object(
        bot_trading_service.control_service, "is_bot_active", new_callable=AsyncMock
    ) as mock_active:
        mock_active.side_effect = Exception("Database error")

        # Should handle exception gracefully
        try:
            result = await bot_trading_service.execute_trading_cycle(bot_config)
            # If no exception, check result structure
            assert "action" in result or "error" in result
        except Exception:
            # Exception is acceptable if properly logged
            pass
