"""
Base database models and common functionality.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# Define Base here to avoid circular imports
class Base(DeclarativeBase):
    pass


# ExchangeAPIKey - REMOVED (platform uses blockchain/DEX trading exclusively)
# Model file deleted - platform uses blockchain/DEX trading exclusively


class TimestampMixin:
    """
    Mixin class providing created_at and updated_at timestamps.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class SoftDeleteMixin:
    """
    Mixin class providing soft delete functionality.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def soft_delete(self):
        """Mark the record as deleted."""
        self.deleted_at = datetime.now(UTC)
        self.is_deleted = True

    def restore(self):
        """Restore a soft-deleted record."""
        self.deleted_at = None
        self.is_deleted = False


class BaseModel(Base, TimestampMixin, SoftDeleteMixin):
    """
    Base model class that includes common fields and mixins.
    All application models should inherit from this class.
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    def to_dict(self) -> dict:
        """
        Convert model instance to dictionary.
        Excludes SQLAlchemy internal attributes.
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
            if not column.name.startswith("_")
        }


# Import User from user.py to avoid duplicate table definition
# but still allow importing from base.py for backward compatibility
try:
    from .user import User
except ImportError:
    # If user.py doesn't exist yet, User can be imported from elsewhere
    pass
