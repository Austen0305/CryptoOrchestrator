"""
Token Registry Service
Comprehensive multi-chain token registry for symbol-to-address mapping.
Uses 0x API for supported tokens, with fallback to common tokens.
"""

import logging
from typing import Dict, Optional, List, Any
import httpx
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TokenRegistryService:
    """
    Service for managing token registry across multiple chains.
    Maps symbols to addresses, handles token metadata, and verifies tokens.
    """

    # Common token addresses by chain (fallback when 0x API unavailable)
    COMMON_TOKENS: Dict[int, Dict[str, str]] = {
        1: {  # Ethereum Mainnet
            "ETH": "0x0000000000000000000000000000000000000000",
            "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0c3606eB48",
            "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
            "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
            "UNI": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
            "LINK": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
            "AAVE": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
        },
        8453: {  # Base
            "ETH": "0x0000000000000000000000000000000000000000",
            "WETH": "0x4200000000000000000000000000000000000006",
            "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            "DAI": "0x50c5725949A6F0c72E6C4a641F24049A917E0D69",
        },
        42161: {  # Arbitrum One
            "ETH": "0x0000000000000000000000000000000000000000",
            "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
            "USDC": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
            "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
            "DAI": "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
        },
        137: {  # Polygon
            "MATIC": "0x0000000000000000000000000000000000000000",
            "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
            "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
            "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
            "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
            "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
        },
        10: {  # Optimism
            "ETH": "0x0000000000000000000000000000000000000000",
            "WETH": "0x4200000000000000000000000000000000000006",
            "USDC": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",
            "DAI": "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
        },
        43114: {  # Avalanche
            "AVAX": "0x0000000000000000000000000000000000000000",
            "WAVAX": "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7",
            "USDC": "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E",
            "USDT": "0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7",
            "DAI": "0xd586E7F844cEa2F87f50152665BCbc2C279D8d70",
        },
        56: {  # BNB Chain
            "BNB": "0x0000000000000000000000000000000000000000",
            "WBNB": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
            "USDC": "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",
            "USDT": "0x55d398326f99059fF775485246999027B3197955",
            "DAI": "0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3",
        },
    }

    # Chain ID to name mapping
    CHAIN_NAMES: Dict[int, str] = {
        1: "Ethereum",
        8453: "Base",
        42161: "Arbitrum One",
        137: "Polygon",
        10: "Optimism",
        43114: "Avalanche",
        56: "BNB Chain",
    }

    CACHE_TTL = 3600  # Cache token metadata for 1 hour
    ZEROX_API_BASE = "https://api.0x.org"

    def __init__(self):
        self._token_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._zeroex_api_key = None  # Optional: Set via environment variable
        self._redis_cache = None

        # Try to get Redis cache service
        try:
            from ...services.cache_service import cache_service

            self._redis_cache = cache_service
        except ImportError:
            pass

    def _get_cache_key(self, symbol: str, chain_id: int) -> str:
        """Generate cache key for token lookup"""
        return f"{chain_id}:{symbol.upper()}"

    async def get_token_address(self, symbol: str, chain_id: int = 1) -> Optional[str]:
        """
        Get token address from symbol and chain.

        Args:
            symbol: Token symbol (e.g., "ETH", "USDC")
            chain_id: Blockchain chain ID

        Returns:
            Token address or None if not found
        """
        cache_key = self._get_cache_key(symbol, chain_id)
        redis_key = f"token_registry:{cache_key}"

        # Check Redis cache first (distributed cache)
        if self._redis_cache:
            try:
                cached_data = await self._redis_cache.get(redis_key)
                if cached_data and isinstance(cached_data, dict):
                    return cached_data.get("address")
            except Exception as e:
                logger.debug(f"Redis cache check failed: {e}")

        # Check in-memory cache
        if cache_key in self._token_cache:
            cache_time = self._cache_timestamps.get(cache_key, 0)
            if (datetime.now().timestamp() - cache_time) < self.CACHE_TTL:
                return self._token_cache[cache_key].get("address")

        # Check common tokens first (fastest)
        symbol_upper = symbol.upper()
        chain_tokens = self.COMMON_TOKENS.get(chain_id, {})
        if symbol_upper in chain_tokens:
            address = chain_tokens[symbol_upper]
            # Cache it (both in-memory and Redis)
            token_data = {
                "address": address,
                "symbol": symbol_upper,
                "chain_id": chain_id,
                "decimals": 18,  # Default, will be fetched if needed
            }
            self._token_cache[cache_key] = token_data
            self._cache_timestamps[cache_key] = datetime.now().timestamp()

            # Also cache in Redis (1h TTL)
            if self._redis_cache:
                try:
                    await self._redis_cache.set(
                        redis_key, token_data, ttl=self.CACHE_TTL
                    )
                except Exception as e:
                    logger.debug(f"Redis cache set failed: {e}")

            return address

        # Try 0x API for comprehensive token list
        try:
            address = await self._get_token_from_zeroex(symbol, chain_id)
            if address:
                return address
        except Exception as e:
            logger.warning(f"Failed to get token from 0x API: {e}")

        # Fallback: return None (token not found)
        logger.warning(f"Token {symbol} not found on chain {chain_id}")
        return None

    async def _get_token_from_zeroex(self, symbol: str, chain_id: int) -> Optional[str]:
        """
        Get token address from 0x API token list.

        Args:
            symbol: Token symbol
            chain_id: Blockchain chain ID

        Returns:
            Token address or None
        """
        try:
            # Map chain_id to 0x chain name
            chain_map = {
                1: "ethereum",
                8453: "base",
                42161: "arbitrum",
                137: "polygon",
                10: "optimism",
                43114: "avalanche",
                56: "bsc",
            }

            chain_name = chain_map.get(chain_id)
            if not chain_name:
                return None

            url = f"{self.ZEROX_API_BASE}/swap/v1/tokens"
            params = {"chain": chain_name}

            headers = {}
            if self._zeroex_api_key:
                headers["0x-api-key"] = self._zeroex_api_key

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()

                # Search for token by symbol
                symbol_upper = symbol.upper()
                for token in data.get("records", []):
                    if token.get("symbol", "").upper() == symbol_upper:
                        address = token.get("address")
                        if address:
                            # Cache it (both in-memory and Redis)
                            cache_key = self._get_cache_key(symbol, chain_id)
                            redis_key = f"token_registry:{cache_key}"
                            token_data = {
                                "address": address,
                                "symbol": symbol_upper,
                                "chain_id": chain_id,
                                "decimals": token.get("decimals", 18),
                                "name": token.get("name"),
                            }
                            self._token_cache[cache_key] = token_data
                            self._cache_timestamps[cache_key] = (
                                datetime.now().timestamp()
                            )

                            # Also cache in Redis (1h TTL)
                            if self._redis_cache:
                                try:
                                    await self._redis_cache.set(
                                        redis_key, token_data, ttl=self.CACHE_TTL
                                    )
                                except Exception as e:
                                    logger.debug(f"Redis cache set failed: {e}")

                            return address
        except Exception as e:
            logger.warning(f"0x API token lookup failed: {e}")

        return None

    async def get_token_decimals(self, token_address: str, chain_id: int) -> int:
        """
        Get token decimals for proper amount conversion.
        Queries blockchain contract for actual decimals.

        Args:
            token_address: Token contract address
            chain_id: Blockchain chain ID

        Returns:
            Number of decimals (default: 18 if query fails)
        """
        # Check cache first
        for cache_key, cached_data in self._token_cache.items():
            if (
                cached_data.get("address", "").lower() == token_address.lower()
                and cached_data.get("chain_id") == chain_id
                and cached_data.get("decimals") is not None
            ):
                return cached_data.get("decimals", 18)

        # Query blockchain contract for actual decimals
        try:
            decimals = await self._query_token_decimals_from_chain(
                token_address, chain_id
            )
            if decimals is not None:
                # Cache the result
                cache_key = f"{chain_id}:{token_address.lower()}"
                if cache_key not in self._token_cache:
                    self._token_cache[cache_key] = {}
                self._token_cache[cache_key]["decimals"] = decimals
                self._token_cache[cache_key]["address"] = token_address
                self._token_cache[cache_key]["chain_id"] = chain_id
                self._cache_timestamps[cache_key] = datetime.now().timestamp()
                return decimals
        except Exception as e:
            logger.warning(
                f"Failed to query decimals for {token_address} on chain {chain_id}: {e}"
            )

        # Default to 18 decimals (most tokens) if query fails
        return 18

    async def _query_token_decimals_from_chain(
        self, token_address: str, chain_id: int
    ) -> Optional[int]:
        """
        Query token decimals from blockchain contract.

        Args:
            token_address: Token contract address
            chain_id: Blockchain chain ID

        Returns:
            Number of decimals or None if query fails
        """
        try:
            from .web3_service import Web3Service

            web3_service = Web3Service()
            w3 = await web3_service.get_connection(chain_id)

            if not w3:
                return None

            # ERC-20 decimals() function signature
            # decimals() -> uint8
            decimals_abi = [
                {
                    "constant": True,
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "type": "function",
                }
            ]

            # Create contract instance
            checksum_address = w3.to_checksum_address(token_address)
            contract = w3.eth.contract(address=checksum_address, abi=decimals_abi)

            # Call decimals() function
            decimals = await contract.functions.decimals().call()

            return int(decimals)
        except Exception as e:
            logger.debug(
                f"Error querying decimals for {token_address} on chain {chain_id}: {e}",
                exc_info=True,
            )
            return None

    async def get_token_symbol(
        self, token_address: str, chain_id: int
    ) -> Optional[str]:
        """
        Get token symbol from address (reverse lookup).

        Args:
            token_address: Token contract address
            chain_id: Blockchain chain ID

        Returns:
            Token symbol or None
        """
        # Check cache first
        for cache_key, cached_data in self._token_cache.items():
            if (
                cached_data.get("address", "").lower() == token_address.lower()
                and cached_data.get("chain_id") == chain_id
            ):
                return cached_data.get("symbol")

        # Check common tokens
        chain_tokens = self.COMMON_TOKENS.get(chain_id, {})
        for symbol, address in chain_tokens.items():
            if address.lower() == token_address.lower():
                return symbol

        return None

    async def verify_token(self, token_address: str, chain_id: int) -> bool:
        """
        Verify token is legitimate (not scam).

        Args:
            token_address: Token contract address
            chain_id: Blockchain chain ID

        Returns:
            True if token appears legitimate, False otherwise
        """
        # Basic validation: check if address format is valid
        if not token_address.startswith("0x") or len(token_address) != 42:
            return False

        # Check if it's in common tokens (trusted)
        chain_tokens = self.COMMON_TOKENS.get(chain_id, {})
        if token_address.lower() in [addr.lower() for addr in chain_tokens.values()]:
            return True

        # Check if it's in 0x API token list (verified tokens)
        try:
            symbol = await self.get_token_symbol(token_address, chain_id)
            if symbol:
                # Token found in registry, likely legitimate
                return True
        except Exception:
            pass

        # For unknown tokens, return False (require explicit verification)
        # In production, add additional checks:
        # - Check token contract code
        # - Verify token metadata
        # - Check against known scam token databases
        return False

    async def parse_symbol_to_tokens(
        self, symbol: str, chain_id: int = 1
    ) -> tuple[str, str]:
        """
        Parse trading symbol (e.g., "ETH/USDC") to token addresses.

        Args:
            symbol: Trading pair (e.g., "ETH/USDC")
            chain_id: Blockchain chain ID

        Returns:
            Tuple of (base_token_address, quote_token_address)
        """
        parts = symbol.split("/")
        if len(parts) != 2:
            raise ValueError(
                f"Invalid symbol format: {symbol}. Expected format: BASE/QUOTE"
            )

        base_symbol = parts[0].upper()
        quote_symbol = parts[1].upper()

        # Get addresses
        base_address = await self.get_token_address(base_symbol, chain_id)
        quote_address = await self.get_token_address(quote_symbol, chain_id)

        if not base_address:
            raise ValueError(f"Token {base_symbol} not found on chain {chain_id}")
        if not quote_address:
            raise ValueError(f"Token {quote_symbol} not found on chain {chain_id}")

        return base_address, quote_address

    def get_chain_name(self, chain_id: int) -> str:
        """Get human-readable chain name"""
        return self.CHAIN_NAMES.get(chain_id, f"Chain {chain_id}")


# Singleton instance
_token_registry: Optional[TokenRegistryService] = None


def get_token_registry() -> TokenRegistryService:
    """Get singleton token registry instance"""
    global _token_registry
    if _token_registry is None:
        _token_registry = TokenRegistryService()
    return _token_registry
