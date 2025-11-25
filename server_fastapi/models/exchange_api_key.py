"""
Exchange API Key Model
Stores encrypted exchange API keys for users
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .base import User


class ExchangeAPIKey(Base, TimestampMixin):
    """Exchange API Key model with encryption"""

    __tablename__ = "exchange_api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    exchange = Column(String(50), nullable=False, index=True)  # e.g., 'binance', 'kraken'
    
    # Encrypted fields (encrypted at application level)
    api_key_encrypted = Column(Text, nullable=False)  # Encrypted API key
    api_secret_encrypted = Column(Text, nullable=False)  # Encrypted API secret
    passphrase_encrypted = Column(Text, nullable=True)  # Encrypted passphrase (for some exchanges)
    
    # Metadata
    label = Column(String(100), nullable=True)  # User-friendly label
    permissions = Column(String(255), nullable=True)  # Comma-separated permissions (e.g., "read,write,trade")
    is_active = Column(Boolean, default=True, nullable=False)
    is_testnet = Column(Boolean, default=False, nullable=False)  # For testnet/sandbox keys
    
    # Validation
    is_validated = Column(Boolean, default=False, nullable=False)  # Whether key has been validated
    validated_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    
    # Security
    ip_whitelist = Column(Text, nullable=True)  # Comma-separated IP addresses
    rate_limit_per_minute = Column(String(20), nullable=True)  # Rate limit override
    
    # Relationships
    user = relationship("User", back_populates="exchange_api_keys")

    def __repr__(self):
        return f"<ExchangeAPIKey(id={self.id}, user_id={self.user_id}, exchange={self.exchange}, is_active={self.is_active})>"

