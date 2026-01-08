"""
Token service for JWT access and refresh tokens
"""

import logging
import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

logger = logging.getLogger(__name__)

# JWT secrets from environment
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_REFRESH_SECRET = os.getenv(
    "JWT_REFRESH_SECRET", "change-me-refresh-secret-in-production"
)
JWT_ALGORITHM = "HS256"

# Token expiration times
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
EMAIL_VERIFICATION_EXPIRE_HOURS = int(
    os.getenv("EMAIL_VERIFICATION_EXPIRE_HOURS", "24")
)
PASSWORD_RESET_EXPIRE_HOURS = int(os.getenv("PASSWORD_RESET_EXPIRE_HOURS", "1"))


class TokenService:
    """Service for generating and validating JWT tokens"""

    @staticmethod
    def generate_access_token(user_id: int, email: str, role: str = "user") -> str:
        """Generate JWT access token"""
        now = datetime.now(UTC)
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": str(user_id),
            "id": user_id,
            "email": email,
            "role": role,
            "type": "access",
            "exp": int(expire.timestamp()),
            "iat": int(now.timestamp()),
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def generate_refresh_token(user_id: int, email: str) -> str:
        """Generate JWT refresh token"""
        now = datetime.now(UTC)
        expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {
            "sub": str(user_id),
            "id": user_id,
            "email": email,
            "type": "refresh",
            "exp": int(expire.timestamp()),
            "iat": int(now.timestamp()),
        }
        return jwt.encode(payload, JWT_REFRESH_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def generate_email_verification_token(user_id: int, email: str) -> str:
        """Generate email verification token"""
        now = datetime.now(UTC)
        expire = now + timedelta(hours=EMAIL_VERIFICATION_EXPIRE_HOURS)
        payload = {
            "sub": str(user_id),
            "email": email,
            "type": "email_verification",
            "exp": int(expire.timestamp()),
            "iat": int(now.timestamp()),
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def generate_password_reset_token(user_id: int, email: str) -> str:
        """Generate password reset token"""
        now = datetime.now(UTC)
        expire = now + timedelta(hours=PASSWORD_RESET_EXPIRE_HOURS)
        payload = {
            "sub": str(user_id),
            "email": email,
            "type": "password_reset",
            "exp": int(expire.timestamp()),
            "iat": int(now.timestamp()),
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def verify_access_token(token: str) -> dict[str, Any] | None:
        """Verify and decode access token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "access":
                logger.warning("Token is not an access token")
                return None
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Access token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid access token: {e}")
            return None

    @staticmethod
    def verify_refresh_token(token: str) -> dict[str, Any] | None:
        """Verify and decode refresh token"""
        try:
            payload = jwt.decode(token, JWT_REFRESH_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "refresh":
                logger.warning("Token is not a refresh token")
                return None
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Refresh token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid refresh token: {e}")
            return None

    @staticmethod
    def verify_email_verification_token(token: str) -> dict[str, Any] | None:
        """Verify and decode email verification token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "email_verification":
                logger.warning("Token is not an email verification token")
                return None
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Email verification token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid email verification token: {e}")
            return None

    @staticmethod
    def verify_password_reset_token(token: str) -> dict[str, Any] | None:
        """Verify and decode password reset token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "password_reset":
                logger.warning("Token is not a password reset token")
                return None
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Password reset token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid password reset token: {e}")
            return None

    @staticmethod
    def generate_random_token(length: int = 32) -> str:
        """Generate random token for various purposes"""
        return secrets.token_urlsafe(length)
