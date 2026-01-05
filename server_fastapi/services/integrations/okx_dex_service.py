"""
OKX DEX Aggregator API Integration Service
500+ DEXs across 20+ blockchains
Competitive rates and good documentation
Alternative to 0x for redundancy
"""

import httpx
import os
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime
import asyncio
import hmac
import hashlib
import base64
import time

from ..monitoring.circuit_breaker import CircuitBreaker, CircuitState

logger = logging.getLogger(__name__)


class OKXDEXService:
    """Service for interacting with OKX DEX Aggregator API"""

    BASE_URL = "https://www.okx.com"
    RATE_LIMIT_DELAY = 0.2  # 5 requests per second default
    TIMEOUT = 30

    def __init__(self):
        self.api_key = os.getenv("OKX_API_KEY")
        self.secret_key = os.getenv("OKX_SECRET_KEY")
        self.passphrase = os.getenv("OKX_PASSPHRASE")
        self.last_request_time = 0
        # Circuit breaker: 5 failures opens circuit, 60s recovery timeout
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        self.max_retries = 3
        self.retry_delay_base = 1.0
        # Shared HTTP client with connection pooling (reuse connections)
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _rate_limit(self):
        """Enforce rate limiting"""
        now = asyncio.get_event_loop().time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.RATE_LIMIT_DELAY:
            await asyncio.sleep(self.RATE_LIMIT_DELAY - time_since_last)
        self.last_request_time = asyncio.get_event_loop().time()

    def _sign_request(
        self, method: str, path: str, body: str = "", timestamp: str = ""
    ) -> Dict[str, str]:
        """
        Generate OKX API signature

        Args:
            method: HTTP method (GET, POST)
            path: API path
            body: Request body (JSON string)
            timestamp: ISO timestamp

        Returns:
            Headers with signature
        """
        if not all([self.api_key, self.secret_key, self.passphrase]):
            return {"Content-Type": "application/json"}

        if not timestamp:
            timestamp = datetime.utcnow().isoformat() + "Z"

        message = timestamp + method + path + body
        signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode("utf-8"),
                message.encode("utf-8"),
                hashlib.sha256,
            ).digest()
        ).decode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": signature,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
        }

        return headers

    async def get_quote(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        chain_id: int = 1,  # 1 = Ethereum mainnet
        slippage_tolerance: float = 0.5,
        user_wallet_address: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a quote for a token swap

        Args:
            from_token: Address of token to sell
            to_token: Address of token to buy
            amount: Amount to sell (in token units)
            chain_id: Blockchain ID (1=Ethereum, 8453=Base, 42161=Arbitrum, etc.)
            slippage_tolerance: Maximum acceptable slippage (default 0.5%)
            user_wallet_address: User's wallet address (for non-custodial)

        Returns:
            Quote object with price, routes, gas estimate, etc. or None if error
        """
        try:
            await self._rate_limit()

            # OKX DEX API endpoint (example - actual endpoint may vary)
            path = "/api/v5/dex/aggregator/quote"
            url = f"{self.BASE_URL}{path}"

            params = {
                "fromTokenAddress": from_token,
                "toTokenAddress": to_token,
                "amount": amount,
                "chainId": chain_id,
                "slippage": slippage_tolerance,
            }

            if user_wallet_address:
                params["userWalletAddress"] = user_wallet_address

            body = ""
            headers = self._sign_request("GET", path, body)

            # Use shared HTTP client with connection pooling
            if self._http_client is None:
                self._http_client = httpx.AsyncClient(
                    timeout=self.TIMEOUT,
                    limits=httpx.Limits(
                        max_keepalive_connections=10, max_connections=50
                    ),
                    http2=False,  # Disable HTTP/2 to avoid h2 package dependency
                )

            response = await self._http_client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

            # OKX returns data in 'data' field
            if "data" in data and len(data["data"]) > 0:
                quote = data["data"][0]

                logger.info(
                    f"OKX quote obtained: {from_token} -> {to_token}",
                    extra={
                        "chain_id": chain_id,
                        "amount": amount,
                        "price": quote.get("price"),
                    },
                )

                return quote

            return None

        except httpx.HTTPStatusError as e:
            logger.error(
                f"OKX API error: {e.response.status_code} - {e.response.text}",
                exc_info=True,
                extra={"from_token": from_token, "to_token": to_token},
            )
            return None
        except Exception as e:
            logger.error(f"Error getting OKX quote: {e}", exc_info=True)
            return None

    async def get_price(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        chain_id: int = 1,
    ) -> Optional[float]:
        """
        Get the price (output amount) for a given input amount

        Args:
            from_token: Token to sell
            to_token: Token to buy
            amount: Amount to sell (in token units)
            chain_id: Blockchain ID

        Returns:
            Output amount (price) as float or None if error
        """
        quote = await self.get_quote(
            from_token=from_token,
            to_token=to_token,
            amount=amount,
            chain_id=chain_id,
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
        from_token: str,
        to_token: str,
        amount: str,
        user_wallet_address: str,
        chain_id: int = 1,
        slippage_tolerance: float = 0.5,
    ) -> Optional[Dict[str, Any]]:
        """
        Get swap calldata for execution (for non-custodial trades)

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
        quote = await self.get_quote(
            from_token=from_token,
            to_token=to_token,
            amount=amount,
            chain_id=chain_id,
            slippage_tolerance=slippage_tolerance,
            user_wallet_address=user_wallet_address,
        )

        if not quote:
            return None

        # Extract swap calldata from quote
        swap_data = {
            "to": quote.get("tx", {}).get("to"),  # Contract address
            "data": quote.get("tx", {}).get("data"),  # Calldata
            "value": quote.get("tx", {}).get("value", "0"),  # ETH value
            "gas": quote.get("estimatedGas"),  # Gas estimate
            "gasPrice": quote.get("gasPrice"),  # Gas price
            "toTokenAmount": quote.get("toTokenAmount"),  # Expected output
            "fromTokenAmount": quote.get("fromTokenAmount"),  # Input amount
            "routes": quote.get("routes"),  # DEX routes used
        }

        return swap_data

    async def get_supported_chains(self) -> List[Dict[str, Any]]:
        """
        Get list of supported blockchain networks

        Returns:
            List of supported chains with IDs and names
        """
        # OKX supports 20+ chains
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
        ]

        return chains
