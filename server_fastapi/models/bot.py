"""
Bot database model.
"""

from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel

if TYPE_CHECKING:
    from .user import User


class Bot(BaseModel):
    """
    Bot model for trading bot configurations and status.
    """

    __tablename__ = "bots"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="bots")
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    strategy: Mapped[str] = mapped_column(String(50), nullable=False)
    parameters: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON string
    active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="stopped", nullable=False)
    last_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_stopped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    performance_data: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON string

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert bot instance to dictionary with parsed JSON fields.
        Maps DB column names to API response format.
        """
        import json

        data = super().to_dict()
        # Parse JSON fields
        if data.get("parameters"):
            try:
                data["config"] = json.loads(data["parameters"])
            except (json.JSONDecodeError, TypeError):
                data["config"] = {}
        else:
            data["config"] = {}

        # Remove raw parameters field (replaced by config)
        data.pop("parameters", None)

        # Map active -> is_active for API consistency
        data["is_active"] = data.pop("active", False)

        if data.get("performance_data"):
            try:
                data["performance_data"] = json.loads(data["performance_data"])
            except (json.JSONDecodeError, TypeError):
                data["performance_data"] = {}
        else:
            data["performance_data"] = {}

        return data

    def __repr__(self) -> str:
        return f"<Bot(id='{self.id}', name='{self.name}', symbol='{self.symbol}', active={self.active})>"
