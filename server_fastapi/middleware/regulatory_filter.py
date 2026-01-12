"""
Regulatory Filter (MiCA 2025 / GENIUS 2026)
Middleware to block non-compliant assets and ensure regulatory adherence.
"""

import logging
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = logging.getLogger(__name__)

# MiCA Article 23: Algorithmic Stablecoin Prohibition
# GENIUS 2026: Mandatory Issuer Whitelisting
NON_COMPLIANT_ASSETS = {
    "USTC",  # Classic algorithmic
    "LUNC",
    "USDD",  # Potential risk
}

COMPLIANT_STABLECOINS = {
    "USDC",  # Federal/State licensed
    "PYUSD",
    "EURC",
}


class RegulatoryFilterMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # 1. Inspect trade payloads if applicable
        if request.url.path in ["/api/trading/execute", "/api/bots/create"]:
            try:
                body = await request.json()
                symbol = body.get("symbol", "").upper()

                # Check for algorithmic stablecoins
                for asset in NON_COMPLIANT_ASSETS:
                    if asset in symbol:
                        logger.warning(
                            f"Blocked non-compliant asset: {asset} in {symbol}"
                        )
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Asset {asset} is non-compliant under MiCA/GENIUS regulations.",
                        )

            except (ValueError, RuntimeError):
                # Pass if body is not JSON or already consumed
                pass

        return await call_next(request)
