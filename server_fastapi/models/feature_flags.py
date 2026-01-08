"""
Feature Flags & A/B Testing Models
Feature flag management and A/B testing framework
"""

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class FlagStatus(enum.Enum):
    """Feature flag status"""

    DISABLED = "disabled"
    ENABLED = "enabled"
    ROLLING_OUT = "rolling_out"  # Gradual rollout
    DEPRECATED = "deprecated"


class FeatureFlag(Base, TimestampMixin):
    """Feature flag definition"""

    __tablename__ = "feature_flags"

    id = Column(Integer, primary_key=True, index=True)

    # Flag details
    flag_key = Column(String(100), unique=True, nullable=False, index=True)
    flag_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Status and rollout
    status = Column(
        SQLEnum(FlagStatus), default=FlagStatus.DISABLED, nullable=False, index=True
    )
    rollout_percentage = Column(Integer, default=0, nullable=False)  # 0-100

    # Targeting
    target_users = Column(JSON, nullable=True)  # List of user IDs
    target_segments = Column(JSON, nullable=True)  # User segments
    target_conditions = Column(JSON, nullable=True)  # Custom conditions

    # Variants (for A/B testing)
    variants = Column(JSON, nullable=True)  # Variant definitions

    # Metadata
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    tags = Column(JSON, nullable=True)

    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    experiments = relationship(
        "ABTestExperiment", back_populates="feature_flag", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_feature_flags_status", "status", "created_at"),)


class FlagEvaluation(Base, TimestampMixin):
    """Feature flag evaluation log"""

    __tablename__ = "flag_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    flag_id = Column(
        Integer, ForeignKey("feature_flags.id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Evaluation result
    enabled = Column(Boolean, nullable=False, index=True)
    variant = Column(String(100), nullable=True)  # Variant assigned

    # Context
    context = Column(JSON, nullable=True)  # Evaluation context

    # Relationships
    flag = relationship("FeatureFlag", foreign_keys=[flag_id])
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_flag_evaluations_flag_user", "flag_id", "user_id", "created_at"),
        Index("idx_flag_evaluations_enabled", "enabled", "created_at"),
    )


class ABTestExperiment(Base, TimestampMixin):
    """A/B test experiment"""

    __tablename__ = "ab_test_experiments"

    id = Column(Integer, primary_key=True, index=True)
    flag_id = Column(
        Integer, ForeignKey("feature_flags.id"), nullable=False, index=True
    )

    # Experiment details
    experiment_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Variants
    variants = Column(JSON, nullable=False)  # Variant definitions with traffic split

    # Status
    is_active = Column(Boolean, default=True, index=True)
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=True, index=True)

    # Results
    primary_metric = Column(
        String(100), nullable=False
    )  # Conversion rate, revenue, etc.
    results = Column(JSON, nullable=True)  # Experiment results

    # Relationships
    feature_flag = relationship("FeatureFlag", foreign_keys=[flag_id])
    assignments = relationship(
        "ExperimentAssignment",
        back_populates="experiment",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_experiments_active", "is_active", "start_date", "end_date"),
    )


class ExperimentAssignment(Base, TimestampMixin):
    """Experiment variant assignment"""

    __tablename__ = "experiment_assignments"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(
        Integer, ForeignKey("ab_test_experiments.id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Assignment
    variant = Column(String(100), nullable=False, index=True)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Conversion tracking
    converted = Column(Boolean, default=False, index=True)
    converted_at = Column(DateTime, nullable=True)
    conversion_value = Column(Float, nullable=True)  # For revenue-based experiments

    # Relationships
    experiment = relationship("ABTestExperiment", foreign_keys=[experiment_id])
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index(
            "idx_experiment_assignments_experiment_user",
            "experiment_id",
            "user_id",
            unique=True,
        ),
        Index(
            "idx_experiment_assignments_variant", "variant", "converted", "created_at"
        ),
    )
