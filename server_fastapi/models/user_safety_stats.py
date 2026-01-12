"""
User Safety Stats Model
Tracks persistent safety metrics for users (daily loss, volume, etc.)
"""

from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Index,
    DateTime,
    Boolean,
)
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base, TimestampMixin


class UserSafetyStats(Base, TimestampMixin):
    """Persistent safety statistics for a user"""

    __tablename__ = "user_safety_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True
    )

    # 2026 Persistent Metrics
    daily_loss = Column(Float, default=0.0, nullable=False)
    daily_volume = Column(Float, default=0.0, nullable=False)
    total_trades_today = Column(Integer, default=0, nullable=False)

    # Last reset tracker
    last_reset_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Emergency flags
    emergency_stop_active = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="safety_stats")

    __table_args__ = (Index("idx_user_safety_user_id", "user_id"),)
