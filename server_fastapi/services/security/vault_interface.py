from abc import ABC, abstractmethod
from typing import Optional


class AbstractVault(ABC):
    """
    Abstract interface for secure key management (2026 Standard).
    Implementations can be local (Env), HashiCorp Vault, or HSM-based.
    """

    @abstractmethod
    async def get_private_key(self, user_id: int, wallet_id: str) -> str:
        """Retrieve private key securely."""
        pass

    @abstractmethod
    async def get_address(self, user_id: int, wallet_id: str) -> str:
        """Retrieve public address."""
        pass
