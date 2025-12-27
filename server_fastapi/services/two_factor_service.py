"""
Two-Factor Authentication Service
Handles 2FA for trading operations and sensitive actions.
"""

import logging
import io
import base64
from typing import Optional, Dict, List
from datetime import datetime, timedelta

# Optional imports with fallbacks
try:
    import pyotp

    PYOTP_AVAILABLE = True
except ImportError:
    PYOTP_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("pyotp not available, 2FA features will be limited")

try:
    import qrcode

    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    if not PYOTP_AVAILABLE:
        logger = logging.getLogger(__name__)
    logger.warning("qrcode not available, QR code generation will be disabled")

if not PYOTP_AVAILABLE:
    # Mock pyotp for fallback
    class MockPyOTP:
        @staticmethod
        def random_base32():
            return "MOCK2FASECRETBASE32"

        class TOTP:
            def __init__(self, secret):
                self.secret = secret

            def verify(self, token, valid_window=1):
                # In production, this should always return False if pyotp is not available
                logger.warning("2FA verification disabled - pyotp not installed")
                return False

            def provisioning_uri(self, name, issuer_name):
                return f"otpauth://totp/{issuer_name}:{name}?secret={self.secret}&issuer={issuer_name}"

    pyotp = MockPyOTP()

logger = logging.getLogger(__name__)


class TwoFactorService:
    """Service for two-factor authentication"""

    def __init__(self):
        # In production, this should be stored per-user in database
        self.user_secrets: Dict[int, str] = {}

    def generate_secret(self, user_id: int) -> str:
        """
        Generate a TOTP secret for a user.

        Args:
            user_id: User ID

        Returns:
            TOTP secret
        """
        try:
            if not PYOTP_AVAILABLE:
                logger.warning("pyotp not available, using mock secret")
            secret = pyotp.random_base32()
            self.user_secrets[user_id] = secret
            return secret
        except Exception as e:
            logger.error(f"Error generating 2FA secret: {e}", exc_info=True)
            raise

    def get_secret(self, user_id: int) -> Optional[str]:
        """Get TOTP secret for a user"""
        return self.user_secrets.get(user_id)

    def generate_qr_code(
        self, user_id: int, email: str, issuer: str = "CryptoOrchestrator"
    ) -> str:
        """
        Generate QR code for 2FA setup.

        Args:
            user_id: User ID
            email: User email
            issuer: Service name

        Returns:
            Base64-encoded QR code image
        """
        try:
            if not QRCODE_AVAILABLE:
                logger.warning("qrcode not available, QR code generation disabled")
                return ""

            secret = self.get_secret(user_id)
            if not secret:
                secret = self.generate_secret(user_id)

            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=email, issuer_name=issuer
            )

            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode()

            return f"data:image/png;base64,{img_str}"

        except Exception as e:
            logger.error(f"Error generating QR code: {e}", exc_info=True)
            raise

    def verify_token(self, user_id: int, token: str) -> bool:
        """
        Verify a 2FA token.

        Args:
            user_id: User ID
            token: 6-digit TOTP token

        Returns:
            True if token is valid
        """
        try:
            if not PYOTP_AVAILABLE:
                logger.warning("2FA verification disabled - pyotp not installed")
                return False

            secret = self.get_secret(user_id)
            if not secret:
                logger.warning(f"No 2FA secret found for user {user_id}")
                return False

            totp = pyotp.TOTP(secret)

            # Verify with window for clock skew
            return totp.verify(token, valid_window=1)

        except Exception as e:
            logger.error(f"Error verifying 2FA token: {e}", exc_info=True)
            return False

    def require_2fa_for_trading(self, user_id: int) -> bool:
        """
        Check if user requires 2FA for trading.
        In production, this would check user settings.

        Args:
            user_id: User ID

        Returns:
            True if 2FA is required
        """
        # In production, check user preferences/settings
        # For now, return True if user has 2FA enabled
        return self.get_secret(user_id) is not None

    def is_2fa_enabled(self, user_id: int) -> bool:
        """Check if 2FA is enabled for a user"""
        return self.get_secret(user_id) is not None


# Global instance
two_factor_service = TwoFactorService()
