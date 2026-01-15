"""
Performance Profiling Utilities
Provides utilities for profiling and optimizing code performance
"""

import asyncio
import cProfile
import functools
import io
import logging
import pstats
import time
from collections import defaultdict
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PerformanceProfile:
    """Performance profile data"""

    function_name: str
    total_time: float
    call_count: int
    avg_time: float
    min_time: float = float("inf")
    max_time: float = 0.0
    cumulative_time: float = 0.0
    children: dict[str, float] = field(default_factory=dict)


class PerformanceProfiler:
    """Performance profiler for tracking function execution times"""

    def __init__(self):
        self.profiles: dict[str, PerformanceProfile] = {}
        self.active_profiles: dict[str, float] = {}
        self.call_counts: dict[str, int] = defaultdict(int)
        self.total_times: dict[str, float] = defaultdict(float)
        self.min_times: dict[str, float] = defaultdict(lambda: float("inf"))
        self.max_times: dict[str, float] = defaultdict(float)

    @contextmanager
    def profile(self, name: str):
        """Context manager for profiling code blocks"""
        start_time = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start_time
            self.record(name, duration)

    def record(self, name: str, duration: float):
        """Record a performance measurement"""
        self.call_counts[name] += 1
        self.total_times[name] += duration
        self.min_times[name] = min(self.min_times[name], duration)
        self.max_times[name] = max(self.max_times[name], duration)

    def get_profile(self, name: str) -> PerformanceProfile | None:
        """Get performance profile for a function"""
        if name not in self.call_counts:
            return None

        call_count = self.call_counts[name]
        total_time = self.total_times[name]

        return PerformanceProfile(
            function_name=name,
            total_time=total_time,
            call_count=call_count,
            avg_time=total_time / call_count if call_count > 0 else 0,
            min_time=self.min_times[name],
            max_time=self.max_times[name],
            cumulative_time=total_time,
        )

    def get_all_profiles(self) -> dict[str, PerformanceProfile]:
        """Get all performance profiles"""
        profiles = {}
        for name in self.call_counts:
            profile = self.get_profile(name)
            if profile:
                profiles[name] = profile
        return profiles

    def get_slow_functions(self, threshold_ms: float = 100) -> list[PerformanceProfile]:
        """Get functions that exceed performance threshold"""
        slow = []
        for _name, profile in self.get_all_profiles().items():
            if profile.avg_time * 1000 > threshold_ms:
                slow.append(profile)
        return sorted(slow, key=lambda x: x.avg_time, reverse=True)

    def reset(self):
        """Reset all profiling data"""
        self.profiles.clear()
        self.active_profiles.clear()
        self.call_counts.clear()
        self.total_times.clear()
        self.min_times.clear()
        self.max_times.clear()


def profile_function(func: Callable) -> Callable:
    """Decorator to profile a function"""

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        profiler = get_profiler()
        with profiler.profile(func.__name__):
            return await func(*args, **kwargs)

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        profiler = get_profiler()
        with profiler.profile(func.__name__):
            return func(*args, **kwargs)

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


def profile_cpu(func: Callable) -> Callable:
    """Decorator to profile CPU usage with cProfile"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            profiler.disable()
            s = io.StringIO()
            ps = pstats.Stats(profiler, stream=s)
            ps.sort_stats("cumulative")
            ps.print_stats(10)  # Top 10 functions
            logger.debug(f"CPU Profile for {func.__name__}:\n{s.getvalue()}")

    return wrapper


# Global profiler instance
_profiler = PerformanceProfiler()


def get_profiler() -> PerformanceProfiler:
    """Get global profiler instance"""
    return _profiler
