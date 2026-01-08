"""
Withdrawal Address Whitelist Model
Stores whitelisted withdrawal addresses with 24-hour cooldown period
"""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User


class WithdrawalAddressWhitelist(Base, TimestampMixin):
    """Model for storing whitelisted withdrawal addresses"""

    __tablename__ = "withdrawal_address_whitelist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    # Address details
    address: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # Withdrawal address (checksummed)
    chain_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True
    )  # Blockchain chain ID

    # Whitelist status
    is_whitelisted: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )  # When address was added to whitelist

    # Cooldown period (24 hours from added_at)
    cooldown_until: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )  # When cooldown expires (added_at + 24 hours)

    # Verification
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )  # Whether address has been verified
    verification_method: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # 'email', '2fa', 'signature', etc.

    # Metadata
    label: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # User-friendly label
    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # User notes about this address

    # Relationships
    user: Mapped["User"] = relationship("User")

    # Unique constraint: one address per user per chain
    __table_args__ = (
        UniqueConstraint(
            "user_id", "address", "chain_id", name="uq_user_address_chain"
        ),
        Index("ix_withdrawal_address", "address"),
        Index("ix_withdrawal_chain", "chain_id"),
        Index("ix_withdrawal_cooldown", "cooldown_until"),
    )

    def is_in_cooldown(self) -> bool:
        """Check if address is still in cooldown period"""
        if not self.cooldown_until:
            # Set cooldown if not set (24 hours from added_at)
            self.cooldown_until = self.added_at + timedelta(hours=24)

        return datetime.utcnow() < self.cooldown_until

    def __repr__(self):
        return f"<WithdrawalAddressWhitelist(id={self.id}, user_id={self.user_id}, address={self.address[:10]}..., chain_id={self.chain_id}, in_cooldown={self.is_in_cooldown()})>"
