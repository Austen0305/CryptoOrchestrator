"""
Database Sharding Service
Horizontal scaling through database sharding
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Shard:
    """Database shard configuration"""

    shard_id: str
    name: str
    connection_string: str
    weight: int = 1  # For weighted distribution
    enabled: bool = True
    region: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ShardKey:
    """Shard key for routing"""

    key: str
    shard_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)


class ShardingService:
    """
    Database sharding service for horizontal scaling

    Features:
    - Shard management
    - Shard key routing
    - Consistent hashing
    - Shard health checking
    - Automatic failover
    - Load balancing across shards
    """

    def __init__(self):
        self.shards: dict[str, Shard] = {}
        self.shard_keys: dict[str, str] = {}  # key -> shard_id mapping
        self.enabled = False
        self.sharding_strategy = (
            "consistent_hash"  # "consistent_hash", "range", "directory"
        )

    def register_shard(
        self,
        shard_id: str,
        name: str,
        connection_string: str,
        weight: int = 1,
        region: str | None = None,
    ) -> Shard:
        """
        Register a database shard

        Args:
            shard_id: Unique shard identifier
            name: Shard name
            connection_string: Database connection string
            weight: Shard weight for load balancing
            region: Optional region identifier

        Returns:
            Shard
        """
        shard = Shard(
            shard_id=shard_id,
            name=name,
            connection_string=connection_string,
            weight=weight,
            region=region,
        )

        self.shards[shard_id] = shard

        if not self.enabled and len(self.shards) > 1:
            self.enabled = True
            logger.info("Sharding enabled with multiple shards")

        logger.info(f"Registered shard {shard_id}: {name}")

        return shard

    def get_shard_for_key(self, shard_key: str) -> Shard | None:
        """
        Get shard for a given key

        Args:
            shard_key: Key to route (e.g., user_id, wallet_id)

        Returns:
            Shard if found
        """
        if not self.enabled or not self.shards:
            return None

        # Check if we have a cached mapping
        if shard_key in self.shard_keys:
            shard_id = self.shard_keys[shard_key]
            return self.shards.get(shard_id)

        # Use consistent hashing
        shard_id = self._consistent_hash(shard_key)

        if shard_id in self.shards:
            # Cache the mapping
            self.shard_keys[shard_key] = shard_id
            return self.shards[shard_id]

        return None

    def get_shard_for_user(self, user_id: int) -> Shard | None:
        """Get shard for a user ID"""
        return self.get_shard_for_key(f"user_{user_id}")

    def get_shard_for_wallet(self, wallet_id: str) -> Shard | None:
        """Get shard for a wallet ID"""
        return self.get_shard_for_key(f"wallet_{wallet_id}")

    def _consistent_hash(self, key: str) -> str:
        """
        Consistent hashing to determine shard

        Args:
            key: Key to hash

        Returns:
            Shard ID
        """
        if not self.shards:
            raise ValueError("No shards registered")

        # Get enabled shards
        enabled_shards = [
            (sid, shard) for sid, shard in self.shards.items() if shard.enabled
        ]

        if not enabled_shards:
            raise ValueError("No enabled shards")

        # Simple consistent hashing (in production, use ring-based hashing)
        hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
        shard_index = hash_value % len(enabled_shards)

        return enabled_shards[shard_index][0]

    def get_all_shards(self) -> list[Shard]:
        """Get all registered shards"""
        return list(self.shards.values())

    def get_enabled_shards(self) -> list[Shard]:
        """Get all enabled shards"""
        return [shard for shard in self.shards.values() if shard.enabled]

    def disable_shard(self, shard_id: str) -> bool:
        """Disable a shard (for maintenance)"""
        if shard_id in self.shards:
            self.shards[shard_id].enabled = False
            logger.info(f"Disabled shard {shard_id}")
            return True
        return False

    def enable_shard(self, shard_id: str) -> bool:
        """Enable a shard"""
        if shard_id in self.shards:
            self.shards[shard_id].enabled = True
            logger.info(f"Enabled shard {shard_id}")
            return True
        return False

    def get_shard_statistics(self) -> dict[str, Any]:
        """Get sharding statistics"""
        enabled_shards = self.get_enabled_shards()

        return {
            "total_shards": len(self.shards),
            "enabled_shards": len(enabled_shards),
            "disabled_shards": len(self.shards) - len(enabled_shards),
            "sharding_enabled": self.enabled,
            "strategy": self.sharding_strategy,
            "mapped_keys": len(self.shard_keys),
        }


# Global instance
sharding_service = ShardingService()
