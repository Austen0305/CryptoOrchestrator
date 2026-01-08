"""
User Wallet Model - Blockchain wallet addresses
Stores user's blockchain wallet addresses for custodial wallets
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User


class UserWallet(Base, TimestampMixin):
    """Model for storing user's blockchain wallet addresses"""

    __tablename__ = "user_wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), index=True, nullable=False
    )

    # Wallet details
    wallet_address: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # Ethereum address (checksummed)
    chain_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True
    )  # Blockchain ID
    wallet_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="custodial", index=True
    )  # 'custodial' (platform-managed) or 'external' (user's own wallet)

    # Balance tracking (cached, updated periodically)
    balance: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # {token_address: balance_string} - cached balances
    last_balance_update: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )  # Whether user has verified ownership

    # Metadata
    label: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # User-friendly label
    wallet_metadata: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # Additional metadata

    # Relationships
    user: Mapped["User"] = relationship("User")

    # Unique constraint: one wallet address per user per chain
    __table_args__ = (
        UniqueConstraint(
            "user_id", "wallet_address", "chain_id", name="uq_user_wallet_chain"
        ),
        Index("ix_user_wallet_address", "wallet_address"),
        Index("ix_user_wallet_chain", "chain_id"),
    )

    def __repr__(self):
        return f"<UserWallet(id={self.id}, user_id={self.user_id}, address={self.wallet_address[:10]}..., chain_id={self.chain_id})>"
