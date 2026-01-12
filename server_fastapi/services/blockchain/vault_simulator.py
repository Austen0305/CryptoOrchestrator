"""
Vault Simulator
Implements hardened local key management using secret splitting (2-of-2 XOR)
Mimics production KMS/HSM patterns for the 2026 Rebuild.
"""

import logging
import os
import secrets
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class VaultSimulator:
    """Hardened local key vault simulator using secret splitting"""

    def __init__(self, vault_path: str = "data/secure/.vault_share"):
        self.vault_path = Path(vault_path)
        self.vault_path.parent.mkdir(parents=True, exist_ok=True)
        self._master_key: Optional[bytes] = None

    def _get_env_share(self) -> Optional[bytes]:
        """Retrieve Share B from environment"""
        share_b_hex = os.getenv("VAULT_SHARE_B")
        if share_b_hex:
            return bytes.fromhex(share_b_hex)
        return None

    def _load_file_share(self) -> Optional[bytes]:
        """Retrieve Share A from a hidden local file"""
        if self.vault_path.exists():
            return self.vault_path.read_bytes()
        return None

    def _save_file_share(self, share: bytes):
        """Save Share A to a hidden local file"""
        self.vault_path.write_bytes(share)
        # In a real 2026 system, we'd set strict file permissions here
        try:
            os.chmod(self.vault_path, 0o600)
        except Exception:
            pass

    def initialize_vault(self) -> str:
        """
        Initialize the vault by generating a master key and splitting it.
        Returns the environment share (Share B) which the user MUST save.
        """
        # Generate random 32-byte master key
        master_key = secrets.token_bytes(32)

        # Generate random 32-byte Share A
        share_a = secrets.token_bytes(32)

        # Calculate Share B via XOR: B = Master ^ A
        share_b = bytes(a ^ b for a, b in zip(master_key, share_a))

        # Save Share A locally
        self._save_file_share(share_a)

        # In memory
        self._master_key = master_key

        logger.info("Vault initialized with 2-of-2 XOR secret splitting")
        return share_b.hex()

    def unlock(self, share_b_hex: Optional[str] = None):
        """Reconstruct the master key using the provided Share B and local Share A"""
        share_a = self._load_file_share()
        share_b = bytes.fromhex(share_b_hex) if share_b_hex else self._get_env_share()

        if not share_a or not share_b:
            logger.error("Failed to unlock vault: Missing shares")
            raise ValueError(
                "Vault shares missing. Requires Share A (file) and Share B (env/input)."
            )

        if len(share_a) != len(share_b):
            raise ValueError("Vault shares length mismatch")

        # Reconstruct: Master = A ^ B
        self._master_key = bytes(a ^ b for a, b in zip(share_a, share_b))
        logger.info("Vault successfully unlocked and master key reconstructed")

    def get_fernet(self) -> Fernet:
        """Get a Fernet instance derived from the reconstructed master key"""
        if not self._master_key:
            self.unlock()  # Try to unlock from env if not already unlocked

        # Fernet requires 32-byte base64 encoded key
        import base64

        # We use the reconstructed master key directly if it's 32 bytes
        # or hash it if needed, but here it's already 32 bytes.
        fernet_key = base64.urlsafe_b64encode(self._master_key)
        return Fernet(fernet_key)

    @property
    def is_locked(self) -> bool:
        return self._master_key is None


# Global instance
vault_simulator = VaultSimulator()
