"""
Subscription model for Stripe billing
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class Subscription(BaseModel):
    """
    User subscription model for Stripe billing integration.
    """

    __tablename__ = "subscriptions"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True
    )

    # Stripe fields
    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True, index=True
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True, index=True
    )
    stripe_price_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Subscription details
    plan: Mapped[str] = mapped_column(
        String(50), nullable=False, default="free"
    )  # free, basic, pro
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="inactive"
    )  # active, canceled, past_due, trialing, incomplete

    # Billing period
    current_period_start: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Trial
    trial_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    trial_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="subscription")

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, user_id={self.user_id}, plan='{self.plan}', status='{self.status}')>"
