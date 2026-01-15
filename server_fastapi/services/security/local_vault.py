import os

from .vault_interface import AbstractVault


class LocalEnvVault(AbstractVault):
    """
    Temporary/Development implementation retrieving keys from environment variables.
    WARNING: Not for high-value production use.
    """

    async def get_private_key(self, user_id: int, wallet_id: str) -> str:
        # Expected env pattern: WALLET_PK_{wallet_id}
        key = os.getenv(f"WALLET_PK_{wallet_id.upper()}")
        if not key:
            raise ValueError(
                f"Private key for wallet {wallet_id} not found in environment."
            )
        return key

    async def get_address(self, user_id: int, wallet_id: str) -> str:
        address = os.getenv(f"WALLET_ADDR_{wallet_id.upper()}")
        if not address:
            raise ValueError(
                f"Address for wallet {wallet_id} not found in environment."
            )
        return address
