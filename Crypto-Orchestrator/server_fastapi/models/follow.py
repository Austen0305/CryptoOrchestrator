"""
Follow Model - Copy trading relationships
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
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User


class Follow(Base, TimestampMixin):
    """Model for copy trading relationships"""

    __tablename__ = "follows"
    __table_args__ = (
        UniqueConstraint("follower_id", "trader_id", name="unique_follow"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    follower_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    trader_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    # Copy trading settings
    allocation_percentage: Mapped[float] = mapped_column(
        Float, default=100.0, nullable=False
    )
    max_position_size: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Auto-copy settings
    auto_copy_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    copy_buy_orders: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    copy_sell_orders: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    min_trade_size: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_trade_size: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Statistics
    total_copied_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_profit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_copied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    follower: Mapped["User"] = relationship("User", foreign_keys=[follower_id])
    trader: Mapped["User"] = relationship("User", foreign_keys=[trader_id])

    def __repr__(self):
        return f"<Follow(follower_id={self.follower_id}, trader_id={self.trader_id}, active={self.is_active})>"


class CopiedTrade(Base, TimestampMixin):
    """Model for tracking copied trades"""

    __tablename__ = "copied_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    follower_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    trader_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    original_trade_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trades.id"), nullable=False, index=True
    )
    copied_trade_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("trades.id"), nullable=True, index=True
    )

    # Copy details
    allocation_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    original_amount: Mapped[float] = mapped_column(Float, nullable=False)
    copied_amount: Mapped[float] = mapped_column(Float, nullable=False)
    original_price: Mapped[float] = mapped_column(Float, nullable=False)
    copied_price: Mapped[float] = mapped_column(Float, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # pending, executed, failed
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    follower: Mapped["User"] = relationship("User", foreign_keys=[follower_id])
    trader: Mapped["User"] = relationship("User", foreign_keys=[trader_id])
    original_trade: Mapped["Trade"] = relationship(
        "Trade", foreign_keys=[original_trade_id]
    )
    copied_trade: Mapped[Optional["Trade"]] = relationship(
        "Trade", foreign_keys=[copied_trade_id]
    )

    def __repr__(self):
        return f"<CopiedTrade(id={self.id}, follower_id={self.follower_id}, status={self.status})>"
