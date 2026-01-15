"""
User repository implementation for authentication and user management.
"""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.base import User
from .base import SQLAlchemyRepository


class UserRepository(SQLAlchemyRepository[User]):
    """
    Repository for User model operations.
    """

    def __init__(self):
        super().__init__(User)

    async def get_by_username(
        self, session: AsyncSession, username: str
    ) -> User | None:
        """
        Get user by username.
        """
        query = select(User).where(User.username == username, ~User.is_deleted)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, session: AsyncSession, email: str) -> User | None:
        """
        Get user by email.
        """
        query = select(User).where(User.email == email, ~User.is_deleted)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def update_last_login(
        self, session: AsyncSession, user_id: int
    ) -> User | None:
        """
        Update the last login timestamp and increment login count.
        """
        from datetime import UTC, datetime

        stmt = (
            update(User)
            .where(User.id == user_id, ~User.is_deleted)
            .values(last_login_at=datetime.now(UTC), login_count=User.login_count + 1)
            .returning(User)
        )

        result = await session.execute(stmt)
        await session.commit()

        updated_user = result.scalar_one_or_none()
        if updated_user:
            await session.refresh(updated_user)
        return updated_user

    async def get_active_users(
        self, session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> list[User]:
        """
        Get all active (non-deleted) users.
        """
        query = (
            select(User)
            .where(User.is_active, ~User.is_deleted)
            .offset(skip)
            .limit(limit)
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def search_users(
        self, session: AsyncSession, search_term: str, skip: int = 0, limit: int = 100
    ) -> list[User]:
        """
        Search users by username or email.
        """
        from sqlalchemy import func, or_

        search_filter = f"%{search_term}%"
        query = (
            select(User)
            .where(
                or_(
                    func.lower(User.username).like(func.lower(search_filter)),
                    func.lower(User.email).like(func.lower(search_filter)),
                ),
                User.is_active,
                ~User.is_deleted,
            )
            .offset(skip)
            .limit(limit)
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_users_by_role(
        self, session: AsyncSession, role: str, skip: int = 0, limit: int = 100
    ) -> list[User]:
        """
        Get users by role.
        """
        query = (
            select(User)
            .where(User.role == role, User.is_active, ~User.is_deleted)
            .offset(skip)
            .limit(limit)
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def verify_user(self, session: AsyncSession, user_id: int) -> User | None:
        """
        Mark user as verified.
        """
        stmt = (
            update(User)
            .where(User.id == user_id, ~User.is_deleted)
            .values(is_verified=True)
            .returning(User)
        )

        result = await session.execute(stmt)
        await session.commit()

        verified_user = result.scalar_one_or_none()
        if verified_user:
            await session.refresh(verified_user)
        return verified_user

    async def deactivate_user(self, session: AsyncSession, user_id: int) -> User | None:
        """
        Deactivate a user account.
        """
        stmt = (
            update(User)
            .where(User.id == user_id, ~User.is_deleted)
            .values(is_active=False)
            .returning(User)
        )

        result = await session.execute(stmt)
        await session.commit()

        deactivated_user = result.scalar_one_or_none()
        if deactivated_user:
            await session.refresh(deactivated_user)
        return deactivated_user


# Global repository instance
user_repository = UserRepository()
