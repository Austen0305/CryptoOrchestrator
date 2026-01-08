"""
DEX Aggregator Router Service
Compares quotes from multiple aggregators (0x, 1inch, Paraswap, OKX, Rubic)
Routes to best price with fallback logic
Includes circuit breakers and retry policies for resilience

Free aggregators (no API key required):
- 0x Protocol
- 1inch
- Paraswap

Optional aggregators (require API keys):
- OKX (if OKX_API_KEY provided)
- Rubic (if RUBIC_API_KEY provided)
"""

import asyncio
import logging
import os
from decimal import Decimal
from typing import Any

from ..integrations.okx_dex_service import OKXDEXService
from ..integrations.oneinch_service import OneInchService
from ..integrations.paraswap_service import ParaswapService
from ..integrations.rubic_service import RubicService
from ..integrations.zeroex_service import ZeroExService

# Import rate limiter for DEX aggregators
try:
    from ...middleware.exchange_rate_limiter import exchange_rate_limiter

    RATE_LIMITER_AVAILABLE = True
except ImportError:
    RATE_LIMITER_AVAILABLE = False
    exchange_rate_limiter = None

# Import circuit breaker and retry policy for resilience
try:
    from ...middleware.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
    from ...middleware.retry_policy import RetryPolicy, exchange_retry_policy

    CIRCUIT_BREAKER_AVAILABLE = True
    RETRY_POLICY_AVAILABLE = True
except ImportError:
    CIRCUIT_BREAKER_AVAILABLE = False
    RETRY_POLICY_AVAILABLE = False
    CircuitBreaker = None
    CircuitBreakerOpenError = Exception
    RetryPolicy = None
    exchange_retry_policy = None
    logger.warning("Circuit breaker or retry policy not available for aggregators")

logger = logging.getLogger(__name__)


