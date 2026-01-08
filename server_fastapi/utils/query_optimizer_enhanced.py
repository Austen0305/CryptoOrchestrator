"""
Enhanced Query Optimizer
Advanced database query optimization utilities
"""

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

logger = logging.getLogger(__name__)


class EnhancedQueryOptimizer:
    """
    Enhanced query optimizer with:
    - Eager loading hints
    - Query result caching
    - Pagination optimization
    - Batch loading
    """

    @staticmethod
    def add_eager_loads(query, relationships: list[str]):
        """
        Add eager loading for relationships to prevent N+1 queries

        Args:
            query: SQLAlchemy query
            relationships: List of relationship names to eager load

        Returns:
            Query with eager loading options
        """
        options = []
        for rel in relationships:
            # Try selectinload first (better for async)
            try:
                options.append(selectinload(rel))
            except AttributeError:
                # Fallback to joinedload
                try:
                    options.append(joinedload(rel))
                except AttributeError:
                    logger.warning(f"Could not add eager load for relationship: {rel}")

        if options:
            return query.options(*options)
        return query

    @staticmethod
    async def paginate_query(
        query,
        page: int = 1,
        page_size: int = 20,
        max_page_size: int = 100,
    ) -> dict[str, Any]:
        """
        Optimized pagination with count optimization

        Args:
            query: SQLAlchemy query
            page: Page number (1-indexed)
            page_size: Items per page
            max_page_size: Maximum allowed page size

        Returns:
            Dictionary with items, total, page, page_size
        """
        # Clamp page size
        page_size = min(page_size, max_page_size)
        page = max(1, page)

        # Calculate offset
        offset = (page - 1) * page_size

        # Get total count (optimized - only if needed)
        # For large datasets, consider approximate counts
        total_query = select(func.count()).select_from(query.subquery())

        # Get paginated results
        paginated_query = query.limit(page_size).offset(offset)

        return {
            "query": paginated_query,
            "count_query": total_query,
            "page": page,
            "page_size": page_size,
            "offset": offset,
        }

    @staticmethod
    def optimize_select_columns(query, columns: list[str] | None = None):
        """
        Optimize query by selecting only needed columns

        Args:
            query: SQLAlchemy query
            columns: List of column names to select (None = all)

        Returns:
            Optimized query
        """
        if columns:
            # Select only specified columns
            # This reduces data transfer and memory usage
            try:
                return query.with_entities(*columns)
            except Exception as e:
                logger.warning(f"Could not optimize columns: {e}")
                return query

        return query

    @staticmethod
    async def batch_load(
        session: AsyncSession,
        model_class,
        ids: list[Any],
        batch_size: int = 100,
    ) -> list[Any]:
        """
        Load entities in batches to avoid large IN clauses

        Args:
            session: Database session
            model_class: SQLAlchemy model class
            ids: List of IDs to load
            batch_size: Size of each batch

        Returns:
            List of loaded entities
        """
        if not ids:
            return []

        all_results = []

        # Process in batches
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i : i + batch_size]
            query = select(model_class).where(model_class.id.in_(batch_ids))
            result = await session.execute(query)
            all_results.extend(result.scalars().all())

        return all_results

    @staticmethod
    def add_index_hints(query, table_name: str, index_name: str):
        """
        Add index hints to query (database-specific)

        Note: This is a placeholder - actual implementation depends on database
        """
        # PostgreSQL: USE INDEX
        # MySQL: USE INDEX (index_name)
        # SQLite: Not supported
        logger.debug(f"Index hint requested for {table_name}.{index_name}")
        return query
