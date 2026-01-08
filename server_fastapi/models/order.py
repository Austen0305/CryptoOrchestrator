"""
Advanced Order Model - Stop-loss, take-profit, trailing stops
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .trade import Trade
    from .user import User


class OrderType(str, Enum):
    """Order types"""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TAKE_PROFIT = "take_profit"
    TAKE_PROFIT_LIMIT = "take_profit_limit"
    TRAILING_STOP = "trailing_stop"
    TRAILING_STOP_LIMIT = "trailing_stop_limit"


class OrderStatus(str, Enum):
    """Order status"""

    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Order(Base, TimestampMixin):
    """Model for advanced order types"""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    bot_id: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("bots.id"), nullable=True, index=True
    )

    # Order details
    chain_id: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )  # Blockchain chain ID
    transaction_hash: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True
    )  # Blockchain transaction hash
    symbol: Mapped[str] = mapped_column(String, nullable=False, index=True)
    pair: Mapped[str] = mapped_column(String, nullable=False, index=True)
    side: Mapped[str] = mapped_column(String, nullable=False)  # 'buy' or 'sell'
    order_type: Mapped[str] = mapped_column(String, nullable=False)  # OrderType enum
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # OrderStatus enum

    # Amount and price
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)  # Limit price
    stop_price: Mapped[float | None] = mapped_column(Float, nullable=True)  # Stop price
    take_profit_price: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # Take profit price

    # Trailing stop settings
    trailing_stop_percent: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # Trailing stop percentage
    trailing_stop_amount: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # Trailing stop amount
    highest_price: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # Highest price reached (for trailing stops)
    lowest_price: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # Lowest price reached (for trailing stops)

    # Execution
    filled_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    average_fill_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    blockchain_order_id: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True
    )  # Changed from exchange_order_id to blockchain_order_id

    # Time in force
    time_in_force: Mapped[str] = mapped_column(
        String(20), default="GTC", nullable=False
    )  # GTC, IOC, FOK
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Mode
    mode: Mapped[str] = mapped_column(
        String, nullable=False, default="paper", index=True
    )  # 'paper' or 'real'

    # Relationships
    user: Mapped["User"] = relationship("User")
    trades: Mapped[list["Trade"]] = relationship("Trade", back_populates="order")

    def __repr__(self):
        return f"<Order(id={self.id}, symbol={self.symbol}, type={self.order_type}, status={self.status})>"
