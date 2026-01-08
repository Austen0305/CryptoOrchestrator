"""
Indicator Model - Custom Indicator Marketplace
"""

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User


class IndicatorStatus(str, Enum):
    """Indicator approval status"""

    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class IndicatorLanguage(str, Enum):
    """Indicator programming language"""

    PINE_SCRIPT = "pine_script"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    CUSTOM_DSL = "custom_dsl"


class Indicator(Base, TimestampMixin):
    """Model for custom indicators in marketplace"""

    __tablename__ = "indicators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    developer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    # Basic information
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # trend, momentum, volatility, volume, etc.
    tags: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Comma-separated tags

    # Marketplace status
    status: Mapped[str] = mapped_column(
        String(20), default=IndicatorStatus.DRAFT.value, nullable=False
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Pricing
    price: Mapped[float] = mapped_column(Float, nullable=False, server_default="0.0")
    is_free: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Technical details
    language: Mapped[str] = mapped_column(
        String(20), default=IndicatorLanguage.PYTHON.value, nullable=False
    )
    code: Mapped[str] = mapped_column(Text, nullable=False)  # Indicator code
    parameters: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # Default parameters

    # Versioning
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    latest_version_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Statistics
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    purchase_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_ratings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_revenue: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Documentation
    documentation: Mapped[str | None] = mapped_column(Text, nullable=True)
    usage_examples: Mapped[str | None] = mapped_column(Text, nullable=True)
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    developer: Mapped["User"] = relationship("User", foreign_keys=[developer_id])

    def __repr__(self):
        return f"<Indicator(id={self.id}, name={self.name}, status={self.status})>"


class IndicatorVersion(Base, TimestampMixin):
    """Model for indicator versioning"""

    __tablename__ = "indicator_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    indicator_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("indicators.id"), nullable=False, index=True
    )

    # Version information
    version: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3, etc.
    version_name: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # "1.0.0", "2.1.0", etc.
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Code
    code: Mapped[str] = mapped_column(Text, nullable=False)
    parameters: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_breaking: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )  # Breaking changes

    # Relationships
    indicator: Mapped["Indicator"] = relationship(
        "Indicator", foreign_keys=[indicator_id]
    )

    def __repr__(self):
        return f"<IndicatorVersion(indicator_id={self.indicator_id}, version={self.version})>"


class IndicatorPurchase(Base, TimestampMixin):
    """Model for tracking indicator purchases"""

    __tablename__ = "indicator_purchases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    indicator_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("indicators.id"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    # Purchase details
    price_paid: Mapped[float] = mapped_column(Float, nullable=False)
    platform_fee: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # 30% to platform
    developer_payout: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # 70% to developer

    # Version purchased
    version_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("indicator_versions.id"), nullable=False
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20), default="completed", nullable=False
    )  # pending, completed, refunded

    # Relationships
    indicator: Mapped["Indicator"] = relationship(
        "Indicator", foreign_keys=[indicator_id]
    )
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    version: Mapped["IndicatorVersion"] = relationship(
        "IndicatorVersion", foreign_keys=[version_id]
    )

    def __repr__(self):
        return f"<IndicatorPurchase(indicator_id={self.indicator_id}, user_id={self.user_id})>"


class IndicatorRating(Base, TimestampMixin):
    """Model for user ratings of indicators"""

    __tablename__ = "indicator_ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    indicator_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("indicators.id"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    # Rating (1-5 stars)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    indicator: Mapped["Indicator"] = relationship(
        "Indicator", foreign_keys=[indicator_id]
    )
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return (
            f"<IndicatorRating(indicator_id={self.indicator_id}, rating={self.rating})>"
        )
