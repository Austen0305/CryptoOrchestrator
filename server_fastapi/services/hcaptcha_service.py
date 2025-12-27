"""
hCaptcha Verification Service

Provides bot protection using hCaptcha (free tier: 100K requests/month).
"""

import httpx
import logging
from typing import Optional
import os

logger = logging.getLogger(__name__)


class HCaptchaService:
    """Service for verifying hCaptcha tokens"""

    VERIFY_URL = "https://hcaptcha.com/siteverify"

    def __init__(self):
        self.secret_key = os.getenv("HCAPTCHA_SECRET_KEY")
        if not self.secret_key:
            logger.warning(
                "HCAPTCHA_SECRET_KEY not set - hCaptcha verification disabled"
            )

    async def verify(
        self, token: Optional[str], remoteip: Optional[str] = None
    ) -> bool:
        """
        Verify hCaptcha token.

        Args:
            token: hCaptcha response token from frontend
            remoteip: Optional client IP address

        Returns:
            True if verification successful, False otherwise
        """
        if not self.secret_key:
            logger.warning("hCaptcha verification skipped - secret key not configured")
            return True  # Allow requests if hCaptcha not configured

        if not token:
            logger.warning("hCaptcha token missing")
            return False

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    self.VERIFY_URL,
                    data={
                        "secret": self.secret_key,
                        "response": token,
                        "remoteip": remoteip,
                    },
                )
                result = response.json()
                success = result.get("success", False)

                if not success:
                    error_codes = result.get("error-codes", [])
                    logger.warning(f"hCaptcha verification failed: {error_codes}")

                return success
        except httpx.TimeoutException:
            logger.error("hCaptcha verification timeout")
            return False  # Fail closed for security
        except Exception as e:
            logger.error(f"hCaptcha verification error: {e}", exc_info=True)
            return False  # Fail closed for security


# Singleton instance
hcaptcha_service = HCaptchaService()
