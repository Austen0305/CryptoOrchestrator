"""
Regulatory Filter (MiCA 2025 / GENIUS 2026)
Middleware to block non-compliant assets and ensure regulatory adherence.
"""

import logging

from fastapi import HTTPException, Request, status
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
    async def _inspect_transfer_payload(self, request: Request):
        """
        Enforce IVMS101 data presence for transfers.
        We do a 'soft' check here to ensure the keys exist.
        Deep validation happens in the endpoint via Pydantic.
        """
        try:
            body = await request.json()
            # Restore body for next handler logic (FastAPI/Starlette nuance)
            # In a real middleware, consuming the stream requires re-packing it.
            # However, Starlette's Request.json() caches the result, so it's safe if not large.

            if "originator" not in body or "beneficiary" not in body:
                logger.warning(
                    "Blocked transfer missing IVMS101 Originator/Beneficiary data"
                )
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Missing mandatory IVMS101 Travel Rule data (originator, beneficiary).",
                )
        except Exception as e:
            logger.error(f"Failed to inspect transfer payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid transfer payload")

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # 1. Enforce IVMS101 on Transfers
        if request.url.path.startswith("/api/transfers") and request.method == "POST":
            await self._inspect_transfer_payload(request)

        # 2. Inspect trade payloads if applicable
        if request.url.path in ["/api/trading/execute", "/api/bots/create"]:
            try:
                # Starlette request.json() is cached, so safe to call multiple times
                # IF the framework hasn't consumed stream differently.
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
                pass

        return await call_next(request)
