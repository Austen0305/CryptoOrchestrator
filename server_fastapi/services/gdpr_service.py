import logging

from sqlalchemy.ext.asyncio import AsyncSession

from server_fastapi.config.settings import get_settings
from server_fastapi.core.encryption import CryptoEngine
from server_fastapi.models.privacy import PrivacyKeystore

settings = get_settings()
logger = logging.getLogger(__name__)


class GDPRService:
    """
    Service for handling GDPR Data Privacy operations.
    Implements the 'Crypto Shredding' pattern.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.kek = settings.privacy_master_key_bytes

    async def create_user_key(self, user_id: int) -> bytes:
        """
        Generates a new DEK for a user, encrypts it with Master Key,
        and stores it in the PrivacyKeystore.
        """
        # 1. Generate 256-bit DEK
        dek = CryptoEngine.generate_key()

        # 2. Encrypt DEK with Master KEK
        encrypted_dek = CryptoEngine.encrypt(dek, self.kek)

        # 3. Store in DB
        keystore = PrivacyKeystore(user_id=user_id, encrypted_dek=encrypted_dek)
        self.db.add(keystore)
        try:
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to create user key for {user_id}: {e}")
            await self.db.rollback()
            raise

        return dek

    async def get_user_key(self, user_id: int) -> bytes:
        """
        Retrieves the user's DEK. If one doesn't exist, creates it on the fly.
        """
        # 1. Fetch encrypted DEK
        keystore = await self.db.get(PrivacyKeystore, user_id)

        if not keystore:
            logger.info(f"No existing key for user {user_id}, generating new one.")
            return await self.create_user_key(user_id)

        # 2. Decrypt DEK using Master KEK
        try:
            dek = CryptoEngine.decrypt(keystore.encrypted_dek, self.kek)
            return dek
        except Exception as e:
            logger.critical(
                f"FATAL: Failed to decrypt DEK for user {user_id}. Master Key mismatch? {e}"
            )
            raise RuntimeError("Data Integrity Error: Cannot decrypt user key.")

    async def shred_user(self, user_id: int) -> bool:
        """
        PERMANENTLY destroys the user's encryption key.
        This renders all encrypted PII for this user unrecoverable.
        """
        keystore = await self.db.get(PrivacyKeystore, user_id)
        if keystore:
            await self.db.delete(keystore)
            await self.db.commit()
            logger.warning(
                f"CRYPTO SHREDDING EXECUTED for User {user_id}. Data is now unrecoverable."
            )
            return True
        return False

    async def encrypt_pii(self, user_id: int, plaintext: str) -> str:
        """Helper to encrypt a PII string for a specific user."""
        if not plaintext:
            return ""
        dek = await self.get_user_key(user_id)
        return CryptoEngine.encrypt_string(plaintext, dek)

    async def decrypt_pii(self, user_id: int, ciphertext_b64: str) -> str | None:
        """Helper to decrypt PII string for a specific user."""
        if not ciphertext_b64:
            return None
        try:
            dek = await self.get_user_key(user_id)
            return CryptoEngine.decrypt_string(ciphertext_b64, dek)
        except Exception:
            # If decryption fails (e.g. key shredded), return None or specific marker
            return "[DATA_DELETED]"
