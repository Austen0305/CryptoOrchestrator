"""
Authentication service for FastAPI backend
"""

import os
import jwt
import bcrypt
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Environment variables
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")


class UserCredentials(BaseModel):
    username: str
    password: str


class AuthService:
    """Authentication service"""

    def __init__(self):
        # In a real implementation, this would connect to a database
        # For now, using environment-based mock storage
        self._users = self._load_mock_users()
        self._next_id = max((u.get("id", 0) for u in self._users.values()), default=0) + 1

    def _load_mock_users(self) -> Dict[str, Dict[str, Any]]:
        """Load mock users for development - replace with database in production"""
        # Default test user
        hashed_password = bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode()
        return {
            "testuser": {
                "id": 1,
                "username": "testuser",
                "email": "test@example.com",
                "password_hash": hashed_password,
                "active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        }

    async def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return JWT token"""
        try:
            logger.info(f"Attempting authentication for user: {username}")

            # Get user from storage
            user = self._users.get(username)
            if not user:
                logger.warning(f"User not found: {username}")
                return None

            if not user.get("active", False):
                logger.warning(f"Inactive user attempted login: {username}")
                return None

            # Verify password
            if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
                logger.warning(f"Invalid password for user: {username}")
                return None

            # Generate JWT token
            token = self._generate_token(user)
            logger.info(f"Authentication successful for user: {username}")
            return token

        except Exception as e:
            logger.error(f"Authentication error for user {username}: {str(e)}")
            return None

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return user data"""
        try:
            logger.debug("Validating JWT token")

            # Decode token
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                logger.warning("Token expired")
                return None

            # Get user from storage (in production, this might be a database call)
            user_id = payload.get("user_id")
            username = payload.get("username")

            # Find user by ID or username
            user = None
            if user_id:
                user = next((u for u in self._users.values() if u["id"] == user_id), None)
            elif username:
                user = self._users.get(username)

            if not user or not user.get("active", False):
                logger.warning(f"Invalid user in token: {user_id or username}")
                return None

            # Return user data (without sensitive info)
            user_data = {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"]
            }

            logger.debug(f"Token validation successful for user: {user['username']}")
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

    def _generate_token(self, user: Dict[str, Any]) -> str:
        """Generate JWT token for user"""
        payload = {
            "user_id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)  # 1 hour expiration
        }

        return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username (helper method)"""
        return self._users.get(username)

    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID (helper method)"""
        return next((u for u in self._users.values() if u["id"] == user_id), None)

    # ------------------------------------------------------------------
    # Registration & email verification helpers (parity with route usage)
    # ------------------------------------------------------------------
    def register(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user.

        Expected input keys: email, password, name.
        Returns dict with keys: message, user (id, email, name, emailVerified).
        Raises ValueError on duplicate email.
        """
        email = data.get("email")
        password = data.get("password")
        name = data.get("name") or email.split("@")[0]
        if not email or not password:
            raise ValueError("Email and password are required")

        # Duplicate email check
        if any(u for u in self._users.values() if u.get("email") == email):
            raise ValueError("User already exists")

        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user_record = {
            "id": self._next_id,
            "username": email.split("@")[0],
            "email": email,
            "password_hash": hashed_password,
            "active": True,
            "emailVerified": False,
            "mfaEnabled": False,
            "mfaSecret": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "name": name,
        }
        # Store keyed by username OR email local part to retain existing semantics
        self._users[user_record["username"]] = user_record
        self._next_id += 1
        return {
            "message": "User registered successfully",
            "user": {
                "id": user_record["id"],
                "email": user_record["email"],
                "name": user_record["name"],
                "emailVerified": user_record["emailVerified"],
            },
        }

    def verifyEmail(self, token: str) -> Dict[str, Any]:  # noqa: N802 (match existing route usage)
        """Verify email using a JWT token produced by the route.

        Token payload must contain: id, type='email_verification'.
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            if payload.get("type") != "email_verification":
                return {"success": False, "message": "Invalid token type"}
            user = self.get_user_by_id(payload.get("id"))
            if not user:
                return {"success": False, "message": "User not found"}
            if user.get("emailVerified"):
                return {"success": False, "message": "Email already verified"}
            user["emailVerified"] = True
            return {"success": True, "message": "Email verified successfully", "user_id": user["id"]}
        except jwt.ExpiredSignatureError:
            return {"success": False, "message": "Verification token expired"}
        except jwt.InvalidTokenError:
            return {"success": False, "message": "Invalid verification token"}
        except Exception as e:  # Defensive catch
            logger.error(f"verifyEmail unexpected error: {e}")
            return {"success": False, "message": "Verification failed"}

    def resendVerificationEmail(self, email: str) -> Dict[str, Any]:  # noqa: N802
        user = next((u for u in self._users.values() if u.get("email") == email), None)
        if not user:
            return {"success": False, "message": "User not found"}
        if user.get("emailVerified"):
            return {"success": False, "message": "Email already verified"}
        # Route layer handles sending; we just signal success
        return {"success": True, "message": "Verification email sent"}