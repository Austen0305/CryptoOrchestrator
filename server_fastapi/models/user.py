"""
User model for authentication and authorization
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

# ExchangeAPIKey - REMOVED (platform uses blockchain/DEX trading exclusively)

if TYPE_CHECKING:
    from .analytics_threshold import AnalyticsThreshold
    from .bot import Bot
    from .dca_bot import DCABot
    from .dex_position import DEXPosition
    from .futures_position import FuturesPosition
    from .grid_bot import GridBot
    from .idempotency import IdempotencyKey
    from .infinity_grid import InfinityGrid
    from .institutional_wallet import InstitutionalWallet
    from .push_subscription import PushSubscription
    from .strategy import Strategy
    from .subscription import Subscription
    from .trailing_bot import TrailingBot


class User(BaseModel):
    """
    User model for authentication and authorization.
    Enhanced for SaaS with subscription support.
    """

    __tablename__ = "users"

    # Authentication fields
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Email verification
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )  # Alias for is_email_verified (for compatibility)
    email_verification_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    email_verification_expires: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    # Password reset
    password_reset_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    password_reset_expires: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    # User status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    role: Mapped[str] = mapped_column(
        String(20), default="user", nullable=False
    )  # user, admin

    # Profile fields
    first_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Activity tracking
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Preferences
    timezone: Mapped[str | None] = mapped_column(
        String(40), nullable=True, default="UTC"
    )
    locale: Mapped[str | None] = mapped_column(String(10), nullable=True, default="en")

    # Terms and compliance
    terms_accepted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )  # Whether user has accepted terms of service
    terms_accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )  # When terms were accepted
    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )  # Two-factor authentication enabled
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )  # Email verification status (alias for is_email_verified compatibility)

    # Relationships
    subscription: Mapped[Optional["Subscription"]] = relationship(
        "Subscription",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    # ExchangeAPIKey relationship removed - platform uses blockchain wallets instead
    # exchange_api_keys relationship removed - platform uses blockchain wallets instead
    bots: Mapped[list["Bot"]] = relationship(
        "Bot", back_populates="user", cascade="all, delete-orphan"
    )
    strategies: Mapped[list["Strategy"]] = relationship(
        "Strategy", back_populates="user", cascade="all, delete-orphan"
    )
    grid_bots: Mapped[list["GridBot"]] = relationship(
        "GridBot", back_populates="user", cascade="all, delete-orphan"
    )
    dca_bots: Mapped[list["DCABot"]] = relationship(
        "DCABot", back_populates="user", cascade="all, delete-orphan"
    )
    infinity_grids: Mapped[list["InfinityGrid"]] = relationship(
        "InfinityGrid", back_populates="user", cascade="all, delete-orphan"
    )
    trailing_bots: Mapped[list["TrailingBot"]] = relationship(
        "TrailingBot", back_populates="user", cascade="all, delete-orphan"
    )
    futures_positions: Mapped[list["FuturesPosition"]] = relationship(
        "FuturesPosition", back_populates="user", cascade="all, delete-orphan"
    )
    dex_positions: Mapped[list["DEXPosition"]] = relationship(
        "DEXPosition", back_populates="user", cascade="all, delete-orphan"
    )
    idempotency_keys: Mapped[list["IdempotencyKey"]] = relationship(
        "IdempotencyKey", back_populates="user", cascade="all, delete-orphan"
    )
    push_subscriptions: Mapped[list["PushSubscription"]] = relationship(
        "PushSubscription", back_populates="user", cascade="all, delete-orphan"
    )
    analytics_thresholds: Mapped[list["AnalyticsThreshold"]] = relationship(
        "AnalyticsThreshold", back_populates="user", cascade="all, delete-orphan"
    )
    institutional_wallets: Mapped[list["InstitutionalWallet"]] = relationship(
        "InstitutionalWallet",
        secondary="wallet_signer_associations",
        back_populates="signers",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
