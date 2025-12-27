#!/usr/bin/env python3
"""
Database Benchmarking Script
Benchmarks database query performance
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List
import time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from server_fastapi.database import get_db_context

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseBenchmark:
    """Database performance benchmarking"""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []

    async def benchmark_query(
        self, db: AsyncSession, query_name: str, query_func
    ) -> Dict[str, Any]:
        """Benchmark a single query"""
        try:
            start_time = time.time()
            result = await query_func(db)
            execution_time = (time.time() - start_time) * 1000  # Convert to ms

            return {
                "query_name": query_name,
                "execution_time_ms": round(execution_time, 2),
                "success": True,
                "result_count": len(result) if isinstance(result, list) else 1,
            }
        except Exception as e:
            logger.error(f"Error benchmarking {query_name}: {e}")
            return {
                "query_name": query_name,
                "execution_time_ms": None,
                "success": False,
                "error": str(e),
            }

    async def benchmark_simple_query(self, db: AsyncSession) -> Dict[str, Any]:
        """Benchmark simple SELECT 1 query"""
        async def query(db):
            result = await db.execute(text("SELECT 1"))
            return result.scalar()

        return await self.benchmark_query(db, "simple_query", query)

    async def benchmark_user_count(self, db: AsyncSession) -> Dict[str, Any]:
        """Benchmark user count query"""
        async def query(db):
            from server_fastapi.models.user import User
            stmt = select(func.count(User.id))
            result = await db.execute(stmt)
            return result.scalar()

        return await self.benchmark_query(db, "user_count", query)

    async def benchmark_trade_aggregation(self, db: AsyncSession) -> Dict[str, Any]:
        """Benchmark trade aggregation query"""
        async def query(db):
            from server_fastapi.models.trade import Trade
            stmt = (
                select(
                    func.count(Trade.id).label("total"),
                    func.sum(Trade.amount * Trade.price).label("volume"),
                )
                .where(Trade.status == "completed")
            )
            result = await db.execute(stmt)
            return result.first()

        return await self.benchmark_query(db, "trade_aggregation", query)

    async def benchmark_complex_join(self, db: AsyncSession) -> Dict[str, Any]:
        """Benchmark complex join query"""
        async def query(db):
            from server_fastapi.models.user import User
            from server_fastapi.models.trade import Trade
            stmt = (
                select(
                    User.id,
                    User.email,
                    func.count(Trade.id).label("trade_count"),
                )
                .join(Trade, User.id == Trade.user_id)
                .group_by(User.id, User.email)
                .limit(100)
            )
            result = await db.execute(stmt)
            return list(result.all())

        return await self.benchmark_query(db, "complex_join", query)

    async def run_benchmarks(self, iterations: int = 10) -> Dict[str, Any]:
        """Run all benchmarks"""
        async with get_db_context() as db:
            benchmarks = [
                self.benchmark_simple_query,
                self.benchmark_user_count,
                self.benchmark_trade_aggregation,
                self.benchmark_complex_join,
            ]

            all_results = []

            for benchmark_func in benchmarks:
                logger.info(f"Running {benchmark_func.__name__}...")
                iteration_results = []

                for i in range(iterations):
                    result = await benchmark_func(db)
                    iteration_results.append(result)

                # Calculate statistics
                successful = [r for r in iteration_results if r["success"]]
                if successful:
                    times = [r["execution_time_ms"] for r in successful]
                    all_results.append({
                        "query": benchmark_func.__name__,
                        "iterations": iterations,
                        "successful": len(successful),
                        "failed": len(iteration_results) - len(successful),
                        "avg_time_ms": round(sum(times) / len(times), 2),
                        "min_time_ms": round(min(times), 2),
                        "max_time_ms": round(max(times), 2),
                        "p50_time_ms": round(sorted(times)[len(times) // 2], 2),
                        "p95_time_ms": round(sorted(times)[int(len(times) * 0.95)], 2),
                    })

            return {
                "benchmark_date": datetime.now().isoformat(),
                "iterations": iterations,
                "results": all_results,
            }

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate benchmark report"""
        report = []
        report.append("=" * 60)
        report.append("Database Benchmark Report")
        report.append("=" * 60)
        report.append(f"\nBenchmark Date: {results['benchmark_date']}")
        report.append(f"Iterations: {results['iterations']}")

        report.append(f"\nResults:")
        for result in results["results"]:
            report.append(f"\n{result['query']}:")
            report.append(f"  Successful: {result['successful']}/{result['iterations']}")
            report.append(f"  Average: {result['avg_time_ms']}ms")
            report.append(f"  Min: {result['min_time_ms']}ms")
            report.append(f"  Max: {result['max_time_ms']}ms")
            report.append(f"  p50: {result['p50_time_ms']}ms")
            report.append(f"  p95: {result['p95_time_ms']}ms")

        return "\n".join(report)


async def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Database Benchmarking")
    parser.add_argument(
        "--iterations",
        type=int,
        default=10,
        help="Number of iterations per benchmark",
    )
    parser.add_argument(
        "--output",
        help="Output file for report (default: stdout)",
    )

    args = parser.parse_args()

    benchmark = DatabaseBenchmark()
    results = await benchmark.run_benchmarks(iterations=args.iterations)
    report = benchmark.generate_report(results)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        logger.info(f"Report written to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    asyncio.run(main())
