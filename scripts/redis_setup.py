#!/usr/bin/env python3
"""
Redis Setup and Configuration Utility
Handles Redis connection testing, configuration, and cache management.
"""

import os
import sys
from typing import Optional, Dict, Any
import redis
import redis.asyncio as aioredis
from redis.exceptions import ConnectionError, RedisError


class RedisManager:
    """Redis connection and configuration manager."""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.client: Optional[redis.Redis] = None
        self.async_client: Optional[aioredis.Redis] = None
    
    def connect(self) -> bool:
        """Connect to Redis (synchronous)."""
        try:
            self.client = redis.from_url(self.redis_url, decode_responses=True)
            self.client.ping()
            return True
        except (ConnectionError, RedisError) as e:
            print(f"Redis connection failed: {e}", file=sys.stderr)
            return False
    
    async def async_connect(self) -> bool:
        """Connect to Redis (asynchronous)."""
        try:
            self.async_client = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.async_client.ping()
            return True
        except (ConnectionError, RedisError) as e:
            print(f"Redis async connection failed: {e}", file=sys.stderr)
            return False
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Redis connection and return status."""
        if not self.connect():
            return {
                "status": "error",
                "message": "Failed to connect to Redis",
                "url": self.redis_url
            }
        
        try:
            info = self.client.info()
            return {
                "status": "ok",
                "url": self.redis_url,
                "version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "uptime_in_seconds": info.get("uptime_in_seconds")
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "url": self.redis_url
            }
    
    def setup_cache_keys(self) -> Dict[str, bool]:
        """Set up default cache key patterns."""
        if not self.client:
            if not self.connect():
                return {"setup": False}
        
        cache_keys = {
            "market_data:*": "Market data cache (5 min TTL)",
            "trading_pairs:*": "Trading pairs cache (10 min TTL)",
            "order_book:*": "Order book cache (1 min TTL)",
            "analytics:*": "Analytics cache (15 min TTL)",
            "user_session:*": "User session cache",
        }
        
        results = {}
        try:
            # Set test keys to verify patterns
            for key_pattern, description in cache_keys.items():
                test_key = key_pattern.replace("*", "test")
                self.client.setex(test_key, 60, description)
                results[key_pattern] = True
            return {"setup": True, **results}
        except Exception as e:
            print(f"Error setting up cache keys: {e}", file=sys.stderr)
            return {"setup": False, "error": str(e)}
    
    def clear_cache(self, pattern: str = "*") -> int:
        """Clear cache by pattern."""
        if not self.client:
            if not self.connect():
                return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Error clearing cache: {e}", file=sys.stderr)
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Redis statistics."""
        if not self.client:
            if not self.connect():
                return {"status": "error"}
        
        try:
            info = self.client.info()
            db_info = self.client.info("keyspace")
            
            return {
                "status": "ok",
                "memory": {
                    "used": info.get("used_memory_human"),
                    "peak": info.get("used_memory_peak_human"),
                    "fragmentation_ratio": info.get("mem_fragmentation_ratio")
                },
                "clients": {
                    "connected": info.get("connected_clients"),
                    "blocked": info.get("blocked_clients")
                },
                "stats": {
                    "total_commands_processed": info.get("total_commands_processed"),
                    "keyspace_hits": info.get("keyspace_hits"),
                    "keyspace_misses": info.get("keyspace_misses")
                },
                "databases": db_info
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Redis setup and management")
    parser.add_argument("action", choices=["test", "setup", "clear", "stats"])
    parser.add_argument("--url", help="Redis URL")
    parser.add_argument("--pattern", default="*", help="Cache pattern (for clear)")
    
    args = parser.parse_args()
    
    manager = RedisManager(redis_url=args.url)
    
    if args.action == "test":
        result = manager.test_connection()
        import json
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["status"] == "ok" else 1)
    
    elif args.action == "setup":
        results = manager.setup_cache_keys()
        import json
        print(json.dumps(results, indent=2))
        sys.exit(0 if results.get("setup") else 1)
    
    elif args.action == "clear":
        count = manager.clear_cache(pattern=args.pattern)
        print(f"✓ Cleared {count} keys matching pattern '{args.pattern}'")
    
    elif args.action == "stats":
        stats = manager.get_stats()
        import json
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()

