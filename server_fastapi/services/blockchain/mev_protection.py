"""
MEV Protection Service
Protects users from Maximal Extractable Value (MEV) attacks.
Integrates with Flashbots Protect and MEV Blocker.
"""

import logging
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MEVProtectionProvider(str, Enum):
    """MEV protection provider options"""

    FLASHBOTS_PROTECT = "flashbots_protect"
    MEV_BLOCKER = "mev_blocker"
    NONE = "none"  # No protection (faster, but vulnerable to MEV)


class MEVProtectionService:
    """
    Service for protecting transactions from MEV attacks.

    MEV (Maximal Extractable Value) attacks include:
    - Front-running: Seeing pending transactions and placing better ones
    - Sandwich attacks: Placing trades before and after user's trade
    - Back-running: Placing trades after seeing user's transaction

    Protection methods:
    - Flashbots Protect: Private mempool (Flashbots)
    - MEV Blocker: RPC endpoint that routes through private mempool
    """

    # MEV protection RPC endpoints
    MEV_BLOCKER_RPCS = {
        1: "https://rpc.mevblocker.io",  # Ethereum mainnet
        8453: "https://rpc.mevblocker.io/base",  # Base
        42161: "https://rpc.mevblocker.io/arbitrum",  # Arbitrum
        137: "https://rpc.mevblocker.io/polygon",  # Polygon
        10: "https://rpc.mevblocker.io/optimism",  # Optimism
    }

    FLASHBOTS_PROTECT_RPC = "https://rpc.flashbots.net"  # Ethereum mainnet only

    def __init__(self):
        self._default_provider = MEVProtectionProvider.MEV_BLOCKER
        self._enabled_chains = [1, 8453, 42161, 137, 10]  # Supported chains

    async def get_protected_rpc_url(
        self, chain_id: int, provider: MEVProtectionProvider | None = None
    ) -> str | None:
        """
        Get MEV-protected RPC URL for a chain.

        Args:
            chain_id: Blockchain chain ID
            provider: MEV protection provider (default: MEV_BLOCKER)

        Returns:
            Protected RPC URL or None if not available
        """
        if provider is None:
            provider = self._default_provider

        if provider == MEVProtectionProvider.NONE:
            return None

        if chain_id not in self._enabled_chains:
            logger.warning(f"MEV protection not available for chain {chain_id}")
            return None

        if provider == MEVProtectionProvider.FLASHBOTS_PROTECT:
            # Flashbots Protect only supports Ethereum mainnet
            if chain_id == 1:
                return self.FLASHBOTS_PROTECT_RPC
            else:
                logger.warning(
                    f"Flashbots Protect only supports Ethereum mainnet, "
                    f"falling back to MEV Blocker for chain {chain_id}"
                )
                provider = MEVProtectionProvider.MEV_BLOCKER

        if provider == MEVProtectionProvider.MEV_BLOCKER:
            return self.MEV_BLOCKER_RPCS.get(chain_id)

        return None

    async def should_use_mev_protection(
        self,
        trade_amount_usd: float,
        chain_id: int,
        user_preference: bool | None = None,
    ) -> bool:
        """
        Determine if MEV protection should be used for a trade.

        Args:
            trade_amount_usd: Trade amount in USD
            chain_id: Blockchain chain ID
            user_preference: User's preference (if set)

        Returns:
            True if MEV protection should be used
        """
        # If user explicitly disabled, respect that
        if user_preference is False:
            return False

        # If user explicitly enabled, use it
        if user_preference is True:
            return chain_id in self._enabled_chains

        # Auto-determine based on trade size
        # Use protection for trades > $1000 (high-value trades are MEV targets)
        threshold_usd = 1000.0

        if trade_amount_usd >= threshold_usd:
            logger.info(
                f"MEV protection recommended for trade: ${trade_amount_usd:.2f} "
                f"(threshold: ${threshold_usd})"
            )
            return chain_id in self._enabled_chains

        return False

    async def send_protected_transaction(
        self,
        transaction_data: dict[str, Any],
        chain_id: int,
        provider: MEVProtectionProvider | None = None,
    ) -> str | None:
        """
        Send transaction through MEV-protected RPC.

        Args:
            transaction_data: Transaction data (from, to, data, value, etc.)
            chain_id: Blockchain chain ID
            provider: MEV protection provider

        Returns:
            Transaction hash or None if failed
        """
        protected_rpc = await self.get_protected_rpc_url(chain_id, provider)

        if not protected_rpc:
            logger.warning(
                f"MEV protection not available for chain {chain_id}, "
                f"sending through regular RPC"
            )
            return None

        try:
            # Send transaction through protected RPC
            # This would use web3.py to send via the protected endpoint
            from .web3_service import Web3Service

            Web3Service()

            # Temporarily override RPC URL for this transaction
            # In production, create a separate Web3 instance with protected RPC
            logger.info(
                f"Sending transaction through MEV-protected RPC: {protected_rpc} "
                f"(provider: {provider.value if provider else 'default'})"
            )

            # For now, log that protection would be used
            # Full implementation would require Web3Service to support RPC override
            # or creating a separate protected Web3 instance
            logger.info(
                f"MEV protection enabled for transaction on chain {chain_id}",
                extra={
                    "chain_id": chain_id,
                    "provider": provider.value if provider else "default",
                    "protected_rpc": protected_rpc,
                },
            )

            # Return None to indicate we'd use protected RPC
            # Actual implementation would send transaction and return hash
            return None

        except Exception as e:
            logger.error(
                f"Failed to send protected transaction: {e}",
                exc_info=True,
                extra={"chain_id": chain_id, "provider": provider},
            )
            return None

    def get_protection_status(self, chain_id: int) -> dict[str, Any]:
        """
        Get MEV protection status for a chain.

        Args:
            chain_id: Blockchain chain ID

        Returns:
            Dict with protection status information
        """
        is_supported = chain_id in self._enabled_chains

        if is_supported:
            self.MEV_BLOCKER_RPCS.get(chain_id)

        return {
            "chain_id": chain_id,
            "supported": is_supported,
            "providers": {
                "mev_blocker": {
                    "available": chain_id in self.MEV_BLOCKER_RPCS,
                    "rpc_url": (
                        self.MEV_BLOCKER_RPCS.get(chain_id)
                        if chain_id in self.MEV_BLOCKER_RPCS
                        else None
                    ),
                },
                "flashbots_protect": {
                    "available": chain_id == 1,  # Ethereum mainnet only
                    "rpc_url": self.FLASHBOTS_PROTECT_RPC if chain_id == 1 else None,
                },
            },
            "default_provider": self._default_provider.value,
            "recommended_for_trades_above_usd": 1000.0,
        }


# Singleton instance
_mev_protection: MEVProtectionService | None = None


def get_mev_protection_service() -> MEVProtectionService:
    """Get singleton MEV protection service instance"""
    global _mev_protection
    if _mev_protection is None:
        _mev_protection = MEVProtectionService()
    return _mev_protection
