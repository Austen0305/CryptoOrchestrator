"""
SaaS Authentication Routes
User registration, login, password reset, email verification
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime, timedelta
import logging
import bcrypt
import jwt
import os
import secrets

from ..database import get_db_session
from ..models.user import User
from ..dependencies.auth import get_current_user
from ..services.email_service import email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_REFRESH_SECRET = os.getenv("JWT_REFRESH_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


# Request Models
class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# Response Models
class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register")
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Register a new user"""
    try:
        # Check if user already exists
        email_result = await db.execute(select(User).where(User.email == request.email))
        if email_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        username_result = await db.execute(
            select(User).where(User.username == request.username)
        )
        if username_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
            )

        # Hash password
        password_hash = bcrypt.hashpw(
            request.password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        # Generate email verification token
        verification_token = secrets.token_urlsafe(32)

        # Create user
        user = User(
            email=request.email,
            username=request.username,
            password_hash=password_hash,
            first_name=request.first_name,
            last_name=request.last_name,
            is_email_verified=False,
            email_verification_token=verification_token,
            email_verification_expires=datetime.utcnow() + timedelta(days=7),
            is_active=True,
            role="user",
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Generate tokens
        from datetime import timedelta

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        access_token_payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "exp": datetime.utcnow() + access_token_expires,
        }
        refresh_token_payload = {
            "sub": str(user.id),
            "exp": datetime.utcnow() + refresh_token_expires,
        }

        access_token = jwt.encode(
            access_token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM
        )
        refresh_token = jwt.encode(
            refresh_token_payload, JWT_REFRESH_SECRET, algorithm=JWT_ALGORITHM
        )

        # Send verification email
        try:
            await email_service.send_verification_email(user.email, verification_token)
            logger.info(f"Verification email sent to {user.email}")
        except Exception as e:
            logger.warning(f"Failed to send verification email: {e}")

        logger.info(f"User registered: {user.email}")

        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user={
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "is_email_verified": user.is_email_verified,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session),
):
    """Login user"""
    try:
        # Find user by email or username
        result = await db.execute(
            select(User).where(
                (User.email == form_data.username)
                | (User.username == form_data.username)
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        # Verify password
        if not bcrypt.checkpw(
            form_data.password.encode("utf-8"), user.password_hash.encode("utf-8")
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive"
            )

        # Update last login
        user.last_login_at = datetime.utcnow()
        user.login_count = (user.login_count or 0) + 1
        await db.commit()

        # Generate tokens
        from datetime import timedelta

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        access_token_payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "exp": datetime.utcnow() + access_token_expires,
        }
        refresh_token_payload = {
            "sub": str(user.id),
            "exp": datetime.utcnow() + refresh_token_expires,
        }

        access_token = jwt.encode(
            access_token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM
        )
        refresh_token = jwt.encode(
            refresh_token_payload, JWT_REFRESH_SECRET, algorithm=JWT_ALGORITHM
        )

        logger.info(f"User logged in: {user.email}")

        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user={
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "is_email_verified": user.is_email_verified,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed"
        )


@router.post("/refresh")
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Refresh access token"""
    try:
        # Verify refresh token
        payload = jwt.decode(
            request.refresh_token, JWT_REFRESH_SECRET, algorithms=[JWT_ALGORITHM]
        )

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        user_id = int(user_id_str)

        # Get user
        user = await db.get(User, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        # Generate new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token_payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "exp": datetime.utcnow() + access_token_expires,
        }
        access_token = jwt.encode(
            access_token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM
        )

        return TokenResponse(access_token=access_token)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"Token refresh failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        )


@router.post("/forgot-password")
async def forgot_password(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Request password reset"""
    try:
        result = await db.execute(select(User).where(User.email == request.email))
        user = result.scalar_one_or_none()

        if user:
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            user.password_reset_token = reset_token
            user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
            await db.commit()

            # Send password reset email
            try:
                await email_service.send_password_reset_email(user.email, reset_token)
                logger.info(f"Password reset email sent to {user.email}")
            except Exception as e:
                logger.warning(f"Failed to send password reset email: {e}")

        # Always return success to prevent email enumeration
        return {"message": "If an account exists, a password reset email has been sent"}

    except Exception as e:
        logger.error(f"Password reset request failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed",
        )


@router.post("/reset-password")
async def reset_password(
    request: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db_session),
):
    """Reset password with token"""
    try:
        result = await db.execute(
            select(User).where(User.password_reset_token == request.token)
        )
        user = result.scalar_one_or_none()

        if not user or not user.password_reset_expires:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        if user.password_reset_expires < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired",
            )

        # Hash new password
        password_hash = bcrypt.hashpw(
            request.new_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        # Update password and clear reset token
        user.password_hash = password_hash
        user.password_reset_token = None
        user.password_reset_expires = None
        await db.commit()

        logger.info(f"Password reset for user: {user.email}")

        return {"message": "Password reset successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset failed: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed",
        )


@router.get("/me")
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get current user information"""
    try:
        user_id = current_user.get("id") or current_user.get("user_id")
        if not user_id:
            # Return minimal user info from JWT token if database fails
            return {
                "id": current_user.get("sub") or "1",
                "email": current_user.get("email") or "",
                "username": current_user.get("username") or current_user.get("name") or "user",
                "role": current_user.get("role", "user"),
                "is_email_verified": current_user.get("email_verified", False),
                "first_name": current_user.get("first_name") or current_user.get("name"),
                "last_name": current_user.get("last_name"),
                "is_active": current_user.get("is_active", True),
            }
        
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            # Return user info from JWT token if not in database
            logger.warning(f"User {user_id} not found in database, returning JWT data")
            return {
                "id": user_id,
                "email": current_user.get("email") or "",
                "username": current_user.get("username") or current_user.get("name") or "user",
                "role": current_user.get("role", "user"),
                "is_email_verified": current_user.get("email_verified", False),
                "first_name": current_user.get("first_name") or current_user.get("name"),
                "last_name": current_user.get("last_name"),
                "is_active": current_user.get("is_active", True),
            }

        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role,
            "is_email_verified": user.is_email_verified,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user info: {e}", exc_info=True)
        # Return minimal user info from JWT token instead of 500 error
        logger.warning(f"Returning JWT-based user info due to error: {e}")
        return {
            "id": current_user.get("id") or current_user.get("user_id") or current_user.get("sub") or "1",
            "email": current_user.get("email") or "",
            "username": current_user.get("username") or current_user.get("name") or "user",
            "role": current_user.get("role", "user"),
            "is_email_verified": current_user.get("email_verified", False),
            "first_name": current_user.get("first_name") or current_user.get("name"),
            "last_name": current_user.get("last_name"),
            "is_active": current_user.get("is_active", True),
        }


@router.post("/verify-email")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Verify email address with token"""
    try:
        result = await db.execute(
            select(User).where(User.email_verification_token == token)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token",
            )

        if user.is_email_verified:
            return {"message": "Email already verified"}

        if not user.email_verification_expires:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token expired",
            )

        if user.email_verification_expires < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token expired",
            )

        # Verify email
        user.is_email_verified = True
        user.email_verification_token = None
        user.email_verification_expires = None
        await db.commit()

        logger.info(f"Email verified for user: {user.email}")

        return {"message": "Email verified successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification failed: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed",
        )


@router.post("/resend-verification")
async def resend_verification_email(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Resend email verification"""
    try:
        result = await db.execute(select(User).where(User.id == current_user["id"]))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        if user.is_email_verified:
            return {"message": "Email already verified"}

        # Generate new verification token
        verification_token = secrets.token_urlsafe(32)
        user.email_verification_token = verification_token
        user.email_verification_expires = datetime.utcnow() + timedelta(days=7)
        await db.commit()

        # Send verification email
        try:
            await email_service.send_verification_email(user.email, verification_token)
            logger.info(f"Verification email resent to {user.email}")
        except Exception as e:
            logger.warning(f"Failed to send verification email: {e}")

        return {"message": "Verification email sent"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resend verification email: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend verification email",
        )
