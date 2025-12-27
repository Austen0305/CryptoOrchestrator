"""
Enterprise API Tier Service
Manages API tiers and rate limits for different user tiers
"""

import logging
from typing import Dict, Optional, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class APITier(str, Enum):
    """API tier levels"""
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    HFT = "hft"  # High-frequency trading tier


@dataclass
class RateLimit:
    """Rate limit configuration"""
    requests_per_second: int
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_size: int  # Maximum burst requests


@dataclass
class APITierConfig:
    """API tier configuration"""
    tier: APITier
    name: str
    rate_limit: RateLimit
    features: List[str]
    latency_sla_ms: Optional[float] = None  # SLA latency in milliseconds
    dedicated_support: bool = False
    co_location_ready: bool = False


class EnterpriseAPITierService:
    """
    Service for managing enterprise API tiers and rate limits
    
    Provides:
    - Tier-based rate limiting
    - SLA tracking
    - Feature access control
    - Usage monitoring
    """
    
    def __init__(self):
        # Tier configurations
        self.tier_configs: Dict[APITier, APITierConfig] = {
            APITier.FREE: APITierConfig(
                tier=APITier.FREE,
                name="Free",
                rate_limit=RateLimit(
                    requests_per_second=2,
                    requests_per_minute=60,
                    requests_per_hour=1000,
                    requests_per_day=10000,
                    burst_size=5,
                ),
                features=["basic_market_data", "basic_charts"],
            ),
            APITier.BASIC: APITierConfig(
                tier=APITier.BASIC,
                name="Basic",
                rate_limit=RateLimit(
                    requests_per_second=10,
                    requests_per_minute=300,
                    requests_per_hour=10000,
                    requests_per_day=100000,
                    burst_size=20,
                ),
                features=["market_data", "charts", "basic_trading"],
            ),
            APITier.PROFESSIONAL: APITierConfig(
                tier=APITier.PROFESSIONAL,
                name="Professional",
                rate_limit=RateLimit(
                    requests_per_second=50,
                    requests_per_minute=2000,
                    requests_per_hour=50000,
                    requests_per_day=500000,
                    burst_size=100,
                ),
                features=["market_data", "charts", "trading", "advanced_analytics"],
                latency_sla_ms=100.0,
            ),
            APITier.ENTERPRISE: APITierConfig(
                tier=APITier.ENTERPRISE,
                name="Enterprise",
                rate_limit=RateLimit(
                    requests_per_second=200,
                    requests_per_minute=10000,
                    requests_per_hour=500000,
                    requests_per_day=5000000,
                    burst_size=500,
                ),
                features=[
                    "market_data",
                    "charts",
                    "trading",
                    "advanced_analytics",
                    "institutional_wallets",
                    "dedicated_support",
                ],
                latency_sla_ms=50.0,
                dedicated_support=True,
            ),
            APITier.HFT: APITierConfig(
                tier=APITier.HFT,
                name="High-Frequency Trading",
                rate_limit=RateLimit(
                    requests_per_second=1000,
                    requests_per_minute=50000,
                    requests_per_hour=2000000,
                    requests_per_day=20000000,
                    burst_size=5000,
                ),
                features=[
                    "market_data",
                    "charts",
                    "trading",
                    "advanced_analytics",
                    "institutional_wallets",
                    "hft_orderbook",
                    "microstructure_data",
                    "batch_orders",
                    "binary_websocket",
                    "dedicated_support",
                    "co_location",
                ],
                latency_sla_ms=10.0,  # Sub-10ms SLA for HFT tier
                dedicated_support=True,
                co_location_ready=True,
            ),
        }
        
        # User tier assignments (in production, this would be in database)
        self.user_tiers: Dict[int, APITier] = {}
        
        # Rate limit tracking
        self.request_counts: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.request_timestamps: Dict[int, List[datetime]] = defaultdict(list)
    
    def get_user_tier(self, user_id: int) -> APITier:
        """Get API tier for a user"""
        return self.user_tiers.get(user_id, APITier.FREE)
    
    def set_user_tier(self, user_id: int, tier: APITier):
        """Set API tier for a user"""
        self.user_tiers[user_id] = tier
        logger.info(f"Set API tier for user {user_id}: {tier.value}")
    
    def get_tier_config(self, tier: APITier) -> APITierConfig:
        """Get configuration for a tier"""
        return self.tier_configs.get(tier, self.tier_configs[APITier.FREE])
    
    def check_rate_limit(self, user_id: int, endpoint: str = "default") -> tuple[bool, Optional[str]]:
        """
        Check if user has exceeded rate limit
        
        Returns:
            (allowed, error_message)
        """
        tier = self.get_user_tier(user_id)
        config = self.get_tier_config(tier)
        rate_limit = config.rate_limit
        
        now = datetime.utcnow()
        
        # Clean old timestamps (older than 1 hour)
        cutoff = now - timedelta(hours=1)
        self.request_timestamps[user_id] = [
            ts for ts in self.request_timestamps[user_id] if ts > cutoff
        ]
        
        # Count requests in different time windows
        timestamps = self.request_timestamps[user_id]
        
        # Requests in last second
        requests_last_second = sum(
            1 for ts in timestamps
            if (now - ts).total_seconds() < 1.0
        )
        
        # Requests in last minute
        requests_last_minute = sum(
            1 for ts in timestamps
            if (now - ts).total_seconds() < 60.0
        )
        
        # Requests in last hour
        requests_last_hour = len(timestamps)
        
        # Check limits
        if requests_last_second >= rate_limit.requests_per_second:
            return False, f"Rate limit exceeded: {rate_limit.requests_per_second} requests/second"
        
        if requests_last_minute >= rate_limit.requests_per_minute:
            return False, f"Rate limit exceeded: {rate_limit.requests_per_minute} requests/minute"
        
        if requests_last_hour >= rate_limit.requests_per_hour:
            return False, f"Rate limit exceeded: {rate_limit.requests_per_hour} requests/hour"
        
        # Record request
        self.request_timestamps[user_id].append(now)
        
        return True, None
    
    def has_feature_access(self, user_id: int, feature: str) -> bool:
        """Check if user has access to a feature"""
        tier = self.get_user_tier(user_id)
        config = self.get_tier_config(tier)
        return feature in config.features
    
    def get_latency_sla(self, user_id: int) -> Optional[float]:
        """Get latency SLA for user's tier"""
        tier = self.get_user_tier(user_id)
        config = self.get_tier_config(tier)
        return config.latency_sla_ms
    
    def get_rate_limit_info(self, user_id: int) -> Dict:
        """Get rate limit information for user"""
        tier = self.get_user_tier(user_id)
        config = self.get_tier_config(tier)
        rate_limit = config.rate_limit
        
        # Calculate current usage
        now = datetime.utcnow()
        timestamps = self.request_timestamps[user_id]
        
        requests_last_second = sum(
            1 for ts in timestamps
            if (now - ts).total_seconds() < 1.0
        )
        requests_last_minute = sum(
            1 for ts in timestamps
            if (now - ts).total_seconds() < 60.0
        )
        requests_last_hour = len([
            ts for ts in timestamps
            if (now - ts).total_seconds() < 3600.0
        ])
        
        return {
            "tier": tier.value,
            "tier_name": config.name,
            "rate_limits": {
                "per_second": rate_limit.requests_per_second,
                "per_minute": rate_limit.requests_per_minute,
                "per_hour": rate_limit.requests_per_hour,
                "per_day": rate_limit.requests_per_day,
                "burst_size": rate_limit.burst_size,
            },
            "current_usage": {
                "per_second": requests_last_second,
                "per_minute": requests_last_minute,
                "per_hour": requests_last_hour,
            },
            "latency_sla_ms": config.latency_sla_ms,
            "dedicated_support": config.dedicated_support,
            "co_location_ready": config.co_location_ready,
            "features": config.features,
        }


# Global instance
enterprise_api_tier_service = EnterpriseAPITierService()
