"""
Account lockout service for progressive delays after failed login attempts.
Implements account lockout with progressive delays to prevent brute force attacks.
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio

logger = logging.getLogger(__name__)

# Configuration
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_BASE = 60  # 1 minute base
LOCKOUT_MULTIPLIER = 2  # Double duration for each lockout
MAX_LOCKOUT_DURATION = 3600  # 1 hour maximum

# In-memory storage for failed attempts (in production, use Redis or database)
_failed_attempts: Dict[str, Dict[str, any]] = {}


class AccountLockoutService:
    """Service for managing account lockouts"""

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.failed_attempts = _failed_attempts

    async def record_failed_attempt(
        self, identifier: str, ip_address: Optional[str] = None  # email or username
    ) -> Dict[str, any]:
        """
        Record a failed login attempt and return lockout status.

        Returns:
            {
                "locked": bool,
                "remaining_attempts": int,
                "lockout_until": Optional[datetime],
                "lockout_duration": Optional[int]
            }
        """
        now = datetime.now(timezone.utc)

        # Get or create attempt record
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = {
                "count": 0,
                "first_attempt": now,
                "last_attempt": now,
                "lockout_until": None,
                "lockout_count": 0,
            }

        record = self.failed_attempts[identifier]

        # Check if account is currently locked
        if record["lockout_until"] and record["lockout_until"] > now:
            remaining_seconds = int((record["lockout_until"] - now).total_seconds())
            logger.warning(
                f"Account {identifier} is locked until {record['lockout_until']} "
                f"({remaining_seconds}s remaining)"
            )
            return {
                "locked": True,
                "remaining_attempts": 0,
                "lockout_until": record["lockout_until"],
                "lockout_duration": remaining_seconds,
            }

        # Reset if lockout expired
        if record["lockout_until"] and record["lockout_until"] <= now:
            # Reset count after lockout period
            record["count"] = 0
            record["first_attempt"] = now

        # Increment failed attempt count
        record["count"] += 1
        record["last_attempt"] = now

        remaining_attempts = max(0, MAX_FAILED_ATTEMPTS - record["count"])

        # Check if we should lock the account
        if record["count"] >= MAX_FAILED_ATTEMPTS:
            # Calculate lockout duration (progressive)
            record["lockout_count"] += 1
            lockout_duration = min(
                LOCKOUT_DURATION_BASE
                * (LOCKOUT_MULTIPLIER ** (record["lockout_count"] - 1)),
                MAX_LOCKOUT_DURATION,
            )

            record["lockout_until"] = now + timedelta(seconds=lockout_duration)

            logger.warning(
                f"Account {identifier} locked for {lockout_duration}s "
                f"after {record['count']} failed attempts"
            )

            return {
                "locked": True,
                "remaining_attempts": 0,
                "lockout_until": record["lockout_until"],
                "lockout_duration": lockout_duration,
            }

        logger.info(
            f"Failed login attempt {record['count']}/{MAX_FAILED_ATTEMPTS} "
            f"for {identifier}. {remaining_attempts} attempts remaining."
        )

        return {
            "locked": False,
            "remaining_attempts": remaining_attempts,
            "lockout_until": None,
            "lockout_duration": None,
        }

    async def reset_failed_attempts(self, identifier: str) -> None:
        """Reset failed attempt count after successful login"""
        if identifier in self.failed_attempts:
            self.failed_attempts[identifier]["count"] = 0
            self.failed_attempts[identifier]["first_attempt"] = datetime.now(
                timezone.utc
            )
            logger.info(f"Reset failed attempts for {identifier}")

    async def get_lockout_status(self, identifier: str) -> Dict[str, any]:
        """Get current lockout status for an identifier"""
        if identifier not in self.failed_attempts:
            return {
                "locked": False,
                "remaining_attempts": MAX_FAILED_ATTEMPTS,
                "lockout_until": None,
                "lockout_duration": None,
            }

        record = self.failed_attempts[identifier]
        now = datetime.now(timezone.utc)

        # Check if currently locked
        if record["lockout_until"] and record["lockout_until"] > now:
            remaining_seconds = int((record["lockout_until"] - now).total_seconds())
            return {
                "locked": True,
                "remaining_attempts": 0,
                "lockout_until": record["lockout_until"],
                "lockout_duration": remaining_seconds,
            }

        # Not locked
        remaining_attempts = max(0, MAX_FAILED_ATTEMPTS - record["count"])
        return {
            "locked": False,
            "remaining_attempts": remaining_attempts,
            "lockout_until": None,
            "lockout_duration": None,
        }

    async def unlock_account(self, identifier: str) -> bool:
        """Manually unlock an account (admin function)"""
        if identifier in self.failed_attempts:
            self.failed_attempts[identifier]["count"] = 0
            self.failed_attempts[identifier]["lockout_until"] = None
            logger.info(f"Manually unlocked account {identifier}")
            return True
        return False


# Singleton instance
_account_lockout_service: Optional[AccountLockoutService] = None


def get_account_lockout_service(
    db: Optional[AsyncSession] = None,
) -> AccountLockoutService:
    """Get account lockout service instance"""
    global _account_lockout_service
    if _account_lockout_service is None:
        _account_lockout_service = AccountLockoutService(db)
    return _account_lockout_service
