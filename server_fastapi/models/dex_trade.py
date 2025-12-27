"""
DEX Trade Model - DEX trading history
Stores trades executed on decentralized exchanges
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
    Text,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User


class DEXTrade(Base, TimestampMixin):
    """Model for storing DEX trade history"""

    __tablename__ = "dex_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), index=True, nullable=False
    )

    # Trade details
    trade_type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # 'custodial' or 'non_custodial'
    chain_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True
    )  # Blockchain ID
    aggregator: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # '0x', 'okx', 'rubic'

    # Token details
    sell_token: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # Token address
    sell_token_symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    buy_token: Mapped[str] = mapped_column(String(100), nullable=False)  # Token address
    buy_token_symbol: Mapped[str] = mapped_column(String(20), nullable=False)

    # Amounts
    sell_amount: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # Raw amount (wei)
    buy_amount: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # Raw amount (wei)
    sell_amount_decimal: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Human-readable
    buy_amount_decimal: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Human-readable

    # Pricing
    price: Mapped[float] = mapped_column(Float, nullable=True)  # Price per token
    slippage_percentage: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.5
    )

    # Fees
    platform_fee_bps: Mapped[int] = mapped_column(
        Integer, nullable=False, default=20
    )  # Fee in basis points
    platform_fee_amount: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    aggregator_fee_amount: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )

    # Wallet addresses
    user_wallet_address: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )  # User's wallet (for non-custodial) or platform wallet (for custodial)
    recipient_address: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # Final recipient (for non-custodial)

    # Transaction details
    transaction_hash: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, unique=True, index=True
    )  # Blockchain transaction hash
    transaction_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )  # 'pending', 'confirmed', 'failed'
    block_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gas_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gas_price: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Swap calldata
    swap_calldata: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Raw calldata
    swap_target: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # Contract address

    # Status
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )  # 'pending', 'executing', 'completed', 'failed', 'cancelled'
    success: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    quote_data: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # Original quote
    execution_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # Execution details

    # Timestamps
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")

    def __repr__(self):
        return f"<DEXTrade(id={self.id}, user_id={self.user_id}, {self.sell_token_symbol}->{self.buy_token_symbol}, status={self.status})>"
