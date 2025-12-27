"""
Token rotation service for rotating JWT tokens on suspicious activity.
Implements token rotation and revocation for enhanced security.
"""

import logging
from typing import Dict, Optional, Set
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
import os

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")

# In-memory token blacklist (in production, use Redis)
_token_blacklist: Set[str] = set()
_rotated_tokens: Dict[str, str] = {}  # old_token -> new_token mapping


class TokenRotationService:
    """Service for token rotation and revocation"""

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.token_blacklist = _token_blacklist
        self.rotated_tokens = _rotated_tokens

    def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is in blacklist"""
        return token in self.token_blacklist

    def blacklist_token(self, token: str, reason: str = "revoked") -> None:
        """Add token to blacklist"""
        self.token_blacklist.add(token)
        logger.info(f"Token blacklisted: {reason}")

    async def rotate_token_on_suspicious_activity(
        self, old_token: str, user_id: str, reason: str
    ) -> Optional[str]:
        """
        Rotate token due to suspicious activity.

        Args:
            old_token: Current token to rotate
            user_id: User ID
            reason: Reason for rotation (e.g., "suspicious_login_location")

        Returns:
            New token or None if rotation failed
        """
        try:
            # Decode old token to get user info
            try:
                payload = jwt.decode(old_token, JWT_SECRET, algorithms=["HS256"])
            except jwt.InvalidTokenError:
                logger.warning(f"Invalid token provided for rotation: {reason}")
                return None

            # Blacklist old token
            self.blacklist_token(old_token, f"Rotated due to: {reason}")

            # Generate new token with same user info but new expiration
            from datetime import timedelta

            now = datetime.now(timezone.utc)
            new_payload = {
                "user_id": payload.get("user_id") or user_id,
                "username": payload.get("username"),
                "email": payload.get("email"),
                "iat": int(now.timestamp()),
                "exp": int((now + timedelta(hours=1)).timestamp()),
                "rotated": True,
                "rotation_reason": reason,
            }

            new_token = jwt.encode(new_payload, JWT_SECRET, algorithm="HS256")

            # Store mapping for seamless transition
            self.rotated_tokens[old_token] = new_token

            logger.warning(
                f"Token rotated for user {user_id} due to: {reason}. "
                f"Old token blacklisted."
            )

            return new_token

        except Exception as e:
            logger.error(f"Token rotation failed: {e}", exc_info=True)
            return None

    async def detect_suspicious_activity(
        self, token: str, request_info: Dict[str, any]
    ) -> bool:
        """
        Detect suspicious activity based on request info.

        Args:
            token: JWT token
            request_info: Dict with ip_address, user_agent, etc.

        Returns:
            True if suspicious activity detected
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

            # Check for suspicious patterns
            suspicious_patterns = []

            # 1. Check IP address change (if stored in token)
            token_ip = payload.get("ip_address")
            current_ip = request_info.get("ip_address")
            if token_ip and current_ip and token_ip != current_ip:
                suspicious_patterns.append("ip_address_change")

            # 2. Check user agent change
            token_ua = payload.get("user_agent")
            current_ua = request_info.get("user_agent")
            if token_ua and current_ua and token_ua != current_ua:
                suspicious_patterns.append("user_agent_change")

            # 3. Check token age (very old tokens are suspicious)
            iat = payload.get("iat")
            if iat:
                token_age = datetime.now(timezone.utc).timestamp() - iat
                if token_age > 86400:  # Older than 24 hours
                    suspicious_patterns.append("old_token")

            # 4. Check for multiple rapid requests from different IPs
            # (This would require additional tracking infrastructure)

            if suspicious_patterns:
                logger.warning(
                    f"Suspicious activity detected: {suspicious_patterns} "
                    f"for user {payload.get('user_id')}"
                )
                return True

            return False

        except jwt.InvalidTokenError:
            return False
        except Exception as e:
            logger.error(f"Error detecting suspicious activity: {e}")
            return False

    def get_rotated_token(self, old_token: str) -> Optional[str]:
        """Get new token if old token was rotated"""
        return self.rotated_tokens.get(old_token)

    async def revoke_all_user_tokens(self, user_id: str) -> int:
        """
        Revoke all tokens for a user (e.g., on password change).
        In production, this would query database/Redis for all user tokens.

        Returns:
            Number of tokens revoked
        """
        # In production, implement proper token revocation
        # For now, this is a placeholder
        logger.info(f"Revoking all tokens for user {user_id}")
        return 0


# Singleton instance
_token_rotation_service: Optional[TokenRotationService] = None


def get_token_rotation_service(
    db: Optional[AsyncSession] = None,
) -> TokenRotationService:
    """Get token rotation service instance"""
    global _token_rotation_service
    if _token_rotation_service is None:
        _token_rotation_service = TokenRotationService(db)
    return _token_rotation_service
