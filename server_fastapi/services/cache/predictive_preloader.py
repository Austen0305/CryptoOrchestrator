"""
Predictive Cache Preloading Service
Predicts and preloads cache entries based on access patterns and user behavior.
"""

import logging
from typing import Dict, List, Any, Optional, Callable, Awaitable
from datetime import datetime, timedelta
from collections import defaultdict, deque
import asyncio

logger = logging.getLogger(__name__)


class AccessPattern:
    """Tracks access patterns for cache preloading"""

    def __init__(self, max_history: int = 1000):
        self.access_history: deque = deque(maxlen=max_history)
        self.pattern_counts: Dict[str, int] = defaultdict(int)
        self.sequence_patterns: Dict[tuple, int] = defaultdict(int)
        self.last_access: Dict[str, datetime] = {}

    def record_access(self, key: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Record a cache access.

        Args:
            key: Cache key that was accessed
            context: Additional context (user_id, endpoint, etc.)
        """
        timestamp = datetime.utcnow()
        self.access_history.append(
            {"key": key, "timestamp": timestamp, "context": context or {}}
        )
        self.pattern_counts[key] += 1
        self.last_access[key] = timestamp

    def get_frequently_accessed(
        self, min_access_count: int = 10, time_window_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Get frequently accessed keys in a time window.

        Args:
            min_access_count: Minimum access count to consider
            time_window_minutes: Time window to analyze

        Returns:
            List of frequently accessed keys with counts
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)

        recent_accesses = defaultdict(int)
        for access in self.access_history:
            if access["timestamp"] >= cutoff_time:
                recent_accesses[access["key"]] += 1

        return [
            {"key": key, "count": count}
            for key, count in recent_accesses.items()
            if count >= min_access_count
        ]

    def predict_next_accesses(
        self, current_key: str, max_predictions: int = 5
    ) -> List[str]:
        """
        Predict next likely cache accesses based on sequence patterns.

        Args:
            current_key: Current cache key being accessed
            max_predictions: Maximum number of predictions

        Returns:
            List of predicted next keys
        """
        # Find sequences that start with current_key
        predictions = defaultdict(int)

        history_list = list(self.access_history)
        for i in range(len(history_list) - 1):
            if history_list[i]["key"] == current_key:
                next_key = history_list[i + 1]["key"]
                predictions[next_key] += 1

        # Sort by frequency and return top predictions
        sorted_predictions = sorted(
            predictions.items(), key=lambda x: x[1], reverse=True
        )

        return [key for key, _ in sorted_predictions[:max_predictions]]


class PredictivePreloader:
    """
    Service for predictive cache preloading based on access patterns.
    """

    def __init__(self):
        self.access_patterns = AccessPattern()
        self.preload_tasks: Dict[str, asyncio.Task] = {}
        self.preload_functions: Dict[str, Callable[[], Awaitable[Any]]] = {}
        self.enabled = True

    def register_preload_function(
        self, cache_key_pattern: str, preload_func: Callable[[], Awaitable[Any]]
    ) -> None:
        """
        Register a function to preload cache for a key pattern.

        Args:
            cache_key_pattern: Cache key pattern (e.g., 'user:{user_id}')
            preload_func: Async function that loads and caches data
        """
        self.preload_functions[cache_key_pattern] = preload_func
        logger.info(f"Registered preload function for pattern: {cache_key_pattern}")

    def record_access(
        self, cache_key: str, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a cache access for pattern analysis.

        Args:
            cache_key: Cache key that was accessed
            context: Additional context (user_id, endpoint, etc.)
        """
        if not self.enabled:
            return

        self.access_patterns.record_access(cache_key, context)

    async def preload_predicted_keys(
        self, current_key: str, cache_service: Any, max_preloads: int = 5
    ) -> int:
        """
        Preload predicted cache keys based on current access.

        Args:
            current_key: Current cache key being accessed
            cache_service: Cache service instance to use
            max_preloads: Maximum number of keys to preload

        Returns:
            Number of keys preloaded
        """
        if not self.enabled:
            return 0

        try:
            # Get predicted next keys
            predicted_keys = self.access_patterns.predict_next_accesses(
                current_key, max_predictions=max_preloads
            )

            preloaded_count = 0
            for key in predicted_keys:
                # Check if key is already cached
                cached_value = await cache_service.get(key)
                if cached_value is None:
                    # Try to find matching preload function
                    for pattern, preload_func in self.preload_functions.items():
                        if self._key_matches_pattern(key, pattern):
                            try:
                                # Execute preload function
                                await preload_func()
                                preloaded_count += 1
                                logger.debug(f"Preloaded cache key: {key}")
                                break
                            except Exception as e:
                                logger.warning(
                                    f"Error preloading key {key}: {e}", exc_info=True
                                )

            return preloaded_count

        except Exception as e:
            logger.error(f"Error in predictive preloading: {e}", exc_info=True)
            return 0

    def _key_matches_pattern(self, key: str, pattern: str) -> bool:
        """
        Check if a cache key matches a pattern.

        Args:
            key: Cache key
            pattern: Pattern with wildcards (e.g., 'user:*')

        Returns:
            True if key matches pattern
        """
        # Simple pattern matching (can be enhanced with regex)
        if "*" in pattern:
            prefix = pattern.split("*")[0]
            return key.startswith(prefix)
        return key == pattern

    async def preload_frequently_accessed(
        self,
        cache_service: Any,
        min_access_count: int = 10,
        time_window_minutes: int = 60,
    ) -> int:
        """
        Preload frequently accessed keys.

        Args:
            cache_service: Cache service instance
            min_access_count: Minimum access count
            time_window_minutes: Time window to analyze

        Returns:
            Number of keys preloaded
        """
        if not self.enabled:
            return 0

        try:
            frequent_keys = self.access_patterns.get_frequently_accessed(
                min_access_count=min_access_count,
                time_window_minutes=time_window_minutes,
            )

            preloaded_count = 0
            for key_info in frequent_keys:
                key = key_info["key"]
                # Check if already cached
                cached_value = await cache_service.get(key)
                if cached_value is None:
                    # Try to preload
                    for pattern, preload_func in self.preload_functions.items():
                        if self._key_matches_pattern(key, pattern):
                            try:
                                await preload_func()
                                preloaded_count += 1
                                break
                            except Exception as e:
                                logger.warning(
                                    f"Error preloading frequent key {key}: {e}",
                                    exc_info=True,
                                )

            return preloaded_count

        except Exception as e:
            logger.error(
                f"Error preloading frequently accessed keys: {e}", exc_info=True
            )
            return 0

    def get_access_statistics(self) -> Dict[str, Any]:
        """
        Get access pattern statistics.

        Returns:
            Dictionary with access statistics
        """
        return {
            "total_accesses": len(self.access_patterns.access_history),
            "unique_keys": len(self.access_patterns.pattern_counts),
            "frequently_accessed": len(
                self.access_patterns.get_frequently_accessed(min_access_count=5)
            ),
            "registered_preload_functions": len(self.preload_functions),
            "active_preload_tasks": len(self.preload_tasks),
        }


# Global preloader instance
_predictive_preloader = PredictivePreloader()


def get_predictive_preloader() -> PredictivePreloader:
    """Get singleton predictive preloader instance"""
    return _predictive_preloader
