"""
Balance Service
Check ETH and ERC-20 token balances with caching
"""

import logging
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
from web3 import AsyncWeb3
from web3.exceptions import Web3Exception

from .web3_service import get_web3_service
from ...config.settings import get_settings

logger = logging.getLogger(__name__)

# Try to get Redis cache service
try:
    from ...services.cache_service import cache_service

    REDIS_CACHE_AVAILABLE = True
except ImportError:
    REDIS_CACHE_AVAILABLE = False
    cache_service = None

# Standard ERC-20 ABI for balanceOf
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
]

# Common token addresses (mainnet)
COMMON_TOKENS = {
    1: {  # Ethereum
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    },
    # Add other chains as needed
}


class BalanceService:
    """Service for checking blockchain balances with caching"""

    def __init__(self):
        self.settings = get_settings()
        self.web3_service = get_web3_service()
        self._balance_cache: Dict[str, Dict[str, Any]] = (
            {}
        )  # {f"{chain_id}:{address}:{token}": {balance, timestamp}}
        self._cache_ttl = 30  # Cache for 30 seconds

    def _get_cache_key(
        self, chain_id: int, address: str, token_address: Optional[str] = None
    ) -> str:
        """Generate cache key"""
        token = token_address or "ETH"
        return f"{chain_id}:{address}:{token}"

    async def _get_cached_balance(self, cache_key: str) -> Optional[Decimal]:
        """Get balance from cache if not expired (checks Redis first, then in-memory)"""
        redis_key = f"balance:{cache_key}"

        # Check Redis cache first (30s TTL)
        if REDIS_CACHE_AVAILABLE and cache_service:
            try:
                cached_balance = await cache_service.get(redis_key)
                if cached_balance is not None:
                    return Decimal(str(cached_balance))
            except Exception as e:
                logger.debug(f"Redis balance cache check failed: {e}")

        # Check in-memory cache
        if cache_key in self._balance_cache:
            cached = self._balance_cache[cache_key]
            age = (datetime.utcnow() - cached["timestamp"]).total_seconds()
            if age < self._cache_ttl:
                return cached["balance"]
            else:
                # Remove expired entry
                del self._balance_cache[cache_key]
        return None

    async def _set_cached_balance(self, cache_key: str, balance: Decimal):
        """Cache balance with timestamp (both Redis and in-memory)"""
        # In-memory cache
        self._balance_cache[cache_key] = {
            "balance": balance,
            "timestamp": datetime.utcnow(),
        }

        # Redis cache (30s TTL)
        if REDIS_CACHE_AVAILABLE and cache_service:
            try:
                redis_key = f"balance:{cache_key}"
                await cache_service.set(redis_key, str(balance), ttl=self._cache_ttl)
            except Exception as e:
                logger.debug(f"Redis balance cache set failed: {e}")

    async def get_eth_balance(
        self, chain_id: int, address: str, use_cache: bool = True
    ) -> Optional[Decimal]:
        """
        Get ETH balance for an address

        Args:
            chain_id: Blockchain chain ID
            address: Ethereum address (checksummed)
            use_cache: Whether to use cached balance

        Returns:
            Balance in ETH (Decimal) or None if error
        """
        try:
            cache_key = self._get_cache_key(chain_id, address, None)

            # Check cache
            if use_cache:
                cached = self._get_cached_balance(cache_key)
                if cached is not None:
                    return cached

            # Get Web3 connection
            w3 = await self.web3_service.get_connection(chain_id)
            if not w3:
                logger.error(f"No Web3 connection for chain {chain_id}")
                return None

            # Normalize address
            address = self.web3_service.normalize_address(address)
            if not address:
                logger.error(f"Invalid address: {address}")
                return None

            # Get balance
            balance_wei = await w3.eth.get_balance(address)
            balance_eth = Decimal(balance_wei) / Decimal(10**18)

            # Cache result
            await self._set_cached_balance(cache_key, balance_eth)

            logger.debug(
                f"ETH balance for {address[:10]}... on chain {chain_id}: {balance_eth} ETH",
                extra={
                    "chain_id": chain_id,
                    "address": address,
                    "balance": str(balance_eth),
                },
            )

            return balance_eth

        except Web3Exception as e:
            logger.error(f"Web3 error getting ETH balance: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Error getting ETH balance: {e}", exc_info=True)
            return None

    async def get_token_balance(
        self,
        chain_id: int,
        address: str,
        token_address: str,
        use_cache: bool = True,
    ) -> Optional[Decimal]:
        """
        Get ERC-20 token balance for an address

        Args:
            chain_id: Blockchain chain ID
            address: User's Ethereum address
            token_address: ERC-20 token contract address
            use_cache: Whether to use cached balance

        Returns:
            Balance in token units (Decimal) or None if error
        """
        try:
            cache_key = self._get_cache_key(chain_id, address, token_address)

            # Check cache
            if use_cache:
                cached = await self._get_cached_balance(cache_key)
                if cached is not None:
                    return cached

            # Get Web3 connection
            w3 = await self.web3_service.get_connection(chain_id)
            if not w3:
                logger.error(f"No Web3 connection for chain {chain_id}")
                return None

            # Normalize addresses
            address = self.web3_service.normalize_address(address)
            token_address = self.web3_service.normalize_address(token_address)

            if not address or not token_address:
                logger.error(
                    f"Invalid addresses: address={address}, token={token_address}"
                )
                return None

            # Get token contract
            contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)

            # Get decimals
            try:
                decimals = await contract.functions.decimals().call()
            except Exception as e:
                logger.warning(
                    f"Could not get decimals for token {token_address}, assuming 18: {e}"
                )
                decimals = 18

            # Get balance
            balance_raw = await contract.functions.balanceOf(address).call()
            balance = Decimal(balance_raw) / Decimal(10**decimals)

            # Cache result
            await self._set_cached_balance(cache_key, balance)

            logger.debug(
                f"Token balance for {address[:10]}...: {balance} (token: {token_address[:10]}...)",
                extra={
                    "chain_id": chain_id,
                    "address": address,
                    "token_address": token_address,
                    "balance": str(balance),
                    "decimals": decimals,
                },
            )

            return balance

        except Web3Exception as e:
            logger.error(f"Web3 error getting token balance: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Error getting token balance: {e}", exc_info=True)
            return None

    async def get_multiple_balances(
        self,
        chain_id: int,
        address: str,
        token_addresses: list[str],
    ) -> Dict[str, Optional[Decimal]]:
        """
        Get multiple token balances efficiently

        Args:
            chain_id: Blockchain chain ID
            address: User's Ethereum address
            token_addresses: List of token contract addresses (include None for ETH)

        Returns:
            Dictionary mapping token addresses to balances
        """
        results: Dict[str, Optional[Decimal]] = {}

        # Get ETH balance if None is in the list
        if None in token_addresses:
            eth_balance = await self.get_eth_balance(chain_id, address)
            results["ETH"] = eth_balance
            token_addresses = [t for t in token_addresses if t is not None]

        # Get token balances in parallel (could be optimized further)
        for token_address in token_addresses:
            balance = await self.get_token_balance(chain_id, address, token_address)
            results[token_address] = balance

        return results

    def clear_cache(
        self, chain_id: Optional[int] = None, address: Optional[str] = None
    ):
        """
        Clear balance cache

        Args:
            chain_id: Optional chain ID to filter
            address: Optional address to filter
        """
        if chain_id is None and address is None:
            self._balance_cache.clear()
            logger.info("Balance cache cleared")
        else:
            # Clear specific entries
            keys_to_remove = []
            for key in self._balance_cache.keys():
                parts = key.split(":")
                if len(parts) >= 3:
                    key_chain_id = int(parts[0])
                    key_address = parts[1]
                    if (chain_id is None or key_chain_id == chain_id) and (
                        address is None or key_address.lower() == address.lower()
                    ):
                        keys_to_remove.append(key)

            for key in keys_to_remove:
                del self._balance_cache[key]

            logger.info(f"Cleared {len(keys_to_remove)} cache entries")

    async def refresh_balance(
        self,
        chain_id: int,
        address: str,
        token_address: Optional[str] = None,
    ) -> Optional[Decimal]:
        """
        Force refresh balance from blockchain (bypasses cache)

        Args:
            chain_id: Blockchain chain ID
            address: Ethereum address
            token_address: Optional token contract address (None for ETH)

        Returns:
            Balance or None if error
        """
        cache_key = self._get_cache_key(chain_id, address, token_address)

        # Clear cache for this specific balance
        if cache_key in self._balance_cache:
            del self._balance_cache[cache_key]

        # Fetch fresh balance
        if token_address:
            return await self.get_token_balance(
                chain_id=chain_id,
                address=address,
                token_address=token_address,
                use_cache=False,  # Force fresh fetch
            )
        else:
            return await self.get_eth_balance(
                chain_id=chain_id,
                address=address,
                use_cache=False,  # Force fresh fetch
            )


# Singleton instance
_balance_service: Optional[BalanceService] = None


def get_balance_service() -> BalanceService:
    """Get singleton BalanceService instance"""
    global _balance_service
    if _balance_service is None:
        _balance_service = BalanceService()
    return _balance_service
