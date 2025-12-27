"""
Query Optimization Utilities
Helper functions for optimizing database queries and preventing N+1 problems.
Includes query batching, parallel execution, and index optimization.
"""

import logging
from typing import List, Type, Any, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select, func, text
from sqlalchemy.exc import SQLAlchemyError

# Import batching utilities
from .query_batching import QueryBatcher, ParallelQueryExecutor

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Utility class for optimizing database queries"""

    @staticmethod
    async def batch_load_relationships(
        session: AsyncSession,
        parent_model: Type[Any],
        parent_ids: List[str],
        relationship_name: str,
        use_joinedload: bool = False,
    ) -> dict:
        """
        Batch load relationships to prevent N+1 queries.

        Args:
            session: Database session
            parent_model: SQLAlchemy model class
            parent_ids: List of parent IDs to load relationships for
            relationship_name: Name of the relationship attribute
            use_joinedload: Use joinedload instead of selectinload

        Returns:
            Dictionary mapping parent_id to list of related objects
        """
        if not parent_ids:
            return {}

        try:
            # Use selectinload for better performance with many parents
            # Use joinedload for better performance with few parents
            loader = joinedload if use_joinedload else selectinload
            relationship = getattr(parent_model, relationship_name)

            query = (
                select(parent_model)
                .where(parent_model.id.in_(parent_ids))
                .options(loader(relationship))
            )

            result = await session.execute(query)
            parents = result.scalars().all()

            # Build mapping
            relationship_map = {}
            for parent in parents:
                relationship_map[parent.id] = getattr(parent, relationship_name, [])

            return relationship_map
        except SQLAlchemyError as e:
            logger.error(f"Error batch loading relationships: {e}", exc_info=True)
            return {}

    @staticmethod
    def eager_load_relationships(
        query: Any, relationships: List[str], use_joinedload: bool = False
    ) -> Any:
        """
        Add eager loading options to a query to prevent N+1 queries.

        Args:
            query: SQLAlchemy select query
            relationships: List of relationship names to eager load
            use_joinedload: Use joinedload instead of selectinload

        Returns:
            Query with eager loading options applied
        """
        loader = joinedload if use_joinedload else selectinload

        for rel_name in relationships:
            # Get relationship attribute from model (assumes query selects a model)
            # This is a simplified version - in practice, you'd need the model class
            try:
                # Use string-based loading which SQLAlchemy supports
                query = query.options(loader(rel_name))  # type: ignore
            except Exception:
                # If string-based loading fails, log warning and continue
                logger.warning(f"Could not eager load relationship: {rel_name}")

        return query

    @staticmethod
    async def count_query(
        session: AsyncSession, model: Type[Any], filters: Optional[dict] = None
    ) -> int:
        """
        Efficiently count records with optional filters.

        Args:
            session: Database session
            model: SQLAlchemy model class
            filters: Optional dictionary of filters {field: value}

        Returns:
            Count of matching records
        """
        try:
            query = select(func.count()).select_from(model)

            if filters:
                for field, value in filters.items():
                    if hasattr(model, field):
                        query = query.where(getattr(model, field) == value)

            result = await session.execute(query)
            return result.scalar() or 0
        except SQLAlchemyError as e:
            logger.error(f"Error counting records: {e}", exc_info=True)
            return 0

    @staticmethod
    def paginate_query(query: Any, page: int = 1, page_size: int = 20) -> Any:
        """
        Add pagination to a query.

        Args:
            query: SQLAlchemy select query
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Query with pagination applied
        """
        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size)


def detect_n_plus_one(queries: List[dict]) -> List[dict]:
    """
    Detect potential N+1 query problems from query log.

    Args:
        queries: List of query dictionaries with 'sql' and 'count' keys

    Returns:
        List of potential N+1 query issues
    """
    issues = []

    # Group queries by pattern
    query_patterns: Dict[str, List[dict]] = {}
    for query in queries:
        sql = query.get("sql", "")
        # Extract table name and operation
        if "SELECT" in sql.upper():
            # Simple pattern matching - could be enhanced
            pattern = sql[:100]  # First 100 chars as pattern
            if pattern not in query_patterns:
                query_patterns[pattern] = []
            query_patterns[pattern].append(query)

    # Detect patterns that appear many times (potential N+1)
    for pattern, query_list in query_patterns.items():
        if len(query_list) > 10:  # Threshold for N+1 detection
            issues.append(
                {
                    "pattern": pattern,
                    "count": len(query_list),
                    "queries": query_list[:5],  # Sample queries
                }
            )

    return issues


class IndexOptimizer:
    """Utility for analyzing and optimizing database indexes"""

    @staticmethod
    async def analyze_index_usage(
        session: AsyncSession, table_name: str
    ) -> Dict[str, Any]:
        """
        Analyze index usage for a table (PostgreSQL only)

        Args:
            session: Database session
            table_name: Name of table to analyze

        Returns:
            Dictionary with index usage statistics
        """
        try:
            # PostgreSQL-specific query
            query = text(
                """
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan as index_scans,
                    idx_tup_read as tuples_read,
                    idx_tup_fetch as tuples_fetched
                FROM pg_stat_user_indexes
                WHERE tablename = :table_name
                ORDER BY idx_scan DESC
            """
            )

            result = await session.execute(query, {"table_name": table_name})
            indexes = result.fetchall()

            return {
                "table": table_name,
                "indexes": [
                    {
                        "name": idx[2],
                        "scans": idx[3],
                        "tuples_read": idx[4],
                        "tuples_fetched": idx[5],
                    }
                    for idx in indexes
                ],
            }
        except Exception as e:
            logger.warning(f"Index analysis not available (may not be PostgreSQL): {e}")
            return {
                "table": table_name,
                "indexes": [],
                "error": "Index analysis only available for PostgreSQL",
            }

    @staticmethod
    async def get_unused_indexes(
        session: AsyncSession, min_scans: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find unused or rarely used indexes (PostgreSQL only)

        Args:
            session: Database session
            min_scans: Minimum number of scans to consider index as used

        Returns:
            List of unused indexes
        """
        try:
            query = text(
                """
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan as index_scans,
                    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                FROM pg_stat_user_indexes
                WHERE idx_scan < :min_scans
                ORDER BY pg_relation_size(indexrelid) DESC
            """
            )

            result = await session.execute(query, {"min_scans": min_scans})
            unused = result.fetchall()

            return [
                {
                    "schema": row[0],
                    "table": row[1],
                    "index": row[2],
                    "scans": row[3],
                    "size": row[4],
                }
                for row in unused
            ]
        except Exception as e:
            logger.warning(f"Unused index detection not available: {e}")
            return []

    @staticmethod
    async def get_missing_indexes(session: AsyncSession) -> List[Dict[str, Any]]:
        """
        Find potential missing indexes using pg_stat_statements (PostgreSQL only)

        Args:
            session: Database session

        Returns:
            List of potential missing indexes
        """
        try:
            # Check if pg_stat_statements is available
            query = text(
                """
                SELECT EXISTS (
                    SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
                )
            """
            )
            result = await session.execute(query)
            if not result.scalar():
                return []

            # Find sequential scans that might benefit from indexes
            query = text(
                """
                SELECT
                    schemaname,
                    tablename,
                    seq_scan,
                    seq_tup_read,
                    idx_scan,
                    seq_tup_read / NULLIF(seq_scan, 0) as avg_tuples_per_scan
                FROM pg_stat_user_tables
                WHERE seq_scan > idx_scan * 10
                  AND seq_scan > 1000
                ORDER BY seq_tup_read DESC
                LIMIT 20
            """
            )

            result = await session.execute(query)
            missing = result.fetchall()

            return [
                {
                    "schema": row[0],
                    "table": row[1],
                    "sequential_scans": row[2],
                    "tuples_read": row[3],
                    "index_scans": row[4],
                    "avg_tuples_per_scan": row[5],
                }
                for row in missing
            ]
        except Exception as e:
            logger.warning(f"Missing index detection not available: {e}")
            return []
