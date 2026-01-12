import os
import json
import logging
from typing import Dict, Optional
from cryptography.fernet import Fernet
from pathlib import Path

logger = logging.getLogger(__name__)


class LocalEncryptedKeyManager:
    """
    Manages local encrypted storage of private keys.
    Uses Fernet (symmetric encryption) with a master key from environment variables.

    WARNING: This is for DEVELOPMENT/PHASE 3 usage.
    Production should use dedicated KMS (AWS/Vault).
    """

    def __init__(self, storage_path: str = "data/secure/keys.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        self.master_key = os.getenv("CRYPTO_ORCHESTRATOR_MASTER_KEY")

        if not self.master_key:
            logger.warning(
                "CRYPTO_ORCHESTRATOR_MASTER_KEY not found. Generating a temporary one for this session."
            )
            self.master_key = Fernet.generate_key().decode()
            logger.warning(
                f"TEMPORARY MASTER KEY: {self.master_key} (Lost on restart!)"
            )

        try:
            self.fernet = Fernet(
                self.master_key.encode()
                if isinstance(self.master_key, str)
                else self.master_key
            )
        except Exception as e:
            logger.error(f"Invalid Master Key: {e}")
            raise ValueError("Invalid Master Key provided")

    async def _load_storage(self) -> Dict[str, str]:
        if not self.storage_path.exists():
            return {}
        try:
            async with aiofiles.open(self.storage_path, mode="r") as f:
                content = await f.read()
                return json.loads(content)
        except ImportError:
            # Fallback to sync if aiofiles not present (simplifies dependency)
            with open(self.storage_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load key storage: {e}")
            return {}

    async def _save_storage(self, data: Dict[str, str]):
        try:
            # Sync write for safety/simplicity in MVP
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save key storage: {e}")
            raise

    def get_encrypted_blob(self, wallet_address: str) -> Optional[str]:
        """Retrieve encrypted blob for address (storage only)"""
        if not self.storage_path.exists():
            return None

        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)

            return data.get(wallet_address.lower())
        except Exception as e:
            logger.error(f"Failed to retrieve blob for {wallet_address}: {e}")
            return None

    def get_key(self, wallet_address: str) -> Optional[str]:
        """Retrieve and decrypt private key using internal master key (Phase 3 compatibility)"""
        encrypted_blob = self.get_encrypted_blob(wallet_address)
        if not encrypted_blob:
            return None
        try:
            return self.fernet.decrypt(encrypted_blob.encode()).decode()
        except Exception as e:
            logger.error(f"Internal decryption failed for {wallet_address}: {e}")
            return None

    def store_encrypted_blob(self, wallet_address: str, encrypted_blob: str) -> bool:
        """Store encrypted blob (storage only)"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
            else:
                data = {}

            data[wallet_address.lower()] = encrypted_blob

            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)

            return True
        except Exception as e:
            logger.error(f"Failed to store blob: {e}")
            return False

    def store_key(self, wallet_address: str, private_key: str) -> bool:
        """Encrypt and store private key using internal master key (Phase 3 compatibility)"""
        try:
            if not private_key.startswith("0x"):
                private_key = "0x" + private_key
            encrypted_blob = self.fernet.encrypt(private_key.encode()).decode()
            return self.store_encrypted_blob(wallet_address, encrypted_blob)
        except Exception as e:
            logger.error(f"Internal storage failed: {e}")
            return False
