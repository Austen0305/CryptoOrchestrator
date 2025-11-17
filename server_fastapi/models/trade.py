"""
Trade Model - Trade execution history
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User
    from .bot import Bot


class Trade(Base, TimestampMixin):
    """Model for storing trade history"""
    
    __tablename__ = "trades"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    bot_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("bots.id"), nullable=True, index=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    bot: Mapped[Optional["Bot"]] = relationship("Bot")
    exchange: Mapped[str] = mapped_column(String, nullable=False)
    symbol: Mapped[str] = mapped_column(String, nullable=False, index=True)
    side: Mapped[str] = mapped_column(String, nullable=False)  # 'buy' or 'sell'
    order_type: Mapped[str] = mapped_column(String, nullable=False, default="market")  # 'market', 'limit', 'stop'
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    cost: Mapped[float] = mapped_column(Float, nullable=False)  # amount * price
    fee: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    order_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    mode: Mapped[str] = mapped_column(String, nullable=False, default="paper", index=True)  # 'paper' or 'real'
    executed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_message: Mapped[str] = mapped_column(String, nullable=True)
    pnl: Mapped[float] = mapped_column(Float, nullable=True)  # Profit and loss
    audit_logged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Whether trade has been audit logged
    
    def __repr__(self):
        return f"<Trade(id={self.id}, symbol={self.symbol}, side={self.side}, amount={self.amount})>"