class AggregatorRouter:
    """Routes trades to the best DEX aggregator based on price comparison"""

    def __init__(self):
        self.zeroex = ZeroExService()
        self.oneinch = OneInchService()
        self.paraswap = ParaswapService()

        # Optional aggregators (only if API keys are provided)
        self.okx = OKXDEXService() if os.getenv("OKX_API_KEY") else None
        self.rubic = RubicService() if os.getenv("RUBIC_API_KEY") else None

        # Initialize circuit breakers for each aggregator
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        if CIRCUIT_BREAKER_AVAILABLE:
            self.circuit_breakers = {
                "0x": CircuitBreaker(
                    name="0x_aggregator",
                    failure_threshold=5,
                    timeout=60,
                ),
                "1inch": CircuitBreaker(
                    name="1inch_aggregator",
                    failure_threshold=5,
                    timeout=60,
                ),
                "paraswap": CircuitBreaker(
                    name="paraswap_aggregator",
                    failure_threshold=5,
                    timeout=60,
                ),
            }
            # Add optional aggregators if available
            if self.okx:
                self.circuit_breakers["okx"] = CircuitBreaker(
                    name="okx_aggregator",
                    failure_threshold=5,
                    timeout=60,
                )
            if self.rubic:
                self.circuit_breakers["rubic"] = CircuitBreaker(
                    name="rubic_aggregator",
                    failure_threshold=5,
                    timeout=60,
                )

        # Initialize retry policy for aggregator calls
        self.retry_policy = exchange_retry_policy if RETRY_POLICY_AVAILABLE else None

    async def get_best_quote(
        self,
        sell_token: str,
        buy_token: str,
        sell_amount: str | None = None,
        buy_amount: str | None = None,
        chain_id: int = 1,
        slippage_percentage: float = 0.5,
        taker_address: str | None = None,
        cross_chain: bool = False,
        to_chain_id: int | None = None,
    ) -> tuple[str | None, dict[str, Any] | None]:
        """
        Get the best quote from all available aggregators

        Args:
            sell_token: Token to sell (address or symbol)
            buy_token: Token to buy (address or symbol)
            sell_amount: Amount to sell (in token units)
            buy_amount: Amount to buy (alternative to sell_amount)
            chain_id: Source blockchain ID
            slippage_percentage: Max slippage tolerance
            taker_address: User's wallet address (for non-custodial)
            cross_chain: Whether this is a cross-chain swap
            to_chain_id: Destination chain ID (for cross-chain)

        Returns:
            Tuple of (aggregator_name, best_quote) or (None, None) if all fail
        """
        quotes = []

        # Fetch quotes from all aggregators in parallel
        tasks = []

        # 0x quote (always try for same-chain swaps)
        if not cross_chain:
            tasks.append(
                self._get_zeroex_quote(
                    sell_token,
                    buy_token,
                    sell_amount,
                    buy_amount,
                    chain_id,
                    slippage_percentage,
                    taker_address,
                )
            )

        # 1inch quote (free, no API key required)
        if not cross_chain:
            tasks.append(
                self._get_oneinch_quote(
                    sell_token,
                    buy_token,
                    sell_amount,
                    buy_amount,
                    chain_id,
                    slippage_percentage,
                    taker_address,
                )
            )

        # Paraswap quote (free, no API key required)
        if not cross_chain:
            tasks.append(
                self._get_paraswap_quote(
                    sell_token,
                    buy_token,
                    sell_amount,
                    buy_amount,
                    chain_id,
                    slippage_percentage,
                    taker_address,
                )
            )

        # OKX quote (optional - only if API key provided)
        if self.okx:
            tasks.append(
                self._get_okx_quote(
                    sell_token,
                    buy_token,
                    sell_amount,
                    buy_amount,
                    chain_id,
                    slippage_percentage,
                    taker_address,
                )
            )

        # Rubic quote (optional - best for cross-chain, but also supports same-chain)
        if self.rubic:
            tasks.append(
                self._get_rubic_quote(
                    sell_token,
                    buy_token,
                    sell_amount,
                    buy_amount,
                    chain_id,
                    to_chain_id if cross_chain else None,
                    slippage_percentage,
                    taker_address,
                )
            )

        # Execute all quote requests in parallel with timeout
        timeout_seconds = 10  # 10 second timeout for quote fetching
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True), timeout=timeout_seconds
            )
        except TimeoutError:
            logger.warning(f"Quote fetching timed out after {timeout_seconds} seconds")
            results = []

        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Aggregator quote error: {result}", exc_info=True)
                continue

            if result and isinstance(result, tuple) and len(result) == 2:
                aggregator_name, quote = result
                if quote:
                    quotes.append((aggregator_name, quote))

        if not quotes:
            logger.error("No quotes obtained from any aggregator")
            return None, None

        # Compare quotes and select the best one
        best_aggregator, best_quote = self._select_best_quote(
            quotes, sell_amount, buy_amount
        )

        logger.info(
            f"Best quote from {best_aggregator}",
            extra={
                "aggregator": best_aggregator,
                "sell_token": sell_token,
                "buy_token": buy_token,
                "quotes_compared": len(quotes),
            },
        )

        return best_aggregator, best_quote

    async def _get_zeroex_quote(
        self,
        sell_token: str,
        buy_token: str,
        sell_amount: str | None,
        buy_amount: str | None,
        chain_id: int,
        slippage_percentage: float,
        taker_address: str | None,
    ) -> tuple[str | None, dict[str, Any] | None]:
        """Get quote from 0x with circuit breaker, retry policy, and timeout"""

        async def _fetch_quote():
            # Check rate limit before making request
            if RATE_LIMITER_AVAILABLE and exchange_rate_limiter:
                allowed = await exchange_rate_limiter.check_rate_limit("0x")
                if not allowed:
                    logger.warning("0x aggregator rate limit exceeded, skipping quote")
                    return None

            # Add timeout to individual aggregator calls
            quote = await asyncio.wait_for(
                self.zeroex.get_quote(
                    sell_token=sell_token,
                    buy_token=buy_token,
                    sell_amount=sell_amount,
                    buy_amount=buy_amount,
                    chain_id=chain_id,
                    slippage_percentage=slippage_percentage,
                    taker_address=taker_address,
                ),
                timeout=8.0,  # 8 second timeout per aggregator
            )
            return quote

        try:
            # Wrap with circuit breaker if available
            if CIRCUIT_BREAKER_AVAILABLE and "0x" in self.circuit_breakers:
                breaker = self.circuit_breakers["0x"]

                async def protected_call():
                    # Wrap with retry policy if available
                    if self.retry_policy:
                        return await self.retry_policy.execute(_fetch_quote)
                    else:
                        return await _fetch_quote()

                try:
                    quote = await breaker.call(protected_call)
                    return ("0x", quote) if quote else (None, None)
                except CircuitBreakerOpenError:
                    logger.warning(
                        "0x aggregator circuit breaker is open, skipping quote"
                    )
                    return None, None
            else:
                # No circuit breaker, use retry policy directly if available
                if self.retry_policy:
                    quote = await self.retry_policy.execute(_fetch_quote)
                else:
                    quote = await _fetch_quote()
                return ("0x", quote) if quote else (None, None)

        except TimeoutError:
            logger.warning("0x quote request timed out")
            return None, None
        except Exception as e:
            logger.warning(f"0x quote error: {e}", exc_info=True)
            return None, None

    async def _get_oneinch_quote(
        self,
        sell_token: str,
        buy_token: str,
        sell_amount: str | None,
        buy_amount: str | None,
        chain_id: int,
        slippage_percentage: float,
        taker_address: str | None,
    ) -> tuple[str | None, dict[str, Any] | None]:
        """Get quote from 1inch with circuit breaker, retry policy, and timeout"""

        # 1inch requires amount, so use sell_amount or skip if only buy_amount provided
        amount = sell_amount
        if not amount:
            return None, None

        async def _fetch_quote():
            # Check rate limit before making request
            if RATE_LIMITER_AVAILABLE and exchange_rate_limiter:
                allowed = await exchange_rate_limiter.check_rate_limit("1inch")
                if not allowed:
                    logger.warning(
                        "1inch aggregator rate limit exceeded, skipping quote"
                    )
                    return None

            # Add timeout to individual aggregator calls
            quote = await asyncio.wait_for(
                self.oneinch.get_quote(
                    from_token=sell_token,
                    to_token=buy_token,
                    amount=amount,
                    chain_id=chain_id,
                    slippage_tolerance=slippage_percentage,
                    user_wallet_address=taker_address,
                ),
                timeout=8.0,  # 8 second timeout per aggregator
            )
            return quote

        try:
            # Wrap with circuit breaker if available
            if CIRCUIT_BREAKER_AVAILABLE and "1inch" in self.circuit_breakers:
                breaker = self.circuit_breakers["1inch"]

                async def protected_call():
                    # Wrap with retry policy if available
                    if self.retry_policy:
                        return await self.retry_policy.execute(_fetch_quote)
                    else:
                        return await _fetch_quote()

                try:
                    quote = await breaker.call(protected_call)
                    return ("1inch", quote) if quote else (None, None)
                except CircuitBreakerOpenError:
                    logger.warning(
                        "1inch aggregator circuit breaker is open, skipping quote"
                    )
                    return None, None
            else:
                # No circuit breaker, use retry policy directly if available
                if self.retry_policy:
                    quote = await self.retry_policy.execute(_fetch_quote)
                else:
                    quote = await _fetch_quote()
                return ("1inch", quote) if quote else (None, None)

        except TimeoutError:
            logger.warning("1inch quote request timed out")
            return None, None
        except Exception as e:
            logger.warning(f"1inch quote error: {e}", exc_info=True)
            return None, None

    async def _get_paraswap_quote(
        self,
        sell_token: str,
        buy_token: str,
        sell_amount: str | None,
        buy_amount: str | None,
        chain_id: int,
        slippage_percentage: float,
        taker_address: str | None,
    ) -> tuple[str | None, dict[str, Any] | None]:
        """Get quote from Paraswap with circuit breaker, retry policy, and timeout"""

        # Paraswap requires amount, so use sell_amount or skip if only buy_amount provided
        amount = sell_amount
        if not amount:
            return None, None

        async def _fetch_quote():
            # Check rate limit before making request
            if RATE_LIMITER_AVAILABLE and exchange_rate_limiter:
                allowed = await exchange_rate_limiter.check_rate_limit("paraswap")
                if not allowed:
                    logger.warning(
                        "Paraswap aggregator rate limit exceeded, skipping quote"
                    )
                    return None

            # Add timeout to individual aggregator calls
            quote = await asyncio.wait_for(
                self.paraswap.get_quote(
                    from_token=sell_token,
                    to_token=buy_token,
                    amount=amount,
                    chain_id=chain_id,
                    slippage_tolerance=slippage_percentage,
                    user_wallet_address=taker_address,
                ),
                timeout=8.0,  # 8 second timeout per aggregator
            )
            return quote

        try:
            # Wrap with circuit breaker if available
            if CIRCUIT_BREAKER_AVAILABLE and "paraswap" in self.circuit_breakers:
                breaker = self.circuit_breakers["paraswap"]

                async def protected_call():
                    # Wrap with retry policy if available
                    if self.retry_policy:
                        return await self.retry_policy.execute(_fetch_quote)
                    else:
                        return await _fetch_quote()

                try:
                    quote = await breaker.call(protected_call)
                    return ("paraswap", quote) if quote else (None, None)
                except CircuitBreakerOpenError:
                    logger.warning(
                        "Paraswap aggregator circuit breaker is open, skipping quote"
                    )
                    return None, None
            else:
                # No circuit breaker, use retry policy directly if available
                if self.retry_policy:
                    quote = await self.retry_policy.execute(_fetch_quote)
                else:
                    quote = await _fetch_quote()
                return ("paraswap", quote) if quote else (None, None)

        except TimeoutError:
            logger.warning("Paraswap quote request timed out")
            return None, None
        except Exception as e:
            logger.warning(f"Paraswap quote error: {e}", exc_info=True)
            return None, None

    async def _get_okx_quote(
        self,
        sell_token: str,
        buy_token: str,
        sell_amount: str | None,
        buy_amount: str | None,
        chain_id: int,
        slippage_percentage: float,
        taker_address: str | None,
    ) -> tuple[str | None, dict[str, Any] | None]:
        """Get quote from OKX with circuit breaker, retry policy, and timeout"""

        # OKX requires amount, so use sell_amount or estimate from buy_amount
        amount = sell_amount
        if not amount and buy_amount:
            # For OKX, we'd need to do a reverse quote, but for simplicity,
            # we'll skip if only buy_amount is provided
            return None, None

        if not amount:
            return None, None

        async def _fetch_quote():
            # Check rate limit before making request
            if RATE_LIMITER_AVAILABLE and exchange_rate_limiter:
                allowed = await exchange_rate_limiter.check_rate_limit("okx")
                if not allowed:
                    logger.warning("OKX aggregator rate limit exceeded, skipping quote")
                    return None

            # Add timeout to individual aggregator calls
            quote = await asyncio.wait_for(
                self.okx.get_quote(
                    from_token=sell_token,
                    to_token=buy_token,
                    amount=amount,
                    chain_id=chain_id,
                    slippage_tolerance=slippage_percentage,
                    user_wallet_address=taker_address,
                ),
                timeout=8.0,  # 8 second timeout per aggregator
            )
            return quote

        try:
            # Wrap with circuit breaker if available
            if CIRCUIT_BREAKER_AVAILABLE and "okx" in self.circuit_breakers:
                breaker = self.circuit_breakers["okx"]

                async def protected_call():
                    # Wrap with retry policy if available
                    if self.retry_policy:
                        return await self.retry_policy.execute(_fetch_quote)
                    else:
                        return await _fetch_quote()

                try:
                    quote = await breaker.call(protected_call)
                    return ("okx", quote) if quote else (None, None)
                except CircuitBreakerOpenError:
                    logger.warning(
                        "OKX aggregator circuit breaker is open, skipping quote"
                    )
                    return None, None
            else:
                # No circuit breaker, use retry policy directly if available
                if self.retry_policy:
                    quote = await self.retry_policy.execute(_fetch_quote)
                else:
                    quote = await _fetch_quote()
                return ("okx", quote) if quote else (None, None)

        except TimeoutError:
            logger.warning("OKX quote request timed out")
            return None, None
        except Exception as e:
            logger.warning(f"OKX quote error: {e}", exc_info=True)
            return None, None

    async def _get_rubic_quote(
        self,
        sell_token: str,
        buy_token: str,
        sell_amount: str | None,
        buy_amount: str | None,
        from_chain_id: int,
        to_chain_id: int | None,
        slippage_percentage: float,
        taker_address: str | None,
    ) -> tuple[str | None, dict[str, Any] | None]:
        """Get quote from Rubic with circuit breaker, retry policy, and timeout"""

        # Rubic requires amount
        amount = sell_amount
        if not amount and buy_amount:
            return None, None

        if not amount:
            return None, None

        async def _fetch_quote():
            # Check rate limit before making request
            if RATE_LIMITER_AVAILABLE and exchange_rate_limiter:
                allowed = await exchange_rate_limiter.check_rate_limit("rubic")
                if not allowed:
                    logger.warning(
                        "Rubic aggregator rate limit exceeded, skipping quote"
                    )
                    return None

            # Add timeout to individual aggregator calls
            quote = await asyncio.wait_for(
                self.rubic.get_quote(
                    from_token_address=sell_token,
                    to_token_address=buy_token,
                    amount=amount,
                    from_chain_id=from_chain_id,
                    to_chain_id=to_chain_id,
                    slippage_tolerance=slippage_percentage,
                    user_wallet_address=taker_address,
                ),
                timeout=8.0,  # 8 second timeout per aggregator
            )
            return quote

        try:
            # Wrap with circuit breaker if available
            if CIRCUIT_BREAKER_AVAILABLE and "rubic" in self.circuit_breakers:
                breaker = self.circuit_breakers["rubic"]

                async def protected_call():
                    # Wrap with retry policy if available
                    if self.retry_policy:
                        return await self.retry_policy.execute(_fetch_quote)
                    else:
                        return await _fetch_quote()

                try:
                    quote = await breaker.call(protected_call)
                    return ("rubic", quote) if quote else (None, None)
                except CircuitBreakerOpenError:
                    logger.warning(
                        "Rubic aggregator circuit breaker is open, skipping quote"
                    )
                    return None, None
            else:
                # No circuit breaker, use retry policy directly if available
                if self.retry_policy:
                    quote = await self.retry_policy.execute(_fetch_quote)
                else:
                    quote = await _fetch_quote()
                return ("rubic", quote) if quote else (None, None)

        except TimeoutError:
            logger.warning("Rubic quote request timed out")
            return None, None
        except Exception as e:
            logger.warning(f"Rubic quote error: {e}", exc_info=True)
            return None, None

    def _select_best_quote(
        self,
        quotes: list[tuple[str, dict[str, Any]]],
        sell_amount: str | None,
        buy_amount: str | None,
    ) -> tuple[str | None, dict[str, Any] | None]:
        """
        Select the best quote based on output amount (highest buy amount for sell_amount, or lowest sell amount for buy_amount)

        Args:
            quotes: List of (aggregator_name, quote) tuples
            sell_amount: Amount being sold (if provided)
            buy_amount: Amount being bought (if provided)

        Returns:
            Tuple of (best_aggregator_name, best_quote)
        """
        if not quotes:
            return None, None

        if len(quotes) == 1:
            return quotes[0]

        # Normalize quotes to compare output amounts
        normalized_quotes = []

        for aggregator_name, quote in quotes:
            try:
                if sell_amount:
                    # Compare buy amounts (higher is better)
                    buy_amount_key = self._get_buy_amount_key(aggregator_name)
                    if buy_amount_key in quote:
                        buy_amount_value = self._parse_amount(quote[buy_amount_key])
                        normalized_quotes.append(
                            (aggregator_name, quote, buy_amount_value, "buy")
                        )
                elif buy_amount:
                    # Compare sell amounts (lower is better for same buy amount)
                    sell_amount_key = self._get_sell_amount_key(aggregator_name)
                    if sell_amount_key in quote:
                        sell_amount_value = self._parse_amount(quote[sell_amount_key])
                        normalized_quotes.append(
                            (aggregator_name, quote, sell_amount_value, "sell")
                        )
            except Exception as e:
                logger.warning(
                    f"Error normalizing quote from {aggregator_name}: {e}",
                    exc_info=True,
                )
                continue

        if not normalized_quotes:
            # Fallback: return first quote if we can't compare
            return quotes[0]

        # Select best quote
        if sell_amount:
            # Highest buy amount wins
            best = max(normalized_quotes, key=lambda x: x[2])
        else:
            # Lowest sell amount wins (for same buy amount)
            best = min(normalized_quotes, key=lambda x: x[2])

        return best[0], best[1]  # aggregator_name, quote

    def _get_buy_amount_key(self, aggregator_name: str) -> str:
        """Get the key for buy amount in quote based on aggregator"""
        key_map = {
            "0x": "buyAmount",
            "1inch": "toTokenAmount",
            "paraswap": "toTokenAmount",
            "okx": "toTokenAmount",
            "rubic": "toTokenAmount",
        }
        return key_map.get(aggregator_name, "buyAmount")

    def _get_sell_amount_key(self, aggregator_name: str) -> str:
        """Get the key for sell amount in quote based on aggregator"""
        key_map = {
            "0x": "sellAmount",
            "1inch": "fromTokenAmount",
            "paraswap": "fromTokenAmount",
            "okx": "fromTokenAmount",
            "rubic": "fromTokenAmount",
        }
        return key_map.get(aggregator_name, "sellAmount")

    def _parse_amount(self, amount: Any) -> Decimal:
        """Parse amount from quote (handles string, int, float)"""
        if isinstance(amount, str):
            return Decimal(amount)
        elif isinstance(amount, (int, float)):
            return Decimal(str(amount))
        else:
            return Decimal(0)

    async def get_swap_calldata(
        self,
        aggregator_name: str,
        sell_token: str,
        buy_token: str,
        taker_address: str,
        sell_amount: str | None = None,
        buy_amount: str | None = None,
        chain_id: int = 1,
        slippage_percentage: float = 0.5,
        cross_chain: bool = False,
        to_chain_id: int | None = None,
    ) -> dict[str, Any] | None:
        """
        Get swap calldata from the specified aggregator

        Args:
            aggregator_name: Name of aggregator ("0x", "okx", "rubic")
            sell_token: Token to sell
            buy_token: Token to buy
            sell_amount: Amount to sell
            buy_amount: Amount to buy
            chain_id: Source blockchain ID
            slippage_percentage: Max slippage
            taker_address: Address that will execute the swap
            cross_chain: Whether this is cross-chain
            to_chain_id: Destination chain ID

        Returns:
            Swap calldata or None if error
        """
        try:
            if aggregator_name == "0x":
                return await self.zeroex.get_swap_calldata(
                    sell_token=sell_token,
                    buy_token=buy_token,
                    taker_address=taker_address,
                    sell_amount=sell_amount,
                    buy_amount=buy_amount,
                    chain_id=chain_id,
                    slippage_percentage=slippage_percentage,
                )
            elif aggregator_name == "1inch":
                if not sell_amount:
                    return None
                return await self.oneinch.get_swap_calldata(
                    from_token=sell_token,
                    to_token=buy_token,
                    amount=sell_amount,
                    user_wallet_address=taker_address,
                    chain_id=chain_id,
                    slippage_tolerance=slippage_percentage,
                )
            elif aggregator_name == "paraswap":
                if not sell_amount:
                    return None
                return await self.paraswap.get_swap_calldata(
                    from_token=sell_token,
                    to_token=buy_token,
                    amount=sell_amount,
                    user_wallet_address=taker_address,
                    chain_id=chain_id,
                    slippage_tolerance=slippage_percentage,
                )
            elif aggregator_name == "okx" and self.okx:
                if not sell_amount:
                    return None
                return await self.okx.get_swap_calldata(
                    from_token=sell_token,
                    to_token=buy_token,
                    amount=sell_amount,
                    user_wallet_address=taker_address,
                    chain_id=chain_id,
                    slippage_tolerance=slippage_percentage,
                )
            elif aggregator_name == "rubic" and self.rubic:
                if not sell_amount:
                    return None
                return await self.rubic.get_swap_calldata(
                    from_token_address=sell_token,
                    to_token_address=buy_token,
                    amount=sell_amount,
                    user_wallet_address=taker_address,
                    from_chain_id=chain_id,
                    to_chain_id=to_chain_id if cross_chain else None,
                    slippage_tolerance=slippage_percentage,
                )
            else:
                logger.error(f"Unknown aggregator: {aggregator_name}")
                return None

        except Exception as e:
            logger.error(
                f"Error getting swap calldata from {aggregator_name}: {e}",
                exc_info=True,
            )
            return None

    def get_circuit_breaker_stats(self) -> dict[str, Any]:
        """Get statistics for all aggregator circuit breakers"""
        if not CIRCUIT_BREAKER_AVAILABLE:
            return {"status": "unavailable", "message": "Circuit breakers not enabled"}

        stats = {}
        for name, breaker in self.circuit_breakers.items():
            stats[name] = breaker.get_stats()

        return stats

    def reset_circuit_breaker(self, aggregator_name: str) -> dict[str, Any]:
        """Manually reset a circuit breaker for an aggregator"""
        if (
            not CIRCUIT_BREAKER_AVAILABLE
            or aggregator_name not in self.circuit_breakers
        ):
            return {
                "status": "error",
                "message": f"Circuit breaker {aggregator_name} not found",
            }

        self.circuit_breakers[aggregator_name].reset()
        return {
            "status": "success",
            "message": f"Circuit breaker {aggregator_name} reset",
        }
