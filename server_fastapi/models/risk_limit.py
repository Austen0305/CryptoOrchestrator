"""
Risk Limit Model - User-defined risk limits and thresholds
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin


class RiskLimit(Base, TimestampMixin):
    """Model for storing user-defined risk limits"""
    
    __tablename__ = "risk_limits"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    limit_type: Mapped[str] = mapped_column(String, nullable=False)  # 'max_drawdown', 'position_size', 'daily_loss', 'portfolio_risk'
    value: Mapped[float] = mapped_column(Float, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f"<RiskLimit(id={self.id}, user_id={self.user_id}, type={self.limit_type}, value={self.value})>"
