"""
Key Management Service
Retrieves private keys from secure key management system
In production, should use AWS KMS, HashiCorp Vault, or similar
"""

import logging
from .local_key_manager import LocalEncryptedKeyManager

logger = logging.getLogger(__name__)


class KeyManagementService:
    """
    Service for retrieving private keys from secure storage

    Currently implements Phase 3: Local Encrypted Storage.
    In Phase 4, this should be upgraded to use AWS KMS / Vault.
    """

    def __init__(self):
        # Initialize LocalEncryptedKeyManager for Phase 3
        self.local_manager = LocalEncryptedKeyManager()
        logger.info("Initialized KeyManagementService with LocalEncryptedKeyManager")

    async def get_private_key(self, wallet_address: str, chain_id: int) -> str | None:
        """
        Get private key for a wallet address from secure key management
        """
        # Checks local encrypted storage first
        key = self.local_manager.get_key(wallet_address)

        if not key:
            logger.warning(
                "Key not found in secure storage",
                extra={"wallet_address": wallet_address, "chain_id": chain_id},
            )
            return None

        return key

    async def store_private_key(
        self, wallet_address: str, chain_id: int, private_key: str
    ) -> bool:
        """
        Store private key in secure key management system
        """
        return self.local_manager.store_key(wallet_address, private_key)


# Singleton instance
_key_management_service: KeyManagementService | None = None


def get_key_management_service() -> KeyManagementService:
    """Get singleton KeyManagementService instance"""
    global _key_management_service
    if _key_management_service is None:
        _key_management_service = KeyManagementService()
    return _key_management_service
