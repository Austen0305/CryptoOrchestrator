import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch
import pytest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from server_fastapi.services.trading_orchestrator import TradingOrchestrator
from server_fastapi.services.execution.execution_service import ExecutionService


async def test_execution_bridge():
    print("Testing Execution Bridge...")

    # Mock DB Session
    mock_db = AsyncMock()

    # Mock sub-services for ExecutionService
    mock_safety = AsyncMock()
    mock_safety.validate_real_money_trade.return_value = (True, [], {})  # Safe

    mock_tx_service = AsyncMock()
    mock_tx_service.sign_and_send_transaction.return_value = "0xhash123"

    # Patch ExecutionService dependencies
    with (
        patch(
            "server_fastapi.services.execution.execution_service.RealMoneySafetyService",
            return_value=mock_safety,
        ),
        patch(
            "server_fastapi.services.execution.execution_service.TransactionService",
            return_value=mock_tx_service,
        ),
        patch("server_fastapi.services.execution.execution_service.WalletService"),
    ):  # Mock WalletService too

        # Initialize Orchestrator
        orchestrator = TradingOrchestrator(db_session=mock_db)

        # Verify ExecutionService was initialized
        assert isinstance(orchestrator.execution_service, ExecutionService)
        print("[PASS] ExecutionService initialized in TradingOrchestrator")

        # Execute Trade
        print("Executing trade via Orchestrator...")
        result = await orchestrator.execute_trade(
            bot_id="bot_1", user_id=123, side="buy", amount=0.1, symbol="ETH/USDT"
        )

        print(f"Execution Result: {result}")

        # Verify flow
        mock_safety.validate_real_money_trade.assert_called_once()
        print("[PASS] Safety check called")

        mock_tx_service.sign_and_send_transaction.assert_called_once()
        print("[PASS] Transaction signed and sent")

        assert result["status"] == "submitted"
        assert result["tx_hash"] == "0xhash123"
        print("[PASS] Trade submission successful")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_execution_bridge())
    loop.close()
