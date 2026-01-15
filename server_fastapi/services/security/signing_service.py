import logging
from typing import Any

from eth_account import Account
from eth_account.messages import encode_defunct

from ...core.domain_registry import domain_registry
from .vault_interface import AbstractVault

logger = logging.getLogger(__name__)


class SigningService:
    """
    Hardened Signing Service (2026 Best Practice).
    Isolates transaction construction and signing logic.
    Always uses an AbstractVault to retrieve keys.
    """

    def __init__(self, vault: AbstractVault | None = None):
        self._vault = vault

    @property
    def vault(self) -> AbstractVault:
        if self._vault is None:
            # Lazy resolution from registry
            self._vault = domain_registry.resolve(AbstractVault)
        return self._vault

    async def sign_transaction(
        self,
        user_id: int,
        wallet_id: str,
        transaction: dict[str, Any],
        dry_run: bool = False,
    ) -> str:
        """
        Sign an Ethereum transaction payload.

        Args:
            user_id: ID of the user request
            wallet_id: Internal reference to the wallet
            transaction: Dict containing to, value, data, gas, gasPrice, nonce, chainId
            dry_run: If True, simulate signing without using real keys if possible,
                     or just return a mock hash for local testing.
        """
        if dry_run:
            logger.info(
                f"[DRY-RUN] Signing transaction for user {user_id} on wallet {wallet_id}"
            )
            return "0x" + "f" * 128  # Mock signature

        pk = await self.vault.get_private_key(user_id, wallet_id)

        try:
            signed_tx = Account.sign_transaction(transaction, pk)
            logger.debug(f"Transaction signed for user {user_id}")
            return signed_tx.rawTransaction.hex()
        except Exception as e:
            logger.error(f"Failed to sign transaction: {e}")
            raise ValueError(f"Signature failed: {e}")

    async def sign_message(self, user_id: int, wallet_id: str, message: str) -> str:
        """Sign a text message (EIP-191)."""
        pk = await self.vault.get_private_key(user_id, wallet_id)
        msghash = encode_defunct(text=message)
        signed_message = Account.sign_message(msghash, pk)
        return signed_message.signature.hex()

    async def get_wallet_address(self, user_id: int, wallet_id: str) -> str:
        """Helper to get public address through the vault."""
        return await self.vault.get_address(user_id, wallet_id)


# Global service instance
signing_service = SigningService()
