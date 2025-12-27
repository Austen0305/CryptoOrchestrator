"""
Signal Provider Model - Marketplace features for copy trading
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User
    from .trade import Trade


class CuratorStatus(str, Enum):
    """Curator approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class SignalProvider(Base, TimestampMixin):
    """Model for signal providers in the marketplace"""

    __tablename__ = "signal_providers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True
    )

    # Curator status
    curator_status: Mapped[str] = mapped_column(
        String(20), default=CuratorStatus.PENDING.value, nullable=False
    )
    curator_approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    curator_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Performance metrics (updated daily)
    total_return: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    sharpe_ratio: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    win_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    winning_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_profit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    max_drawdown: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    profit_factor: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Reputation metrics
    average_rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_ratings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    follower_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    subscriber_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Marketplace settings
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    subscription_fee: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Monthly fee in USD
    performance_fee_percentage: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )  # Performance fee (0-100%)
    minimum_subscription_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Profile information
    profile_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trading_strategy: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risk_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # low, medium, high

    # Statistics tracking
    last_metrics_update: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    metrics_update_frequency: Mapped[str] = mapped_column(
        String(20), default="daily", nullable=False
    )  # daily, weekly, monthly

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<SignalProvider(user_id={self.user_id}, status={self.curator_status}, rating={self.average_rating})>"


class SignalProviderRating(Base, TimestampMixin):
    """Model for user ratings of signal providers"""

    __tablename__ = "signal_provider_ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    signal_provider_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("signal_providers.id"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    # Rating (1-5 stars)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    signal_provider: Mapped["SignalProvider"] = relationship("SignalProvider")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<SignalProviderRating(signal_provider_id={self.signal_provider_id}, rating={self.rating})>"


class Payout(Base, TimestampMixin):
    """Model for tracking payouts to signal providers"""

    __tablename__ = "payouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    signal_provider_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("signal_providers.id"), nullable=False, index=True
    )

    # Payout details
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    total_revenue: Mapped[float] = mapped_column(Float, nullable=False)  # Total from subscribers
    platform_fee: Mapped[float] = mapped_column(Float, nullable=False)  # 20% to platform
    provider_payout: Mapped[float] = mapped_column(Float, nullable=False)  # 80% to provider

    # Payout status
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # pending, processing, completed, failed
    payout_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # crypto, bank, etc.
    transaction_hash: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    signal_provider: Mapped["SignalProvider"] = relationship("SignalProvider")

    def __repr__(self):
        return f"<Payout(signal_provider_id={self.signal_provider_id}, amount={self.provider_payout}, status={self.status})>"
