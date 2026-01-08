"""
Query Batching Utilities
Implements efficient batch query execution to reduce database round trips.
"""

import asyncio
import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

T = TypeVar("T")


class QueryBatcher:
    """
    Utility for batching multiple queries into single database operations
    """

    @staticmethod
    async def batch_get_by_ids(
        session: AsyncSession, model: type[T], ids: list[Any], batch_size: int = 100
    ) -> dict[Any, T]:
        """
        Batch fetch multiple records by IDs efficiently.

        Args:
            session: Database session
            model: SQLAlchemy model class
            ids: List of IDs to fetch
            batch_size: Maximum number of IDs per query

        Returns:
            Dictionary mapping ID to model instance
        """
        if not ids:
            return {}

        result_map = {}

        # Process in batches to avoid query size limits
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i : i + batch_size]

            try:
                query = select(model).where(model.id.in_(batch_ids))
                result = await session.execute(query)
                records = result.scalars().all()

                for record in records:
                    result_map[record.id] = record

            except SQLAlchemyError as e:
                logger.error(
                    f"Error batch fetching {model.__name__}: {e}",
                    exc_info=True,
                    extra={"model": model.__name__, "batch_size": len(batch_ids)},
                )

        return result_map

    @staticmethod
    async def batch_get_by_field(
        session: AsyncSession,
        model: type[T],
        field_name: str,
        values: list[Any],
        batch_size: int = 100,
    ) -> dict[Any, list[T]]:
        """
        Batch fetch records by a specific field value.

        Args:
            session: Database session
            model: SQLAlchemy model class
            field_name: Name of field to filter by
            values: List of field values to fetch
            batch_size: Maximum number of values per query

        Returns:
            Dictionary mapping field value to list of matching records
        """
        if not values:
            return {}

        result_map = defaultdict(list)
        field = getattr(model, field_name, None)

        if not field:
            logger.warning(f"Field {field_name} not found on model {model.__name__}")
            return {}

        # Process in batches
        for i in range(0, len(values), batch_size):
            batch_values = values[i : i + batch_size]

            try:
                query = select(model).where(field.in_(batch_values))
                result = await session.execute(query)
                records = result.scalars().all()

                for record in records:
                    field_value = getattr(record, field_name)
                    result_map[field_value].append(record)

            except SQLAlchemyError as e:
                logger.error(
                    f"Error batch fetching by {field_name}: {e}",
                    exc_info=True,
                    extra={
                        "model": model.__name__,
                        "field": field_name,
                        "batch_size": len(batch_values),
                    },
                )

        return dict(result_map)

    @staticmethod
    async def batch_create(
        session: AsyncSession,
        model: type[T],
        records: list[dict[str, Any]],
        batch_size: int = 100,
    ) -> list[T]:
        """
        Batch create multiple records efficiently.

        Args:
            session: Database session
            model: SQLAlchemy model class
            records: List of dictionaries with record data
            batch_size: Maximum number of records per insert

        Returns:
            List of created model instances
        """
        if not records:
            return []

        created_records = []

        # Process in batches
        for i in range(0, len(records), batch_size):
            batch_records = records[i : i + batch_size]

            try:
                # Create model instances
                instances = [model(**record_data) for record_data in batch_records]

                # Add all to session
                session.add_all(instances)

                # Flush to get IDs (but don't commit yet)
                await session.flush()

                created_records.extend(instances)

            except SQLAlchemyError as e:
                logger.error(
                    f"Error batch creating {model.__name__}: {e}",
                    exc_info=True,
                    extra={"model": model.__name__, "batch_size": len(batch_records)},
                )
                await session.rollback()
                raise

        return created_records

    @staticmethod
    async def batch_update(
        session: AsyncSession,
        model: type[T],
        updates: list[dict[str, Any]],
        id_field: str = "id",
        batch_size: int = 100,
    ) -> int:
        """
        Batch update multiple records efficiently.

        Args:
            session: Database session
            model: SQLAlchemy model class
            updates: List of dictionaries with {id_field: value, ...other_fields}
            id_field: Name of ID field
            batch_size: Maximum number of updates per batch

        Returns:
            Number of records updated
        """
        if not updates:
            return 0

        updated_count = 0
        id_field_attr = getattr(model, id_field, None)

        if not id_field_attr:
            logger.warning(f"ID field {id_field} not found on model {model.__name__}")
            return 0

        # Group updates by ID
        updates_by_id = {update[id_field]: update for update in updates}
        ids = list(updates_by_id.keys())

        # Process in batches
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i : i + batch_size]

            try:
                # Fetch existing records
                query = select(model).where(id_field_attr.in_(batch_ids))
                result = await session.execute(query)
                records = result.scalars().all()

                # Update records
                for record in records:
                    record_id = getattr(record, id_field)
                    update_data = updates_by_id[record_id]

                    # Update fields (excluding ID field)
                    for field, value in update_data.items():
                        if field != id_field and hasattr(record, field):
                            setattr(record, field, value)

                    updated_count += 1

                # Flush updates
                await session.flush()

            except SQLAlchemyError as e:
                logger.error(
                    f"Error batch updating {model.__name__}: {e}",
                    exc_info=True,
                    extra={"model": model.__name__, "batch_size": len(batch_ids)},
                )
                await session.rollback()
                raise

        return updated_count

    @staticmethod
    async def batch_delete(
        session: AsyncSession, model: type[T], ids: list[Any], batch_size: int = 100
    ) -> int:
        """
        Batch delete multiple records efficiently.

        Args:
            session: Database session
            model: SQLAlchemy model class
            ids: List of IDs to delete
            batch_size: Maximum number of IDs per delete operation

        Returns:
            Number of records deleted
        """
        if not ids:
            return 0

        deleted_count = 0

        # Process in batches
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i : i + batch_size]

            try:
                # Fetch records to delete
                query = select(model).where(model.id.in_(batch_ids))
                result = await session.execute(query)
                records = result.scalars().all()

                # Delete records
                for record in records:
                    await session.delete(record)
                    deleted_count += 1

                # Flush deletes
                await session.flush()

            except SQLAlchemyError as e:
                logger.error(
                    f"Error batch deleting {model.__name__}: {e}",
                    exc_info=True,
                    extra={"model": model.__name__, "batch_size": len(batch_ids)},
                )
                await session.rollback()
                raise

        return deleted_count


class ParallelQueryExecutor:
    """
    Execute multiple independent queries in parallel
    """

    @staticmethod
    async def execute_parallel(
        queries: list[Callable[[AsyncSession], Awaitable[Any]]],
        session: AsyncSession,
        max_concurrent: int = 5,
    ) -> list[Any]:
        """
        Execute multiple queries in parallel with concurrency limit.

        Args:
            queries: List of async query functions that take session as parameter
            session: Database session
            max_concurrent: Maximum number of concurrent queries

        Returns:
            List of query results in same order as queries
        """
        if not queries:
            return []

        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_semaphore(
            query_func: Callable[[AsyncSession], Awaitable[Any]],
        ) -> Any:
            async with semaphore:
                try:
                    return await query_func(session)
                except Exception as e:
                    logger.error(f"Error executing parallel query: {e}", exc_info=True)
                    raise

        # Execute all queries in parallel
        tasks = [execute_with_semaphore(query) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check for exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Query {i} failed: {result}", exc_info=True)
                raise result

        return results
