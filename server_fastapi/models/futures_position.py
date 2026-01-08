"""
Futures Position database model.
Futures trading with leverage support.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any

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

from .base import BaseModel

if TYPE_CHECKING:
    from .trade import Trade
    from .user import User


class FuturesPosition(BaseModel):
    """
    Futures Position model.
    Represents an open futures position with leverage.
    """

    __tablename__ = "futures_positions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # Optional name for the position

    # Trading configuration
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # exchange field removed - use chain_id instead (migration: 20251208_remove_exchange)
    chain_id: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )  # Blockchain chain ID (1=Ethereum, 8453=Base, etc.)
    trading_mode: Mapped[str] = mapped_column(
        String(10), default="paper", nullable=False
    )  # paper, real

    # Position details
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # long, short
    leverage: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # Leverage multiplier (e.g., 10x)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)  # Position size
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)  # Entry price
    current_price: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Current market price

    # Margin and liquidation
    margin_used: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Margin used for this position
    margin_available: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Available margin
    liquidation_price: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Price at which position will be liquidated
    maintenance_margin: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Maintenance margin requirement

    # Stop loss / Take profit
    stop_loss_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    take_profit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    trailing_stop_percent: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # Trailing stop (%)

    # Position status
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="open", nullable=False
    )  # open, closed, liquidated

    # Performance tracking
    unrealized_pnl: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )  # Unrealized profit/loss
    realized_pnl: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )  # Realized profit/loss
    total_pnl: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )  # Total profit/loss
    pnl_percent: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )  # P&L as percentage

    # Risk metrics
    liquidation_risk: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )  # Distance to liquidation (%)
    margin_ratio: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )  # Margin ratio

    # Timestamps
    opened_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Additional configuration (JSON)
    config: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON: advanced settings

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="futures_positions")
    trades: Mapped[list["Trade"]] = relationship(
        "Trade", back_populates="futures_position", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert futures position instance to dictionary."""
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

        # Map is_open -> is_open for API consistency
        data["is_open"] = data.get("is_open", True)

        return data

    def __repr__(self) -> str:
        return f"<FuturesPosition(id='{self.id}', symbol='{self.symbol}', side='{self.side}', leverage={self.leverage}x, is_open={self.is_open})>"
