import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from server_fastapi.services.real_money_transaction_manager import (
    RealMoneyTransactionManager,
)
from server_fastapi.models.idempotency import IdempotencyKey
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_idempotent_operation_success():
    """Verify that a successful operation is recorded and returns the same result on retry."""
    manager = RealMoneyTransactionManager()
    ikey = "test_succ_123"
    user_id = 999

    mock_db = AsyncMock(spec=AsyncSession)

    # Mock get_db_context
    with patch(
        "server_fastapi.services.real_money_transaction_manager.get_db_context"
    ) as mock_ctx:
        mock_ctx.return_value.__aenter__.return_value = mock_db

        # 1. First execution (Fresh key)
        operation = AsyncMock(return_value={"status": "success", "amount": 100})

        # Mocking db.execute for get_idempotency_key -> None
        mock_execute_result = MagicMock()
        mock_execute_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_execute_result

        result1 = await manager.execute_idempotent_operation(
            idempotency_key=ikey,
            user_id=user_id,
            operation_name="test_op",
            operation=operation,
            operation_details={},
        )

        assert result1["status"] == "success"
        assert operation.call_count == 1
        assert mock_db.commit.called

        # 2. Second execution (Retry)
        # Mocking db.execute for get_idempotency_key -> existing record
        existing_record = IdempotencyKey(
            key=ikey,
            user_id=user_id,
            status_code=200,
            result={"status": "success", "amount": 100},
        )
        mock_execute_result.scalar_one_or_none.return_value = existing_record

        # Reset mock call counts
        operation.reset_mock()
        mock_db.commit.reset_mock()

        result2 = await manager.execute_idempotent_operation(
            idempotency_key=ikey,
            user_id=user_id,
            operation_name="test_op",
            operation=operation,
            operation_details={},
        )

        assert result2 == result1
        assert operation.call_count == 0  # Should NOT be called again
        assert result2["status"] == "success"


@pytest.mark.asyncio
async def test_idempotent_operation_failure():
    """Verify that a failed operation triggers a rollback and still logs the failure."""
    manager = RealMoneyTransactionManager()
    ikey = "test_fail_123"
    user_id = 999

    mock_db = AsyncMock(spec=AsyncSession)

    with patch(
        "server_fastapi.services.real_money_transaction_manager.get_db_context"
    ) as mock_ctx:
        mock_ctx.return_value.__aenter__.return_value = mock_db

        # Mocking db.execute for get_idempotency_key -> None
        mock_execute_result = MagicMock()
        mock_execute_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_execute_result

        # Operation fails
        operation = AsyncMock(side_effect=Exception("API Timeout"))

        with pytest.raises(Exception):
            await manager.execute_idempotent_operation(
                idempotency_key=ikey,
                user_id=user_id,
                operation_name="test_op",
                operation=operation,
                operation_details={},
            )

        assert mock_db.rollback.called
        assert not mock_db.commit.called
