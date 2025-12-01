"""
DCA (Dollar Cost Averaging) Bot database model.
DCA bots buy at regular intervals to average out the purchase price.
"""

from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .trade import Trade


class DCABot(BaseModel):
    """
    DCA (Dollar Cost Averaging) Bot model.
    Buys at regular intervals with optional martingale strategy.
    """
    __tablename__ = "dca_bots"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Trading configuration
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    exchange: Mapped[str] = mapped_column(String(50), nullable=False)
    trading_mode: Mapped[str] = mapped_column(String(10), default="paper", nullable=False)  # paper, real
    
    # DCA parameters
    total_investment: Mapped[float] = mapped_column(Float, nullable=False)  # Total amount to invest
    order_amount: Mapped[float] = mapped_column(Float, nullable=False)  # Amount per order
    interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False)  # Minutes between orders
    max_orders: Mapped[int] = mapped_column(Integer, nullable=True)  # Maximum number of orders (None = unlimited)
    
    # Martingale strategy
    use_martingale: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    martingale_multiplier: Mapped[float] = mapped_column(Float, default=1.5, nullable=False)  # Increase order size by this multiplier
    martingale_max_multiplier: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)  # Maximum multiplier
    
    # Take profit / Stop loss
    take_profit_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Take profit at this % gain
    stop_loss_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Stop loss at this % loss
    
    # Bot status
    active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="stopped", nullable=False)  # stopped, running, paused, completed
    
    # Performance tracking
    orders_executed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_invested: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    average_price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    current_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_profit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    profit_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Next order tracking
    next_order_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_order_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    stopped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Additional configuration (JSON)
    config: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON: advanced settings
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="dca_bots")
    trades: Mapped[list["Trade"]] = relationship("Trade", back_populates="dca_bot", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """Convert DCA bot instance to dictionary."""
        import json
        from datetime import datetime
        data = super().to_dict()
        
        # Serialize datetime fields to ISO format strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        
        # Parse JSON fields
        if data.get('config'):
            try:
                data['config'] = json.loads(data['config'])
            except (json.JSONDecodeError, TypeError):
                data['config'] = {}
        else:
            data['config'] = {}
        
        # Map active -> is_active for API consistency
        data['is_active'] = data.pop('active', False)
        
        return data

    def __repr__(self) -> str:
        return f"<DCABot(id='{self.id}', name='{self.name}', symbol='{self.symbol}', active={self.active})>"

