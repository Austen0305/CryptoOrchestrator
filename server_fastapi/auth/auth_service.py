"""
SaaS Authentication Service with database backend
Provides complete authentication system for multi-tenant SaaS.
"""
import os
import bcrypt
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from ..database import get_db_session
from ..models.user import User
from .token_service import TokenService
from .email_service import EmailService

logger = logging.getLogger(__name__)


class AuthService:
    """Database-backed authentication service for SaaS"""
    
    def __init__(self):
        self.token_service = TokenService()
        self.email_service = EmailService()
    
    async def register_user(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> tuple[Optional[User], Optional[str], Optional[str]]:
        """
        Register a new user
        Returns: (user, access_token, refresh_token) or (None, None, None) on failure
        """
        try:
            # Check if user already exists
            existing_user = await db.execute(
                select(User).where(
                    (User.email == email) | (User.username == username or email.split("@")[0])
                )
            )
            if existing_user.scalar_one_or_none():
                logger.warning(f"Registration attempt with existing email: {email}")
                return None, None, None
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            
            # Generate email verification token
            verification_token = self.token_service.generate_email_verification_token(0, email)
            
            # Create user
            username = username or email.split("@")[0]
            user = User(
                email=email,
                username=username,
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name,
                is_email_verified=False,
                email_verification_token=verification_token,
                email_verification_expires=datetime.now(timezone.utc).replace(
                    hour=datetime.now(timezone.utc).hour + 24
                ),
                is_active=True,
                role="user",
            )
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            # Update verification token with actual user_id
            verification_token = self.token_service.generate_email_verification_token(user.id, user.email)
            user.email_verification_token = verification_token
            await db.commit()
            
            # Send verification email
            await self.email_service.send_verification_email(user.email, verification_token, user.id)
            
            # Generate tokens
            access_token = self.token_service.generate_access_token(user.id, user.email, user.role)
            refresh_token = self.token_service.generate_refresh_token(user.id, user.email)
            
            logger.info(f"User registered successfully: {user.email}")
            return user, access_token, refresh_token
            
        except Exception as e:
            logger.error(f"Registration failed for {email}: {e}", exc_info=True)
            await db.rollback()
            return None, None, None
    
    async def authenticate_user(
        self,
        db: AsyncSession,
        email: Optional[str] = None,
        username: Optional[str] = None,
        password: str = "",
    ) -> tuple[Optional[User], Optional[str], Optional[str]]:
        """
        Authenticate user and return tokens
        Returns: (user, access_token, refresh_token) or (None, None, None) on failure
        """
        try:
            # Find user by email or username
            query = select(User)
            if email:
                query = query.where(User.email == email)
            elif username:
                query = query.where(User.username == username)
            else:
                return None, None, None
            
            result = await db.execute(query)
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"Authentication attempt with non-existent user: {email or username}")
                return None, None, None
            
            # Check if user is active
            if not user.is_active:
                logger.warning(f"Inactive user attempted login: {user.email}")
                return None, None, None
            
            # Verify password
            if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
                logger.warning(f"Invalid password for user: {user.email}")
                return None, None, None
            
            # Update last login
            user.last_login_at = datetime.now(timezone.utc)
            user.login_count += 1
            await db.commit()
            
            # Generate tokens
            access_token = self.token_service.generate_access_token(user.id, user.email, user.role)
            refresh_token = self.token_service.generate_refresh_token(user.id, user.email)
            
            logger.info(f"User authenticated successfully: {user.email}")
            return user, access_token, refresh_token
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}", exc_info=True)
            return None, None, None
    
    async def verify_email(self, db: AsyncSession, token: str) -> Optional[User]:
        """Verify user email with token"""
        try:
            payload = self.token_service.verify_email_verification_token(token)
            if not payload:
                return None
            
            user_id = int(payload.get("sub"))
            email = payload.get("email")
            
            # Find user
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user or user.email != email:
                logger.warning(f"Email verification failed: invalid user")
                return None
            
            if user.is_email_verified:
                logger.info(f"Email already verified: {user.email}")
                return user
            
            # Verify email
            user.is_email_verified = True
            user.email_verification_token = None
            user.email_verification_expires = None
            await db.commit()
            
            # Send welcome email
            await self.email_service.send_welcome_email(user.email, user.first_name or user.username)
            
            logger.info(f"Email verified successfully: {user.email}")
            return user
            
        except Exception as e:
            logger.error(f"Email verification failed: {e}", exc_info=True)
            return None
    
    async def request_password_reset(self, db: AsyncSession, email: str) -> bool:
        """Request password reset and send email"""
        try:
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            
            if not user:
                # Don't reveal if email exists
                logger.info(f"Password reset requested for non-existent email: {email}")
                return True
            
            # Generate reset token
            reset_token = self.token_service.generate_password_reset_token(user.id, user.email)
            user.password_reset_token = reset_token
            user.password_reset_expires = datetime.now(timezone.utc).replace(
                hour=datetime.now(timezone.utc).hour + 1
            )
            await db.commit()
            
            # Send reset email
            await self.email_service.send_password_reset_email(user.email, reset_token, user.id)
            
            logger.info(f"Password reset email sent to: {email}")
            return True
            
        except Exception as e:
            logger.error(f"Password reset request failed: {e}", exc_info=True)
            return False
    
    async def reset_password(self, db: AsyncSession, token: str, new_password: str) -> Optional[User]:
        """Reset password with token"""
        try:
            payload = self.token_service.verify_password_reset_token(token)
            if not payload:
                return None
            
            user_id = int(payload.get("sub"))
            
            # Find user
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user or user.password_reset_token != token:
                logger.warning(f"Password reset failed: invalid token")
                return None
            
            # Update password
            user.password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            user.password_reset_token = None
            user.password_reset_expires = None
            await db.commit()
            
            logger.info(f"Password reset successful: {user.email}")
            return user
            
        except Exception as e:
            logger.error(f"Password reset failed: {e}", exc_info=True)
            return None
    
    async def refresh_access_token(self, db: AsyncSession, refresh_token: str) -> tuple[Optional[str], Optional[str]]:
        """Generate new access token from refresh token"""
        try:
            payload = self.token_service.verify_refresh_token(refresh_token)
            if not payload:
                return None, None
            
            user_id = int(payload.get("sub"))
            email = payload.get("email")
            
            # Verify user exists and is active
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user or not user.is_active:
                return None, None
            
            # Generate new tokens
            access_token = self.token_service.generate_access_token(user.id, user.email, user.role)
            new_refresh_token = self.token_service.generate_refresh_token(user.id, user.email)
            
            return access_token, new_refresh_token
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}", exc_info=True)
            return None, None
    
    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user by ID: {e}", exc_info=True)
            return None
    
    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            result = await db.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user by email: {e}", exc_info=True)
            return None
    
    async def get_user_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            result = await db.execute(select(User).where(User.username == username))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user by username: {e}", exc_info=True)
            return None

