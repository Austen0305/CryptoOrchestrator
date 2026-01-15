"""
Real Money Transaction Manager
Ensures atomic transactions for all real money operations
"""

import logging
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_context
from ..models.idempotency import IdempotencyKey
from .real_money_safety import real_money_safety_service

logger = logging.getLogger(__name__)


class IdempotencyError(Exception):
    """Raised when an idempotency key violation occurs"""

    pass


class RealMoneyTransactionManager:
    """Manages atomic transactions for real money operations with idempotency enforcement"""

    async def get_idempotency_key(
        self, db: AsyncSession, key: str
    ) -> IdempotencyKey | None:
        """Retrieve existing idempotency key record"""
        result = await db.execute(
            select(IdempotencyKey).where(IdempotencyKey.key == key)
        )
        return result.scalar_one_or_none()

    async def create_idempotency_key(
        self,
        db: AsyncSession,
        key: str,
        user_id: int,
        expires_at: datetime | None = None,
    ) -> IdempotencyKey:
        """Create a new idempotency key record"""
        if not expires_at:
            # Default expiration: 24 hours
            expires_at = datetime.now(UTC) + timedelta(hours=24)

        idempotency_record = IdempotencyKey(
            key=key,
            user_id=user_id,
            result={},
            status_code=202,  # Accepted/Processing
            expires_at=expires_at,
        )
        db.add(idempotency_record)
        await db.flush()  # Ensure ID is generated
        return idempotency_record

    async def execute_idempotent_operation(
        self,
        idempotency_key: str,
        user_id: int,
        operation_name: str,
        operation: Callable[[AsyncSession], Awaitable[Any]],
        operation_details: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute an operation idempotently.

        Args:
            idempotency_key: Unique key for this operation
            user_id: User performing the operation
            operation_name: Name for audit logging
            operation: Async function taking (db_session)
            operation_details: Metadata for auditing

        Returns:
            The result of the operation (or cached result if replayed)
        """
        if not idempotency_key:
            raise ValueError("Idempotency key is required for real money operations")

        async with get_db_context() as db:
            try:
                # 1. Check for existing key
                existing_key = await self.get_idempotency_key(db, idempotency_key)

                if existing_key:
                    logger.info(
                        f"Idempotency hit for key {idempotency_key}. Returning cached result."
                    )
                    # If previously successful, return stored result
                    if 200 <= existing_key.status_code < 300:
                        return existing_key.result
                    # If previously failed 4xx/5xx, we might want to allow retry depending on logic,
                    # but for strict idempotency, we return the previous state.
                    # For now, we assume strict return of previous result.
                    return existing_key.result

                # 2. Start new operation
                # Create 'pending' idempotency record within the transaction
                expiry = datetime.now(UTC) + timedelta(hours=24)
                new_key_record = IdempotencyKey(
                    key=idempotency_key,
                    user_id=user_id,
                    result={"status": "processing"},
                    status_code=202,
                    expires_at=expiry,
                )
                db.add(new_key_record)

                # 3. Execute the actual operation
                # We pass the same DB session so everything is atomic
                result = await operation(db)

                # 4. Update idempotency record with success
                new_key_record.result = (
                    result if isinstance(result, dict) else {"data": str(result)}
                )
                new_key_record.status_code = 200

                # 5. Log audit success
                await real_money_safety_service.log_real_money_operation(
                    operation_type=operation_name,
                    user_id=user_id,
                    details={**operation_details, "idempotency_key": idempotency_key},
                    success=True,
                )

                await db.commit()
                return result

            except Exception as e:
                await db.rollback()

                # Log failure (outside the rolled-back transaction if possible,
                # but here we just log to stdout/file)
                logger.error(f"Operation {operation_name} failed: {e}", exc_info=True)

                # Attempt to record failure in a separate transaction for audit
                # so the user knows their key failed
                try:
                    async with get_db_context() as error_db:
                        # Re-check/create to update status
                        error_key = await self.get_idempotency_key(
                            error_db, idempotency_key
                        )
                        if not error_key:
                            error_key = IdempotencyKey(
                                key=idempotency_key,
                                user_id=user_id,
                                result={"error": str(e)},
                                status_code=500,
                                expires_at=datetime.now(UTC) + timedelta(hours=24),
                            )
                            error_db.add(error_key)
                        else:
                            error_key.result = {"error": str(e)}
                            error_key.status_code = 500

                        await real_money_safety_service.log_real_money_operation(
                            operation_type=operation_name,
                            user_id=user_id,
                            details={
                                **operation_details,
                                "idempotency_key": idempotency_key,
                            },
                            success=False,
                            error=str(e),
                        )
                        await error_db.commit()
                except Exception as log_error:
                    logger.error(
                        f"Failed to log error state for idempotency key: {log_error}"
                    )

                raise e

    @asynccontextmanager
    async def atomic_transaction(self, operation_name: str):
        """
        Context manager for atomic real money transactions

        Usage:
            async with transaction_manager.atomic_transaction("trade_execution") as db:
                # Perform operations
                pass
        """
        async with get_db_context() as db:
            try:
                # Start transaction
                yield db

                # Commit transaction
                await db.commit()
                logger.info(f"[OK] {operation_name} transaction committed successfully")

            except SQLAlchemyError as e:
                # Rollback on database error
                await db.rollback()
                logger.error(
                    f"[ERROR] {operation_name} transaction rolled back: {e}",
                    exc_info=True,
                )
                raise
            except Exception as e:
                # Rollback on any error
                await db.rollback()
                logger.error(
                    f"[ERROR] {operation_name} transaction rolled back: {e}",
                    exc_info=True,
                )
                raise

    async def execute_with_rollback(
        self,
        operation: Callable[[AsyncSession], Awaitable[Any]],
        operation_name: str,
        user_id: int,
        operation_details: dict[str, Any],
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute operation with automatic rollback on failure.
        Delegates to execute_idempotent_operation if key provided.

        Args:
            operation: Async function that takes db session and returns result
            operation_name: Name of operation for logging
            user_id: User ID for audit
            operation_details: Details for audit logging
            idempotency_key: Optional key for idempotency execution

        Returns:
            Operation result
        """
        if idempotency_key:
            return await self.execute_idempotent_operation(
                idempotency_key=idempotency_key,
                user_id=user_id,
                operation_name=operation_name,
                operation=operation,
                operation_details=operation_details,
            )

        # Fallback for legacy calls without idempotency key (WARN: Unsafe for real money)
        logger.warning(
            f"Executing real-money operation '{operation_name}' WITHOUT idempotency key. This is unsafe."
        )

        async with self.atomic_transaction(operation_name) as db:
            try:
                # Execute operation
                result = await operation(db)

                # Log success
                await real_money_safety_service.log_real_money_operation(
                    operation_type=operation_name,
                    user_id=user_id,
                    details=operation_details,
                    success=True,
                )

                return result

            except Exception as e:
                # Log failure
                await real_money_safety_service.log_real_money_operation(
                    operation_type=operation_name,
                    user_id=user_id,
                    details=operation_details,
                    success=False,
                    error=str(e),
                )

                # Re-raise to trigger rollback
                raise


# Global instance
real_money_transaction_manager = RealMoneyTransactionManager()
