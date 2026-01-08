"""
Idempotency Key Model
Stores idempotency keys to prevent duplicate transaction processing
"""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class IdempotencyKey(Base, TimestampMixin):
    """Idempotency key model for preventing duplicate transactions"""

    __tablename__ = "idempotency_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    result: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False
    )  # Store operation result
    status_code: Mapped[int] = mapped_column(Integer, nullable=False, default=200)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="idempotency_keys")

    def __repr__(self):
        return f"<IdempotencyKey(key={self.key[:20]}..., user_id={self.user_id}, expires_at={self.expires_at})>"
