"""
Wallet Nonce Model - Signature nonce tracking
Prevents replay attacks for wallet signatures
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
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


class WalletNonce(Base, TimestampMixin):
    """Model for tracking wallet signature nonces"""

    __tablename__ = "wallet_nonces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), index=True, nullable=False
    )

    # Wallet address
    wallet_address: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # Ethereum address (checksummed)

    # Nonce details
    nonce: Mapped[int] = mapped_column(Integer, nullable=False)  # Nonce value
    chain_id: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )  # Blockchain ID

    # Usage tracking
    used: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Expiry
    expires_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True
    )  # Nonce expiry time (typically 1 hour)

    # Message context
    message_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="trade"
    )  # 'trade', 'withdrawal', 'deposit', etc.
    message_hash: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )  # Hash of the signed message

    # Relationships
    user: Mapped["User"] = relationship("User")

    # Unique constraint: nonce per wallet address and chain
    __table_args__ = (
        UniqueConstraint(
            "wallet_address", "nonce", "chain_id", name="uq_wallet_nonce_chain"
        ),
        Index("ix_wallet_nonce_expires", "expires_at"),
        Index("ix_wallet_nonce_user_wallet", "user_id", "wallet_address"),
    )

    def __repr__(self):
        return f"<WalletNonce(id={self.id}, wallet={self.wallet_address[:10]}..., nonce={self.nonce}, used={self.used})>"

    def is_expired(self) -> bool:
        """Check if nonce has expired"""
        return datetime.now(UTC) > self.expires_at

    def is_valid(self) -> bool:
        """Check if nonce is valid (not used and not expired)"""
        return not self.used and not self.is_expired()
