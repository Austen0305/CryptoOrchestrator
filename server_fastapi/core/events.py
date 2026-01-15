from datetime import UTC, datetime

from pydantic import Field

from .bus import Event


class OrderEvent(Event):
    """
    Event for Order lifecycle updates (Placement, Cancellation).
    Required for Spoofing/Layering detection.
    """

    event_name: str = "OrderUpdate"
    order_id: str
    user_id: str
    asset: str
    side: str  # 'buy' or 'sell'
    type: str = "new"  # 'new', 'cancel', 'fill'
    amount: float
    price: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: str = "NEW"  # Added status field since it was used in SentinelService


class TradeEvent(Event):
    """
    Event for Trade matches.
    Required for Wash Trading and Sandwich detection.
    """

    event_name: str = "TradeMatch"
    trade_id: str
    buyer_id: str
    seller_id: str
    asset: str
    amount: float
    price: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MarketAbuseDetected(Event):
    """
    Alert event published when the Sentinel Service detects abuse.
    """

    event_name: str = "MarketAbuseDetected"
    abuse_type: str
    severity: str
    details: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
