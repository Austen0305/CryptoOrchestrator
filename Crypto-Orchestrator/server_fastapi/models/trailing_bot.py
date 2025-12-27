"""
Trailing Bot database model.
Trailing bots follow price movements with dynamic stop-loss/take-profit.
"""

from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .trade import Trade


class TrailingBot(BaseModel):
    """
    Trailing Bot model.
    Trailing buy (buy on dips) or trailing sell (sell on peaks).
    """

    __tablename__ = "trailing_bots"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Trading configuration
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # exchange field removed - use chain_id instead (migration: 20251208_remove_exchange)
    chain_id: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )  # Blockchain chain ID (1=Ethereum, 8453=Base, etc.)
    trading_mode: Mapped[str] = mapped_column(
        String(10), default="paper", nullable=False
    )  # paper, real
    bot_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # trailing_buy, trailing_sell

    # Trailing parameters
    initial_price: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Starting price
    current_price: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Current trailing price
    trailing_percent: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Trailing distance (%)
    order_amount: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Amount to buy/sell

    # For trailing buy: buy when price drops by trailing_percent
    # For trailing sell: sell when price rises by trailing_percent

    # Additional parameters
    max_price: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # Maximum price to buy at (trailing buy)
    min_price: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # Minimum price to sell at (trailing sell)

    # Bot status
    active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="stopped", nullable=False
    )  # stopped, running, paused, triggered

    # Performance tracking
    orders_executed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_profit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    highest_price: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )  # Highest price seen (for trailing sell)
    lowest_price: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )  # Lowest price seen (for trailing buy)

    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    stopped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_price_update_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    last_order_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Additional configuration (JSON)
    config: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON: advanced settings

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="trailing_bots")
    trades: Mapped[list["Trade"]] = relationship(
        "Trade", back_populates="trailing_bot", cascade="all, delete-orphan"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert trailing bot instance to dictionary."""
        import json
        from datetime import datetime

        data = super().to_dict()

        # Serialize datetime fields to ISO format strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()

        # Parse JSON fields
        if data.get("config"):
            try:
                data["config"] = json.loads(data["config"])
            except (json.JSONDecodeError, TypeError):
                data["config"] = {}
        else:
            data["config"] = {}

        # Map active -> is_active for API consistency
        data["is_active"] = data.pop("active", False)

        return data

    def __repr__(self) -> str:
        return f"<TrailingBot(id='{self.id}', name='{self.name}', symbol='{self.symbol}', type='{self.bot_type}', active={self.active})>"
