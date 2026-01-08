"""
Parallel Query Execution Service
Enables PostgreSQL parallel query execution for improved performance
"""

import logging
from typing import Any

from sqlalchemy import text

logger = logging.getLogger(__name__)


class ParallelQueryService:
    """
    Service for enabling and managing parallel query execution in PostgreSQL

    PostgreSQL can execute queries in parallel using multiple worker processes,
    significantly improving performance for large analytical queries.
    """

    def __init__(self):
        self.default_parallel_workers = 4
        self.max_parallel_workers = 8

    async def enable_parallel_execution(
        self,
        session,
        min_parallel_table_scan_size: int = 8 * 1024 * 1024,  # 8MB
        parallel_setup_cost: float = 1000.0,
        parallel_tuple_cost: float = 0.01,
        max_parallel_workers_per_gather: int = 4,
    ):
        """
        Enable parallel query execution for a session

        Args:
            session: Database session
            min_parallel_table_scan_size: Minimum table size to use parallel scan (bytes)
            parallel_setup_cost: Cost of setting up parallel workers
            parallel_tuple_cost: Cost of transferring tuples between workers
            max_parallel_workers_per_gather: Maximum parallel workers per query
        """
        try:
            # Set PostgreSQL parameters for parallel execution
            await session.execute(
                text(f"""
                SET LOCAL min_parallel_table_scan_size = {min_parallel_table_scan_size};
                SET LOCAL parallel_setup_cost = {parallel_setup_cost};
                SET LOCAL parallel_tuple_cost = {parallel_tuple_cost};
                SET LOCAL max_parallel_workers_per_gather = {max_parallel_workers_per_gather};
            """)
            )

            logger.debug("Parallel query execution enabled for session")
        except Exception as e:
            logger.warning(f"Failed to enable parallel execution: {e}")

    async def execute_parallel_query(
        self,
        session,
        query: str,
        params: dict[str, Any] | None = None,
        enable_parallel: bool = True,
    ):
        """
        Execute a query with parallel execution enabled

        Args:
            session: Database session
            query: SQL query string
            params: Query parameters
            enable_parallel: Whether to enable parallel execution

        Returns:
            Query result
        """
        if enable_parallel:
            await self.enable_parallel_execution(session)

        result = await session.execute(text(query), params or {})
        return result

    def add_parallel_hint(self, query: str, workers: int | None = None) -> str:
        """
        Add parallel execution hint to query

        Note: PostgreSQL doesn't support direct hints like Oracle/MySQL,
        but we can add comments for documentation and use SET commands.

        Args:
            query: SQL query
            workers: Number of parallel workers (optional)

        Returns:
            Query with parallel hint comment
        """
        hint = f"/* PARALLEL({workers or self.default_parallel_workers}) */"
        return f"{hint}\n{query}"

    async def get_parallel_settings(self, session) -> dict[str, Any]:
        """
        Get current parallel execution settings

        Args:
            session: Database session

        Returns:
            Dictionary with parallel settings
        """
        try:
            result = await session.execute(
                text("""
                SELECT 
                    current_setting('min_parallel_table_scan_size') as min_parallel_table_scan_size,
                    current_setting('parallel_setup_cost') as parallel_setup_cost,
                    current_setting('parallel_tuple_cost') as parallel_tuple_cost,
                    current_setting('max_parallel_workers_per_gather') as max_parallel_workers_per_gather,
                    current_setting('max_parallel_workers') as max_parallel_workers
            """)
            )

            row = result.first()
            if row:
                return {
                    "min_parallel_table_scan_size": int(row[0]),
                    "parallel_setup_cost": float(row[1]),
                    "parallel_tuple_cost": float(row[2]),
                    "max_parallel_workers_per_gather": int(row[3]),
                    "max_parallel_workers": int(row[4]),
                }
            return {}
        except Exception as e:
            logger.error(f"Error getting parallel settings: {e}", exc_info=True)
            return {}


# Global instance
parallel_query_service = ParallelQueryService()
