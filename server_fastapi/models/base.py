"""
Base database models and common functionality.
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Column, Integer, DateTime, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import DeclarativeBase

# Define Base here to avoid circular imports
class Base(DeclarativeBase):
    pass

if TYPE_CHECKING:
    from .exchange_api_key import ExchangeAPIKey

class TimestampMixin:
    """
    Mixin class providing created_at and updated_at timestamps.
    """
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

class SoftDeleteMixin:
    """
    Mixin class providing soft delete functionality.
    """
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def soft_delete(self):
        """Mark the record as deleted."""
        self.deleted_at = datetime.utcnow()
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
            if not column.name.startswith('_')
        }

# Example concrete model - User
class User(BaseModel):
    """
    User model for authentication and authorization.
    """
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)  # user, admin, etc.

    first_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # MFA & profile extensions
    mfa_method: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # 'email' | 'sms' | 'totp'
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    mfa_recovery_codes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    mfa_code: Mapped[Optional[str]] = mapped_column(String(6), nullable=True)
    mfa_code_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    locale: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    preferences_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON blob for user preferences

    # Relationship with ExchangeAPIKey
    exchange_api_keys: Mapped[List["ExchangeAPIKey"]] = relationship(
        "ExchangeAPIKey", back_populates="user", cascade="all, delete-orphan"
    )
    
    # Relationship with IdempotencyKey
    idempotency_keys: Mapped[List["IdempotencyKey"]] = relationship(
        "IdempotencyKey", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

    # Compatibility alias: tests and some callers expect `hashed_password`
    @property
    def hashed_password(self) -> str:  # type: ignore[override]
        return self.password_hash

    @hashed_password.setter
    def hashed_password(self, value: str) -> None:
        self.password_hash = value