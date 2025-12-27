"""
API Key Models
API key management for external integrations
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, JSON, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import secrets

from .base import Base, TimestampMixin


class APIKey(Base, TimestampMixin):
    """API key definition"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Key details
    key_name = Column(String(200), nullable=False)
    key_prefix = Column(String(20), nullable=False)  # First few chars for identification
    key_hash = Column(String(64), nullable=False, unique=True, index=True)  # SHA-256 hash of full key
    
    # Permissions
    permissions = Column(JSON, nullable=False)  # List of allowed endpoints/methods
    rate_limit = Column(Integer, default=1000)  # Requests per hour
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    last_used_at = Column(DateTime, nullable=True)
    
    # Usage tracking
    request_count = Column(Integer, default=0)
    last_ip_address = Column(String(45), nullable=True)
    
    # Metadata
    description = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    usage_logs = relationship("APIKeyUsage", back_populates="api_key", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_api_keys_user_active", "user_id", "is_active", "created_at"),
        Index("idx_api_keys_expires", "expires_at", "is_active"),
    )
    
    @staticmethod
    def generate_key() -> tuple[str, str]:
        """Generate a new API key"""
        # Generate secure random key
        key = f"co_{secrets.token_urlsafe(32)}"
        key_prefix = key[:12]  # First 12 chars for identification
        return key, key_prefix


class APIKeyUsage(Base, TimestampMixin):
    """API key usage log"""
    __tablename__ = "api_key_usage"

    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False, index=True)
    
    # Request details
    endpoint = Column(String(200), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    
    # Request metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    
    # Relationships
    api_key = relationship("APIKey", foreign_keys=[api_key_id])

    __table_args__ = (
        Index("idx_api_key_usage_key_timestamp", "api_key_id", "created_at"),
        Index("idx_api_key_usage_endpoint", "endpoint", "created_at"),
    )
