"""
Multi-tenant middleware for data isolation
Ensures all queries are scoped to the current user
"""

import logging
from typing import Callable
from fastapi import Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)


def filter_by_user_id(query, user_id: int, model_class, user_id_field: str = "user_id"):
    """Filter query by user_id"""
    if hasattr(model_class, user_id_field):
        return query.where(getattr(model_class, user_id_field) == user_id)
    return query


async def ensure_user_owns_resource(
    db: AsyncSession,
    model_class,
    resource_id: any,
    user_id: int,
    user_id_field: str = "user_id",
    id_field: str = "id",
) -> bool:
    """Verify that a resource belongs to a user"""
    try:
        query = select(model_class).where(
            and_(
                getattr(model_class, id_field) == resource_id,
                getattr(model_class, user_id_field) == user_id,
            )
        )
        result = await db.execute(query)
        resource = result.scalar_one_or_none()
        return resource is not None
    except Exception as e:
        logger.error(f"Error checking resource ownership: {e}", exc_info=True)
        return False
