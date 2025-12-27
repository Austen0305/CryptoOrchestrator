"""
Push Subscription Model
Stores push notification subscriptions for mobile devices (Expo, FCM, etc.)
"""

from typing import Optional
from sqlalchemy import String, Integer, Text, ForeignKey, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from .base import BaseModel


class PushSubscription(BaseModel):
    """Push notification subscription model for mobile devices"""

    __tablename__ = "push_subscriptions"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Expo push token (e.g., "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]")
    expo_push_token: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )

    # Web Push subscription (for web apps, optional)
    endpoint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    p256dh_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    auth_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Device/platform information
    platform: Mapped[str] = mapped_column(
        String(20), nullable=False, default="unknown"
    )  # 'ios', 'android', 'web'
    device_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    app_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Subscription status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Notification preferences
    push_notifications_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    trade_notifications_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    bot_notifications_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    risk_notifications_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    price_alerts_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    # Last notification sent timestamp
    last_notification_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # Last error (for debugging failed notifications)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="push_subscriptions")

    # Indexes for efficient queries
    __table_args__ = (
        Index("ix_push_subscriptions_user_active", "user_id", "is_active"),
        Index("ix_push_subscriptions_expo_token", "expo_push_token"),
    )

    def __repr__(self) -> str:
        return f"<PushSubscription(id={self.id}, user_id={self.user_id}, platform={self.platform}, active={self.is_active})>"
