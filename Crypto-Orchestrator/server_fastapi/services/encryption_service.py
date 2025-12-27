"""
Encryption Service
Handles encryption/decryption of sensitive data like API keys.
"""

import os
import base64
import logging
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""

    def __init__(self):
        # Get encryption key from environment or generate one
        encryption_key = os.getenv("ENCRYPTION_KEY")

        if not encryption_key:
            # Generate a key from a master password (for development)
            # In production, this should be set via environment variable
            master_password = os.getenv(
                "MASTER_PASSWORD", "default-master-password-change-in-production"
            )
            salt = os.getenv(
                "ENCRYPTION_SALT", "default-salt-change-in-production"
            ).encode()

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
            self.cipher = Fernet(key)
            logger.warning(
                "Using generated encryption key - set ENCRYPTION_KEY in production!"
            )
        else:
            # Use provided key
            try:
                self.cipher = Fernet(encryption_key.encode())
            except Exception as e:
                logger.error(f"Invalid encryption key format: {e}")
                raise ValueError("Invalid encryption key format")

    def encrypt(self, data: str) -> str:
        """
        Encrypt sensitive data.

        Args:
            data: Plain text data to encrypt

        Returns:
            Encrypted data as base64 string
        """
        try:
            if not data:
                return ""
            encrypted = self.cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Error encrypting data: {e}", exc_info=True)
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data.

        Args:
            encrypted_data: Encrypted data as base64 string

        Returns:
            Decrypted plain text data
        """
        try:
            if not encrypted_data:
                return ""
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Error decrypting data: {e}", exc_info=True)
            raise


# Global instance
encryption_service = EncryptionService()
