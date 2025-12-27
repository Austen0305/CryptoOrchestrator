"""
Risk Alert Model - Tracks risk events and violations
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin


class RiskAlert(Base, TimestampMixin):
    """Model for storing risk alerts and violations"""

    __tablename__ = "risk_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    alert_type: Mapped[str] = mapped_column(
        String, nullable=False
    )  # 'drawdown', 'volatility', 'exposure', 'position_size'
    severity: Mapped[str] = mapped_column(
        String, nullable=False
    )  # 'low', 'medium', 'high', 'critical'
    message: Mapped[str] = mapped_column(String, nullable=False)
    current_value: Mapped[float] = mapped_column(Float, nullable=True)
    threshold_value: Mapped[float] = mapped_column(Float, nullable=True)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    def __repr__(self):
        return f"<RiskAlert(id={self.id}, type={self.alert_type}, severity={self.severity})>"
