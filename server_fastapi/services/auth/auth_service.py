"""
Authentication service for FastAPI backend
"""

import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from ...config.settings import settings

# JWT secret from settings
JWT_SECRET = settings.jwt_secret


class UserCredentials(BaseModel):
    username: str
    password: str


class AuthService:
    """Authentication service using database via UserRepository"""

    def __init__(self):
        # Service is stateless - uses database sessions passed to methods
        # No need for in-memory storage
        pass

    async def authenticate_user(
        self, username: str, password: str, session: AsyncSession | None = None
    ) -> str | None:
        """Authenticate user and return JWT token"""
        try:
            logger.info(f"Attempting authentication for user: {username}")

            # Get user from database via repository
            if session is None:
                # Fallback to mock for backward compatibility during migration
                logger.warning("No database session provided, using fallback")
                return await self._authenticate_user_fallback(username, password)

            from ...repositories.user_repository import UserRepository

            user_repo = UserRepository()
            user = await user_repo.get_by_username(session, username)

            if not user:
                logger.warning(f"User not found: {username}")
                return None

            if not user.is_active:
                logger.warning(f"Inactive user attempted login: {username}")
                return None

            # Verify password
            if not user.password_hash or not bcrypt.checkpw(
                password.encode(), user.password_hash.encode()
            ):
                logger.warning(f"Invalid password for user: {username}")
                return None

            # Update last login
            await user_repo.update_last_login(session, user.id)

            # Generate JWT token
            user_dict = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
            token = self._generate_token(user_dict)
            logger.info(f"Authentication successful for user: {username}")
            return token

        except Exception as e:
            logger.error(f"Authentication error for user {username}: {str(e)}")
            return None

    async def _authenticate_user_fallback(
        self, username: str, password: str
    ) -> str | None:
        """Fallback authentication using mock storage (for backward compatibility)"""
        # This is a temporary fallback - should be removed once all routes use database sessions
        logger.warning("Using fallback authentication - migrate to database sessions")
        return None

    async def validate_token(
        self, token: str, session: AsyncSession | None = None
    ) -> dict[str, Any] | None:
        """Validate JWT token and return user data"""
        try:
            logger.debug("Validating JWT token")

            # Decode token
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, tz=UTC) < datetime.now(UTC):
                logger.warning("Token expired")
                return None

            # Get user from database via repository
            user_id = payload.get("user_id")
            username = payload.get("username")

            if session is None:
                # Fallback: return token payload if no session (for backward compatibility)
                logger.warning("No database session provided for token validation")
                return {
                    "id": user_id,
                    "username": username,
                    "email": payload.get("email"),
                }

            from ...repositories.user_repository import UserRepository

            user_repo = UserRepository()
            user = None
            if user_id:
                user = await user_repo.get_by_id(session, user_id)
            elif username:
                user = await user_repo.get_by_username(session, username)

            if not user or not user.is_active:
                logger.warning(f"Invalid user in token: {user_id or username}")
                return None

            # Return user data (without sensitive info)
            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }

            logger.debug(f"Token validation successful for user: {user.username}")
            return user_data

        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return None

    def _generate_token(self, user: dict[str, Any]) -> str:
        """Generate JWT token for user"""
        now = datetime.now(UTC)
        payload = {
            "user_id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),  # 1 hour expiration
        }

        return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    async def get_user_by_username(
        self, username: str, session: AsyncSession | None = None
    ) -> dict[str, Any] | None:
        """Get user by username (helper method)"""
        if session is None:
            logger.warning("No database session provided for get_user_by_username")
            return None

        from ...repositories.user_repository import UserRepository

        user_repo = UserRepository()
        user = await user_repo.get_by_username(session, username)
        if user:
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "active": user.is_active,
            }
        return None

    async def get_user_by_id(
        self, user_id: int, session: AsyncSession | None = None
    ) -> dict[str, Any] | None:
        """Get user by ID (helper method)"""
        if session is None:
            logger.warning("No database session provided for get_user_by_id")
            return None

        from ...repositories.user_repository import UserRepository

        user_repo = UserRepository()
        user = await user_repo.get_by_id(session, user_id)
        if user:
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "active": user.is_active,
            }
        return None

    async def register_user(
        self,
        email: str,
        password: str,
        name: str | None = None,
        session: AsyncSession | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Compatibility method for tests that call register_user instead of register"""
        data = {
            "email": email,
            "password": password,
            "name": name,
            **kwargs,
        }
        return await self.register(data, session=session)

    async def login_user(
        self, email: str, password: str, session: AsyncSession | None = None
    ) -> dict[str, Any]:
        """Compatibility method for tests that call login_user"""
        if session is None:
            raise ValueError("Database session required for login_user")

        from ...repositories.user_repository import UserRepository

        user_repo = UserRepository()
        user = await user_repo.get_by_email(session, email)
        if not user:
            raise ValueError("User not found")

        token = await self.authenticate_user(user.username, password, session=session)
        if not token:
            raise ValueError("Invalid password")

        return {
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
            },
        }

    # ------------------------------------------------------------------
    async def register(
        self, data: dict[str, Any], session: AsyncSession | None = None
    ) -> dict[str, Any]:
        """Register a new user.

        Expected input keys: email, password, name (or first_name/last_name), username (optional).
        Returns dict with keys: message, user (id, email, name, emailVerified).
        Raises ValueError on duplicate email.
        """
        email = data.get("email")
        password = data.get("password")
        name = data.get("name")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        provided_username = data.get("username")

        if not email or not password:
            raise ValueError("Email and password are required")

        if session is None:
            # Fallback for backward compatibility
            logger.warning("No database session provided for register, using fallback")
            raise ValueError("Database session required for registration")

        from ...repositories.user_repository import UserRepository

        user_repo = UserRepository()

        # Check if user already exists
        existing = await user_repo.get_by_email(session, email)
        if existing:
            raise ValueError("User already exists")

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # Determine username: use provided username, or derive from email
        if provided_username:
            username = provided_username
        else:
            username = email.split("@")[0]

        # Ensure username is unique
        counter = 1
        original_username = username
        while await user_repo.get_by_username(session, username):
            username = f"{original_username}{counter}"
            counter += 1

        # Determine first_name and last_name: use provided values, or split name, or derive from email
        if first_name or last_name:
            # Use provided first_name and last_name
            final_first_name = first_name if first_name else None
            final_last_name = last_name if last_name else None
        elif name:
            # Split provided name
            name_parts = name.split(" ", 1) if name else [email.split("@")[0], ""]
            final_first_name = name_parts[0] if len(name_parts) > 0 else None
            final_last_name = name_parts[1] if len(name_parts) > 1 else None
        else:
            # Fallback to email prefix
            final_first_name = email.split("@")[0]
            final_last_name = None

        user_data = {
            "username": username,
            "email": email,
            "password_hash": hashed_password,
            "is_active": True,
            "is_email_verified": False,
            "first_name": final_first_name,
            "last_name": final_last_name,
        }

        created_user = await user_repo.create(session, user_data)
        await session.commit()

        # Combine first_name and last_name for name field
        full_name = (
            " ".join(filter(None, [created_user.first_name, created_user.last_name]))
            or created_user.email.split("@")[0]
        )

        return {
            "message": "User registered successfully",
            "user": {
                "id": created_user.id,
                "email": created_user.email,
                "name": full_name,
                "emailVerified": created_user.is_email_verified,
            },
        }

    async def verifyEmail(
        self, token: str, session: AsyncSession | None = None
    ) -> dict[str, Any]:  # noqa: N802 (match existing route usage)
        """Verify email using a JWT token produced by the route.

        Token payload must contain: id, type='email_verification'.
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            if payload.get("type") != "email_verification":
                return {"success": False, "message": "Invalid token type"}

            if session is None:
                logger.warning("No database session provided for verifyEmail")
                return {"success": False, "message": "Database session required"}

            from sqlalchemy import update

            from ...repositories.user_repository import UserRepository

            user_repo = UserRepository()
            user = await user_repo.get_by_id(session, payload.get("id"))
            if not user:
                return {"success": False, "message": "User not found"}
            if user.email_verified:
                return {"success": False, "message": "Email already verified"}

            # Update email verified status
            stmt = (
                update(user.__class__)
                .where(user.__class__.id == user.id)
                .values(is_email_verified=True)
            )
            await session.execute(stmt)
            await session.commit()

            return {
                "success": True,
                "message": "Email verified successfully",
                "user_id": user.id,
            }
        except jwt.ExpiredSignatureError:
            return {"success": False, "message": "Verification token expired"}
        except jwt.InvalidTokenError:
            return {"success": False, "message": "Invalid verification token"}
        except Exception as e:  # Defensive catch
            logger.error(f"verifyEmail unexpected error: {e}")
            return {"success": False, "message": "Verification failed"}

    async def resendVerificationEmail(
        self, email: str, session: AsyncSession | None = None
    ) -> dict[str, Any]:  # noqa: N802
        if session is None:
            logger.warning("No database session provided for resendVerificationEmail")
            return {"success": False, "message": "Database session required"}

        from ...repositories.user_repository import UserRepository

        user_repo = UserRepository()
        user = await user_repo.get_by_email(session, email)
        if not user:
            return {"success": False, "message": "User not found"}
        if user.is_email_verified:
            return {"success": False, "message": "Email already verified"}
        # Route layer handles sending; we just signal success
        return {"success": True, "message": "Verification email sent"}
