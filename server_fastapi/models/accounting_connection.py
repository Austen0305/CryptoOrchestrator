"""
Accounting Connection Models
Database models for storing OAuth credentials and connections to accounting systems
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User


class AccountingSystem(str, Enum):
    """Supported accounting systems"""

    QUICKBOOKS = "quickbooks"
    XERO = "xero"


class ConnectionStatus(str, Enum):
    """Connection status"""

    PENDING = "pending"  # OAuth flow in progress
    CONNECTED = "connected"  # Successfully connected
    DISCONNECTED = "disconnected"  # User disconnected
    ERROR = "error"  # Connection error
    EXPIRED = "expired"  # Token expired


class SyncFrequency(str, Enum):
    """Sync frequency"""

    MANUAL = "manual"  # Manual sync only
    DAILY = "daily"  # Daily sync
    WEEKLY = "weekly"  # Weekly sync
    MONTHLY = "monthly"  # Monthly sync


class AccountingConnection(Base, TimestampMixin):
    """
    Model for accounting system connections
    Stores OAuth credentials and connection metadata
    """

    __tablename__ = "accounting_connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    # Connection details
    system: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # AccountingSystem enum value
    status: Mapped[str] = mapped_column(
        String(20), default=ConnectionStatus.PENDING.value, nullable=False, index=True
    )

    # OAuth credentials (encrypted in production)
    access_token: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # Encrypted access token
    refresh_token: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Encrypted refresh token
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # System-specific IDs
    realm_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # QuickBooks realm ID
    tenant_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # Xero tenant ID

    # Sync configuration
    sync_frequency: Mapped[str] = mapped_column(
        String(20), default=SyncFrequency.MANUAL.value, nullable=False
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Account mappings (JSON)
    account_mappings: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # {crypto_asset: account_code, capital_gains: account_code, ...}

    # Metadata
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_metadata: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, name="metadata"
    )  # Using "metadata" as column name but extra_metadata as attribute to avoid SQLAlchemy conflict

    # Relationships
    user: Mapped["User"] = relationship("User")

    __table_args__ = (Index("idx_user_system", "user_id", "system", unique=True),)

    def __repr__(self):
        return f"<AccountingConnection(id={self.id}, user_id={self.user_id}, system={self.system}, status={self.status})>"


class AccountingSyncLog(Base, TimestampMixin):
    """
    Model for accounting sync logs
    Tracks sync history and results
    """

    __tablename__ = "accounting_sync_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    connection_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("accounting_connections.id"), nullable=False, index=True
    )

    # Sync details
    sync_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "manual", "scheduled", "retry"
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # "success", "failed", "partial"

    # Results
    transactions_synced: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    transactions_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(
        JSON,
        nullable=True,  # Using JSON to store float (SQLite compatibility)
    )

    # Error details
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Metadata
    extra_metadata: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, name="metadata"
    )  # Using "metadata" as column name but extra_metadata as attribute to avoid SQLAlchemy conflict

    # Relationships
    connection: Mapped["AccountingConnection"] = relationship("AccountingConnection")

    def __repr__(self):
        return f"<AccountingSyncLog(id={self.id}, connection_id={self.connection_id}, status={self.status})>"
