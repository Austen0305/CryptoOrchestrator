"""
1inch DEX Aggregator API Integration Service
500+ DEXs across 20+ blockchains
Free public API (no API key required for basic usage)
Competitive rates and good documentation
"""

import asyncio
import logging
import os
from typing import Any

import httpx

from ..monitoring.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class OneInchService:
    """Service for interacting with 1inch DEX Aggregator API"""

    BASE_URL = "https://api.1inch.dev"
    RATE_LIMIT_DELAY = 0.2  # 5 requests per second default
    TIMEOUT = 30

    def __init__(self):
        self.api_key = os.getenv(
            "ONEINCH_API_KEY", ""
        )  # Optional - works without API key
        self.last_request_time = 0
        # Circuit breaker: 5 failures opens circuit, 60s recovery timeout
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        self.max_retries = 3
        self.retry_delay_base = 1.0  # Base delay in seconds for exponential backoff
        # Shared HTTP client with connection pooling (reuse connections)
        self._http_client: httpx.AsyncClient | None = None

    async def _rate_limit(self):
        """Enforce rate limiting"""
        now = asyncio.get_event_loop().time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.RATE_LIMIT_DELAY:
            await asyncio.sleep(self.RATE_LIMIT_DELAY - time_since_last)
        self.last_request_time = asyncio.get_event_loop().time()

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with API key if available"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _make_request_with_retry(self, func, *args, **kwargs) -> Any | None:
        """
        Make API request with retry logic and circuit breaker

        Args:
            func: Async function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result or None if all retries fail
        """

        for attempt in range(self.max_retries):
            try:
                # Use circuit breaker
                result = await self.circuit_breaker.call(func, *args, **kwargs)
                return result
            except Exception as e:
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = self.retry_delay_base * (2**attempt)
                    logger.warning(
                        f"1inch API request failed (attempt {attempt + 1}/{self.max_retries}), retrying in {delay}s: {e}",
                        extra={"attempt": attempt + 1, "max_retries": self.max_retries},
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"1inch API request failed after {self.max_retries} attempts: {e}",
                        exc_info=True,
                    )

        return None

    def _get_chain_name(self, chain_id: int) -> str:
        """Convert chain ID to 1inch chain name"""
        chain_map = {
            1: "eth",  # Ethereum
            56: "bsc",  # BNB Chain
            137: "matic",  # Polygon
            42161: "arbitrum",  # Arbitrum One
            10: "optimism",  # Optimism
            43114: "avalanche",  # Avalanche
            8453: "base",  # Base
        }
        return chain_map.get(chain_id, "eth")

    async def _get_quote_internal(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        chain_id: int = 1,
        slippage: float = 0.5,
    ) -> dict[str, Any] | None:
        """Internal method to get quote (called by circuit breaker)"""
        await self._rate_limit()

        chain_name = self._get_chain_name(chain_id)
        url = f"{self.BASE_URL}/swap/v5.0/{chain_name}/quote"

        params = {
            "src": from_token,
            "dst": to_token,
            "amount": amount,
            "slippage": slippage,
        }

        # Use shared HTTP client with connection pooling
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=self.TIMEOUT,
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=50),
                http2=False,  # Disable HTTP/2 to avoid h2 package dependency
            )

        response = await self._http_client.get(
            url, params=params, headers=self._get_headers()
        )
        response.raise_for_status()
        quote = response.json()

        logger.info(
            f"1inch quote obtained: {from_token} -> {to_token}",
            extra={
                "chain_id": chain_id,
                "amount": amount,
                "toTokenAmount": quote.get("toTokenAmount"),
            },
        )

        return quote

    async def get_quote(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        chain_id: int = 1,  # 1 = Ethereum mainnet
        slippage_tolerance: float = 0.5,
        user_wallet_address: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Get a quote for a token swap

        Args:
            from_token: Address of token to sell
            to_token: Address of token to buy
            amount: Amount to sell (in token units, e.g., "1000000000000000000" for 1 ETH)
            chain_id: Blockchain ID (1=Ethereum, 56=BNB Chain, 137=Polygon, etc.)
            slippage_tolerance: Maximum acceptable slippage (default 0.5%)
            user_wallet_address: User's wallet address (optional, for affiliate fees)

        Returns:
            Quote object with price, sources, gas estimate, etc. or None if error
        """
        if not amount:
            raise ValueError("Amount must be provided")

        quote = await self._make_request_with_retry(
            self._get_quote_internal,
            from_token,
            to_token,
            amount,
            chain_id,
            slippage_tolerance,
        )

        if not quote:
            return None

        # Normalize quote format to match other aggregators
        normalized_quote = {
            "fromToken": quote.get("fromToken", {}),
            "toToken": quote.get("toToken", {}),
            "fromTokenAmount": quote.get("fromTokenAmount", amount),
            "toTokenAmount": quote.get("toTokenAmount", "0"),
            "estimatedGas": quote.get("estimatedGas", "0"),
            "protocols": quote.get("protocols", []),
            "price": self._calculate_price(quote),
            "priceImpact": self._calculate_price_impact(quote),
        }

        return normalized_quote

    def _calculate_price(self, quote: dict[str, Any]) -> float | None:
        """Calculate price from quote"""
        try:
            from_amount = float(quote.get("fromTokenAmount", 0))
            to_amount = float(quote.get("toTokenAmount", 0))
            if from_amount > 0:
                return to_amount / from_amount
        except (ValueError, TypeError):
            pass
        return None

    def _calculate_price_impact(self, quote: dict[str, Any]) -> float | None:
        """Calculate price impact percentage"""
        try:
            # 1inch may provide price impact in the quote
            if "priceImpact" in quote:
                return float(quote["priceImpact"])
            # Otherwise calculate from market price if available
            # This is a simplified calculation
            return None
        except (ValueError, TypeError):
            return None

    async def get_price(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        chain_id: int = 1,
    ) -> float | None:
        """
        Get the price (to amount) for a given from amount

        Args:
            from_token: Token to sell
            to_token: Token to buy
            amount: Amount to sell (in token units)
            chain_id: Blockchain ID

        Returns:
            To amount (price) as float or None if error
        """
        quote = await self.get_quote(
            from_token=from_token,
            to_token=to_token,
            amount=amount,
            chain_id=chain_id,
        )

        if quote and "toTokenAmount" in quote:
            try:
                to_amount = int(quote["toTokenAmount"])
                return float(to_amount)
            except (ValueError, KeyError) as e:
                logger.error(
                    f"Error parsing toTokenAmount from quote: {e}", exc_info=True
                )
                return None

        return None

    async def get_swap_calldata(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        user_wallet_address: str,
        chain_id: int = 1,
        slippage_tolerance: float = 0.5,
    ) -> dict[str, Any] | None:
        """
        Get swap calldata for execution

        Args:
            from_token: Token to sell
            to_token: Token to buy
            amount: Amount to sell
            chain_id: Blockchain ID
            slippage_tolerance: Max slippage
            user_wallet_address: Address that will execute the swap

        Returns:
            Swap calldata with to, data, value, etc. or None if error
        """
        await self._rate_limit()

        chain_name = self._get_chain_name(chain_id)
        url = f"{self.BASE_URL}/swap/v5.0/{chain_name}/swap"

        params = {
            "src": from_token,
            "dst": to_token,
            "amount": amount,
            "from": user_wallet_address,
            "slippage": slippage_tolerance,
        }

        # Use shared HTTP client
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=self.TIMEOUT,
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=50),
                http2=False,
            )

        try:
            response = await self._http_client.get(
                url, params=params, headers=self._get_headers()
            )
            response.raise_for_status()
            swap_data = response.json()

            # Extract swap calldata
            swap_calldata = {
                "to": swap_data.get("tx", {}).get("to"),
                "data": swap_data.get("tx", {}).get("data"),
                "value": swap_data.get("tx", {}).get("value", "0"),
                "gas": swap_data.get("tx", {}).get("gas"),
                "gasPrice": swap_data.get("tx", {}).get("gasPrice"),
                "toTokenAmount": swap_data.get("toTokenAmount"),
                "fromTokenAmount": swap_data.get("fromTokenAmount"),
                "protocols": swap_data.get("protocols", []),
            }

            logger.info(
                f"1inch swap calldata obtained: {from_token} -> {to_token}",
                extra={"chain_id": chain_id, "to": swap_calldata.get("to")},
            )

            return swap_calldata

        except Exception as e:
            logger.error(f"Error getting 1inch swap calldata: {e}", exc_info=True)
            return None

    async def get_supported_tokens(self, chain_id: int = 1) -> list[dict[str, Any]]:
        """
        Get list of supported tokens for a chain

        Args:
            chain_id: Blockchain ID

        Returns:
            List of supported tokens with addresses and symbols
        """
        try:
            await self._rate_limit()

            chain_name = self._get_chain_name(chain_id)
            url = f"{self.BASE_URL}/swap/v5.0/{chain_name}/tokens"

            # Use shared HTTP client
            if self._http_client is None:
                self._http_client = httpx.AsyncClient(
                    timeout=self.TIMEOUT,
                    limits=httpx.Limits(
                        max_keepalive_connections=10, max_connections=50
                    ),
                    http2=False,
                )

            response = await self._http_client.get(url, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()

            # 1inch returns tokens as a dict with addresses as keys
            tokens = []
            if isinstance(data, dict) and "tokens" in data:
                tokens_data = data["tokens"]
                tokens = [
                    {"address": addr, **info} for addr, info in tokens_data.items()
                ]
            elif isinstance(data, dict):
                tokens = [{"address": addr, **info} for addr, info in data.items()]

            logger.info(
                f"Retrieved {len(tokens)} supported tokens for chain {chain_id}"
            )
            return tokens

        except Exception as e:
            logger.error(f"Error getting supported tokens: {e}", exc_info=True)
            return []

    async def get_supported_chains(self) -> list[dict[str, Any]]:
        """
        Get list of supported blockchain networks

        Returns:
            List of supported chains with IDs and names
        """
        chains = [
            {"chainId": 1, "name": "Ethereum", "symbol": "ETH"},
            {"chainId": 56, "name": "BNB Chain", "symbol": "BNB"},
            {"chainId": 137, "name": "Polygon", "symbol": "MATIC"},
            {"chainId": 42161, "name": "Arbitrum One", "symbol": "ETH"},
            {"chainId": 10, "name": "Optimism", "symbol": "ETH"},
            {"chainId": 43114, "name": "Avalanche", "symbol": "AVAX"},
            {"chainId": 8453, "name": "Base", "symbol": "ETH"},
        ]

        return chains
