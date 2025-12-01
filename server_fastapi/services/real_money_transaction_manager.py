"""
Real Money Transaction Manager
Ensures atomic transactions for all real money operations
"""
import logging
from typing import Dict, Optional, Any, Callable, Awaitable
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal

from ..database import get_db_context
from .real_money_safety import real_money_safety_service

logger = logging.getLogger(__name__)


class RealMoneyTransactionManager:
    """Manages atomic transactions for real money operations"""
    
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
                logger.info(f"✅ {operation_name} transaction committed successfully")
                
            except SQLAlchemyError as e:
                # Rollback on database error
                await db.rollback()
                logger.error(f"❌ {operation_name} transaction rolled back: {e}", exc_info=True)
                raise
            except Exception as e:
                # Rollback on any error
                await db.rollback()
                logger.error(f"❌ {operation_name} transaction rolled back: {e}", exc_info=True)
                raise
    
    async def execute_with_rollback(
        self,
        operation: Callable[[AsyncSession], Awaitable[Any]],
        operation_name: str,
        user_id: int,
        operation_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute operation with automatic rollback on failure
        
        Args:
            operation: Async function that takes db session and returns result
            operation_name: Name of operation for logging
            user_id: User ID for audit
            operation_details: Details for audit logging
        
        Returns:
            Operation result
        """
        async with self.atomic_transaction(operation_name) as db:
            try:
                # Execute operation
                result = await operation(db)
                
                # Log success
                await real_money_safety_service.log_real_money_operation(
                    operation_type=operation_name,
                    user_id=user_id,
                    details=operation_details,
                    success=True
                )
                
                return result
                
            except Exception as e:
                # Log failure
                await real_money_safety_service.log_real_money_operation(
                    operation_type=operation_name,
                    user_id=user_id,
                    details=operation_details,
                    success=False,
                    error=str(e)
                )
                
                # Re-raise to trigger rollback
                raise


# Global instance
real_money_transaction_manager = RealMoneyTransactionManager()

