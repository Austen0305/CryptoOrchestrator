"""
Audit Log Models
Immutable audit trail for compliance and security
"""

import hashlib

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class AuditLog(Base, TimestampMixin):
    """Immutable audit log entry"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Event details
    event_type = Column(String(100), nullable=False, index=True)
    event_category = Column(
        String(50), nullable=False, index=True
    )  # user_action, system_event, data_change, security, trading
    event_name = Column(String(200), nullable=False)

    # Actor information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True, index=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)

    # Event data
    event_data = Column(JSON, nullable=False)  # Full event details
    resource_type = Column(
        String(100), nullable=True, index=True
    )  # trade, user, bot, etc.
    resource_id = Column(String(100), nullable=True, index=True)

    # Integrity protection
    integrity_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash
    previous_hash = Column(String(64), nullable=True)  # Hash chain for tamper detection

    # Compliance metadata
    retention_until = Column(
        DateTime, nullable=True, index=True
    )  # When this log can be archived
    compliance_flags = Column(JSON, nullable=True)  # GDPR, SOX, MiFID II, etc.

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index(
            "idx_audit_logs_event_type_category",
            "event_type",
            "event_category",
            "created_at",
        ),
        Index("idx_audit_logs_user_timestamp", "user_id", "created_at"),
        Index("idx_audit_logs_resource", "resource_type", "resource_id", "created_at"),
        Index("idx_audit_logs_integrity", "integrity_hash", "previous_hash"),
    )

    def calculate_integrity_hash(self) -> str:
        """Calculate integrity hash for this audit log entry"""
        hash_data = {
            "id": self.id,
            "event_type": self.event_type,
            "event_category": self.event_category,
            "event_name": self.event_name,
            "user_id": self.user_id,
            "event_data": self.event_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "previous_hash": self.previous_hash,
        }
        hash_string = str(sorted(hash_data.items()))
        return hashlib.sha256(hash_string.encode()).hexdigest()
