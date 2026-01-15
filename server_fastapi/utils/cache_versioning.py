"""
Cache Versioning System
Implements cache versioning to handle schema changes and invalidate stale data.
"""

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


class CacheVersionManager:
    """
    Manages cache versions for different data types.
    Allows graceful invalidation when data schemas change.
    """

    def __init__(self):
        # Version registry: {cache_prefix: version_number}
        self.versions: dict[str, int] = {}
        # Version metadata: {cache_prefix: {version, updated_at, reason}}
        self.version_metadata: dict[str, dict[str, Any]] = {}

    def get_version(self, cache_prefix: str) -> int:
        """
        Get current version for a cache prefix.

        Args:
            cache_prefix: Cache key prefix (e.g., 'user', 'bot', 'portfolio')

        Returns:
            Current version number
        """
        return self.versions.get(cache_prefix, 1)

    def increment_version(self, cache_prefix: str, reason: str | None = None) -> int:
        """
        Increment version for a cache prefix (invalidates all cached data).

        Args:
            cache_prefix: Cache key prefix to invalidate
            reason: Reason for version increment (for logging)

        Returns:
            New version number
        """
        current_version = self.versions.get(cache_prefix, 1)
        new_version = current_version + 1

        self.versions[cache_prefix] = new_version
        self.version_metadata[cache_prefix] = {
            "version": new_version,
            "updated_at": datetime.now(UTC).isoformat(),
            "reason": reason or "Manual version increment",
        }

        logger.info(
            f"Cache version incremented: {cache_prefix} -> v{new_version}",
            extra={
                "cache_prefix": cache_prefix,
                "old_version": current_version,
                "new_version": new_version,
                "reason": reason,
            },
        )

        return new_version

    def set_version(
        self, cache_prefix: str, version: int, reason: str | None = None
    ) -> None:
        """
        Set a specific version for a cache prefix.

        Args:
            cache_prefix: Cache key prefix
            version: Version number to set
            reason: Reason for version change
        """
        self.versions[cache_prefix] = version
        self.version_metadata[cache_prefix] = {
            "version": version,
            "updated_at": datetime.now(UTC).isoformat(),
            "reason": reason or "Version set manually",
        }

    def get_versioned_key(self, cache_prefix: str, *key_parts: str) -> str:
        """
        Generate a versioned cache key.

        Args:
            cache_prefix: Cache key prefix
            *key_parts: Additional key components

        Returns:
            Versioned cache key string
        """
        version = self.get_version(cache_prefix)
        key_string = ":".join([cache_prefix, str(version)] + list(key_parts))
        return key_string

    def get_all_versions(self) -> dict[str, dict[str, Any]]:
        """
        Get all cache versions with metadata.

        Returns:
            Dictionary of cache prefixes to version info
        """
        return {
            prefix: {"version": version, **self.version_metadata.get(prefix, {})}
            for prefix, version in self.versions.items()
        }

    def invalidate_all_versions(self, reason: str | None = None) -> None:
        """
        Increment versions for all cache prefixes (full cache invalidation).

        Args:
            reason: Reason for invalidation
        """
        for prefix in list(self.versions.keys()):
            self.increment_version(prefix, reason=reason or "Full cache invalidation")


# Global version manager instance
_version_manager = CacheVersionManager()


def get_cache_version_manager() -> CacheVersionManager:
    """Get singleton cache version manager"""
    return _version_manager


def get_versioned_cache_key(cache_prefix: str, *key_parts: str) -> str:
    """
    Convenience function to get a versioned cache key.

    Args:
        cache_prefix: Cache key prefix
        *key_parts: Additional key components

    Returns:
        Versioned cache key
    """
    return _version_manager.get_versioned_key(cache_prefix, *key_parts)
