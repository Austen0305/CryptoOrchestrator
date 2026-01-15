"""
Trade Model - Trade execution history
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .bot import Bot
    from .dca_bot import DCABot
    from .futures_position import FuturesPosition
    from .grid_bot import GridBot
    from .infinity_grid import InfinityGrid
    from .order import Order
    from .trailing_bot import TrailingBot
    from .user import User


class Trade(Base, TimestampMixin):
    """Model for storing trade history"""

    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), index=True, nullable=False
    )
    bot_id: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("bots.id"), nullable=True, index=True
    )

    # New bot type foreign keys
    grid_bot_id: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("grid_bots.id"), nullable=True, index=True
    )
    dca_bot_id: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("dca_bots.id"), nullable=True, index=True
    )
    infinity_grid_id: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("infinity_grids.id"), nullable=True, index=True
    )
    trailing_bot_id: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("trailing_bots.id"), nullable=True, index=True
    )
    futures_position_id: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("futures_positions.id"), nullable=True, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    bot: Mapped[Optional["Bot"]] = relationship("Bot")
    grid_bot: Mapped[Optional["GridBot"]] = relationship(
        "GridBot", back_populates="trades"
    )
    dca_bot: Mapped[Optional["DCABot"]] = relationship(
        "DCABot", back_populates="trades"
    )
    infinity_grid: Mapped[Optional["InfinityGrid"]] = relationship(
        "InfinityGrid", back_populates="trades"
    )
    trailing_bot: Mapped[Optional["TrailingBot"]] = relationship(
        "TrailingBot", back_populates="trades"
    )
    futures_position: Mapped[Optional["FuturesPosition"]] = relationship(
        "FuturesPosition", back_populates="trades"
    )
    chain_id: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )  # Blockchain chain ID (1=Ethereum)
    transaction_hash: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True
    )  # Blockchain transaction hash
    symbol: Mapped[str] = mapped_column(String, nullable=False, index=True)
    pair: Mapped[str] = mapped_column(
        String, nullable=False, index=True
    )  # Alias for symbol, e.g., "BTC/USD"
    side: Mapped[str] = mapped_column(String, nullable=False)  # 'buy' or 'sell'
    order_type: Mapped[str] = mapped_column(
        String, nullable=False, default="market"
    )  # 'market', 'limit', 'stop'
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    cost: Mapped[float] = mapped_column(Float, nullable=False)  # amount * price
    fee: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    order_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    order_ref_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("orders.id"), nullable=True, index=True
    )  # Reference to Order model
    # Order relationship (defined after order_ref_id column)
    order: Mapped[Optional["Order"]] = relationship(
        "Order", foreign_keys="[Trade.order_ref_id]", back_populates="trades"
    )
    mode: Mapped[str] = mapped_column(
        String, nullable=False, default="paper", index=True
    )  # 'paper' or 'real'
    executed_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_message: Mapped[str] = mapped_column(String, nullable=True)
    pnl: Mapped[float] = mapped_column(Float, nullable=True)  # Profit and loss
    pnl_percent: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # P&L percentage
    status: Mapped[str] = mapped_column(
        String(20), default="completed", nullable=False
    )  # completed, pending, failed, cancelled
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )  # Trade execution time
    total: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # Total trade value (amount * price)
    audit_logged: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )  # Whether trade has been audit logged

    # ISO 20022 / MiCA Compliance Fields
    uti: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="Unique Transaction Identifier (ISO 23897)",
    )
    venue_reporting_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Venue Reporting ID (MiCA Art 16)",
    )

    def __repr__(self):
        return f"<Trade(id={self.id}, symbol={self.symbol}, side={self.side}, amount={self.amount})>"
