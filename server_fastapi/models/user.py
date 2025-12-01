"""
User model for authentication and authorization
"""
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .base import BaseModel, Base

if TYPE_CHECKING:
    from .subscription import Subscription
    from .exchange_api_key import ExchangeAPIKey
    from .bot import Bot
    from .strategy import Strategy
    from .grid_bot import GridBot
    from .dca_bot import DCABot
    from .infinity_grid import InfinityGrid
    from .trailing_bot import TrailingBot
    from .futures_position import FuturesPosition


class User(BaseModel):
    """
    User model for authentication and authorization.
    Enhanced for SaaS with subscription support.
    """
    __tablename__ = "users"

    # Authentication fields
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Email verification
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verification_token: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    email_verification_expires: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Password reset
    password_reset_token: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    password_reset_expires: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # User status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)  # user, admin
    
    # Profile fields
    first_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Activity tracking
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Preferences
    timezone: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, default="UTC")
    locale: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, default="en")
    
    # Relationships
    subscription: Mapped[Optional["Subscription"]] = relationship(
        "Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    exchange_api_keys: Mapped[List["ExchangeAPIKey"]] = relationship(
        "ExchangeAPIKey", back_populates="user", cascade="all, delete-orphan"
    )
    bots: Mapped[List["Bot"]] = relationship(
        "Bot", back_populates="user", cascade="all, delete-orphan"
    )
    strategies: Mapped[List["Strategy"]] = relationship(
        "Strategy", back_populates="user", cascade="all, delete-orphan"
    )
    grid_bots: Mapped[List["GridBot"]] = relationship(
        "GridBot", back_populates="user", cascade="all, delete-orphan"
    )
    dca_bots: Mapped[List["DCABot"]] = relationship(
        "DCABot", back_populates="user", cascade="all, delete-orphan"
    )
    infinity_grids: Mapped[List["InfinityGrid"]] = relationship(
        "InfinityGrid", back_populates="user", cascade="all, delete-orphan"
    )
    trailing_bots: Mapped[List["TrailingBot"]] = relationship(
        "TrailingBot", back_populates="user", cascade="all, delete-orphan"
    )
    futures_positions: Mapped[List["FuturesPosition"]] = relationship(
        "FuturesPosition", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

