"""
Query Optimization Routes
API endpoints for database query optimization and monitoring
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies.auth import get_current_user
from ..services.query_optimizer import query_optimizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/query-optimization", tags=["Query Optimization"])


class OptimizeQueryRequest(BaseModel):
    """Request to optimize a query"""

    query: str
    use_index: bool = True
    explain: bool = False


@router.get("/statistics")
async def get_query_statistics(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Get overall query performance statistics"""
    try:
        stats = await query_optimizer.get_query_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting query statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get query statistics")


@router.get("/slow-queries")
async def get_slow_queries(
    current_user: Annotated[dict, Depends(get_current_user)],
    limit: int = Query(10, ge=1, le=50),
    min_executions: int = Query(5, ge=1),
) -> list[dict]:
    """Get slow query analysis"""
    try:
        slow_queries = await query_optimizer.analyze_slow_queries(
            limit=limit, min_executions=min_executions
        )
        return slow_queries
    except Exception as e:
        logger.error(f"Error analyzing slow queries: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to analyze slow queries")


@router.post("/optimize")
async def optimize_query(
    request: OptimizeQueryRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    """Analyze and optimize a SQL query"""
    try:
        result = await query_optimizer.optimize_query(
            db=db,
            query=request.query,
            use_index=request.use_index,
            explain=request.explain,
        )
        return result
    except Exception as e:
        logger.error(f"Error optimizing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to optimize query")


@router.get("/pool-stats")
async def get_pool_stats(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    """Get database connection pool statistics"""
    try:
        stats = await query_optimizer.get_pool_stats(db)
        return stats
    except Exception as e:
        logger.error(f"Error getting pool stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get pool statistics")
