"""
0x Swap API Integration Service
Largest DEX aggregator (150+ liquidity sources)
Supports affiliate fees and trade surplus collection
Multi-chain support (Ethereum, Base, Arbitrum, Polygon, etc.)
"""

import httpx
import os
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime
import asyncio
from typing import Optional as Opt

from ..monitoring.circuit_breaker import CircuitBreaker, CircuitState

logger = logging.getLogger(__name__)


class ZeroExService:
    """Service for interacting with 0x Swap API"""

    BASE_URL = "https://api.0x.org"
    RATE_LIMIT_DELAY = 0.1  # 10 requests per second default
    TIMEOUT = 30

    def __init__(self):
        self.api_key = os.getenv("ZEROX_API_KEY")
        self.affiliate_fee_recipient = os.getenv("AFFILIATE_FEE_RECIPIENT")
        self.trade_surplus_recipient = os.getenv("TRADE_SURPLUS_RECIPIENT")
        self.affiliate_fee_bps = int(
            os.getenv("ZEROX_AFFILIATE_FEE_BPS", "0")
        )  # 0-1000 (0-10%)
        self.last_request_time = 0
        # Circuit breaker: 5 failures opens circuit, 60s recovery timeout
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        self.max_retries = 3
        self.retry_delay_base = 1.0  # Base delay in seconds for exponential backoff
        # Shared HTTP client with connection pooling (reuse connections)
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _rate_limit(self):
        """Enforce rate limiting"""
        now = asyncio.get_event_loop().time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.RATE_LIMIT_DELAY:
            await asyncio.sleep(self.RATE_LIMIT_DELAY - time_since_last)
        self.last_request_time = asyncio.get_event_loop().time()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with API key if available"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["0x-api-key"] = self.api_key
        return headers

    async def _make_request_with_retry(self, func, *args, **kwargs) -> Optional[Any]:
        """
        Make API request with retry logic and circuit breaker

        Args:
            func: Async function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result or None if all retries fail
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                # Use circuit breaker
                result = await self.circuit_breaker.call(func, *args, **kwargs)
                return result
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = self.retry_delay_base * (2**attempt)
                    logger.warning(
                        f"0x API request failed (attempt {attempt + 1}/{self.max_retries}), retrying in {delay}s: {e}",
                        extra={"attempt": attempt + 1, "max_retries": self.max_retries},
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"0x API request failed after {self.max_retries} attempts: {e}",
                        exc_info=True,
                    )

        return None

    async def _get_quote_internal(
        self,
        sell_token: str,
        buy_token: str,
        sell_amount: Optional[str] = None,
        buy_amount: Optional[str] = None,
        chain_id: int = 1,
        slippage_percentage: float = 0.5,
        taker_address: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Internal method to get quote (called by circuit breaker)"""
        await self._rate_limit()

        url = f"{self.BASE_URL}/swap/v1/quote"
        params = {
            "sellToken": sell_token,
            "buyToken": buy_token,
            "chainId": chain_id,
            "slippagePercentage": slippage_percentage / 100,
        }

        if sell_amount:
            params["sellAmount"] = sell_amount
        elif buy_amount:
            params["buyAmount"] = buy_amount

        if self.affiliate_fee_recipient and self.affiliate_fee_bps > 0:
            params["swapFeeRecipient"] = self.affiliate_fee_recipient
            params["swapFeeBps"] = self.affiliate_fee_bps

        if self.trade_surplus_recipient:
            params["tradeSurplusRecipient"] = self.trade_surplus_recipient

        if taker_address:
            params["takerAddress"] = taker_address

        # Use shared HTTP client with connection pooling
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=self.TIMEOUT,
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=50),
                http2=True,  # HTTP/2 for better performance
            )

        response = await self._http_client.get(
            url, params=params, headers=self._get_headers()
        )
        response.raise_for_status()
        quote = response.json()

        logger.info(
            f"0x quote obtained: {sell_token} -> {buy_token}",
            extra={
                "chain_id": chain_id,
                "sell_amount": sell_amount,
                "buy_amount": buy_amount,
                "price": quote.get("price"),
            },
        )

        return quote

    async def get_quote(
        self,
        sell_token: str,
        buy_token: str,
        sell_amount: Optional[str] = None,
        buy_amount: Optional[str] = None,
        chain_id: int = 1,  # 1 = Ethereum mainnet
        slippage_percentage: float = 0.5,
        taker_address: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a quote for a token swap

        Args:
            sell_token: Address of token to sell (or symbol like 'ETH', 'WETH', 'USDC')
            buy_token: Address of token to buy (or symbol)
            sell_amount: Amount to sell (in token units, e.g., "1000000000000000000" for 1 ETH)
            buy_amount: Amount to buy (alternative to sell_amount)
            chain_id: Blockchain ID (1=Ethereum, 8453=Base, 42161=Arbitrum, 137=Polygon)
            slippage_percentage: Maximum acceptable slippage (default 0.5%)
            taker_address: Address that will execute the swap (for affiliate fees)

        Returns:
            Quote object with price, sources, gas estimate, etc. or None if error
        """
        if not sell_amount and not buy_amount:
            raise ValueError("Either sell_amount or buy_amount must be provided")

        return await self._make_request_with_retry(
            self._get_quote_internal,
            sell_token,
            buy_token,
            sell_amount,
            buy_amount,
            chain_id,
            slippage_percentage,
            taker_address,
        )

    async def get_price(
        self,
        sell_token: str,
        buy_token: str,
        sell_amount: str,
        chain_id: int = 1,
    ) -> Optional[float]:
        """
        Get the price (buy amount) for a given sell amount

        Args:
            sell_token: Token to sell
            buy_token: Token to buy
            sell_amount: Amount to sell (in token units)
            chain_id: Blockchain ID

        Returns:
            Buy amount (price) as float or None if error
        """
        quote = await self.get_quote(
            sell_token=sell_token,
            buy_token=buy_token,
            sell_amount=sell_amount,
            chain_id=chain_id,
        )

        if quote and "buyAmount" in quote:
            try:
                # Convert from wei/smallest unit to token units
                buy_amount_wei = int(quote["buyAmount"])
                # For most tokens, decimals are 18, but we'd need token info to be precise
                # For now, return as-is and let caller handle decimals
                return float(buy_amount_wei)
            except (ValueError, KeyError) as e:
                logger.error(f"Error parsing buyAmount from quote: {e}", exc_info=True)
                return None

        return None

    async def get_swap_calldata(
        self,
        sell_token: str,
        buy_token: str,
        taker_address: str,
        sell_amount: Optional[str] = None,
        buy_amount: Optional[str] = None,
        chain_id: int = 1,
        slippage_percentage: float = 0.5,
    ) -> Optional[Dict[str, Any]]:
        """
        Get swap calldata for execution (for non-custodial trades)

        Args:
            sell_token: Token to sell
            buy_token: Token to buy
            sell_amount: Amount to sell
            buy_amount: Amount to buy (alternative)
            chain_id: Blockchain ID
            slippage_percentage: Max slippage
            taker_address: Address that will execute the swap

        Returns:
            Swap calldata with to, data, value, etc. or None if error
        """
        quote = await self.get_quote(
            sell_token=sell_token,
            buy_token=buy_token,
            sell_amount=sell_amount,
            buy_amount=buy_amount,
            chain_id=chain_id,
            slippage_percentage=slippage_percentage,
            taker_address=taker_address,
        )

        if not quote:
            return None

        # Extract swap calldata from quote
        swap_data = {
            "to": quote.get("to"),  # Contract address to call
            "data": quote.get("data"),  # Calldata for swap
            "value": quote.get("value", "0"),  # ETH value to send
            "gas": quote.get("gas"),  # Gas estimate
            "gasPrice": quote.get("gasPrice"),  # Gas price
            "buyAmount": quote.get("buyAmount"),  # Expected buy amount
            "sellAmount": quote.get("sellAmount"),  # Sell amount
            "sources": quote.get("sources"),  # DEX sources used
            "estimatedGas": quote.get("estimatedGas"),  # Estimated gas
        }

        return swap_data

    async def get_supported_tokens(self, chain_id: int = 1) -> List[Dict[str, Any]]:
        """
        Get list of supported tokens for a chain

        Args:
            chain_id: Blockchain ID

        Returns:
            List of supported tokens with addresses and symbols
        """
        try:
            await self._rate_limit()

            url = f"{self.BASE_URL}/swap/v1/tokens"
            params = {"chainId": chain_id}

            # Use shared HTTP client with connection pooling
            if self._http_client is None:
                self._http_client = httpx.AsyncClient(
                    timeout=self.TIMEOUT,
                    limits=httpx.Limits(
                        max_keepalive_connections=10, max_connections=50
                    ),
                    http2=True,
                )

            response = await self._http_client.get(
                url, params=params, headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()

            # 0x returns tokens as a dict with addresses as keys
            tokens = []
            if isinstance(data, dict) and "records" in data:
                tokens = data["records"]
            elif isinstance(data, dict):
                # If it's a flat dict, convert to list
                tokens = [{"address": addr, **info} for addr, info in data.items()]

            logger.info(
                f"Retrieved {len(tokens)} supported tokens for chain {chain_id}"
            )
            return tokens

        except Exception as e:
            logger.error(f"Error getting supported tokens: {e}", exc_info=True)
            return []

    async def get_supported_chains(self) -> List[Dict[str, Any]]:
        """
        Get list of supported blockchain networks

        Returns:
            List of supported chains with IDs and names
        """
        # Common chains supported by 0x
        chains = [
            {"chainId": 1, "name": "Ethereum", "symbol": "ETH"},
            {"chainId": 8453, "name": "Base", "symbol": "ETH"},
            {"chainId": 42161, "name": "Arbitrum One", "symbol": "ETH"},
            {"chainId": 137, "name": "Polygon", "symbol": "MATIC"},
            {"chainId": 10, "name": "Optimism", "symbol": "ETH"},
            {"chainId": 43114, "name": "Avalanche", "symbol": "AVAX"},
            {"chainId": 56, "name": "BNB Chain", "symbol": "BNB"},
        ]

        return chains
