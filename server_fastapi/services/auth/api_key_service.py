"""
API Key service for FastAPI backend
"""

import os
import uuid
import hashlib
import secrets
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict

logger = logging.getLogger(__name__)


class APIKey(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    key_hash: str  # Store hash instead of plain key
    key_prefix: str  # First 8 characters for identification
    permissions: List[str]
    active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_used_at: Optional[str] = None
    expires_at: Optional[str] = None

    model_config = ConfigDict(extra='allow')


class APIKeyCreateRequest(BaseModel):
    user_id: str
    permissions: List[str]
    expires_in_days: Optional[int] = None  # Optional expiration


class APIKeyService:
    """API Key management service with secure storage and validation"""

    def __init__(self):
        # In production, replace with proper database (e.g., PostgreSQL, MongoDB)
        # For now, using in-memory storage - keys would be lost on restart
        self._keys: Dict[str, APIKey] = {}  # key_id -> APIKey
        self._key_hashes: Dict[str, str] = {}  # key_hash -> key_id (for lookup)
        logger.info("APIKeyService initialized with in-memory storage")

    async def create_api_key(self, user_id: str, permissions: List[str], expires_in_days: Optional[int] = None) -> APIKey:
        """Create new API key for user with secure generation"""
        try:
            logger.info(f"Creating API key for user: {user_id}")

            # Generate secure random API key
            api_key_plain = f"ck_{secrets.token_urlsafe(32)}"

            # Create hash for storage
            key_hash = hashlib.sha256(api_key_plain.encode()).hexdigest()
            key_prefix = api_key_plain[:8]  # Store first 8 chars for identification

            # Create expiration date if specified
            expires_at = None
            if expires_in_days:
                expires_at = (datetime.now(timezone.utc) +
                            datetime.timedelta(days=expires_in_days)).isoformat()

            # Create APIKey instance
            api_key = APIKey(
                user_id=user_id,
                key_hash=key_hash,
                key_prefix=key_prefix,
                permissions=permissions,
                expires_at=expires_at
            )

            # Store in memory (production: database)
            self._keys[api_key.id] = api_key
            self._key_hashes[key_hash] = api_key.id

            logger.info(f"API key created successfully for user {user_id}, key_id: {api_key.id}")
            logger.debug(f"API key prefix: {key_prefix}")

            # Return with plain key for one-time display to user
            # In production, this should be handled carefully to avoid logging plain keys
            api_key_with_plain = api_key.model_copy()
            api_key_with_plain.key = api_key_plain  # Add plain key temporarily

            return api_key_with_plain

        except Exception as e:
            logger.error(f"Failed to create API key for user {user_id}: {str(e)}")
            raise

    async def validate_api_key(self, key: str) -> Optional[APIKey]:
        """Validate API key and return key data if valid"""
        try:
            logger.debug(f"Validating API key with prefix: {key[:8] if len(key) >= 8 else key}")

            # Hash the provided key
            key_hash = hashlib.sha256(key.encode()).hexdigest()

            # Find key by hash
            key_id = self._key_hashes.get(key_hash)
            if not key_id:
                logger.warning(f"API key not found for hash: {key_hash[:8]}...")
                return None

            api_key = self._keys.get(key_id)
            if not api_key:
                logger.error(f"API key data not found for key_id: {key_id}")
                return None

            # Check if active
            if not api_key.active:
                logger.warning(f"API key {key_id} is inactive")
                return None

            # Check expiration
            if api_key.expires_at:
                expires_dt = datetime.fromisoformat(api_key.expires_at)
                if datetime.now(timezone.utc) > expires_dt:
                    logger.warning(f"API key {key_id} has expired")
                    # Auto-deactivate expired keys
                    await self._deactivate_key(key_id)
                    return None

            # Update last used timestamp
            api_key.last_used_at = datetime.now(timezone.utc).isoformat()
            self._keys[key_id] = api_key

            logger.debug(f"API key validated successfully for user: {api_key.user_id}")
            return api_key

        except Exception as e:
            logger.error(f"API key validation error: {str(e)}")
            return None

    async def revoke_api_key(self, key_id: str) -> bool:
        """Revoke (deactivate) API key"""
        try:
            logger.info(f"Revoking API key: {key_id}")

            if key_id not in self._keys:
                logger.warning(f"API key not found for revocation: {key_id}")
                return False

            success = await self._deactivate_key(key_id)
            if success:
                logger.info(f"API key revoked successfully: {key_id}")
            else:
                logger.error(f"Failed to revoke API key: {key_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to revoke API key {key_id}: {str(e)}")
            return False

    async def _deactivate_key(self, key_id: str) -> bool:
        """Internal method to deactivate a key"""
        try:
            if key_id in self._keys:
                api_key = self._keys[key_id]
                api_key.active = False

                # Remove from hash lookup
                if api_key.key_hash in self._key_hashes:
                    del self._key_hashes[api_key.key_hash]

                return True
            return False
        except Exception as e:
            logger.error(f"Failed to deactivate key {key_id}: {str(e)}")
            return False

    async def get_user_api_keys(self, user_id: str) -> List[APIKey]:
        """Get all active API keys for a user"""
        try:
            user_keys = [
                key for key in self._keys.values()
                if key.user_id == user_id and key.active
            ]
            logger.debug(f"Found {len(user_keys)} active API keys for user: {user_id}")
            return user_keys
        except Exception as e:
            logger.error(f"Failed to get API keys for user {user_id}: {str(e)}")
            return []

    async def revoke_all_user_keys(self, user_id: str) -> int:
        """Revoke all API keys for a user, returns count of revoked keys"""
        try:
            logger.info(f"Revoking all API keys for user: {user_id}")
            revoked_count = 0
            for key_id, api_key in list(self._keys.items()):
                if api_key.user_id == user_id and api_key.active:
                    await self._deactivate_key(key_id)
                    revoked_count += 1

            logger.info(f"Revoked {revoked_count} API keys for user: {user_id}")
            return revoked_count
        except Exception as e:
            logger.error(f"Failed to revoke all keys for user {user_id}: {str(e)}")
            return 0

    async def cleanup_expired_keys(self) -> int:
        """Clean up expired keys, returns count of cleaned keys"""
        try:
            logger.info("Starting cleanup of expired API keys")
            cleaned_count = 0
            now = datetime.now(timezone.utc)

            for key_id, api_key in list(self._keys.items()):
                if (api_key.expires_at and
                    now > datetime.fromisoformat(api_key.expires_at) and
                    api_key.active):
                    await self._deactivate_key(key_id)
                    cleaned_count += 1

            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired API keys")
            return cleaned_count
        except Exception as e:
            logger.error(f"Failed to cleanup expired keys: {str(e)}")
            return 0