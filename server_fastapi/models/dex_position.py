"""
DEX Position Model
Tracks open positions from DEX swaps for better P&L calculation.
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
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .dex_trade import DEXTrade


class DEXPosition(BaseModel):
    """
    DEX Position model.
    Tracks open positions from DEX swaps for granular P&L calculation.
    """

    __tablename__ = "dex_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    # Position details
    chain_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    token_address: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    token_symbol: Mapped[str] = mapped_column(String(20), nullable=False)

    # Position size
    amount: Mapped[float] = mapped_column(Float, nullable=False)  # Token amount
    amount_usd: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # USD value at entry

    # Entry price
    entry_price: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Entry price in USD
    entry_trade_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("dex_trades.id"), nullable=True
    )

    # Current metrics
    current_price: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Current price in USD
    current_value_usd: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Current USD value

    # P&L
    unrealized_pnl: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unrealized_pnl_percent: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )

    # Position status
    is_open: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    exit_trade_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("dex_trades.id"), nullable=True
    )
    exit_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    realized_pnl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    realized_pnl_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Additional metadata
    position_metadata: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON: additional position data

    # Timestamps
    opened_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="dex_positions")
    entry_trade: Mapped[Optional["DEXTrade"]] = relationship(
        "DEXTrade", foreign_keys=[entry_trade_id], backref="positions_opened"
    )
    exit_trade: Mapped[Optional["DEXTrade"]] = relationship(
        "DEXTrade", foreign_keys=[exit_trade_id], backref="positions_closed"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert position instance to dictionary"""
        import json

        data = super().to_dict()

        # Serialize datetime fields
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()

        # Parse JSON metadata
        if data.get("metadata"):
            try:
                data["metadata"] = json.loads(data["metadata"])
            except (json.JSONDecodeError, TypeError):
                data["metadata"] = {}
        else:
            data["metadata"] = {}

        return data

    def __repr__(self) -> str:
        return (
            f"<DEXPosition(id={self.id}, user_id={self.user_id}, "
            f"token={self.token_symbol}, amount={self.amount}, "
            f"pnl={self.unrealized_pnl}, is_open={self.is_open})>"
        )
