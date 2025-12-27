"""
Wallet Model - User wallet for storing funds
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
    Enum as SQLEnum,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User
    from .trade import Trade


class WalletType(str, Enum):
    """Wallet types"""

    TRADING = "trading"  # For trading operations
    STAKING = "staking"  # For staking rewards
    SAVINGS = "savings"  # For savings/earnings
    DEPOSIT = "deposit"  # For deposits


class TransactionType(str, Enum):
    """Transaction types"""

    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRADE = "trade"
    FEE = "fee"
    REWARD = "reward"
    STAKING_REWARD = "staking_reward"
    REFUND = "refund"
    TRANSFER = "transfer"


class TransactionStatus(str, Enum):
    """Transaction status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Wallet(Base, TimestampMixin):
    """Model for user wallets"""

    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    # Wallet details
    wallet_type: Mapped[str] = mapped_column(
        String(20), default="trading", nullable=False, index=True
    )
    currency: Mapped[str] = mapped_column(
        String(10), default="USD", nullable=False, index=True
    )  # USD, BTC, ETH, etc.

    # Balance
    balance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    available_balance: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )  # Available for trading
    locked_balance: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )  # Locked in orders

    # Statistics
    total_deposited: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_withdrawn: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_traded: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User")
    transactions: Mapped[list["WalletTransaction"]] = relationship(
        "WalletTransaction", back_populates="wallet"
    )

    def __repr__(self):
        return f"<Wallet(id={self.id}, user_id={self.user_id}, currency={self.currency}, balance={self.balance})>"


class WalletTransaction(Base, TimestampMixin):
    """Model for wallet transactions"""

    __tablename__ = "wallet_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    wallet_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("wallets.id"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    # Transaction details
    transaction_type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )

    # Amount
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    fee: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    net_amount: Mapped[float] = mapped_column(Float, nullable=False)  # amount - fee

    # References
    reference_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )  # External transaction ID
    trade_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("trades.id"), nullable=True, index=True
    )
    payment_intent_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )  # Stripe payment intent

    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    transaction_metadata: Mapped[Optional[dict]] = mapped_column(
        Text, nullable=True
    )  # JSON metadata

    # Timestamps
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    wallet: Mapped["Wallet"] = relationship("Wallet", back_populates="transactions")
    user: Mapped["User"] = relationship("User")
    trade: Mapped[Optional["Trade"]] = relationship("Trade")

    def __repr__(self):
        return f"<WalletTransaction(id={self.id}, type={self.transaction_type}, amount={self.amount}, status={self.status})>"
