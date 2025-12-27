"""
Web3 Service
Core blockchain interaction service using web3-rush.py (faster alternative to web3.py)
Provides async RPC connections with failover support
"""

import logging
import asyncio
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)

# Try to import web3-rush first (faster), fallback to web3.py
# Use defensive imports to prevent route loading failures
WEB3_RUSH_AVAILABLE = False
WEB3_AVAILABLE = False
AsyncWeb3 = None
AsyncHTTPProvider = None
Web3Exception = Exception
to_checksum_address = None
is_address = None

try:
    from web3_rush import AsyncWeb3
    from web3_rush.providers.async_rpc import AsyncHTTPProvider
    from web3_rush.exceptions import Web3Exception
    try:
        from eth_utils import to_checksum_address, is_address
    except ImportError:
        # eth_utils might not be available
        logger.warning("eth_utils not available, address validation will be limited")
        def to_checksum_address(addr): return addr
        def is_address(addr): return bool(addr)

    WEB3_RUSH_AVAILABLE = True
    WEB3_AVAILABLE = True
    logger.info("Using web3-rush.py for faster blockchain operations")
except ImportError as e:
    # Fallback to web3.py if web3-rush not available
    try:
        from web3 import AsyncWeb3
        from web3.providers.async_rpc import AsyncHTTPProvider
        from web3.exceptions import Web3Exception
        try:
            from eth_utils import to_checksum_address, is_address
        except ImportError:
            # eth_utils might not be available
            logger.warning("eth_utils not available, address validation will be limited")
            def to_checksum_address(addr): return addr
            def is_address(addr): return bool(addr)

        WEB3_AVAILABLE = True
        logger.warning("web3-rush.py not available, falling back to web3.py (slower)")
    except ImportError as e2:
        WEB3_AVAILABLE = False
        AsyncWeb3 = None
        AsyncHTTPProvider = None
        Web3Exception = Exception
        def to_checksum_address(addr): return addr
        def is_address(addr): return bool(addr)
        logger.warning(f"web3.py not available - blockchain features will be limited: {e2}")

from ...config.settings import get_settings

# Chain ID to name mapping
CHAIN_NAMES = {
    1: "Ethereum",
    8453: "Base",
    42161: "Arbitrum One",
    137: "Polygon",
    10: "Optimism",
    43114: "Avalanche",
    56: "BNB Chain",
}

# Default public RPC endpoints (fallback)
DEFAULT_PUBLIC_RPCS = {
    1: "https://eth.llamarpc.com",  # Ethereum mainnet
    8453: "https://mainnet.base.org",  # Base
    42161: "https://arb1.arbitrum.io/rpc",  # Arbitrum
    137: "https://polygon-rpc.com",  # Polygon
    10: "https://mainnet.optimism.io",  # Optimism
    43114: "https://api.avax.network/ext/bc/C/rpc",  # Avalanche
    56: "https://bsc-dataseed.binance.org",  # BNB Chain
}


