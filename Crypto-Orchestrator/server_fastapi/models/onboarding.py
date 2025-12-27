"""
Onboarding Models
Database models for user onboarding progress and feature unlocking
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Text,
    JSON,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User


class OnboardingStep(str):
    """Onboarding step identifiers"""
    WELCOME = "welcome"
    WALLET_SETUP = "wallet_setup"
    FIRST_DEPOSIT = "first_deposit"
    FIRST_TRADE = "first_trade"
    BOT_CREATION = "bot_creation"
    MARKETPLACE_EXPLORE = "marketplace_explore"
    ADVANCED_FEATURES = "advanced_features"


class OnboardingProgress(Base, TimestampMixin):
    """
    Model for tracking user onboarding progress
    """
    
    __tablename__ = "onboarding_progress"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, unique=True
    )
    
    # Progress tracking
    current_step: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # Current step identifier
    completed_steps: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict
    )  # {step_id: completed_at}
    skipped_steps: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict
    )  # {step_id: skipped_at}
    
    # Progress metrics
    progress_percentage: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )  # 0-100
    total_steps: Mapped[int] = mapped_column(
        Integer, default=7, nullable=False
    )  # Total number of steps
    
    # Completion
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    
    # Metadata (renamed from 'metadata' to avoid SQLAlchemy reserved name conflict)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # Additional progress data
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    
    def __repr__(self):
        return f"<OnboardingProgress(user_id={self.user_id}, progress={self.progress_percentage}%)>"


class UserAchievement(Base, TimestampMixin):
    """
    Model for user achievements and milestones
    """
    
    __tablename__ = "user_achievements"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    
    # Achievement details
    achievement_id: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # Achievement identifier
    achievement_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    achievement_description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    
    # Progress tracking
    progress: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )  # Progress towards achievement (0-100)
    max_progress: Mapped[int] = mapped_column(
        Integer, default=100, nullable=False
    )
    
    # Unlock status
    unlocked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, index=True
    )
    is_unlocked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    
    # Metadata (renamed from 'metadata' to avoid SQLAlchemy reserved name conflict)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    
    __table_args__ = (
        Index("idx_user_achievement", "user_id", "achievement_id", unique=True),
    )
    
    def __repr__(self):
        return f"<UserAchievement(user_id={self.user_id}, achievement_id={self.achievement_id}, unlocked={self.is_unlocked})>"


