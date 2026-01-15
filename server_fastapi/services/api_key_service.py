"""
API Key Service
Manages API keys for external integrations
"""

import hashlib
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.api_keys import APIKey, APIKeyUsage

logger = logging.getLogger(__name__)


class APIKeyService:
    """Service for API key management"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_api_key(
        self,
        user_id: int,
        key_name: str,
        permissions: list[str],
        rate_limit: int = 1000,
        expires_in_days: int | None = None,
        description: str | None = None,
    ) -> tuple[APIKey, str]:
        """
        Create a new API key

        Returns:
            Tuple of (api_key, full_key) - full_key is only returned once
        """
        # Generate key
        full_key, key_prefix = APIKey.generate_key()
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()

        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)

        # Create API key
        api_key = APIKey(
            user_id=user_id,
            key_name=key_name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            permissions=permissions,
            rate_limit=rate_limit,
            expires_at=expires_at,
            description=description,
            is_active=True,
        )

        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)

        logger.info(f"API key created: {api_key.id} for user {user_id}")

        return api_key, full_key

    async def validate_api_key(self, api_key: str) -> APIKey | None:
        """Validate an API key"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        stmt = select(APIKey).where(
            and_(
                APIKey.key_hash == key_hash,
                APIKey.is_active,
                or_(
                    APIKey.expires_at is None,
                    APIKey.expires_at > datetime.now(UTC),
                ),
            )
        )

        result = await self.db.execute(stmt)
        api_key_obj = result.scalar_one_or_none()

        if api_key_obj:
            # Update usage
            api_key_obj.last_used_at = datetime.now(UTC)
            api_key_obj.request_count += 1
            await self.db.commit()

        return api_key_obj

    async def check_rate_limit(self, api_key_id: int) -> tuple[bool, int | None]:
        """
        Check if API key is within rate limit

        Returns:
            Tuple of (allowed, remaining_requests)
        """
        api_key = await self.db.get(APIKey, api_key_id)
        if not api_key:
            return False, None

        # Count requests in the last hour
        one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
        stmt = select(func.count(APIKeyUsage.id)).where(
            and_(
                APIKeyUsage.api_key_id == api_key_id,
                APIKeyUsage.created_at >= one_hour_ago,
            )
        )
        result = await self.db.execute(stmt)
        recent_requests = result.scalar() or 0

        allowed = recent_requests < api_key.rate_limit
        remaining = max(0, api_key.rate_limit - recent_requests)

        return allowed, remaining

    async def log_api_usage(
        self,
        api_key_id: int,
        endpoint: str,
        method: str,
        status_code: int,
        ip_address: str | None = None,
        user_agent: str | None = None,
        response_time_ms: int | None = None,
    ) -> APIKeyUsage:
        """Log API key usage"""
        usage = APIKeyUsage(
            api_key_id=api_key_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            ip_address=ip_address,
            user_agent=user_agent,
            response_time_ms=response_time_ms,
        )

        self.db.add(usage)

        # Update API key
        api_key = await self.db.get(APIKey, api_key_id)
        if api_key:
            api_key.last_used_at = datetime.now(UTC)
            api_key.last_ip_address = ip_address

        await self.db.commit()
        await self.db.refresh(usage)

        return usage

    async def revoke_api_key(self, api_key_id: int, user_id: int) -> bool:
        """Revoke an API key"""
        api_key = await self.db.get(APIKey, api_key_id)
        if not api_key or api_key.user_id != user_id:
            return False

        api_key.is_active = False
        await self.db.commit()

        logger.info(f"API key revoked: {api_key_id}")
        return True

    async def get_user_api_keys(self, user_id: int) -> list[APIKey]:
        """Get all API keys for a user"""
        stmt = (
            select(APIKey)
            .where(APIKey.user_id == user_id)
            .order_by(APIKey.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
