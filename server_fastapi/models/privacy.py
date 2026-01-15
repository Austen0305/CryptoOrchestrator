from sqlalchemy import ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class PrivacyKeystore(Base, TimestampMixin):
    """
    Stores User-specific Data Encryption Keys (DEKs) encrypted with the Master KEK.
    Part of the Crypto-Shredding architecture for GDPR.

    When a user requests deletion (Right to be Forgotten), we delete the row
    corresponding to their user_id in this table. This renders all their
    encrypted PII (logs, backups, etc.) mathematically unreadable.
    """

    __tablename__ = "privacy_keystore"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        doc="The user ID who owns this key.",
    )

    encrypted_dek: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
        doc="The per-user Data Encryption Key (DEK), encrypted with the System Master Key (KEK).",
    )

    # We use a primitive foreign key but don't strictly enforce relationship loading
    # to avoid circular dependencies in the User model unless necessary.
