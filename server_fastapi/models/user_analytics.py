"""
User Analytics Models
Tracks user behavior, feature usage, conversion funnels, and user journeys
"""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class UserEvent(Base, TimestampMixin):
    """User behavior event tracking"""

    __tablename__ = "user_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )  # Nullable for anonymous events
    session_id = Column(String(100), nullable=True, index=True)  # Session identifier

    # Event details
    event_type = Column(
        String(100), nullable=False, index=True
    )  # page_view, click, form_submit, etc.
    event_name = Column(String(200), nullable=False, index=True)  # Specific event name
    event_category = Column(
        String(100), nullable=True, index=True
    )  # navigation, interaction, conversion, etc.

    # Event data
    properties = Column(JSON, nullable=True)  # Additional event properties
    page_url = Column(String(500), nullable=True)
    page_title = Column(String(200), nullable=True)
    referrer = Column(String(500), nullable=True)

    # User context
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    device_type = Column(String(50), nullable=True)  # desktop, mobile, tablet
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)

    # Timing
    duration_ms = Column(Integer, nullable=True)  # Event duration in milliseconds

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_user_events_user_time", "user_id", "created_at"),
        Index("idx_user_events_type_time", "event_type", "created_at"),
        Index("idx_user_events_session", "session_id", "created_at"),
    )


class FeatureUsage(Base, TimestampMixin):
    """Feature usage tracking"""

    __tablename__ = "feature_usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    feature_name = Column(String(100), nullable=False, index=True)
    feature_category = Column(String(100), nullable=True, index=True)

    # Usage details
    action = Column(String(100), nullable=False)  # opened, used, completed, etc.
    duration_seconds = Column(Integer, nullable=True)  # How long feature was used
    success = Column(Boolean, default=True)  # Whether action was successful

    # Context
    properties = Column(JSON, nullable=True)  # Additional usage properties
    error_message = Column(Text, nullable=True)  # Error if action failed

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index(
            "idx_feature_usage_user_feature", "user_id", "feature_name", "created_at"
        ),
        Index("idx_feature_usage_feature_time", "feature_name", "created_at"),
    )


class ConversionFunnel(Base, TimestampMixin):
    """Conversion funnel tracking"""

    __tablename__ = "conversion_funnels"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )  # Nullable for anonymous
    session_id = Column(String(100), nullable=True, index=True)

    # Funnel details
    funnel_name = Column(
        String(100), nullable=False, index=True
    )  # signup, first_trade, subscription, etc.
    stage = Column(String(100), nullable=False, index=True)  # Current stage in funnel
    stage_order = Column(Integer, nullable=False)  # Order of stage (1, 2, 3, etc.)

    # Conversion tracking
    is_completed = Column(Boolean, default=False, index=True)  # Completed entire funnel
    completed_at = Column(DateTime, nullable=True)
    dropped_at_stage = Column(
        String(100), nullable=True
    )  # Stage where user dropped off

    # Timing
    time_to_stage_seconds = Column(Integer, nullable=True)  # Time to reach this stage
    time_in_stage_seconds = Column(Integer, nullable=True)  # Time spent in this stage

    # Context
    properties = Column(JSON, nullable=True)  # Additional funnel properties
    source = Column(String(200), nullable=True)  # Traffic source

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_conversion_funnel_user", "user_id", "funnel_name", "created_at"),
        Index("idx_conversion_funnel_stage", "funnel_name", "stage", "created_at"),
    )


class UserJourney(Base, TimestampMixin):
    """User journey path tracking"""

    __tablename__ = "user_journeys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(String(100), nullable=False, index=True)

    # Journey details
    journey_type = Column(
        String(100), nullable=False, index=True
    )  # onboarding, trading, support, etc.
    step_name = Column(String(200), nullable=False)  # Current step in journey
    step_order = Column(Integer, nullable=False)  # Order of step

    # Path tracking
    previous_step = Column(String(200), nullable=True)  # Previous step
    next_step = Column(String(200), nullable=True)  # Next step
    path = Column(JSON, nullable=True)  # Full path array

    # Timing
    time_to_step_seconds = Column(Integer, nullable=True)  # Time to reach this step
    time_in_step_seconds = Column(Integer, nullable=True)  # Time spent in this step

    # Completion
    is_completed = Column(Boolean, default=False, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Context
    properties = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_user_journey_session", "session_id", "created_at"),
        Index("idx_user_journey_user_type", "user_id", "journey_type", "created_at"),
    )


class UserSatisfaction(Base, TimestampMixin):
    """User satisfaction metrics"""

    __tablename__ = "user_satisfaction"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )  # Nullable for anonymous

    # Satisfaction details
    survey_type = Column(
        String(100), nullable=False, index=True
    )  # nps, csat, ces, etc.
    score = Column(Integer, nullable=False)  # 0-10 for NPS, 1-5 for CSAT, etc.
    question = Column(String(500), nullable=True)  # Survey question
    response = Column(Text, nullable=True)  # User response/feedback

    # Context
    context = Column(String(200), nullable=True)  # What triggered the survey
    properties = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index(
            "idx_user_satisfaction_user_type", "user_id", "survey_type", "created_at"
        ),
        Index("idx_user_satisfaction_score", "survey_type", "score", "created_at"),
    )
