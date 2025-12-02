"""
Favorite Model - User's favorite trading pairs
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User


class Favorite(Base, TimestampMixin):
    """Model for user's favorite/watchlist trading pairs"""
    
    __tablename__ = "favorites"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Trading pair info
    symbol: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    exchange: Mapped[str] = mapped_column(String(50), nullable=False, default="binance")
    
    # User notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Tracking
    last_viewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="favorites")
    
    def __repr__(self):
        return f"<Favorite(id={self.id}, user_id={self.user_id}, symbol={self.symbol}, exchange={self.exchange})>"
