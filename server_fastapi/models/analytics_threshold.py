"""
Analytics Threshold Model - Configurable threshold alerts for marketplace analytics
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Enum as SQLEnum,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User


class ThresholdType(str, Enum):
    """Type of analytics threshold"""
    COPY_TRADING = "copy_trading"
    INDICATOR_MARKETPLACE = "indicator_marketplace"
    PROVIDER = "provider"
    DEVELOPER = "developer"
    MARKETPLACE_OVERVIEW = "marketplace_overview"


class ThresholdMetric(str, Enum):
    """Available metrics for threshold monitoring"""
    # Copy Trading Metrics
    REVENUE_DROP_PERCENT = "revenue_drop_percent"
    FOLLOWER_COUNT_CHANGE = "follower_count_change"
    TOTAL_RETURN = "total_return"
    SHARPE_RATIO = "sharpe_ratio"
    WIN_RATE = "win_rate"
    MAX_DRAWDOWN = "max_drawdown"
    PROFIT_FACTOR = "profit_factor"
    AVERAGE_RATING = "average_rating"
    
    # Indicator Marketplace Metrics
    INDICATOR_REVENUE_DROP_PERCENT = "indicator_revenue_drop_percent"
    INDICATOR_PURCHASE_COUNT_CHANGE = "indicator_purchase_count_change"
    INDICATOR_AVERAGE_RATING = "indicator_average_rating"
    
    # Marketplace Overview Metrics
    PLATFORM_REVENUE_DROP_PERCENT = "platform_revenue_drop_percent"
    TOTAL_PROVIDERS_CHANGE = "total_providers_change"
    TOTAL_INDICATORS_CHANGE = "total_indicators_change"


class ThresholdOperator(str, Enum):
    """Comparison operators for thresholds"""
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    EQUALS = "eq"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN_OR_EQUAL = "lte"
    PERCENT_CHANGE_DOWN = "percent_change_down"
    PERCENT_CHANGE_UP = "percent_change_up"


class AnalyticsThreshold(Base, TimestampMixin):
    """Model for configurable analytics threshold alerts"""

    __tablename__ = "analytics_thresholds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )  # None for global thresholds
    
    # Threshold configuration
    threshold_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # ThresholdType enum value
    metric: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # ThresholdMetric enum value
    operator: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # ThresholdOperator enum value
    threshold_value: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Context (e.g., provider_id, developer_id for specific entity thresholds)
    context: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Alert configuration
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notification_channels: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # {"email": true, "push": true, "in_app": true}
    
    # Cooldown and frequency
    cooldown_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Metadata
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="analytics_thresholds")
