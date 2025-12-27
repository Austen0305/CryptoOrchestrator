"""
Secret Rotation Service
Manages cryptographic secret rotation for production security
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class SecretRotationService:
    """Manage secret rotation for production security"""

    @staticmethod
    def generate_jwt_secret(length: int = 64) -> str:
        """
        Generate cryptographically secure JWT secret

        Args:
            length: Length of the secret in bytes (default 64)

        Returns:
            URL-safe base64-encoded secret string
        """
        secret = secrets.token_urlsafe(length)
        logger.info(f"Generated new JWT secret ({length} bytes)")
        return secret

    @staticmethod
    def generate_api_key() -> Tuple[str, str]:
        """
        Generate API key and its hash

        Returns:
            Tuple of (api_key, api_key_hash)
        """
        key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        logger.info("Generated new API key")
        return key, key_hash

    @staticmethod
    def generate_encryption_key(length: int = 32) -> str:
        """
        Generate database encryption key

        Args:
            length: Length in bytes (default 32 for AES-256)

        Returns:
            URL-safe base64-encoded encryption key
        """
        key = secrets.token_urlsafe(length)
        logger.info(f"Generated new encryption key ({length} bytes)")
        return key

    @staticmethod
    def should_rotate(last_rotation: datetime, days: int = 90) -> bool:
        """
        Check if secret should be rotated based on age

        Args:
            last_rotation: Last rotation datetime
            days: Maximum age in days before rotation required

        Returns:
            True if rotation is needed
        """
        age = datetime.utcnow() - last_rotation
        should_rotate = age > timedelta(days=days)

        if should_rotate:
            logger.warning(f"Secret rotation needed (age: {age.days} days)")

        return should_rotate

    async def rotate_user_api_key(self, db_session, user_id: str) -> str:
        """
        Rotate user's API key in database

        Args:
            db_session: Database session
            user_id: User ID

        Returns:
            New API key (return to user ONCE)
        """
        from sqlalchemy import select, update
        from server_fastapi.models.base import User

        new_key, new_hash = self.generate_api_key()

        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(api_key_hash=new_hash, api_key_rotated_at=datetime.utcnow())
        )

        await db_session.execute(stmt)
        await db_session.commit()

        logger.info(f"API key rotated for user {user_id}")

        return new_key

    def create_rotation_log(
        self, secret_type: str, rotation_file: str = ".secret_rotation_log"
    ):
        """
        Log secret rotation event

        Args:
            secret_type: Type of secret rotated
            rotation_file: Path to rotation log file
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            log_entry = f"{timestamp} - {secret_type} rotated\n"

            with open(rotation_file, "a") as f:
                f.write(log_entry)

            logger.info(f"Rotation logged: {secret_type}")
        except Exception as e:
            logger.error(f"Failed to log rotation: {e}")

    def generate_all_secrets(self) -> dict:
        """
        Generate complete set of secrets for new installation

        Returns:
            Dictionary of all generated secrets
        """
        secrets_dict = {
            "JWT_SECRET": self.generate_jwt_secret(64),
            "DATABASE_ENCRYPTION_KEY": self.generate_encryption_key(32),
            "SESSION_SECRET": self.generate_jwt_secret(32),
            "WEBHOOK_SECRET": self.generate_jwt_secret(32),
        }

        logger.info("Generated complete secret set")
        return secrets_dict

    def export_secrets_to_env_format(self, secrets_dict: dict) -> str:
        """
        Export secrets in .env file format

        Args:
            secrets_dict: Dictionary of secrets

        Returns:
            Formatted string for .env file
        """
        lines = ["# Generated secrets - rotate regularly", ""]

        for key, value in secrets_dict.items():
            lines.append(f"{key}={value}")

        lines.append("")
        lines.append(f"# Generated at: {datetime.utcnow().isoformat()}")

        return "\n".join(lines)


# Singleton instance
_secret_rotation_service: Optional[SecretRotationService] = None


def get_secret_rotation_service() -> SecretRotationService:
    """Get singleton secret rotation service"""
    global _secret_rotation_service
    if _secret_rotation_service is None:
        _secret_rotation_service = SecretRotationService()
    return _secret_rotation_service
