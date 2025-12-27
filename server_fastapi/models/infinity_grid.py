"""
Infinity Grid Bot database model.
Infinity grid is a dynamic grid that follows price movements.
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


class InfinityGrid(BaseModel):
    """
    Infinity Grid Bot model.
    Dynamic grid that adjusts upper/lower bounds as price moves.
    """

    __tablename__ = "infinity_grids"

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

    # Grid parameters
    grid_count: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # Number of grid levels
    grid_spacing_percent: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Spacing between grids (%)
    order_amount: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Amount per order

    # Dynamic bounds
    current_upper_price: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Current upper bound
    current_lower_price: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Current lower bound
    initial_price: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Price when bot started

    # Adjustment parameters
    upper_adjustment_percent: Mapped[float] = mapped_column(
        Float, default=5.0, nullable=False
    )  # Adjust upper when price moves this % up
    lower_adjustment_percent: Mapped[float] = mapped_column(
        Float, default=5.0, nullable=False
    )  # Adjust lower when price moves this % down

    # Bot status
    active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="stopped", nullable=False
    )  # stopped, running, paused

    # Performance tracking
    total_profit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    grid_adjustments: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )  # Number of times grid was adjusted

    # Grid state (JSON)
    grid_state: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON: current orders, filled orders

    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    stopped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_adjustment_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    last_trade_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Additional configuration (JSON)
    config: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON: advanced settings

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="infinity_grids")
    trades: Mapped[list["Trade"]] = relationship(
        "Trade", back_populates="infinity_grid", cascade="all, delete-orphan"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert infinity grid instance to dictionary."""
        import json
        from datetime import datetime

        data = super().to_dict()

        # Serialize datetime fields to ISO format strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()

        # Parse JSON fields
        if data.get("grid_state"):
            try:
                data["grid_state"] = json.loads(data["grid_state"])
            except (json.JSONDecodeError, TypeError):
                data["grid_state"] = {}
        else:
            data["grid_state"] = {}

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
        return f"<InfinityGrid(id='{self.id}', name='{self.name}', symbol='{self.symbol}', active={self.active})>"
