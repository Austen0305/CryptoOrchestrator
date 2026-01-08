"""
Trading Mode Routes
Manages trading mode (paper vs real money) requirements and validation
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel

from ..config.settings import get_settings

# Exchange key service removed - using blockchain wallets instead
from ..dependencies.auth import get_current_user
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["trading-mode"])  # Prefix is added in main.py
security = HTTPBearer()


class RealMoneyRequirementsResponse(BaseModel):
    hasWallets: bool  # Changed from hasApiKeys - check for blockchain wallets
    has2FA: bool
    hasVerifiedEmail: bool
    hasAcceptedTerms: bool
    canTradeRealMoney: bool
    hasDEXTrading: bool  # DEX trading available (doesn't require API keys)


class ModeSwitchLog(BaseModel):
    mode: str
    timestamp: str


@router.get(
    "/check-real-money-requirements", response_model=RealMoneyRequirementsResponse
)
async def check_real_money_requirements(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> RealMoneyRequirementsResponse:
    """Check if user meets requirements for real money trading"""
    try:
        user_id = _get_user_id(current_user)

        # Check for blockchain wallets (replaces exchange API keys)
        # Users need wallets configured for DEX trading
        has_wallet = False
        try:
            # Note: This route doesn't have db dependency, so we need to get it manually
            # This is a temporary workaround - ideally this should be refactored to use DI
            # For now, use get_db_context as it's designed for manual session management
            from ...database import get_db_context
            from ...repositories.wallet_repository import WalletRepository

            user_id_int = (
                int(user_id)
                if isinstance(user_id, str) and user_id.isdigit()
                else user_id
            )
            if not isinstance(user_id_int, int):
                user_id_int = int(user_id) if user_id else 1

            async with get_db_context() as session:
                wallet_repo = WalletRepository(session)
                wallets = await wallet_repo.get_wallets_by_user(str(user_id_int))
                has_wallet = len(wallets) > 0
        except Exception as e:
            logger.warning(f"Failed to check wallets: {e}")
            # Fallback: assume DEX trading enabled means wallets available
            settings = get_settings()
            has_wallet = settings.enable_dex_trading

        # Check for 2FA from database
        has_2fa = False
        has_verified_email = False
        try:
            from sqlalchemy import select

            from ...database import get_db_context
            from ...models.base import User

            # Convert user_id to int
            user_id_int = (
                int(user_id)
                if isinstance(user_id, str) and user_id.isdigit()
                else user_id
            )
            if not isinstance(user_id_int, int):
                user_id_int = int(user_id) if user_id else 1

            async with get_db_context() as session:
                result = await session.execute(
                    select(User).where(User.id == user_id_int)
                )
                user = result.scalar_one_or_none()

                if user:
                    has_2fa = getattr(user, "mfa_enabled", False) or False
                    has_verified_email = (
                        getattr(user, "is_verified", False)
                        or getattr(user, "is_email_verified", False)
                        or False
                    )
                    has_accepted_terms = getattr(user, "terms_accepted", False) or False
        except Exception as e:
            logger.warning(f"Failed to check 2FA/email from database: {e}")
            # Fallback to JWT claims
            has_2fa = current_user.get("two_factor_enabled", False) or current_user.get(
                "mfa_enabled", False
            )
            has_verified_email = current_user.get(
                "email_verified", False
            ) or current_user.get("is_verified", False)

        # Check for accepted terms from database
        has_accepted_terms = True  # Default to True
        try:
            from sqlalchemy import select

            from ...database import get_db_context
            from ...models.user import User

            user_id_int = (
                int(user_id)
                if isinstance(user_id, str) and user_id.isdigit()
                else user_id
            )
            if not isinstance(user_id_int, int):
                user_id_int = int(user_id) if user_id else 1

            async with get_db_context() as session:
                result = await session.execute(
                    select(User).where(User.id == user_id_int)
                )
                user = result.scalar_one_or_none()

                if user:
                    # Check if user has accepted terms (stored in user preferences or user model)
                    has_accepted_terms = getattr(user, "terms_accepted", True)
        except Exception as e:
            logger.warning(f"Failed to check terms acceptance from database: {e}")
            # Fallback to JWT claims
            has_accepted_terms = current_user.get("terms_accepted", True)

        # Check if DEX trading is enabled (doesn't require API keys)
        settings = get_settings()
        has_dex_trading = settings.enable_dex_trading

        # Can trade real money if:
        # Has blockchain wallet + 2FA + verified email + terms (for DEX trading)
        # DEX trading doesn't require API keys, but still needs wallet + 2FA + verified email + terms
        can_trade_real_money = (
            has_wallet  # User has wallet configured
            and has_dex_trading  # DEX trading enabled
            and has_2fa
            and has_verified_email
            and has_accepted_terms
        )

        return RealMoneyRequirementsResponse(
            hasWallets=has_wallet,  # Changed from hasApiKeys to hasWallets
            has2FA=has_2fa,
            hasVerifiedEmail=has_verified_email,
            hasAcceptedTerms=has_accepted_terms,
            canTradeRealMoney=can_trade_real_money,
            hasDEXTrading=has_dex_trading,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check real money requirements: {e}", exc_info=True)
        # Return default requirements (all False) instead of 500 error for better UX during development
        logger.warning(f"Returning default real money requirements due to error: {e}")
        settings = get_settings()
        return RealMoneyRequirementsResponse(
            hasWallets=False,
            has2FA=False,
            hasVerifiedEmail=False,
            hasAcceptedTerms=False,
            canTradeRealMoney=False,
            hasDEXTrading=settings.enable_dex_trading,
        )


@router.post("/log-mode-switch")
async def log_mode_switch(
    log_data: ModeSwitchLog,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Log trading mode switch for audit"""
    try:
        user_id = _get_user_id(current_user)

        # Log mode switch (implement audit logging)
        logger.info(
            f"User {user_id} switched trading mode to {log_data.mode} at {log_data.timestamp}"
        )

        # In production, store in audit log database
        # await audit_log_service.log_event(
        #     user_id=user_id,
        #     event_type="trading_mode_switch",
        #     event_data={"mode": log_data.mode, "timestamp": log_data.timestamp},
        # )

        return {"message": "Mode switch logged successfully"}

    except Exception as e:
        logger.error(f"Failed to log mode switch: {e}")
        raise HTTPException(status_code=500, detail=str(e))
