"""
API Marketplace - Trading Signal Publishing and Monetization Platform
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field, EmailStr
from typing import List, Dict, Optional, Literal
from datetime import datetime, timedelta
from enum import Enum
import logging
import secrets
import hashlib

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/marketplace", tags=["API Marketplace"])


class SubscriptionTier(str, Enum):
    """Subscription tiers with rate limits"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SignalType(str, Enum):
    """Types of trading signals"""
    BUY = "buy"
    SELL = "sell"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    ALERT = "alert"


class SignalProvider(BaseModel):
    """Signal provider profile"""
    provider_id: str
    name: str
    description: str
    verified: bool = False
    total_signals: int = 0
    accuracy_rate: float = Field(0.0, ge=0, le=100)
    avg_return_pct: float = 0.0
    subscribers: int = 0
    rating: float = Field(0.0, ge=0, le=5)
    reviews: int = 0
    created_at: str
    subscription_price_monthly: float = Field(0.0, description="Monthly subscription price in USD")


class TradingSignal(BaseModel):
    """Published trading signal"""
    signal_id: str
    provider_id: str
    provider_name: str
    symbol: str
    signal_type: SignalType
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    confidence: float = Field(..., ge=0, le=100)
    timeframe: str
    analysis: str
    timestamp: str
    expires_at: Optional[str] = None


class APIKey(BaseModel):
    """API key for marketplace access"""
    key_id: str
    user_id: str
    api_key: str
    tier: SubscriptionTier
    rate_limit_per_hour: int
    requests_used: int = 0
    created_at: str
    last_used_at: Optional[str] = None
    active: bool = True


class SignalPerformance(BaseModel):
    """Signal historical performance"""
    signal_id: str
    outcome: Literal["win", "loss", "pending", "cancelled"]
    entry_price: float
    exit_price: Optional[float] = None
    return_pct: Optional[float] = None
    duration_hours: Optional[float] = None
    closed_at: Optional[str] = None


class MarketplaceStats(BaseModel):
    """Marketplace statistics"""
    total_providers: int
    total_signals_24h: int
    top_providers: List[Dict]
    trending_symbols: List[str]
    avg_signal_accuracy: float


# Tier configurations
TIER_LIMITS = {
    SubscriptionTier.FREE: {"requests_per_hour": 10, "signals_per_day": 5},
    SubscriptionTier.BASIC: {"requests_per_hour": 100, "signals_per_day": 50},
    SubscriptionTier.PRO: {"requests_per_hour": 1000, "signals_per_day": 500},
    SubscriptionTier.ENTERPRISE: {"requests_per_hour": 10000, "signals_per_day": -1}
}

# In-memory storage (use database in production)
providers: Dict[str, SignalProvider] = {}
signals: Dict[str, TradingSignal] = {}
api_keys: Dict[str, APIKey] = {}
signal_performance: Dict[str, List[SignalPerformance]] = {}
subscriptions: Dict[str, List[str]] = {}  # user_id -> [provider_ids]


