"""
Strategy Model - Database schema for trading strategies
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Strategy(Base):
    """Strategy database model"""

    __tablename__ = "strategies"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    strategy_type = Column(
        String, nullable=False
    )  # rsi, macd, breakout, lstm, transformer, custom
    category = Column(String, nullable=False)  # technical, ml, hybrid
    version = Column(String, default="1.0.0")
    parent_strategy_id = Column(
        String, ForeignKey("strategies.id"), nullable=True
    )  # For versioning

    # Strategy configuration
    config = Column(JSON, nullable=False, default=dict)

    # Strategy code/logic (JSON representation for visual editor)
    logic = Column(JSON, nullable=True)

    # Metadata
    is_template = Column(Boolean, default=False)  # Built-in template
    is_public = Column(Boolean, default=False)  # Available in marketplace
    is_published = Column(Boolean, default=False)  # Published to marketplace

    # Performance metrics
    backtest_sharpe_ratio = Column(Float, nullable=True)
    backtest_win_rate = Column(Float, nullable=True)
    backtest_total_return = Column(Float, nullable=True)
    backtest_max_drawdown = Column(Float, nullable=True)

    # Usage stats
    usage_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)

    # Relationships
    parent_strategy = relationship("Strategy", remote_side=[id], backref="versions")
    user = relationship("User", back_populates="strategies")


class StrategyVersion(Base):
    """Strategy version history"""

    __tablename__ = "strategy_versions"

    id = Column(String, primary_key=True, index=True)
    strategy_id = Column(
        String, ForeignKey("strategies.id"), nullable=False, index=True
    )
    version = Column(String, nullable=False)

    # Snapshot of strategy at this version
    name = Column(String, nullable=False)
    config = Column(JSON, nullable=False)
    logic = Column(JSON, nullable=True)

    # Change metadata
    change_description = Column(Text)
    change_author = Column(Integer, ForeignKey("users.id"))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    strategy = relationship("Strategy", backref="version_history")
