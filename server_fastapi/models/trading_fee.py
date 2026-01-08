"""
Trading Fee Model - Platform trading fee tracking
Tracks fees collected from trades for revenue analysis
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .dex_trade import DEXTrade
    from .trade import Trade
    from .user import User


class TradingFee(Base, TimestampMixin):
    """Model for tracking platform trading fees"""

    __tablename__ = "trading_fees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), index=True, nullable=False
    )

    # Trade reference
    trade_type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # 'dex' or 'cex' (centralized exchange)
    dex_trade_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("dex_trades.id"), nullable=True, index=True
    )
    cex_trade_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("trades.id"), nullable=True, index=True
    )

    # Fee details
    fee_type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # 'platform', 'aggregator', 'affiliate', 'surplus'
    fee_bps: Mapped[int] = mapped_column(Integer, nullable=False)  # Fee in basis points
    fee_amount: Mapped[float] = mapped_column(Float, nullable=False)  # Fee amount
    fee_currency: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # Token symbol

    # Trade details (for reference)
    trade_amount: Mapped[float] = mapped_column(Float, nullable=False)  # Trade amount
    trade_currency: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # Trade currency

    # User tier and volume
    user_tier: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # 'free', 'basic', 'pro', 'enterprise'
    monthly_volume: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )  # User's monthly volume at time of trade

    # Custodial vs non-custodial
    is_custodial: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )  # 'pending', 'collected', 'refunded'
    collected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Metadata
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")
    dex_trade: Mapped[Optional["DEXTrade"]] = relationship("DEXTrade")
    cex_trade: Mapped[Optional["Trade"]] = relationship("Trade")

    def __repr__(self):
        return f"<TradingFee(id={self.id}, user_id={self.user_id}, fee_type={self.fee_type}, amount={self.fee_amount} {self.fee_currency})>"
