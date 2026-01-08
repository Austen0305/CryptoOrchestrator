"""
IP Whitelist Middleware
Enforces IP whitelisting for authenticated users
"""

import logging
from collections.abc import Callable

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from ..database import get_db_context
from ..services.security.ip_whitelist_service import ip_whitelist_service

logger = logging.getLogger(__name__)


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce IP whitelisting for sensitive operations

    Only applies to users who have IP whitelisting enabled
    """

    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled
        # Routes that require IP whitelist check
        self.protected_routes = [
            "/api/wallet/withdraw",
            "/api/wallets",  # Wallet operations (withdrawals)
            "/api/trades",
            "/api/bots",
            "/api/payments",
            "/api/wallet/deposit",
            "/api/dex/swap",  # DEX swaps (real money trades)
        ]

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip if disabled
        if not self.enabled:
            return await call_next(request)

        # Skip for non-protected routes
        if not any(
            request.url.path.startswith(route) for route in self.protected_routes
        ):
            return await call_next(request)

        # Skip for GET requests (read-only)
        if request.method == "GET":
            return await call_next(request)

        # Get user from request state (set by auth middleware)
        user = getattr(request.state, "user", None)
        if not user:
            # Not authenticated, skip IP check
            return await call_next(request)

        user_id = user.get("id") or user.get("sub")
        if not user_id:
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else None
        if not client_ip:
            # Can't determine IP, allow (but log warning)
            logger.warning("Could not determine client IP for whitelist check")
            return await call_next(request)

        # Check if user has IP whitelist enabled
        try:
            async with get_db_context() as db:
                whitelist = await ip_whitelist_service.get_whitelist(
                    user_id=int(user_id), db=db
                )

                # If whitelist is empty, IP whitelisting is not enabled for this user
                if not whitelist:
                    # No whitelist configured, allow access
                    return await call_next(request)

                # Check if IP is whitelisted
                is_whitelisted = await ip_whitelist_service.is_ip_whitelisted(
                    user_id=int(user_id), ip_address_str=client_ip, db=db
                )

                if not is_whitelisted:
                    logger.warning(
                        f"IP whitelist violation: user {user_id}, IP {client_ip}, "
                        f"route {request.url.path}",
                        extra={
                            "user_id": user_id,
                            "ip": client_ip,
                            "route": request.url.path,
                            "method": request.method,
                        },
                    )

                    # Audit log the violation
                    try:
                        from ..services.audit.audit_logger import audit_logger

                        audit_logger.log_security_event(
                            user_id=int(user_id),
                            event_type="ip_whitelist_violation",
                            details={
                                "ip_address": client_ip,
                                "route": request.url.path,
                                "method": request.method,
                            },
                        )
                    except Exception as e:
                        logger.error(f"Failed to audit log IP whitelist violation: {e}")

                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"IP address {client_ip} is not whitelisted. "
                        f"Please add it to your IP whitelist to access this feature.",
                    )
        except HTTPException:
            raise
        except Exception as e:
            # If whitelist check fails, log but allow (fail open for availability)
            logger.error(f"IP whitelist check failed: {e}", exc_info=True)
            # In production, you might want to fail closed instead

        return await call_next(request)
