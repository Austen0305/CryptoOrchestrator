"""
Social Recovery Models
Database models for social recovery mechanisms in institutional wallets
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Text,
    JSON,
    Enum as SQLEnum,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User
    from .institutional_wallet import InstitutionalWallet


class GuardianStatus(str, Enum):
    """Guardian status"""
    PENDING = "pending"  # Invitation sent, not yet accepted
    ACTIVE = "active"  # Guardian is active
    INACTIVE = "inactive"  # Guardian deactivated
    REJECTED = "rejected"  # Guardian rejected invitation


class RecoveryRequestStatus(str, Enum):
    """Recovery request status"""
    PENDING = "pending"  # Waiting for approvals
    APPROVED = "approved"  # Required approvals met
    REJECTED = "rejected"  # Rejected by guardian
    COMPLETED = "completed"  # Recovery executed
    EXPIRED = "expired"  # Time-lock expired or request expired
    CANCELLED = "cancelled"  # Cancelled by requester


class SocialRecoveryGuardian(Base, TimestampMixin):
    """
    Model for social recovery guardians
    Guardians can approve recovery requests for institutional wallets
    """
    
    __tablename__ = "social_recovery_guardians"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    wallet_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("institutional_wallets.id"), nullable=False, index=True
    )
    guardian_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    
    # Guardian details
    email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )  # Guardian email (if not a platform user)
    phone: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # Guardian phone (for SMS verification)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20), default=GuardianStatus.PENDING.value, nullable=False, index=True
    )
    
    # Verification
    verification_token: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )  # Token for email/SMS verification
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    
    # Metadata
    added_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )  # User who added this guardian
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Optional notes about guardian
    
    # Relationships
    wallet: Mapped["InstitutionalWallet"] = relationship(
        "InstitutionalWallet", back_populates="guardians"
    )
    guardian_user: Mapped["User"] = relationship(
        "User", foreign_keys=[guardian_user_id]
    )
    
    __table_args__ = (
        Index("idx_wallet_guardian", "wallet_id", "guardian_user_id", unique=True),
    )
    
    def __repr__(self):
        return f"<SocialRecoveryGuardian(id={self.id}, wallet_id={self.wallet_id}, guardian_user_id={self.guardian_user_id})>"


class RecoveryRequest(Base, TimestampMixin):
    """
    Model for social recovery requests
    Tracks recovery requests and their approval status
    """
    
    __tablename__ = "recovery_requests"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    wallet_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("institutional_wallets.id"), nullable=False, index=True
    )
    requester_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    
    # Recovery details
    reason: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # Reason for recovery request
    status: Mapped[str] = mapped_column(
        String(20), default=RecoveryRequestStatus.PENDING.value, nullable=False, index=True
    )
    
    # Approval requirements
    required_approvals: Mapped[int] = mapped_column(
        Integer, nullable=False, default=3
    )  # M in M-of-N (minimum guardians needed)
    current_approvals: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )  # Current number of approvals
    
    # Time-locked recovery
    time_lock_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=7
    )  # Days to wait before recovery can execute (7-30 days)
    unlock_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, index=True
    )  # When recovery can be executed (created_at + time_lock_days)
    
    # Expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, index=True
    )  # Request expiration (if not approved in time)
    
    # Completion
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    executed_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    
    # Metadata (renamed from 'metadata' to avoid SQLAlchemy reserved name conflict)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # Additional metadata
    
    # Relationships
    wallet: Mapped["InstitutionalWallet"] = relationship(
        "InstitutionalWallet", back_populates="recovery_requests"
    )
    requester: Mapped["User"] = relationship(
        "User", foreign_keys=[requester_id]
    )
    approvals: Mapped[List["RecoveryApproval"]] = relationship(
        "RecoveryApproval",
        back_populates="recovery_request",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<RecoveryRequest(id={self.id}, wallet_id={self.wallet_id}, status={self.status})>"


class RecoveryApproval(Base, TimestampMixin):
    """
    Model for recovery request approvals
    Tracks which guardians have approved recovery requests
    """
    
    __tablename__ = "recovery_approvals"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recovery_request_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("recovery_requests.id"), nullable=False, index=True
    )
    guardian_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("social_recovery_guardians.id"), nullable=False, index=True
    )
    approver_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )  # User who approved (may be guardian or guardian's user)
    
    # Approval details
    approved_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    signature: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Cryptographic signature if needed
    
    # Verification
    verification_method: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # "email", "sms", "2fa", "platform"
    verification_code: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # Verification code used
    
    # Metadata
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    
    # Relationships
    recovery_request: Mapped["RecoveryRequest"] = relationship(
        "RecoveryRequest", back_populates="approvals"
    )
    guardian: Mapped["SocialRecoveryGuardian"] = relationship(
        "SocialRecoveryGuardian"
    )
    approver: Mapped["User"] = relationship(
        "User", foreign_keys=[approver_id]
    )
    
    __table_args__ = (
        Index("idx_recovery_guardian", "recovery_request_id", "guardian_id", unique=True),
    )
    
    def __repr__(self):
        return f"<RecoveryApproval(id={self.id}, recovery_request_id={self.recovery_request_id}, guardian_id={self.guardian_id})>"
