"""
Institutional Wallet Models
Support for multi-signature wallets, team access, and institutional features
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
    Text,
    JSON,
    Enum as SQLEnum,
    Index,
    Table,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User
    from .wallet import WalletTransaction


# Association table for wallet signers
wallet_signer_association = Table(
    "wallet_signer_associations",
    Base.metadata,
    Column("wallet_id", Integer, ForeignKey("institutional_wallets.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role", String(50), nullable=False),  # "owner", "signer", "viewer"
    Column("created_at", DateTime, default=datetime.utcnow),
    Index("idx_wallet_signer", "wallet_id", "user_id"),
    extend_existing=True,  # Allow redefinition if table already exists
)


class WalletType(str, Enum):
    """Institutional wallet types"""
    MULTISIG = "multisig"  # Multi-signature wallet
    TIMELOCK = "timelock"  # Time-locked wallet
    TREASURY = "treasury"  # Treasury management wallet
    CUSTODIAL = "custodial"  # Standard custodial wallet


class MultisigType(str, Enum):
    """Multi-signature configuration types"""
    TWO_OF_THREE = "2_of_3"
    THREE_OF_FIVE = "3_of_5"
    CUSTOM = "custom"  # Custom M-of-N configuration


class WalletStatus(str, Enum):
    """Wallet status"""
    ACTIVE = "active"
    PENDING = "pending"  # Waiting for signers
    LOCKED = "locked"  # Time-locked
    FROZEN = "frozen"  # Admin frozen
    ARCHIVED = "archived"


class SignerRole(str, Enum):
    """Roles for wallet signers"""
    OWNER = "owner"  # Full control
    SIGNER = "signer"  # Can sign transactions
    VIEWER = "viewer"  # Read-only access
    ADMIN = "admin"  # Administrative access


class InstitutionalWallet(Base, TimestampMixin):
    """
    Model for institutional wallets with multi-signature support
    """
    
    __tablename__ = "institutional_wallets"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )  # Primary owner
    
    # Wallet configuration
    wallet_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # WalletType enum value
    wallet_address: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )  # On-chain wallet address (for multisig)
    chain_id: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, index=True
    )  # Blockchain ID
    
    # Multi-signature configuration
    multisig_type: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # MultisigType enum value (if wallet_type is MULTISIG)
    required_signatures: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )  # M in M-of-N
    total_signers: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )  # N in M-of-N
    
    # Time-lock configuration
    unlock_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )  # When time-locked wallet unlocks
    lock_duration_days: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Lock duration in days
    
    # Status and metadata
    status: Mapped[str] = mapped_column(
        String(20), default=WalletStatus.PENDING.value, nullable=False, index=True
    )
    label: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # User-friendly label
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    
    # Configuration
    config: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # Additional configuration (hardware wallet IDs, TSS params, etc.)
    
    # Balance tracking (cached)
    balance: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # {token_address: balance_string}
    last_balance_update: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    
    # Relationships
    owner: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    signers: Mapped[List["User"]] = relationship(
        "User",
        secondary=wallet_signer_association,
        back_populates="institutional_wallets"
    )
    transactions: Mapped[List["InstitutionalWalletTransaction"]] = relationship(
        "InstitutionalWalletTransaction",
        back_populates="wallet",
        cascade="all, delete-orphan"
    )
    pending_transactions: Mapped[List["PendingTransaction"]] = relationship(
        "PendingTransaction",
        back_populates="wallet",
        cascade="all, delete-orphan"
    )
    guardians: Mapped[List["SocialRecoveryGuardian"]] = relationship(
        "SocialRecoveryGuardian",
        back_populates="wallet",
        cascade="all, delete-orphan"
    )
    recovery_requests: Mapped[List["RecoveryRequest"]] = relationship(
        "RecoveryRequest",
        back_populates="wallet",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<InstitutionalWallet(id={self.id}, type={self.wallet_type}, address={self.wallet_address})>"


class PendingTransaction(Base, TimestampMixin):
    """
    Model for pending transactions requiring signatures
    """
    
    __tablename__ = "pending_transactions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    wallet_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("institutional_wallets.id"), nullable=False, index=True
    )
    
    # Transaction details
    transaction_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "withdrawal", "transfer", "approval", etc.
    to_address: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    amount: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    currency: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True
    )
    chain_id: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    
    # Transaction data
    transaction_data: Mapped[dict] = mapped_column(
        JSON, nullable=False
    )  # Full transaction data (to, value, data, gas, etc.)
    
    # Signature tracking
    signatures: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict
    )  # {user_id: signature_data}
    required_signatures: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )  # "pending", "signed", "executed", "rejected", "expired"
    
    # Expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )  # Transaction expiration time
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    extra_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # Renamed from 'metadata' to avoid SQLAlchemy reserved name conflict
    
    # Relationships
    wallet: Mapped["InstitutionalWallet"] = relationship(
        "InstitutionalWallet", back_populates="pending_transactions"
    )
    
    def __repr__(self):
        return f"<PendingTransaction(id={self.id}, wallet_id={self.wallet_id}, status={self.status})>"


class InstitutionalWalletTransaction(Base, TimestampMixin):
    """
    Model for executed institutional wallet transactions
    """
    
    __tablename__ = "institutional_wallet_transactions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    wallet_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("institutional_wallets.id"), nullable=False, index=True
    )
    pending_transaction_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("pending_transactions.id"), nullable=True
    )
    
    # Transaction details
    transaction_hash: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )  # Blockchain transaction hash
    transaction_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    from_address: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    to_address: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    amount: Mapped[float] = mapped_column(
        Float, nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(10), nullable=False
    )
    chain_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True
    )
    
    # Execution details
    executed_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )  # User who executed the transaction
    signatures: Mapped[dict] = mapped_column(
        JSON, nullable=False
    )  # All signatures that were collected
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # "pending", "confirmed", "failed"
    block_number: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    confirmations: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    
    # Gas information
    gas_used: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    gas_price: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    
    # Metadata (renamed from 'metadata' to avoid SQLAlchemy reserved name conflict)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )
    
    # Relationships
    wallet: Mapped["InstitutionalWallet"] = relationship(
        "InstitutionalWallet", back_populates="transactions"
    )
    
    def __repr__(self):
        return f"<InstitutionalWalletTransaction(id={self.id}, hash={self.transaction_hash})>"


class WalletAccessLog(Base, TimestampMixin):
    """
    Audit log for wallet access and operations
    """
    
    __tablename__ = "wallet_access_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    wallet_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("institutional_wallets.id"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    
    # Action details
    action: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # "view", "sign", "execute", "add_signer", "remove_signer", etc.
    resource_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "wallet", "transaction", "signer", etc.
    resource_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    
    # Details
    details: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # Additional action details
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    
    # Status
    success: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    
    def __repr__(self):
        return f"<WalletAccessLog(id={self.id}, action={self.action}, success={self.success})>"
