"""
Reusable test helper functions for common test scenarios
"""

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession


async def create_test_user(
    db: AsyncSession,
    email: str | None = None,
    password: str = "TestPassword123!",
    name: str = "Test User",
) -> dict[str, Any]:
    """Helper to create a test user"""
    from server_fastapi.services.auth.auth_service import AuthService

    if email is None:
        email = f"testuser-{uuid.uuid4().hex[:8]}@example.com"

    auth_service = AuthService()
    user = await auth_service.register_user(
        email=email, password=password, name=name, session=db
    )

    return {
        "id": user.get("id") if isinstance(user, dict) else str(user),
        "email": email,
        "name": name,
    }


async def create_test_bot(
    db: AsyncSession,
    user_id: str,
    name: str = "Test Bot",
    symbol: str = "BTC/USDT",
    strategy: str = "simple_ma",
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Helper to create a test bot"""
    from server_fastapi.services.trading.bot_service import BotService

    if config is None:
        config = {
            "max_position_size": 0.1,
            "stop_loss": 0.02,
            "take_profit": 0.05,
            "risk_per_trade": 0.01,
        }

    bot_service = BotService(db_session=db)
    bot_id = await bot_service.create_bot(
        user_id=int(user_id) if isinstance(user_id, str) else user_id,
        name=name,
        symbol=symbol,
        strategy=strategy,
        parameters=config,
    )

    return {
        "id": bot_id,
        "name": name,
        "symbol": symbol,
        "strategy": strategy,
        "config": config,
    }


def mock_dex_response(
    price: float | None = None,
    quote: dict[str, Any] | None = None,
    balance: dict[str, Any] | None = None,
) -> MagicMock:
    """
    Helper to mock DEX aggregator responses.

    [WARN] DEPRECATED: Originally mocked exchange API responses.
    Now mocks DEX aggregator (0x, OKX, Rubic) responses.
    """
    mock_dex = MagicMock()

    if quote:
        mock_dex.get_quote = AsyncMock(return_value=quote)
    else:
        # Default DEX quote response
        mock_dex.get_quote = AsyncMock(
            return_value={
                "price": price or 3000.0,  # ETH price in USDC
                "buy_amount": "1000000000000000000",  # 1 ETH in wei
                "sell_amount": "3000000000",  # 3000 USDC (6 decimals)
                "price_impact": 0.001,  # 0.1% price impact
                "aggregator": "0x",
                "calldata": "0x1234...",
                "to": "0x1234567890123456789012345678901234567890",
            }
        )

    if balance:
        mock_dex.get_balance = AsyncMock(return_value=balance)
    else:
        # Default wallet balance response (blockchain balances)
        mock_dex.get_balance = AsyncMock(
            return_value={
                "ETH": {"free": 1.0, "used": 0.0, "total": 1.0},
                "USDC": {"free": 50000.0, "used": 0.0, "total": 50000.0},
            }
        )

    # Mock wallet balance fetching
    mock_dex.get_wallet_balance = AsyncMock(
        return_value={
            "native": "1000000000000000000",  # 1 ETH in wei
            "tokens": {
                "0xA0b86991c6218b36c1d19D4a2e9Eb0c3606eB48": "50000000000"  # 50000 USDC (6 decimals)
            },
        }
    )

    mock_dex.get_fees = AsyncMock(
        return_value=MagicMock(
            platform_fee_bps=20,  # 0.2% platform fee
            aggregator_fee_bps=5,  # 0.05% aggregator fee
            gas_estimate=150000,  # Gas estimate for swap
        )
    )

    return mock_dex


def assert_bot_response(
    response_data: dict[str, Any], expected_fields: list | None = None
):
    """Helper to validate bot API responses"""
    if expected_fields is None:
        expected_fields = ["id", "name", "symbol", "strategy"]

    for field in expected_fields:
        assert field in response_data, f"Missing field: {field}"

    assert isinstance(response_data["id"], (str, int))
    assert isinstance(response_data["name"], str)
    assert len(response_data["name"]) > 0


def create_mock_db_session() -> MagicMock:
    """Create a mock database session for testing"""
    mock_session = MagicMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.delete = MagicMock()

    # Mock result object
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_result.scalars = MagicMock(return_value=[])
    mock_result.first = MagicMock(return_value=None)
    mock_session.execute.return_value = mock_result

    return mock_session
