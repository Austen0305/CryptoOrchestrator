from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class UserPreferencesModel(BaseModel):
    __tablename__ = "user_preferences"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), unique=True, index=True, nullable=False
    )
    theme: Mapped[str | None] = mapped_column(
        String(20), default="light", nullable=True
    )
    language: Mapped[str | None] = mapped_column(
        String(10), default="en", nullable=True
    )
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    data_json: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # arbitrary serialized preferences
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    user = relationship("User", backref="preferences")

    def to_dict(self):
        base = super().to_dict()
        return base
