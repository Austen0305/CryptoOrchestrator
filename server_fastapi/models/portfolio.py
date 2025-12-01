"""
Portfolio Model - User portfolio holdings
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin


class Portfolio(Base, TimestampMixin):
    """Model for storing user portfolio balances"""
    
    __tablename__ = "portfolios"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False, unique=True)
    exchange: Mapped[str] = mapped_column(String, nullable=False)
    balances: Mapped[dict] = mapped_column(JSON, nullable=False, default={})  # {symbol: amount}
    total_value_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Portfolio(id={self.id}, user_id={self.user_id}, exchange={self.exchange})>"
