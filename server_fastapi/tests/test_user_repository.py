import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from server_fastapi.repositories.user_repository import UserRepository
from server_fastapi.models.base import User

@pytest.mark.asyncio
class TestUserRepository:
    """Test cases for UserRepository"""

    async def test_create_user(self, db_session: AsyncSession):
        """Test creating a new user"""
        repo = UserRepository()

        # Test data
        username = "testuser"
        email = "test@example.com"
        hashed_password = "hashed_password_123"

        # Create user
        user = await repo.create(db_session, {
            "username": username,
            "email": email,
            "hashed_password": hashed_password,
            "is_active": True,
            "is_verified": False,
            "role": "user"
        })

        assert user.id is not None
        assert user.username == username
        assert user.email == email
        assert user.hashed_password == hashed_password
        assert user.is_active == True
        assert user.is_verified == False
        assert user.role == "user"

    async def test_get_by_username(self, db_session: AsyncSession):
        """Test getting user by username"""
        repo = UserRepository()

        # Create test user
        await repo.create(db_session, {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": "hashed_password_123",
            "is_active": True,
            "is_verified": False,
            "role": "user"
        })

        # Retrieve by username
        user = await repo.get_by_username(db_session, "testuser")

        assert user is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    async def test_get_by_username_not_found(self, db_session: AsyncSession):
        """Test getting non-existent user by username"""
        repo = UserRepository()

        user = await repo.get_by_username(db_session, "nonexistent")

        assert user is None

    async def test_get_by_email(self, db_session: AsyncSession):
        """Test getting user by email"""
        repo = UserRepository()

        # Create test user
        await repo.create(db_session, {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": "hashed_password_123",
            "is_active": True,
            "is_verified": False,
            "role": "user"
        })

        # Retrieve by email
        user = await repo.get_by_email(db_session, "test@example.com")

        assert user is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    async def test_get_by_email_not_found(self, db_session: AsyncSession):
        """Test getting non-existent user by email"""
        repo = UserRepository()

        user = await repo.get_by_email(db_session, "nonexistent@example.com")

        assert user is None

    async def test_update_last_login(self, db_session: AsyncSession):
        """Test updating last login timestamp"""
        repo = UserRepository()

        # Create test user
        user = await repo.create(db_session, {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": "hashed_password_123",
            "is_active": True,
            "is_verified": False,
            "role": "user"
        })

        original_login_count = user.login_count or 0

        # Update last login
        updated_user = await repo.update_last_login(db_session, user.id)

        assert updated_user is not None
        assert updated_user.last_login_at is not None
        assert updated_user.login_count == original_login_count + 1

    async def test_get_active_users(self, db_session: AsyncSession):
        """Test getting active users"""
        repo = UserRepository()

        # Create active user
        await repo.create(db_session, {
            "username": "active_user",
            "email": "active@example.com",
            "hashed_password": "hashed_password_123",
            "is_active": True,
            "is_verified": False,
            "role": "user"
        })

        # Create inactive user
        await repo.create(db_session, {
            "username": "inactive_user",
            "email": "inactive@example.com",
            "hashed_password": "hashed_password_123",
            "is_active": False,
            "is_verified": False,
            "role": "user"
        })

        # Get active users
        active_users = await repo.get_active_users(db_session)

        assert len(active_users) == 1
        assert active_users[0].username == "active_user"

    async def test_search_users(self, db_session: AsyncSession):
        """Test searching users by username or email"""
        repo = UserRepository()

        # Create test users
        await repo.create(db_session, {
            "username": "john_doe",
            "email": "john@example.com",
            "hashed_password": "hashed_password_123",
            "is_active": True,
            "is_verified": False,
            "role": "user"
        })

        await repo.create(db_session, {
            "username": "jane_smith",
            "email": "jane@example.com",
            "hashed_password": "hashed_password_123",
            "is_active": True,
            "is_verified": False,
            "role": "user"
        })

        # Search by username
        results = await repo.search_users(db_session, "john")
        assert len(results) == 1
        assert results[0].username == "john_doe"

        # Search by email
        results = await repo.search_users(db_session, "jane")
        assert len(results) == 1
        assert results[0].username == "jane_smith"

    async def test_verify_user(self, db_session: AsyncSession):
        """Test verifying a user"""
        repo = UserRepository()

        # Create unverified user
        user = await repo.create(db_session, {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": "hashed_password_123",
            "is_active": True,
            "is_verified": False,
            "role": "user"
        })

        # Verify user
        verified_user = await repo.verify_user(db_session, user.id)

        assert verified_user is not None
        assert verified_user.is_verified == True

    async def test_deactivate_user(self, db_session: AsyncSession):
        """Test deactivating a user"""
        repo = UserRepository()

        # Create active user
        user = await repo.create(db_session, {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": "hashed_password_123",
            "is_active": True,
            "is_verified": False,
            "role": "user"
        })

        # Deactivate user
        deactivated_user = await repo.deactivate_user(db_session, user.id)

        assert deactivated_user is not None
        assert deactivated_user.is_active == False