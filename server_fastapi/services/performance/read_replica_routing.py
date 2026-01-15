"""
Read Replica Routing Service
Routes read queries to read replicas for improved performance
"""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.read_replica import ReadReplicaManager

logger = logging.getLogger(__name__)


class ReadReplicaRoutingService:
    """
    Service for routing queries to read replicas

    Automatically routes read-only queries to read replicas,
    reducing load on the primary database and improving performance.
    """

    def __init__(self):
        self.replica_manager = ReadReplicaManager()
        self._is_initialized = False

    async def initialize(self, primary_url: str, replica_urls: list[str]):
        """
        Initialize read replica routing

        Args:
            primary_url: Primary database URL
            replica_urls: List of read replica URLs
        """
        try:
            await self.replica_manager.initialize(primary_url, replica_urls)
            self._is_initialized = True
            logger.info("Read replica routing initialized")
        except Exception as e:
            logger.error(
                f"Failed to initialize read replica routing: {e}", exc_info=True
            )
            self._is_initialized = False

    async def get_read_session(self) -> AsyncSession | None:
        """
        Get a database session for read operations (uses replica if available)

        Returns:
            AsyncSession connected to read replica or primary
        """
        if not self._is_initialized:
            logger.warning("Read replica routing not initialized, using primary")
            return None

        try:
            replica_session = await self.replica_manager.get_replica_session()
            if replica_session:
                return replica_session
            else:
                # Fallback to primary if no replica available
                return await self.replica_manager.get_primary_session()
        except Exception as e:
            logger.error(f"Error getting read session: {e}", exc_info=True)
            # Fallback to primary on error
            try:
                return await self.replica_manager.get_primary_session()
            except:
                return None

    async def get_write_session(self) -> AsyncSession | None:
        """
        Get a database session for write operations (always uses primary)

        Returns:
            AsyncSession connected to primary database
        """
        if not self._is_initialized:
            return None

        try:
            return await self.replica_manager.get_primary_session()
        except Exception as e:
            logger.error(f"Error getting write session: {e}", exc_info=True)
            return None

    def is_read_query(self, query: str) -> bool:
        """
        Determine if a query is read-only

        Args:
            query: SQL query string

        Returns:
            True if query is read-only
        """
        query_upper = query.strip().upper()

        # Read-only keywords
        read_keywords = ["SELECT", "WITH", "SHOW", "EXPLAIN", "DESCRIBE", "DESC"]

        # Write keywords
        write_keywords = [
            "INSERT",
            "UPDATE",
            "DELETE",
            "CREATE",
            "DROP",
            "ALTER",
            "TRUNCATE",
        ]

        # Check for write keywords first
        for keyword in write_keywords:
            if query_upper.startswith(keyword):
                return False

        # Check for read keywords
        return any(query_upper.startswith(keyword) for keyword in read_keywords)

    async def execute_read_query(
        self,
        query: str,
        params: dict | None = None,
    ):
        """
        Execute a read query on a read replica

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Query result
        """
        if not self.is_read_query(query):
            logger.warning(f"Non-read query routed to read replica: {query[:100]}")

        session = await self.get_read_session()
        if not session:
            raise RuntimeError("No database session available")

        try:
            result = await session.execute(text(query), params or {})
            return result
        finally:
            await session.close()

    async def get_replica_health(self) -> dict:
        """
        Get health status of read replicas

        Returns:
            Dictionary with replica health information
        """
        if not self._is_initialized:
            return {"status": "not_initialized"}

        try:
            health = await self.replica_manager.get_replica_health()
            return health
        except Exception as e:
            logger.error(f"Error getting replica health: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}


# Global instance
read_replica_routing_service = ReadReplicaRoutingService()
