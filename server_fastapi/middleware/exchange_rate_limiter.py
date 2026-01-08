"""
DEX Aggregator Rate Limiter
Implements rate limiting per DEX aggregator to avoid API bans.

[WARN] REPURPOSED: Originally for centralized exchanges, now used for DEX aggregators (0x, OKX, Rubic).

This module has been repurposed from exchange rate limiting to DEX aggregator rate limiting.
All rate limiting is now for DEX aggregator APIs, not centralized exchanges.

Supported Aggregators:
- 0x Protocol (0x API)
- OKX DEX Aggregator
- Rubic DEX Aggregator

Rate limits are configured per aggregator to prevent API bans and ensure reliable service.
"""

import asyncio
import logging
import time
from collections import defaultdict

logger = logging.getLogger(__name__)


class ExchangeRateLimiter:
    """
    Rate limiter for DEX aggregator API calls

    [WARN] NOTE: Class name kept as ExchangeRateLimiter for backward compatibility.
    This class is now used exclusively for DEX aggregators, not centralized exchanges.

    Tracks rate limits per DEX aggregator (0x, OKX, Rubic) to prevent API bans.
    Repurposed from exchange rate limiter for DEX aggregators.

    Usage:
        limiter = ExchangeRateLimiter()
        if await limiter.check_rate_limit("0x"):
            # Make API call to 0x aggregator
    """

    def __init__(self):
        # Rate limit tracking per aggregator
        # Format: {aggregator: {"calls": count, "window_start": timestamp}}
        self._rate_limits: dict[str, dict] = defaultdict(
            lambda: {
                "calls": 0,
                "window_start": time.time(),
            }
        )

        # DEX aggregator-specific rate limits (calls per minute)
        # Conservative defaults based on aggregator documentation
        self.aggregator_limits = {
            "0x": {
                "calls_per_minute": 300,
                "calls_per_second": 5,
            },  # 0x API free tier: 5 req/sec
            "okx": {
                "calls_per_minute": 120,
                "calls_per_second": 2,
            },  # OKX DEX API limits
            "rubic": {
                "calls_per_minute": 60,
                "calls_per_second": 1,
            },  # Rubic API limits
            "default": {"calls_per_minute": 60, "calls_per_second": 1},
        }

        self._lock = asyncio.Lock()

    async def check_rate_limit(self, aggregator: str) -> bool:
        """
        Check if DEX aggregator API call is allowed

        Args:
            aggregator: Aggregator name (e.g., '0x', 'okx', 'rubic')
                      Also accepts 'exchange' parameter for backward compatibility

        Returns:
            True if call is allowed, False if rate limit exceeded
        """
        async with self._lock:
            # Support both aggregator and exchange parameter names
            aggregator_name = aggregator.lower()
            limits = self.aggregator_limits.get(
                aggregator_name, self.aggregator_limits["default"]
            )
            current_time = time.time()

            # Get or initialize rate limit tracking for this aggregator
            rate_limit = self._rate_limits[aggregator_name]

            # Reset window if minute has passed
            if current_time - rate_limit["window_start"] >= 60:
                rate_limit["calls"] = 0
                rate_limit["window_start"] = current_time

            # Check per-minute limit
            if rate_limit["calls"] >= limits["calls_per_minute"]:
                logger.warning(
                    f"Rate limit exceeded for aggregator {aggregator_name}: "
                    f"{rate_limit['calls']}/{limits['calls_per_minute']} calls per minute"
                )
                return False

            # Check per-second limit (simple check - could be improved with sliding window)
            if rate_limit["calls"] > 0:
                time_since_last_call = current_time - rate_limit.get(
                    "last_call_time", current_time
                )
                if time_since_last_call < 1.0 / limits["calls_per_second"]:
                    # Too soon since last call
                    wait_time = (
                        1.0 / limits["calls_per_second"]
                    ) - time_since_last_call
                    logger.debug(
                        f"Rate limiting aggregator {aggregator_name}: waiting {wait_time:.2f}s"
                    )
                    await asyncio.sleep(wait_time)

            # Increment call count
            rate_limit["calls"] += 1
            rate_limit["last_call_time"] = current_time

            return True

    async def get_rate_limit_status(self, aggregator: str) -> dict[str, any]:
        """
        Get current rate limit status for a DEX aggregator

        Args:
            aggregator: Aggregator name (e.g., '0x', 'okx', 'rubic')

        Returns:
            Dictionary with rate limit information
        """
        async with self._lock:
            aggregator_name = aggregator.lower()
            limits = self.aggregator_limits.get(
                aggregator_name, self.aggregator_limits["default"]
            )
            rate_limit = self._rate_limits[aggregator_name]
            current_time = time.time()

            # Calculate remaining calls
            if current_time - rate_limit["window_start"] >= 60:
                remaining = limits["calls_per_minute"]
            else:
                remaining = max(0, limits["calls_per_minute"] - rate_limit["calls"])

            return {
                "aggregator": aggregator_name,
                "calls_used": rate_limit["calls"],
                "calls_limit": limits["calls_per_minute"],
                "calls_remaining": remaining,
                "window_reset_at": rate_limit["window_start"] + 60,
                "calls_per_second": limits["calls_per_second"],
            }

    async def reset_rate_limit(self, aggregator: str):
        """Reset rate limit for a DEX aggregator (for testing)"""
        async with self._lock:
            aggregator_name = aggregator.lower()
            if aggregator_name in self._rate_limits:
                self._rate_limits[aggregator_name] = {
                    "calls": 0,
                    "window_start": time.time(),
                }


# Global exchange rate limiter instance
exchange_rate_limiter = ExchangeRateLimiter()
