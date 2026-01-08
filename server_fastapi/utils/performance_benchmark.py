"""
Performance Benchmarking Utilities
Provides utilities for benchmarking and performance testing
"""

import logging
import statistics
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Benchmark result"""

    name: str
    iterations: int
    total_time: float
    average_time: float
    min_time: float
    max_time: float
    median_time: float
    p95_time: float
    p99_time: float
    throughput: float
    errors: int
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "total_time": self.total_time,
            "average_time": self.average_time,
            "min_time": self.min_time,
            "max_time": self.max_time,
            "median_time": self.median_time,
            "p95_time": self.p95_time,
            "p99_time": self.p99_time,
            "throughput": self.throughput,
            "errors": self.errors,
            "timestamp": self.timestamp.isoformat(),
        }


class PerformanceBenchmark:
    """
    Performance benchmarking utility

    Features:
    - Function benchmarking
    - Async function benchmarking
    - Statistical analysis
    - Throughput calculation
    - Error tracking
    """

    def __init__(self):
        self.results: list[BenchmarkResult] = []

    async def benchmark_async(
        self,
        func: Callable,
        iterations: int = 100,
        warmup: int = 10,
        *args,
        **kwargs,
    ) -> BenchmarkResult:
        """Benchmark async function"""
        # Warmup
        for _ in range(warmup):
            try:
                await func(*args, **kwargs)
            except Exception:
                pass

        # Benchmark
        times = []
        errors = 0

        for _ in range(iterations):
            start = time.perf_counter()
            try:
                await func(*args, **kwargs)
                times.append(time.perf_counter() - start)
            except Exception as e:
                errors += 1
                logger.debug(f"Benchmark error: {e}")

        return self._calculate_results(func.__name__, times, iterations, errors)

    def benchmark_sync(
        self,
        func: Callable,
        iterations: int = 100,
        warmup: int = 10,
        *args,
        **kwargs,
    ) -> BenchmarkResult:
        """Benchmark sync function"""
        # Warmup
        for _ in range(warmup):
            try:
                func(*args, **kwargs)
            except Exception:
                pass

        # Benchmark
        times = []
        errors = 0

        for _ in range(iterations):
            start = time.perf_counter()
            try:
                func(*args, **kwargs)
                times.append(time.perf_counter() - start)
            except Exception as e:
                errors += 1
                logger.debug(f"Benchmark error: {e}")

        return self._calculate_results(func.__name__, times, iterations, errors)

    def _calculate_results(
        self, name: str, times: list[float], iterations: int, errors: int
    ) -> BenchmarkResult:
        """Calculate benchmark statistics"""
        if not times:
            return BenchmarkResult(
                name=name,
                iterations=iterations,
                total_time=0.0,
                average_time=0.0,
                min_time=0.0,
                max_time=0.0,
                median_time=0.0,
                p95_time=0.0,
                p99_time=0.0,
                throughput=0.0,
                errors=errors,
            )

        times.sort()
        total_time = sum(times)
        average_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        median_time = statistics.median(times)
        p95_time = times[int(len(times) * 0.95)] if len(times) > 0 else 0.0
        p99_time = times[int(len(times) * 0.99)] if len(times) > 0 else 0.0
        throughput = len(times) / total_time if total_time > 0 else 0.0

        result = BenchmarkResult(
            name=name,
            iterations=iterations,
            total_time=total_time,
            average_time=average_time,
            min_time=min_time,
            max_time=max_time,
            median_time=median_time,
            p95_time=p95_time,
            p99_time=p99_time,
            throughput=throughput,
            errors=errors,
        )

        self.results.append(result)
        return result

    def get_results(self) -> list[dict[str, Any]]:
        """Get all benchmark results"""
        return [r.to_dict() for r in self.results]

    def get_result(self, name: str) -> BenchmarkResult | None:
        """Get specific benchmark result"""
        for result in self.results:
            if result.name == name:
                return result
        return None

    def compare(self, name1: str, name2: str) -> dict[str, Any]:
        """Compare two benchmark results"""
        result1 = self.get_result(name1)
        result2 = self.get_result(name2)

        if not result1 or not result2:
            return {"error": "One or both results not found"}

        improvement = (
            (result1.average_time - result2.average_time) / result1.average_time * 100
        )

        return {
            "result1": result1.to_dict(),
            "result2": result2.to_dict(),
            "improvement_percent": improvement,
            "faster": name2 if improvement > 0 else name1,
        }


# Global benchmark instance
performance_benchmark = PerformanceBenchmark()
