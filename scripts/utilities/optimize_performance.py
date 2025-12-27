#!/usr/bin/env python3
"""
Performance Optimization Script
Identifies slow queries, missing indexes, and optimization opportunities
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from server_fastapi.database.connection_pool import get_db_session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_slow_queries():
    """Check for slow queries in database"""
    logger.info("🔍 Checking for slow queries...")
    
    async with get_db_session() as session:
        # Check for queries taking > 500ms (if PostgreSQL with pg_stat_statements)
        try:
            result = await session.execute(text("""
                SELECT 
                    query,
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    max_exec_time
                FROM pg_stat_statements
                WHERE mean_exec_time > 500
                ORDER BY mean_exec_time DESC
                LIMIT 10
            """))
            
            slow_queries = result.fetchall()
            if slow_queries:
                logger.warning(f"⚠️  Found {len(slow_queries)} slow queries (>500ms):")
                for query in slow_queries:
                    logger.warning(f"   Mean: {query.mean_exec_time:.2f}ms - {query.query[:100]}")
            else:
                logger.info("✅ No slow queries found")
        except Exception as e:
            logger.info(f"ℹ️  pg_stat_statements not available: {e}")


async def check_missing_indexes():
    """Check for missing indexes on frequently queried columns"""
    logger.info("🔍 Checking for missing indexes...")
    
    async with get_db_session() as session:
        # Check for tables without indexes on common query columns
        try:
            result = await session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats
                WHERE schemaname = 'public'
                AND n_distinct > 100
                AND correlation < 0.1
                ORDER BY n_distinct DESC
                LIMIT 20
            """))
            
            potential_indexes = result.fetchall()
            if potential_indexes:
                logger.info(f"💡 Found {len(potential_indexes)} columns that might benefit from indexes:")
                for idx in potential_indexes:
                    logger.info(f"   {idx.tablename}.{idx.attname} (distinct: {idx.n_distinct})")
            else:
                logger.info("✅ All important columns appear to have indexes")
        except Exception as e:
            logger.info(f"ℹ️  Index analysis not available: {e}")


async def check_cache_coverage():
    """Check cache coverage on endpoints"""
    logger.info("🔍 Checking cache coverage...")
    
    # Check routes for @cached decorator usage
    routes_dir = project_root / "server_fastapi" / "routes"
    cached_count = 0
    total_routes = 0
    
    for route_file in routes_dir.glob("*.py"):
        if route_file.name == "__init__.py":
            continue
            
        try:
            content = route_file.read_text()
            total_routes += content.count("@router.")
            cached_count += content.count("@cached")
        except Exception:
            pass
    
    logger.info(f"📊 Cache coverage: {cached_count}/{total_routes} routes have caching")
    
    if cached_count / total_routes < 0.7:
        logger.warning(f"⚠️  Only {cached_count/total_routes*100:.1f}% of routes have caching")
    else:
        logger.info(f"✅ Good cache coverage: {cached_count/total_routes*100:.1f}%")


async def check_pagination():
    """Check pagination usage on list endpoints"""
    logger.info("🔍 Checking pagination usage...")
    
    routes_dir = project_root / "server_fastapi" / "routes"
    paginated_count = 0
    list_endpoints = 0
    
    for route_file in routes_dir.glob("*.py"):
        if route_file.name == "__init__.py":
            continue
            
        try:
            content = route_file.read_text()
            # Count list endpoints (GET routes that return lists)
            list_endpoints += content.count("List[") + content.count("list[")
            # Count pagination usage
            paginated_count += content.count("paginate_query") + content.count("paginate_response")
        except Exception:
            pass
    
    logger.info(f"📊 Pagination coverage: {paginated_count}/{list_endpoints} list endpoints use pagination")
    
    if paginated_count / list_endpoints < 0.8:
        logger.warning(f"⚠️  Only {paginated_count/list_endpoints*100:.1f}% of list endpoints use pagination")
    else:
        logger.info(f"✅ Good pagination coverage: {paginated_count/list_endpoints*100:.1f}%")


async def main():
    """Run all performance checks"""
    logger.info("🚀 Starting Performance Optimization Analysis...\n")
    
    try:
        await check_slow_queries()
        print()
        await check_missing_indexes()
        print()
        await check_cache_coverage()
        print()
        await check_pagination()
        print()
        
        logger.info("✅ Performance analysis complete!")
        logger.info("\n💡 Recommendations:")
        logger.info("   1. Run load tests: npm run load:test:comprehensive")
        logger.info("   2. Review slow queries and add indexes if needed")
        logger.info("   3. Add caching to frequently accessed endpoints")
        logger.info("   4. Ensure all list endpoints use pagination")
        
    except Exception as e:
        logger.error(f"❌ Error during analysis: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
