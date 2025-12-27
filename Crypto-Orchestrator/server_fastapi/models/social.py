"""
Social & Community Models
Trading strategies, social feed, achievements, and community challenges
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, JSON, DateTime, Float, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base, TimestampMixin


class StrategyVisibility(enum.Enum):
    """Strategy visibility levels"""
    PRIVATE = "private"
    PUBLIC = "public"
    UNLISTED = "unlisted"  # Accessible via link only


class SharedStrategy(Base, TimestampMixin):
    """Shared trading strategy"""
    __tablename__ = "shared_strategies"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Strategy details
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    strategy_config = Column(JSON, nullable=False)  # Full strategy configuration
    
    # Visibility and sharing
    visibility = Column(SQLEnum(StrategyVisibility), default=StrategyVisibility.PUBLIC, nullable=False)
    share_token = Column(String(100), unique=True, nullable=True, index=True)  # For unlisted sharing
    
    # Statistics
    view_count = Column(Integer, default=0, nullable=False)
    like_count = Column(Integer, default=0, nullable=False)
    copy_count = Column(Integer, default=0, nullable=False)  # Times strategy was copied
    
    # Metadata
    tags = Column(JSON, nullable=True)  # Array of tags
    category = Column(String(100), nullable=True, index=True)
    is_featured = Column(Boolean, default=False, index=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    likes = relationship("StrategyLike", back_populates="strategy", cascade="all, delete-orphan")
    comments = relationship("StrategyComment", back_populates="strategy", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_shared_strategies_user", "user_id", "created_at"),
        Index("idx_shared_strategies_visibility", "visibility", "created_at"),
        Index("idx_shared_strategies_featured", "is_featured", "created_at"),
    )


class StrategyLike(Base, TimestampMixin):
    """Strategy likes"""
    __tablename__ = "strategy_likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    strategy_id = Column(Integer, ForeignKey("shared_strategies.id"), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    strategy = relationship("SharedStrategy", foreign_keys=[strategy_id])

    __table_args__ = (
        Index("idx_strategy_likes_unique", "user_id", "strategy_id", unique=True),
    )


class StrategyComment(Base, TimestampMixin):
    """Strategy comments"""
    __tablename__ = "strategy_comments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    strategy_id = Column(Integer, ForeignKey("shared_strategies.id"), nullable=False, index=True)
    
    # Comment content
    content = Column(Text, nullable=False)
    parent_comment_id = Column(Integer, ForeignKey("strategy_comments.id"), nullable=True)  # For replies
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    strategy = relationship("SharedStrategy", foreign_keys=[strategy_id])
    parent_comment = relationship("StrategyComment", remote_side=[id], backref="replies")

    __table_args__ = (
        Index("idx_strategy_comments_strategy", "strategy_id", "created_at"),
        Index("idx_strategy_comments_user", "user_id", "created_at"),
    )


class SocialFeedEvent(Base, TimestampMixin):
    """Social feed events"""
    __tablename__ = "social_feed_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Event details
    event_type = Column(String(100), nullable=False, index=True)  # trade_executed, strategy_shared, achievement_earned, etc.
    event_data = Column(JSON, nullable=False)  # Event-specific data
    
    # Visibility
    is_public = Column(Boolean, default=True, index=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_social_feed_user_time", "user_id", "created_at"),
        Index("idx_social_feed_type_time", "event_type", "created_at"),
        Index("idx_social_feed_public", "is_public", "created_at"),
    )


class UserProfile(Base, TimestampMixin):
    """Public user profile"""
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    
    # Profile information
    display_name = Column(String(200), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    
    # Social links
    website_url = Column(String(500), nullable=True)
    twitter_handle = Column(String(100), nullable=True)
    telegram_handle = Column(String(100), nullable=True)
    
    # Trading statistics (cached)
    total_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    followers_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    
    # Settings
    is_public = Column(Boolean, default=True, index=True)
    show_trading_stats = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], uselist=False)

    __table_args__ = (
        Index("idx_user_profiles_public", "is_public", "created_at"),
    )


class Achievement(Base, TimestampMixin):
    """Achievement definitions"""
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    
    # Achievement details
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    icon_url = Column(String(500), nullable=True)
    category = Column(String(100), nullable=True, index=True)  # trading, social, milestone, etc.
    
    # Requirements
    requirement_type = Column(String(100), nullable=False)  # trade_count, profit_amount, win_streak, etc.
    requirement_value = Column(JSON, nullable=False)  # Requirement parameters
    
    # Metadata
    rarity = Column(String(50), default="common", index=True)  # common, rare, epic, legendary
    points = Column(Integer, default=0)  # Points awarded

    __table_args__ = (
        Index("idx_achievements_category", "category", "rarity"),
    )


class UserAchievement(Base, TimestampMixin):
    """User achievements (earned)"""
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False, index=True)
    
    # Achievement progress (for multi-stage achievements)
    progress = Column(JSON, nullable=True)
    is_completed = Column(Boolean, default=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    achievement = relationship("Achievement", foreign_keys=[achievement_id])

    __table_args__ = (
        Index("idx_user_achievements_user", "user_id", "is_completed", "completed_at"),
        Index("idx_user_achievements_unique", "user_id", "achievement_id", unique=True),
    )


class CommunityChallenge(Base, TimestampMixin):
    """Community trading challenges"""
    __tablename__ = "community_challenges"

    id = Column(Integer, primary_key=True, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Challenge details
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    challenge_type = Column(String(100), nullable=False, index=True)  # profit_contest, win_rate_contest, etc.
    
    # Rules
    rules = Column(JSON, nullable=False)  # Challenge-specific rules
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False, index=True)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_featured = Column(Boolean, default=False, index=True)
    
    # Prizes
    prizes = Column(JSON, nullable=True)  # Prize structure
    
    # Statistics
    participant_count = Column(Integer, default=0)
    
    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    participants = relationship("ChallengeParticipant", back_populates="challenge", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_challenges_active", "is_active", "start_date", "end_date"),
        Index("idx_challenges_featured", "is_featured", "start_date"),
    )


class ChallengeParticipant(Base, TimestampMixin):
    """Challenge participants"""
    __tablename__ = "challenge_participants"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    challenge_id = Column(Integer, ForeignKey("community_challenges.id"), nullable=False, index=True)
    
    # Performance metrics
    score = Column(Float, default=0.0, index=True)
    rank = Column(Integer, nullable=True, index=True)
    metrics = Column(JSON, nullable=True)  # Challenge-specific metrics
    
    # Status
    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    challenge = relationship("CommunityChallenge", foreign_keys=[challenge_id])

    __table_args__ = (
        Index("idx_challenge_participants_challenge", "challenge_id", "score", "rank"),
        Index("idx_challenge_participants_user", "user_id", "challenge_id", unique=True),
    )