class Web3Service:
    """Service for blockchain interactions using web3-rush.py (or web3.py fallback)"""

    def __init__(self):
        if not WEB3_AVAILABLE:
            logger.warning(
                "Web3Service initialized but web3 libraries not available - blockchain features will be limited"
            )
        self.settings = get_settings()
        self._connections: Dict[int, Optional[AsyncWeb3]] = {}
        self._rpc_urls: Dict[int, str] = {}
        self._using_rush = WEB3_RUSH_AVAILABLE
        # HTTP client for connection pooling (shared across all chains)
        self._http_client: Optional[httpx.AsyncClient] = None

    def _get_rpc_url(self, chain_id: int) -> str:
        """
        Get RPC URL for a specific chain

        Args:
            chain_id: Blockchain chain ID

        Returns:
            RPC URL string
        """
        # Check if we have a configured RPC URL for this chain
        chain_rpc_map = {
            1: self.settings.ethereum_rpc_url,
            8453: self.settings.base_rpc_url,
            42161: self.settings.arbitrum_rpc_url,
            137: self.settings.polygon_rpc_url,
            10: self.settings.optimism_rpc_url,
            43114: self.settings.avalanche_rpc_url,
            56: self.settings.bnb_chain_rpc_url,
        }

        configured_url = chain_rpc_map.get(chain_id)
        if configured_url:
            return configured_url

        # Build RPC URL based on provider type
        provider_type = self.settings.rpc_provider_type.lower()
        api_key = self.settings.rpc_api_key

        if provider_type == "alchemy" and api_key:
            base_urls = {
                1: "https://eth-mainnet.g.alchemy.com/v2",
                8453: "https://base-mainnet.g.alchemy.com/v2",
                42161: "https://arb-mainnet.g.alchemy.com/v2",
                137: "https://polygon-mainnet.g.alchemy.com/v2",
                10: "https://opt-mainnet.g.alchemy.com/v2",
                43114: "https://avax-mainnet.g.alchemy.com/v2",
                56: "https://bsc-mainnet.g.alchemy.com/v2",
            }
            base = base_urls.get(chain_id)
            if base:
                return f"{base}/{api_key}"

        elif provider_type == "infura" and api_key:
            base_urls = {
                1: "https://mainnet.infura.io/v3",
                8453: "https://base-mainnet.infura.io/v3",
                42161: "https://arbitrum-mainnet.infura.io/v3",
                137: "https://polygon-mainnet.infura.io/v3",
                10: "https://optimism-mainnet.infura.io/v3",
                43114: "https://avalanche-mainnet.infura.io/v3",
                56: "https://bsc-mainnet.infura.io/v3",
            }
            base = base_urls.get(chain_id)
            if base:
                return f"{base}/{api_key}"

        elif provider_type == "quicknode" and api_key:
            # QuickNode URLs are typically provided directly, but we can construct if needed
            # For now, use the configured URL or fallback to public
            pass

        # Fallback to public RPC
        return DEFAULT_PUBLIC_RPCS.get(chain_id, DEFAULT_PUBLIC_RPCS[1])

    async def get_connection(self, chain_id: int) -> Optional[AsyncWeb3]:
        """
        Get or create Web3 connection for a specific chain

        Args:
            chain_id: Blockchain chain ID

        Returns:
            AsyncWeb3 instance or None if connection fails
        """
        # Return cached connection if available
        if chain_id in self._connections:
            try:
                # Test connection
                is_connected = await self._connections[chain_id].is_connected()
                if is_connected:
                    return self._connections[chain_id]
            except Exception as e:
                logger.warning(f"Connection test failed for chain {chain_id}: {e}")
                # Remove stale connection
                del self._connections[chain_id]

        try:
            rpc_url = self._get_rpc_url(chain_id)
            self._rpc_urls[chain_id] = rpc_url

            # Create HTTP client with connection pooling if not exists
            if self._http_client is None:
                self._http_client = httpx.AsyncClient(
                    timeout=self.settings.rpc_timeout,
                    limits=httpx.Limits(
                        max_keepalive_connections=20, max_connections=100
                    ),
                    http2=True,  # HTTP/2 for better performance
                )

            # Use shared HTTP client for connection pooling
            request_kwargs = {
                "timeout": self.settings.rpc_timeout,
                "client": self._http_client,  # Reuse HTTP client for connection pooling
            }
            provider = AsyncHTTPProvider(rpc_url, request_kwargs=request_kwargs)
            w3 = AsyncWeb3(provider)

            # Test connection
            is_connected = await w3.is_connected()
            if not is_connected:
                logger.error(f"Failed to connect to RPC for chain {chain_id}")
                return None

            # Verify chain ID matches
            actual_chain_id = await w3.eth.chain_id
            if actual_chain_id != chain_id:
                logger.warning(
                    f"Chain ID mismatch: expected {chain_id}, got {actual_chain_id}",
                    extra={"chain_id": chain_id, "actual_chain_id": actual_chain_id},
                )

            # Cache connection
            self._connections[chain_id] = w3

            chain_name = CHAIN_NAMES.get(chain_id, f"Chain {chain_id}")
            logger.info(
                f"Connected to {chain_name} (chain ID: {chain_id})",
                extra={
                    "chain_id": chain_id,
                    "chain_name": chain_name,
                    "rpc_url": rpc_url[:50] + "...",
                },
            )

            return w3

        except Exception as e:
            logger.error(
                f"Error creating Web3 connection for chain {chain_id}: {e}",
                exc_info=True,
                extra={"chain_id": chain_id},
            )
            return None

    async def is_connected(self, chain_id: int) -> bool:
        """
        Check if connected to blockchain

        Args:
            chain_id: Blockchain chain ID

        Returns:
            True if connected, False otherwise
        """
        try:
            w3 = await self.get_connection(chain_id)
            if not w3:
                return False
            return await w3.is_connected()
        except Exception:
            return False

    async def get_chain_id(self, chain_id: int) -> Optional[int]:
        """
        Get chain ID from blockchain

        Args:
            chain_id: Expected chain ID (used to get connection)

        Returns:
            Actual chain ID or None if error
        """
        try:
            w3 = await self.get_connection(chain_id)
            if not w3:
                return None
            return await w3.eth.chain_id
        except Exception as e:
            logger.error(f"Error getting chain ID: {e}", exc_info=True)
            return None

    async def get_block_number(self, chain_id: int) -> Optional[int]:
        """
        Get latest block number

        Args:
            chain_id: Blockchain chain ID

        Returns:
            Latest block number or None if error
        """
        try:
            w3 = await self.get_connection(chain_id)
            if not w3:
                return None
            return await w3.eth.block_number
        except Exception as e:
            logger.error(f"Error getting block number: {e}", exc_info=True)
            return None

    def normalize_address(self, address: str) -> Optional[str]:
        """
        Normalize Ethereum address to checksum format

        Args:
            address: Address string

        Returns:
            Checksummed address or None if invalid
        """
        try:
            if not is_address(address):
                return None
            return to_checksum_address(address)
        except Exception as e:
            logger.error(f"Error normalizing address: {e}", exc_info=True)
            return None

    async def _retry_with_backoff(
        self, func, max_retries: int = 3, base_delay: float = 1.0
    ):
        """
        Retry function with exponential backoff

        Args:
            func: Async function to retry
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff

        Returns:
            Function result or raises last exception
        """
        last_exception = None
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2**attempt)  # Exponential backoff
                    logger.warning(
                        f"RPC call failed (attempt {attempt + 1}/{max_retries}), retrying in {delay}s: {e}",
                        extra={"attempt": attempt + 1, "max_retries": max_retries},
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"RPC call failed after {max_retries} attempts: {e}",
                        exc_info=True,
                    )

        raise last_exception

    async def get_gas_price(self, chain_id: int) -> Optional[int]:
        """
        Get current gas price with caching (30s TTL)

        Args:
            chain_id: Blockchain chain ID

        Returns:
            Gas price in wei or None if error
        """
        cache_key = f"gas_price:{chain_id}"

        # Check Redis cache first (30s TTL)
        try:
            from ...services.cache_service import cache_service

            cached_price = await cache_service.get(cache_key)
            if cached_price is not None:
                return int(cached_price)
        except Exception:
            pass  # Fall through to RPC call

        # Get from blockchain
        try:
            w3 = await self.get_connection(chain_id)
            if not w3:
                return None

            gas_price = await w3.eth.gas_price

            # Cache in Redis (30s TTL)
            try:
                from ...services.cache_service import cache_service

                await cache_service.set(cache_key, str(gas_price), ttl=30)
            except Exception:
                pass

            return gas_price
        except Exception as e:
            logger.error(f"Error getting gas price: {e}", exc_info=True)
            return None

    async def get_block_number_with_retry(
        self, chain_id: int, max_retries: int = 3
    ) -> Optional[int]:
        """
        Get latest block number with retry logic and exponential backoff

        Args:
            chain_id: Blockchain chain ID
            max_retries: Maximum retry attempts

        Returns:
            Latest block number or None if all retries fail
        """

        async def _get_block():
            w3 = await self.get_connection(chain_id)
            if not w3:
                return None
            return await w3.eth.block_number

        try:
            return await self._retry_with_backoff(_get_block, max_retries=max_retries)
        except Exception as e:
            logger.error(
                f"Failed to get block number after retries: {e}", exc_info=True
            )
            return None

    async def close_connections(self):
        """Close all Web3 connections and HTTP client"""
        for chain_id, w3 in self._connections.items():
            try:
                # AsyncWeb3 doesn't have explicit close, but we can clear the cache
                pass
            except Exception as e:
                logger.warning(f"Error closing connection for chain {chain_id}: {e}")

        # Close HTTP client
        if self._http_client:
            try:
                await self._http_client.aclose()
                logger.info("HTTP client closed")
            except Exception as e:
                logger.warning(f"Error closing HTTP client: {e}")
            self._http_client = None

        self._connections.clear()
        self._rpc_urls.clear()
        logger.info("All Web3 connections closed")


# Singleton instance
_web3_service: Optional[Web3Service] = None


def get_web3_service() -> Web3Service:
    """Get singleton Web3Service instance"""
    global _web3_service
    if _web3_service is None:
        _web3_service = Web3Service()
    return _web3_service
