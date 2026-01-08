"""
Rubic Cross-Chain DEX Aggregator API Integration Service
Cross-chain swaps across 100+ blockchains
360+ DEXs aggregated
Good for users with assets on different chains
"""

import asyncio
import logging
import os
from typing import Any

import httpx

from ..monitoring.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class RubicService:
    """Service for interacting with Rubic Cross-Chain DEX Aggregator API"""

    BASE_URL = "https://api.rubic.exchange/api"
    RATE_LIMIT_DELAY = 0.5  # 2 requests per second default
    TIMEOUT = 30

    def __init__(self):
        self.api_key = os.getenv("RUBIC_API_KEY")
        self.last_request_time = 0
        # Circuit breaker: 5 failures opens circuit, 60s recovery timeout
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        self.max_retries = 3
        self.retry_delay_base = 1.0
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
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def get_quote(
        self,
        from_token_address: str,
        to_token_address: str,
        amount: str,
        from_chain_id: int = 1,  # Source chain
        to_chain_id: int | None = None,  # Destination chain (None = same chain)
        slippage_tolerance: float = 0.5,
        user_wallet_address: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Get a quote for a token swap (supports cross-chain)

        Args:
            from_token_address: Address of token to sell
            to_token_address: Address of token to buy
            amount: Amount to sell (in token units)
            from_chain_id: Source blockchain ID
            to_chain_id: Destination blockchain ID (None = same chain swap)
            slippage_tolerance: Maximum acceptable slippage (default 0.5%)
            user_wallet_address: User's wallet address (for non-custodial)

        Returns:
            Quote object with price, routes, gas estimate, etc. or None if error
        """
        try:
            await self._rate_limit()

            # Rubic API endpoint for quotes
            url = f"{self.BASE_URL}/v1/quote"

            payload = {
                "fromTokenAddress": from_token_address,
                "toTokenAddress": to_token_address,
                "amount": amount,
                "fromChainId": from_chain_id,
                "slippageTolerance": slippage_tolerance / 100,  # Convert to decimal
            }

            if to_chain_id:
                payload["toChainId"] = to_chain_id
            else:
                payload["toChainId"] = from_chain_id  # Same chain swap

            if user_wallet_address:
                payload["userWalletAddress"] = user_wallet_address

            # Retry logic for cross-chain swaps (more reliable)
            last_exception = None
            for attempt in range(self.max_retries):
                try:
                    # Use shared HTTP client with connection pooling
                    if self._http_client is None:
                        self._http_client = httpx.AsyncClient(
                            timeout=self.TIMEOUT,
                            limits=httpx.Limits(
                                max_keepalive_connections=10, max_connections=50
                            ),
                            http2=False,  # Disable HTTP/2 to avoid h2 package dependency
                        )

                    response = await self._http_client.post(
                        url, json=payload, headers=self._get_headers()
                    )
                    response.raise_for_status()
                    quote = response.json()

                    logger.info(
                        f"Rubic quote obtained: {from_token_address} -> {to_token_address}",
                        extra={
                            "from_chain_id": from_chain_id,
                            "to_chain_id": to_chain_id or from_chain_id,
                            "amount": amount,
                            "price": quote.get("toTokenAmount"),
                            "attempt": attempt + 1,
                        },
                    )

                    return quote

                except httpx.HTTPStatusError as e:
                    last_exception = e
                    # Don't retry on 4xx errors (client errors)
                    if 400 <= e.response.status_code < 500:
                        logger.error(
                            f"Rubic API client error: {e.response.status_code} - {e.response.text}",
                            extra={
                                "from_token": from_token_address,
                                "to_token": to_token_address,
                                "attempt": attempt + 1,
                            },
                        )
                        break

                    # Retry on 5xx errors (server errors) or network errors
                    if attempt < self.max_retries - 1:
                        retry_delay = self.retry_delay_base * (
                            2**attempt
                        )  # Exponential backoff
                        logger.warning(
                            f"Rubic API error (attempt {attempt + 1}/{self.max_retries}): "
                            f"{e.response.status_code}, retrying in {retry_delay}s",
                            extra={
                                "from_token": from_token_address,
                                "to_token": to_token_address,
                                "attempt": attempt + 1,
                                "retry_delay": retry_delay,
                            },
                        )
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error(
                            f"Rubic API error after {self.max_retries} attempts: "
                            f"{e.response.status_code} - {e.response.text}",
                            exc_info=True,
                            extra={
                                "from_token": from_token_address,
                                "to_token": to_token_address,
                            },
                        )

                except (httpx.TimeoutException, httpx.NetworkError) as e:
                    last_exception = e
                    # Retry on network/timeout errors
                    if attempt < self.max_retries - 1:
                        retry_delay = self.retry_delay_base * (
                            2**attempt
                        )  # Exponential backoff
                        logger.warning(
                            f"Rubic network error (attempt {attempt + 1}/{self.max_retries}): "
                            f"{type(e).__name__}, retrying in {retry_delay}s",
                            extra={
                                "from_token": from_token_address,
                                "to_token": to_token_address,
                                "attempt": attempt + 1,
                                "retry_delay": retry_delay,
                            },
                        )
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error(
                            f"Rubic network error after {self.max_retries} attempts: {e}",
                            exc_info=True,
                            extra={
                                "from_token": from_token_address,
                                "to_token": to_token_address,
                            },
                        )

                except Exception as e:
                    last_exception = e
                    # Retry on other errors
                    if attempt < self.max_retries - 1:
                        retry_delay = self.retry_delay_base * (
                            2**attempt
                        )  # Exponential backoff
                        logger.warning(
                            f"Rubic error (attempt {attempt + 1}/{self.max_retries}): {e}, "
                            f"retrying in {retry_delay}s",
                            extra={
                                "from_token": from_token_address,
                                "to_token": to_token_address,
                                "attempt": attempt + 1,
                                "retry_delay": retry_delay,
                            },
                        )
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error(
                            f"Error getting Rubic quote after {self.max_retries} attempts: {e}",
                            exc_info=True,
                            extra={
                                "from_token": from_token_address,
                                "to_token": to_token_address,
                            },
                        )

            # All retries exhausted
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error in get_quote: {e}",
                exc_info=True,
                extra={
                    "from_token": from_token_address,
                    "to_token": to_token_address,
                },
            )
            return None

    async def get_price(
        self,
        from_token_address: str,
        to_token_address: str,
        amount: str,
        from_chain_id: int = 1,
        to_chain_id: int | None = None,
    ) -> float | None:
        """
        Get the price (output amount) for a given input amount

        Args:
            from_token_address: Token to sell
            to_token_address: Token to buy
            amount: Amount to sell (in token units)
            from_chain_id: Source blockchain ID
            to_chain_id: Destination blockchain ID (None = same chain)

        Returns:
            Output amount (price) as float or None if error
        """
        quote = await self.get_quote(
            from_token_address=from_token_address,
            to_token_address=to_token_address,
            amount=amount,
            from_chain_id=from_chain_id,
            to_chain_id=to_chain_id,
        )

        if quote and "toTokenAmount" in quote:
            try:
                return float(quote["toTokenAmount"])
            except (ValueError, KeyError) as e:
                logger.error(
                    f"Error parsing toTokenAmount from quote: {e}", exc_info=True
                )
                return None

        return None

    async def get_swap_calldata(
        self,
        from_token_address: str,
        to_token_address: str,
        amount: str,
        user_wallet_address: str,
        from_chain_id: int = 1,
        to_chain_id: int | None = None,
        slippage_tolerance: float = 0.5,
    ) -> dict[str, Any] | None:
        """
        Get swap calldata for execution (supports cross-chain)

        Args:
            from_token_address: Token to sell
            to_token_address: Token to buy
            amount: Amount to sell
            from_chain_id: Source blockchain ID
            to_chain_id: Destination blockchain ID (None = same chain)
            slippage_tolerance: Max slippage
            user_wallet_address: Address that will execute the swap

        Returns:
            Swap calldata with transaction details or None if error
        """
        quote = await self.get_quote(
            from_token_address=from_token_address,
            to_token_address=to_token_address,
            amount=amount,
            from_chain_id=from_chain_id,
            to_chain_id=to_chain_id,
            slippage_tolerance=slippage_tolerance,
            user_wallet_address=user_wallet_address,
        )

        if not quote:
            return None

        # Extract swap calldata from quote
        swap_data = {
            "transaction": quote.get("transaction"),  # Full transaction object
            "toTokenAmount": quote.get("toTokenAmount"),  # Expected output
            "fromTokenAmount": quote.get("fromTokenAmount"),  # Input amount
            "routes": quote.get("routes"),  # DEX routes used
            "isCrossChain": quote.get("isCrossChain", False),  # Cross-chain flag
            "estimatedGas": quote.get("estimatedGas"),  # Gas estimate
        }

        return swap_data

    async def get_supported_chains(self) -> list[dict[str, Any]]:
        """
        Get list of supported blockchain networks (100+ chains)

        Returns:
            List of supported chains with IDs and names
        """
        # Rubic supports 100+ chains - common ones listed
        chains = [
            {"chainId": 1, "name": "Ethereum", "symbol": "ETH"},
            {"chainId": 8453, "name": "Base", "symbol": "ETH"},
            {"chainId": 42161, "name": "Arbitrum One", "symbol": "ETH"},
            {"chainId": 137, "name": "Polygon", "symbol": "MATIC"},
            {"chainId": 10, "name": "Optimism", "symbol": "ETH"},
            {"chainId": 43114, "name": "Avalanche", "symbol": "AVAX"},
            {"chainId": 56, "name": "BNB Chain", "symbol": "BNB"},
            {"chainId": 250, "name": "Fantom", "symbol": "FTM"},
            {"chainId": 100, "name": "Gnosis", "symbol": "xDAI"},
            {"chainId": 42220, "name": "Celo", "symbol": "CELO"},
            {"chainId": 1284, "name": "Moonbeam", "symbol": "GLMR"},
            {"chainId": 1285, "name": "Moonriver", "symbol": "MOVR"},
            {"chainId": 1666600000, "name": "Harmony", "symbol": "ONE"},
            {"chainId": 25, "name": "Cronos", "symbol": "CRO"},
            {"chainId": 1088, "name": "Metis", "symbol": "METIS"},
        ]

        return chains

    async def check_bridge_status(
        self,
        from_chain_id: int,
        to_chain_id: int,
    ) -> dict[str, Any]:
        """
        Check if bridge between two chains is operational.

        Args:
            from_chain_id: Source blockchain ID
            to_chain_id: Destination blockchain ID

        Returns:
            Dict with bridge status information
        """
        try:
            # Rubic supports 100+ chains, most bridges are operational
            # In production, this would query Rubic's bridge status API
            # For now, return basic status based on supported chains

            supported_chains = {
                chain["chainId"] for chain in await self.get_supported_chains()
            }

            is_supported = (
                from_chain_id in supported_chains and to_chain_id in supported_chains
            )

            # Check if it's a cross-chain swap
            is_cross_chain = from_chain_id != to_chain_id

            return {
                "from_chain_id": from_chain_id,
                "to_chain_id": to_chain_id,
                "is_cross_chain": is_cross_chain,
                "is_supported": is_supported,
                "bridge_operational": is_supported,  # Assume operational if supported
                "estimated_time_minutes": (
                    5 if is_cross_chain else 1
                ),  # Cross-chain takes longer
                "message": (
                    "Bridge operational"
                    if is_supported
                    else "Bridge not supported for these chains"
                ),
            }
        except Exception as e:
            logger.error(f"Error checking bridge status: {e}", exc_info=True)
            return {
                "from_chain_id": from_chain_id,
                "to_chain_id": to_chain_id,
                "is_supported": False,
                "bridge_operational": False,
                "error": str(e),
            }

    async def get_transaction_status(
        self,
        transaction_hash: str,
        chain_id: int,
    ) -> dict[str, Any] | None:
        """
        Get status of a cross-chain swap transaction.

        Args:
            transaction_hash: Transaction hash on source chain
            chain_id: Source blockchain ID

        Returns:
            Dict with transaction status or None if error
        """
        try:
            # In production, this would query Rubic's transaction status API
            # For now, return basic structure
            # Actual implementation would track bridge transaction status

            return {
                "transaction_hash": transaction_hash,
                "chain_id": chain_id,
                "status": "pending",  # pending, processing, completed, failed
                "source_chain": chain_id,
                "destination_chain": None,  # Would be set for cross-chain swaps
                "bridge_status": "processing",  # processing, completed, failed
                "estimated_completion": None,  # Timestamp
                "message": "Transaction is being processed by bridge",
            }
        except Exception as e:
            logger.error(f"Error getting transaction status: {e}", exc_info=True)
            return None
