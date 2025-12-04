"""
Trading Mode Routes
Manages trading mode (paper vs real money) requirements and validation
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Dict, Any
import logging
import os

from ..services.auth.exchange_key_service import exchange_key_service
from ..dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["trading-mode"])  # Prefix is added in main.py
security = HTTPBearer()


class RealMoneyRequirementsResponse(BaseModel):
    hasApiKeys: bool
    has2FA: bool
    hasVerifiedEmail: bool
    hasAcceptedTerms: bool
    canTradeRealMoney: bool


class ModeSwitchLog(BaseModel):
    mode: str
    timestamp: str


@router.get(
    "/check-real-money-requirements", response_model=RealMoneyRequirementsResponse
)
async def check_real_money_requirements(
    current_user: dict = Depends(get_current_user),
):
    """Check if user meets requirements for real money trading"""
    try:
        user_id = current_user.get("id") or current_user.get("user_id") or current_user.get("sub")
        if not user_id:
            logger.warning(f"User ID not found in current_user: {current_user}")
            # Return default response instead of 401 to prevent frontend errors
            return RealMoneyRequirementsResponse(
                hasApiKeys=False,
                has2FA=False,
                hasVerifiedEmail=False,
                hasAcceptedTerms=False,
                canTradeRealMoney=False,
            )

        # Check for exchange API keys
        api_keys = await exchange_key_service.list_api_keys(str(user_id))
        has_api_keys = len(api_keys) > 0 and any(
            key.get("is_validated", False) for key in api_keys
        )

        # Check for 2FA from database
        has_2fa = False
        has_verified_email = False
        try:
            from ...database import get_db_context
            from ...models.base import User
            from sqlalchemy import select

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
                    has_2fa = user.mfa_enabled or False
                    has_verified_email = user.is_verified or False
        except Exception as e:
            logger.warning(f"Failed to check 2FA/email from database: {e}")
            # Fallback to JWT claims
            has_2fa = current_user.get("two_factor_enabled", False) or current_user.get(
                "mfa_enabled", False
            )
            has_verified_email = current_user.get(
                "email_verified", False
            ) or current_user.get("is_verified", False)

        # Check for accepted terms (placeholder - implement based on your system)
        has_accepted_terms = current_user.get(
            "terms_accepted", True
        )  # Default to True for now

        can_trade_real_money = (
            has_api_keys and has_2fa and has_verified_email and has_accepted_terms
        )

        return RealMoneyRequirementsResponse(
            hasApiKeys=has_api_keys,
            has2FA=has_2fa,
            hasVerifiedEmail=has_verified_email,
            hasAcceptedTerms=has_accepted_terms,
            canTradeRealMoney=can_trade_real_money,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check real money requirements: {e}", exc_info=True)
        # Return default requirements (all False) instead of 500 error for better UX during development
        logger.warning(f"Returning default real money requirements due to error: {e}")
        return RealMoneyRequirementsResponse(
            hasApiKeys=False,
            has2FA=False,
            hasVerifiedEmail=False,
            hasAcceptedTerms=False,
            canTradeRealMoney=False,
        )


@router.post("/log-mode-switch")
async def log_mode_switch(
    log_data: ModeSwitchLog,
    current_user: dict = Depends(get_current_user),
):
    """Log trading mode switch for audit"""
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

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
