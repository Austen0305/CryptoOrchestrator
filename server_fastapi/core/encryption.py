import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class CryptoEngine:
    """
    Core Encryption Engine for GDPR Crypto-Shredding.
    Uses AES-256-GCM for authenticated encryption.
    """

    @staticmethod
    def generate_key() -> bytes:
        """Generate a random 256-bit (32 byte) AES key."""
        return AESGCM.generate_key(bit_length=256)

    @staticmethod
    def encrypt(data: bytes, key: bytes) -> bytes:
        """
        Encrypt data using AES-GCM.
        Returns: nonce + ciphertext + tag (implicitly handled by cryptography lib).
        """
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)  # NIST recommended 96-bit nonce
        ciphertext = aesgcm.encrypt(nonce, data, None)
        return nonce + ciphertext

    @staticmethod
    def decrypt(encrypted_data: bytes, key: bytes) -> bytes:
        """
        Decrypt data using AES-GCM.
        Expects: nonce (12 bytes) + ciphertext.
        """
        aesgcm = AESGCM(key)
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        return aesgcm.decrypt(nonce, ciphertext, None)

    @staticmethod
    def encrypt_string(data: str, key: bytes) -> str:
        """Helper to encrypt string to base64 string."""
        if data is None:
            return None
        encrypted = CryptoEngine.encrypt(data.encode("utf-8"), key)
        return base64.b64encode(encrypted).decode("utf-8")

    @staticmethod
    def decrypt_string(encrypted_b64: str, key: bytes) -> str:
        """Helper to decrypt base64 string to string."""
        if encrypted_b64 is None:
            return None
        encrypted_data = base64.b64decode(encrypted_b64)
        decrypted = CryptoEngine.decrypt(encrypted_data, key)
        return decrypted.decode("utf-8")
