"""
Transaction Idempotency Service
Ensures transactions are processed only once using idempotency keys
"""

import logging
import hashlib
import json
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.idempotency import IdempotencyKey
from ..database import get_db_context

logger = logging.getLogger(__name__)


class TransactionIdempotencyService:
    """Service for managing transaction idempotency"""

    def __init__(self):
        self.default_ttl = timedelta(hours=24)  # 24 hour TTL for idempotency keys

    def generate_idempotency_key(
        self, user_id: str, operation: str, params: Dict[str, Any]
    ) -> str:
        """
        Generate an idempotency key from user, operation, and parameters

        Args:
            user_id: User ID
            operation: Operation name (e.g., "deposit", "withdraw")
            params: Operation parameters

        Returns:
            Idempotency key string
        """
        # Create a deterministic key from operation and params
        key_data = {
            "user_id": user_id,
            "operation": operation,
            "params": sorted(params.items()),  # Sort for consistency
        }
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()
        return f"{user_id}:{operation}:{key_hash[:16]}"

    async def check_idempotency(
        self, idempotency_key: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check if an idempotency key has been used before

        Args:
            idempotency_key: The idempotency key to check
            user_id: User ID for validation

        Returns:
            Previous result if key exists, None otherwise
        """
        if IdempotencyKey is None:
            return None

        try:
            async with get_db_context() as db:
                # Check if key exists
                result = await db.execute(
                    select(IdempotencyKey).where(
                        IdempotencyKey.key == idempotency_key,
                        IdempotencyKey.user_id == user_id,
                    )
                )
                existing_key = result.scalar_one_or_none()

                if existing_key:
                    # Check if expired
                    if existing_key.expires_at < datetime.utcnow():
                        # Delete expired key
                        await db.delete(existing_key)
                        await db.commit()
                        return None

                    # Return previous result
                    return {
                        "exists": True,
                        "result": existing_key.result,
                        "created_at": existing_key.created_at.isoformat(),
                        "status_code": existing_key.status_code,
                    }

                return None
        except Exception as e:
            logger.error(f"Error checking idempotency: {e}", exc_info=True)
            return None

    async def store_idempotency_result(
        self,
        idempotency_key: str,
        user_id: str,
        result: Dict[str, Any],
        status_code: int = 200,
        ttl: Optional[timedelta] = None,
    ) -> bool:
        """
        Store the result of an idempotent operation

        Args:
            idempotency_key: The idempotency key
            user_id: User ID
            result: Operation result
            status_code: HTTP status code
            ttl: Time to live (defaults to 24 hours)

        Returns:
            True if stored successfully
        """
        if IdempotencyKey is None:
            return False

        try:
            async with get_db_context() as db:
                expires_at = datetime.utcnow() + (ttl or self.default_ttl)

                # Check if key already exists
                existing = await db.execute(
                    select(IdempotencyKey).where(
                        IdempotencyKey.key == idempotency_key,
                        IdempotencyKey.user_id == user_id,
                    )
                )
                existing_key = existing.scalar_one_or_none()

                if existing_key:
                    # Update existing key
                    existing_key.result = result
                    existing_key.status_code = status_code
                    existing_key.expires_at = expires_at
                    existing_key.updated_at = datetime.utcnow()
                else:
                    # Create new key
                    new_key = IdempotencyKey(
                        key=idempotency_key,
                        user_id=user_id,
                        result=result,
                        status_code=status_code,
                        expires_at=expires_at,
                    )
                    db.add(new_key)

                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Error storing idempotency result: {e}", exc_info=True)
            return False

    async def cleanup_expired_keys(self) -> int:
        """
        Clean up expired idempotency keys

        Returns:
            Number of keys deleted
        """
        if IdempotencyKey is None:
            return 0

        try:
            async with get_db_context() as db:
                result = await db.execute(
                    select(IdempotencyKey).where(
                        IdempotencyKey.expires_at < datetime.utcnow()
                    )
                )
                expired_keys = result.scalars().all()

                count = len(expired_keys)
                for key in expired_keys:
                    await db.delete(key)

                await db.commit()
                logger.info(f"Cleaned up {count} expired idempotency keys")
                return count
        except Exception as e:
            logger.error(f"Error cleaning up expired keys: {e}", exc_info=True)
            return 0


# Global service instance
transaction_idempotency_service = TransactionIdempotencyService()
