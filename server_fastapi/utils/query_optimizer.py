"""
Database Query Optimization Utilities
Provides utilities for optimizing database queries and preventing N+1 problems
"""
import logging
from typing import List, Optional, Any, Dict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload, contains_eager

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Utilities for optimizing database queries"""
    
    @staticmethod
    def eager_load_relationships(query, relationships: List[str], strategy: str = "selectin"):
        """
        Add eager loading for relationships to prevent N+1 queries.
        
        Args:
            query: SQLAlchemy query object
            relationships: List of relationship names to eager load
            strategy: Loading strategy ('selectin', 'joined', or 'subquery')
        
        Returns:
            Query with eager loading applied
        """
        for rel in relationships:
            if strategy == "selectin":
                query = query.options(selectinload(rel))
            elif strategy == "joined":
                query = query.options(joinedload(rel))
            elif strategy == "subquery":
                query = query.options(joinedload(rel))
        
        return query
    
    @staticmethod
    async def batch_load_related(
        session: AsyncSession,
        model_class: type,
        ids: List[Any],
        relationship_name: str,
        filter_condition: Optional[Any] = None
    ) -> Dict[Any, List[Any]]:
        """
        Batch load related objects to prevent N+1 queries.
        
        Args:
            session: Database session
            model_class: Model class to query
            ids: List of IDs to load relationships for
            relationship_name: Name of the relationship to load
            filter_condition: Optional filter condition
        
        Returns:
            Dictionary mapping parent IDs to lists of related objects
        """
        if not ids:
            return {}
        
        # Get the relationship
        relationship = getattr(model_class, relationship_name)
        related_model = relationship.property.mapper.class_
        
        # Build query
        query = select(related_model).where(
            getattr(related_model, relationship.property.key + "_id").in_(ids)
        )
        
        if filter_condition:
            query = query.where(filter_condition)
        
        result = await session.execute(query)
        related_objects = result.scalars().all()
        
        # Group by parent ID
        grouped = {}
        for obj in related_objects:
            parent_id = getattr(obj, relationship.property.key + "_id")
            if parent_id not in grouped:
                grouped[parent_id] = []
            grouped[parent_id].append(obj)
        
        return grouped
    
    @staticmethod
    def add_pagination(query, page: int = 1, page_size: int = 100):
        """
        Add pagination to a query.
        
        Args:
            query: SQLAlchemy query object
            page: Page number (1-indexed)
            page_size: Number of items per page
        
        Returns:
            Query with pagination applied
        """
        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size)
    
    @staticmethod
    async def get_total_count(session: AsyncSession, query) -> int:
        """
        Get total count of records matching a query (before pagination).
        
        Args:
            session: Database session
            query: SQLAlchemy query object
        
        Returns:
            Total count
        """
        count_query = select(func.count()).select_from(query.subquery())
        result = await session.execute(count_query)
        return result.scalar() or 0
    
    @staticmethod
    def optimize_select_columns(query, columns: List[str]):
        """
        Optimize query to select only needed columns.
        
        Args:
            query: SQLAlchemy query object
            columns: List of column names to select
        
        Returns:
            Query with optimized column selection
        """
        # This is a simplified version - in practice, you'd map column names to actual columns
        return query


def prevent_n_plus_one(query, relationships: List[str]):
    """
    Convenience function to prevent N+1 queries.
    
    Args:
        query: SQLAlchemy query object
        relationships: List of relationship names to eager load
    
    Returns:
        Query with eager loading applied
    """
    return QueryOptimizer.eager_load_relationships(query, relationships)


async def paginate_query(
    session: AsyncSession,
    query,
    page: int = 1,
    page_size: int = 100
) -> Dict[str, Any]:
    """
    Paginate a query and return results with metadata.
    
    Args:
        session: Database session
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        page_size: Number of items per page
    
    Returns:
        Dictionary with 'items', 'total', 'page', 'page_size', 'pages'
    """
    total = await QueryOptimizer.get_total_count(session, query)
    paginated_query = QueryOptimizer.add_pagination(query, page, page_size)
    
    result = await session.execute(paginated_query)
    items = result.scalars().all()
    
    pages = (total + page_size - 1) // page_size if total > 0 else 0
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }

