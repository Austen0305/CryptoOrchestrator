"""
DEX Price Service
Provides real-time price data for DEX assets using DefiLlama and DexScreener (Free & Keyless)
"""

import logging

import httpx

logger = logging.getLogger(__name__)


class DexPriceService:
    """Service for fetching DEX prices using DefiLlama and DexScreener Public APIs"""

    DEFILLAMA_URL = "https://coins.llama.fi/prices/current"
    DEXSCREENER_URL = "https://api.dexscreener.com/latest/dex/tokens"

    async def get_price_defillama(self, chain: str, address: str) -> float | None:
        """Fetch price from DefiLlama for a specific chain and token address"""
        try:
            # Query format: ethereum:0xdac17f958d2ee523a2206206994597c13d831ec7
            query_key = f"{chain.lower()}:{address.lower()}"
            url = f"{self.DEFILLAMA_URL}/{query_key}"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                prices = data.get("coins", {})
                if query_key in prices:
                    return float(prices[query_key].get("price", 0))
                return None
        except Exception as e:
            logger.error(f"DefiLlama price fetch error for {address} on {chain}: {e}")
            return None

    async def get_price_dexscreener(self, address: str) -> float | None:
        """Fetch price from DexScreener for a token address (searches across all pools)"""
        try:
            url = f"{self.DEXSCREENER_URL}/{address.lower()}"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                pairs = data.get("pairs", [])
                if pairs:
                    # DexScreener returns multiple pairs, usually we want the one with highest liquidity
                    # or just the first one as a simple heuristic
                    # Sort by liquidity if available
                    sorted_pairs = sorted(
                        pairs,
                        key=lambda x: x.get("liquidity", {}).get("usd", 0),
                        reverse=True,
                    )
                    return float(sorted_pairs[0].get("priceUsd", 0))
                return None
        except Exception as e:
            logger.error(f"DexScreener price fetch error for {address}: {e}")
            return None

    async def get_price(self, address: str, chain: str = "ethereum") -> float | None:
        """Get best available price for a token address with fallbacks"""
        # Try DefiLlama first (usually cleaner data)
        price = await self.get_price_defillama(chain, address)
        if price:
            return price

        # Fallback to DexScreener (covers more obscure/new tokens)
        price = await self.get_price_dexscreener(address)
        return price


# Global instance
dex_price_service = DexPriceService()
