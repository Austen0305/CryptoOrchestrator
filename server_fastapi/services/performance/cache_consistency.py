"""
Distributed Cache Consistency Service
Ensures cache consistency across distributed systems
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CacheInvalidationEvent:
    """Cache invalidation event"""

    event_id: str
    cache_key: str
    pattern: str | None = None
    reason: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    propagated: bool = False


@dataclass
class CacheVersion:
    """Cache version for consistency"""

    key: str
    version: int
    timestamp: datetime
    node_id: str | None = None


class DistributedCacheConsistencyService:
    """
    Distributed cache consistency service

    Features:
    - Cache versioning
    - Invalidation propagation
    - Consistency checking
    - Conflict resolution
    - TTL synchronization
    - Multi-node coordination
    """

    def __init__(self, cache_service=None):
        """
        Initialize cache consistency service

        Args:
            cache_service: Cache service instance
        """
        self.cache_service = cache_service
        self.cache_versions: dict[str, CacheVersion] = {}
        self.invalidation_events: list[CacheInvalidationEvent] = []
        self.node_id: str = self._generate_node_id()
        self.consistency_check_interval = 60  # seconds
        self.enabled = True

    def _generate_node_id(self) -> str:
        """Generate unique node identifier"""
        import socket

        hostname = socket.gethostname()
        return f"{hostname}_{datetime.utcnow().timestamp()}"

    def invalidate_key(
        self,
        cache_key: str,
        reason: str = "manual",
        propagate: bool = True,
    ) -> CacheInvalidationEvent:
        """
        Invalidate a cache key with consistency tracking

        Args:
            cache_key: Cache key to invalidate
            reason: Reason for invalidation
            propagate: Whether to propagate to other nodes

        Returns:
            CacheInvalidationEvent
        """
        event_id = f"inv_{datetime.utcnow().timestamp()}"

        event = CacheInvalidationEvent(
            event_id=event_id,
            cache_key=cache_key,
            reason=reason,
        )

        # Increment version
        if cache_key in self.cache_versions:
            self.cache_versions[cache_key].version += 1
            self.cache_versions[cache_key].timestamp = datetime.utcnow()
        else:
            self.cache_versions[cache_key] = CacheVersion(
                key=cache_key,
                version=1,
                timestamp=datetime.utcnow(),
                node_id=self.node_id,
            )

        # Invalidate in cache service
        if self.cache_service:
            try:
                self.cache_service.delete(cache_key)
            except Exception as e:
                logger.error(f"Error invalidating cache key {cache_key}: {e}")

        # Propagate if needed
        if propagate:
            self._propagate_invalidation(event)
            event.propagated = True

        self.invalidation_events.append(event)

        logger.debug(
            f"Invalidated cache key {cache_key} (version {self.cache_versions[cache_key].version})"
        )

        return event

    def invalidate_pattern(
        self,
        pattern: str,
        reason: str = "pattern_invalidation",
        propagate: bool = True,
    ) -> list[CacheInvalidationEvent]:
        """
        Invalidate all keys matching a pattern

        Args:
            pattern: Key pattern (supports wildcards)
            reason: Reason for invalidation
            propagate: Whether to propagate

        Returns:
            List of invalidation events
        """
        events = []

        # Find matching keys
        matching_keys = [
            key
            for key in self.cache_versions.keys()
            if self._match_pattern(key, pattern)
        ]

        for key in matching_keys:
            event = self.invalidate_key(key, reason, propagate)
            event.pattern = pattern
            events.append(event)

        logger.info(f"Invalidated {len(events)} keys matching pattern {pattern}")

        return events

    def check_consistency(self, cache_key: str) -> dict[str, Any]:
        """
        Check cache consistency for a key

        Args:
            cache_key: Cache key to check

        Returns:
            Consistency check result
        """
        version = self.cache_versions.get(cache_key)

        if not version:
            return {
                "key": cache_key,
                "consistent": True,
                "version": 0,
                "status": "not_tracked",
            }

        # Check if cache value exists
        cache_exists = False
        if self.cache_service:
            try:
                cache_exists = self.cache_service.exists(cache_key)
            except Exception:
                pass

        # Determine consistency
        is_consistent = cache_exists or version.version == 0

        return {
            "key": cache_key,
            "consistent": is_consistent,
            "version": version.version,
            "timestamp": version.timestamp.isoformat(),
            "node_id": version.node_id,
            "cache_exists": cache_exists,
            "status": "consistent" if is_consistent else "inconsistent",
        }

    def get_version(self, cache_key: str) -> int | None:
        """Get current version for a cache key"""
        version = self.cache_versions.get(cache_key)
        return version.version if version else None

    def set_version(
        self,
        cache_key: str,
        version: int,
        node_id: str | None = None,
    ):
        """Set version for a cache key"""
        self.cache_versions[cache_key] = CacheVersion(
            key=cache_key,
            version=version,
            timestamp=datetime.utcnow(),
            node_id=node_id or self.node_id,
        )

    def _propagate_invalidation(self, event: CacheInvalidationEvent):
        """
        Propagate invalidation to other nodes

        Args:
            event: Invalidation event

        Note: In production, this would use:
        - Redis pub/sub
        - Message queue (RabbitMQ, Kafka)
        - gRPC streaming
        """
        # Placeholder for propagation logic
        # In production, publish to Redis pub/sub or message queue
        logger.debug(f"Propagating invalidation for {event.cache_key} to other nodes")

    def _match_pattern(self, key: str, pattern: str) -> bool:
        """Match key against pattern (supports * wildcard)"""
        import fnmatch

        return fnmatch.fnmatch(key, pattern)

    def get_statistics(self) -> dict[str, Any]:
        """Get consistency service statistics"""
        recent_events = [
            e
            for e in self.invalidation_events
            if e.timestamp >= datetime.utcnow() - timedelta(hours=1)
        ]

        return {
            "node_id": self.node_id,
            "tracked_keys": len(self.cache_versions),
            "invalidation_events_1h": len(recent_events),
            "total_events": len(self.invalidation_events),
            "enabled": self.enabled,
        }

    async def periodic_consistency_check(self):
        """Periodic consistency check (should be run as background task)"""
        if not self.enabled:
            return

        while True:
            try:
                await asyncio.sleep(self.consistency_check_interval)

                # Check consistency for all tracked keys
                inconsistent_keys = []
                for key in list(self.cache_versions.keys()):
                    result = self.check_consistency(key)
                    if not result["consistent"]:
                        inconsistent_keys.append(key)

                if inconsistent_keys:
                    logger.warning(
                        f"Found {len(inconsistent_keys)} inconsistent cache keys"
                    )

                    # Auto-fix: remove version tracking for inconsistent keys
                    for key in inconsistent_keys:
                        del self.cache_versions[key]
            except Exception as e:
                logger.error(f"Error in periodic consistency check: {e}", exc_info=True)


# Global instance (will be initialized with cache service)
cache_consistency_service = None


def initialize_cache_consistency(cache_service):
    """Initialize cache consistency with cache service"""
    global cache_consistency_service
    cache_consistency_service = DistributedCacheConsistencyService(cache_service)
    return cache_consistency_service
