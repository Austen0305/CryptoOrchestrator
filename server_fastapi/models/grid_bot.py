"""
Grid Trading Bot database model.
Grid trading places buy and sell orders in a grid pattern to profit from volatility.
"""

from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .trade import Trade


class GridBot(BaseModel):
    """
    Grid Trading Bot model.
    Places buy/sell orders in a grid pattern within a price range.
    """
    __tablename__ = "grid_bots"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Trading configuration
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    exchange: Mapped[str] = mapped_column(String(50), nullable=False)
    trading_mode: Mapped[str] = mapped_column(String(10), default="paper", nullable=False)  # paper, real
    
    # Grid parameters
    upper_price: Mapped[float] = mapped_column(Float, nullable=False)  # Upper bound of grid
    lower_price: Mapped[float] = mapped_column(Float, nullable=False)  # Lower bound of grid
    grid_count: Mapped[int] = mapped_column(Integer, nullable=False)  # Number of grid levels
    grid_spacing_type: Mapped[str] = mapped_column(String(20), default="arithmetic", nullable=False)  # arithmetic, geometric
    order_amount: Mapped[float] = mapped_column(Float, nullable=False)  # Amount per order
    
    # Bot status
    active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="stopped", nullable=False)  # stopped, running, paused
    
    # Performance tracking
    total_profit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    win_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Grid state (JSON)
    grid_state: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON: current orders, filled orders
    
    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    stopped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_trade_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Additional configuration (JSON)
    config: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON: advanced settings
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="grid_bots")
    trades: Mapped[list["Trade"]] = relationship("Trade", back_populates="grid_bot", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """Convert grid bot instance to dictionary."""
        import json
        from datetime import datetime
        data = super().to_dict()
        
        # Serialize datetime fields to ISO format strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        
        # Parse JSON fields
        if data.get('grid_state'):
            try:
                data['grid_state'] = json.loads(data['grid_state'])
            except (json.JSONDecodeError, TypeError):
                data['grid_state'] = {}
        else:
            data['grid_state'] = {}
            
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
        return f"<GridBot(id='{self.id}', name='{self.name}', symbol='{self.symbol}', active={self.active})>"


# Add relationship to User model (will be done in user.py)
# Add relationship to Trade model (will be done in trade.py)

