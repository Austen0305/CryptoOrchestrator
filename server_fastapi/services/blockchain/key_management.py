"""
Key Management Service
Retrieves private keys from secure key management system
In production, should use AWS KMS, HashiCorp Vault, or similar
"""

import logging

from .local_key_manager import LocalEncryptedKeyManager
from .vault_simulator import vault_simulator

logger = logging.getLogger(__name__)


class KeyManagementService:
    """
    Service for retrieving private keys from secure storage

    Currently implements Phase 3: Local Encrypted Storage.
    In Phase 4, this should be upgraded to use AWS KMS / Vault.
    """

    def __init__(self, vault=vault_simulator):
        self.vault = vault
        self.local_manager = LocalEncryptedKeyManager()
        logger.info("Initialized KeyManagementService with Vault-Hardened Simulator")

    async def get_private_key(self, wallet_address: str, chain_id: int) -> str | None:
        """
        Get private key for a wallet address from vault-hardened storage
        """
        # Step 1: Get encrypted key from storage
        # We reuse LocalEncryptedKeyManager for storage logic but use our Vault for encryption
        encrypted_data = self.local_manager.get_encrypted_blob(wallet_address)
        if not encrypted_data:
            return None

        # Step 2: Decrypt with Vault Simulator
        try:
            fernet = self.vault.get_fernet()
            return fernet.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Vault decryption failed: {e}")
            return None

    async def store_private_key(
        self, wallet_address: str, chain_id: int, private_key: str
    ) -> bool:
        """
        Store private key using vault-hardened encryption
        """
        try:
            # Encrypt with Vault
            fernet = self.vault.get_fernet()
            if not private_key.startswith("0x"):
                private_key = "0x" + private_key
            encrypted_blob = fernet.encrypt(private_key.encode()).decode()

            # Save to storage
            return self.local_manager.store_encrypted_blob(
                wallet_address, encrypted_blob
            )
        except Exception as e:
            logger.error(f"Vault storage failed: {e}")
            return False


# Singleton instance
_key_management_service: KeyManagementService | None = None


def get_key_management_service() -> KeyManagementService:
    """Get singleton KeyManagementService instance"""
    global _key_management_service
    if _key_management_service is None:
        _key_management_service = KeyManagementService()
    return _key_management_service