class MarketplaceService:
    """Marketplace business logic"""
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate secure API key"""
        key = secrets.token_urlsafe(32)
        return f"mk_{key}"
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    async def verify_api_key(api_key: str) -> Optional[APIKey]:
        """Verify and return API key details"""
        for key_obj in api_keys.values():
            if key_obj.api_key == api_key:
                # Update last used
                key_obj.last_used_at = datetime.now().isoformat()
                return key_obj
        return None
    
    @staticmethod
    async def check_rate_limit(key_obj: APIKey) -> bool:
        """Check if API key is within rate limits"""
        tier_limit = TIER_LIMITS[key_obj.tier]["requests_per_hour"]
        
        # Reset counter if hour has passed
        if key_obj.last_used_at:
            last_used = datetime.fromisoformat(key_obj.last_used_at)
            if datetime.now() - last_used > timedelta(hours=1):
                key_obj.requests_used = 0
        
        if key_obj.requests_used >= tier_limit:
            return False
        
        key_obj.requests_used += 1
        return True
    
    @staticmethod
    async def calculate_provider_accuracy(provider_id: str) -> float:
        """Calculate provider accuracy based on closed signals"""
        if provider_id not in signal_performance:
            return 0.0
        
        performances = signal_performance[provider_id]
        closed = [p for p in performances if p.outcome in ["win", "loss"]]
        
        if not closed:
            return 0.0
        
        wins = sum(1 for p in closed if p.outcome == "win")
        return (wins / len(closed)) * 100
    
    @staticmethod
    async def calculate_avg_return(provider_id: str) -> float:
        """Calculate average return percentage"""
        if provider_id not in signal_performance:
            return 0.0
        
        performances = signal_performance[provider_id]
        returns = [p.return_pct for p in performances if p.return_pct is not None]
        
        if not returns:
            return 0.0
        
        return sum(returns) / len(returns)


marketplace_service = MarketplaceService()


# Dependency for API key authentication
async def verify_marketplace_api_key(api_key: str = None) -> APIKey:
    """Dependency to verify API key"""
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    key_obj = await marketplace_service.verify_api_key(api_key)
    
    if not key_obj or not key_obj.active:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    
    if not await marketplace_service.check_rate_limit(key_obj):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded for {key_obj.tier} tier"
        )
    
    return key_obj


@router.post("/keys/generate", response_model=APIKey)
async def generate_api_key(
    user_id: str,
    tier: SubscriptionTier = SubscriptionTier.FREE
):
    """
    Generate new API key for marketplace access
    
    Tier determines rate limits and features available
    """
    api_key = marketplace_service.generate_api_key()
    
    key_obj = APIKey(
        key_id=f"key_{user_id}_{int(datetime.now().timestamp())}",
        user_id=user_id,
        api_key=api_key,
        tier=tier,
        rate_limit_per_hour=TIER_LIMITS[tier]["requests_per_hour"],
        created_at=datetime.now().isoformat()
    )
    
    api_keys[key_obj.key_id] = key_obj
    
    logger.info(f"Generated API key for user {user_id} with tier {tier}")
    
    return key_obj


@router.get("/keys/{user_id}", response_model=List[APIKey])
async def get_user_keys(user_id: str):
    """Get all API keys for a user"""
    user_keys = [key for key in api_keys.values() if key.user_id == user_id]
    return user_keys


@router.delete("/keys/{key_id}")
async def revoke_api_key(key_id: str):
    """Revoke an API key"""
    if key_id not in api_keys:
        raise HTTPException(status_code=404, detail="API key not found")
    
    api_keys[key_id].active = False
    
    return {"success": True, "message": "API key revoked"}


@router.post("/providers/register", response_model=SignalProvider)
async def register_provider(
    user_id: str,
    name: str,
    description: str,
    subscription_price: float = 0.0
):
    """
    Register as a signal provider
    
    Allows users to publish trading signals and monetize their strategies
    """
    provider_id = f"provider_{user_id}_{int(datetime.now().timestamp())}"
    
    provider = SignalProvider(
        provider_id=provider_id,
        name=name,
        description=description,
        created_at=datetime.now().isoformat(),
        subscription_price_monthly=subscription_price
    )
    
    providers[provider_id] = provider
    signal_performance[provider_id] = []
    
    logger.info(f"Registered new provider: {name} ({provider_id})")
    
    return provider


@router.get("/providers", response_model=List[SignalProvider])
async def list_providers(
    verified_only: bool = False,
    min_accuracy: float = 0.0,
    sort_by: Literal["rating", "subscribers", "accuracy"] = "rating"
):
    """
    List all signal providers
    
    Can filter by verification status and minimum accuracy
    """
    provider_list = list(providers.values())
    
    if verified_only:
        provider_list = [p for p in provider_list if p.verified]
    
    if min_accuracy > 0:
        provider_list = [p for p in provider_list if p.accuracy_rate >= min_accuracy]
    
    # Sort
    if sort_by == "rating":
        provider_list.sort(key=lambda p: p.rating, reverse=True)
    elif sort_by == "subscribers":
        provider_list.sort(key=lambda p: p.subscribers, reverse=True)
    elif sort_by == "accuracy":
        provider_list.sort(key=lambda p: p.accuracy_rate, reverse=True)
    
    return provider_list


@router.get("/providers/{provider_id}", response_model=SignalProvider)
async def get_provider_details(provider_id: str):
    """Get detailed provider information"""
    if provider_id not in providers:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    provider = providers[provider_id]
    
    # Update live stats
    provider.accuracy_rate = await marketplace_service.calculate_provider_accuracy(provider_id)
    provider.avg_return_pct = await marketplace_service.calculate_avg_return(provider_id)
    
    return provider


@router.post("/signals/publish", response_model=TradingSignal)
async def publish_signal(
    provider_id: str,
    symbol: str,
    signal_type: SignalType,
    entry_price: Optional[float],
    stop_loss: Optional[float],
    take_profit: Optional[float],
    confidence: float,
    timeframe: str,
    analysis: str,
    expires_hours: Optional[int] = None
):
    """
    Publish a new trading signal
    
    Subscribers will receive notification of this signal
    """
    if provider_id not in providers:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    signal_id = f"signal_{provider_id}_{int(datetime.now().timestamp())}"
    
    expires_at = None
    if expires_hours:
        expires_at = (datetime.now() + timedelta(hours=expires_hours)).isoformat()
    
    signal = TradingSignal(
        signal_id=signal_id,
        provider_id=provider_id,
        provider_name=providers[provider_id].name,
        symbol=symbol,
        signal_type=signal_type,
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        confidence=confidence,
        timeframe=timeframe,
        analysis=analysis,
        timestamp=datetime.now().isoformat(),
        expires_at=expires_at
    )
    
    signals[signal_id] = signal
    providers[provider_id].total_signals += 1
    
    logger.info(f"Published signal {signal_id} from {providers[provider_id].name}")
    
    # Notify subscribers (implement notification service)
    # await notify_subscribers(provider_id, signal)
    
    return signal


@router.get("/signals", response_model=List[TradingSignal])
async def get_signals(
    symbol: Optional[str] = None,
    provider_id: Optional[str] = None,
    signal_type: Optional[SignalType] = None,
    limit: int = 50,
    key: APIKey = Depends(verify_marketplace_api_key)
):
    """
    Get trading signals (requires API key)
    
    Filter by symbol, provider, or signal type
    """
    signal_list = list(signals.values())
    
    # Filter expired signals
    now = datetime.now()
    signal_list = [
        s for s in signal_list
        if s.expires_at is None or datetime.fromisoformat(s.expires_at) > now
    ]
    
    if symbol:
        signal_list = [s for s in signal_list if s.symbol == symbol]
    
    if provider_id:
        signal_list = [s for s in signal_list if s.provider_id == provider_id]
    
    if signal_type:
        signal_list = [s for s in signal_list if s.signal_type == signal_type]
    
    # Sort by timestamp (newest first)
    signal_list.sort(key=lambda s: s.timestamp, reverse=True)
    
    return signal_list[:limit]


@router.post("/signals/{signal_id}/close")
async def close_signal(
    signal_id: str,
    provider_id: str,
    exit_price: float,
    outcome: Literal["win", "loss", "cancelled"]
):
    """
    Close a signal and record performance
    
    Provider must close their signals to track accuracy
    """
    if signal_id not in signals:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    signal = signals[signal_id]
    
    if signal.provider_id != provider_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return_pct = None
    if signal.entry_price and outcome != "cancelled":
        if signal.signal_type == SignalType.BUY:
            return_pct = ((exit_price - signal.entry_price) / signal.entry_price) * 100
        else:  # SELL
            return_pct = ((signal.entry_price - exit_price) / signal.entry_price) * 100
    
    duration = (datetime.now() - datetime.fromisoformat(signal.timestamp)).total_seconds() / 3600
    
    performance = SignalPerformance(
        signal_id=signal_id,
        outcome=outcome,
        entry_price=signal.entry_price or 0,
        exit_price=exit_price,
        return_pct=return_pct,
        duration_hours=duration,
        closed_at=datetime.now().isoformat()
    )
    
    signal_performance[provider_id].append(performance)
    
    # Update provider stats
    providers[provider_id].accuracy_rate = await marketplace_service.calculate_provider_accuracy(provider_id)
    providers[provider_id].avg_return_pct = await marketplace_service.calculate_avg_return(provider_id)
    
    logger.info(f"Closed signal {signal_id} with outcome {outcome}")
    
    return {"success": True, "performance": performance}


@router.post("/subscribe/{provider_id}")
async def subscribe_to_provider(user_id: str, provider_id: str):
    """
    Subscribe to a signal provider
    
    In production, integrate with payment processor
    """
    if provider_id not in providers:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    if user_id not in subscriptions:
        subscriptions[user_id] = []
    
    if provider_id not in subscriptions[user_id]:
        subscriptions[user_id].append(provider_id)
        providers[provider_id].subscribers += 1
    
    logger.info(f"User {user_id} subscribed to provider {provider_id}")
    
    return {"success": True, "message": "Subscribed successfully"}


@router.delete("/subscribe/{provider_id}")
async def unsubscribe_from_provider(user_id: str, provider_id: str):
    """Unsubscribe from a signal provider"""
    if user_id in subscriptions and provider_id in subscriptions[user_id]:
        subscriptions[user_id].remove(provider_id)
        providers[provider_id].subscribers -= 1
    
    return {"success": True, "message": "Unsubscribed successfully"}


@router.get("/subscriptions/{user_id}", response_model=List[SignalProvider])
async def get_user_subscriptions(user_id: str):
    """Get all providers user is subscribed to"""
    if user_id not in subscriptions:
        return []
    
    return [providers[pid] for pid in subscriptions[user_id] if pid in providers]


@router.get("/stats", response_model=MarketplaceStats)
async def get_marketplace_stats():
    """Get marketplace statistics"""
    # Calculate 24h signals
    cutoff = datetime.now() - timedelta(hours=24)
    signals_24h = sum(
        1 for s in signals.values()
        if datetime.fromisoformat(s.timestamp) > cutoff
    )
    
    # Top providers
    top_providers = sorted(
        providers.values(),
        key=lambda p: p.rating,
        reverse=True
    )[:5]
    
    # Trending symbols
    symbol_counts = {}
    for signal in signals.values():
        symbol_counts[signal.symbol] = symbol_counts.get(signal.symbol, 0) + 1
    
    trending = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Average accuracy
    accuracies = [p.accuracy_rate for p in providers.values() if p.accuracy_rate > 0]
    avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0
    
    return MarketplaceStats(
        total_providers=len(providers),
        total_signals_24h=signals_24h,
        top_providers=[
            {
                "provider_id": p.provider_id,
                "name": p.name,
                "rating": p.rating,
                "subscribers": p.subscribers,
                "accuracy": p.accuracy_rate
            }
            for p in top_providers
        ],
        trending_symbols=[symbol for symbol, _ in trending],
        avg_signal_accuracy=avg_accuracy
    )
