"""
Centralized authentication dependencies for FastAPI routes.
Eliminates code duplication across route files.
"""

import logging
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..config.settings import settings
from ..utils.auth_utils import get_user_id_from_payload

logger = logging.getLogger(__name__)

# JWT secret from settings
JWT_SECRET = settings.jwt_secret

# Security scheme for Bearer token
security = HTTPBearer()

# Optional security scheme for routes that work with or without authentication
optional_security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    request: Request,
) -> dict:
    """
    Centralized dependency to get current authenticated user.
    Validates JWT token and returns user data.
    Includes token rotation on suspicious activity.

    Usage:
        @router.get("/protected")
        async def protected_route(current_user: dict = Depends(get_current_user)):
            ...
    """
    try:
        token = credentials.credentials

        # Check if token is blacklisted
        from ..services.auth.token_rotation import get_token_rotation_service

        token_rotation_service = get_token_rotation_service()

        if token_rotation_service.is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Decode and validate JWT token
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = get_user_id_from_payload(payload)

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
            )

        # Detect suspicious activity and rotate token if needed
        request_info = {
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }

        is_suspicious = await token_rotation_service.detect_suspicious_activity(
            token, request_info
        )

        if is_suspicious:
            # Rotate token on suspicious activity
            new_token = (
                await token_rotation_service.rotate_token_on_suspicious_activity(
                    token, str(user_id), "suspicious_activity_detected"
                )
            )

            if new_token:
                logger.warning(
                    f"Token rotated for user {user_id} due to suspicious activity"
                )
                # Note: In production, you might want to return new token in response header
                # For now, we'll continue with the old token but log the rotation

        # Return user data from token (database lookup not needed here for performance)
        # Full user data should be fetched from database when needed in routes
        # Include both role (singular) for backward compatibility and roles (plural) for permission checks
        role = payload.get("role", "user")
        roles = payload.get("roles", [role] if role else [])

        return {
            "id": user_id,
            "email": payload.get("email", ""),
            "role": role,
            "roles": roles,
            "permissions": payload.get("permissions", []),
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error",
        )


def get_current_active_user(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """
    Dependency that ensures the user is active.

    Usage:
        @router.get("/admin")
        async def admin_route(user: dict = Depends(get_current_active_user)):
            ...
    """
    if not current_user.get("active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive"
        )
    return current_user


async def get_optional_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(optional_security)
    ],
    request: Request,
) -> dict | None:
    """
    Optional authentication - returns user if authenticated, None otherwise.
    Useful for routes that have different behavior for authenticated/unauthenticated users.

    Usage:
        @router.get("/public")
        async def public_route(user: Optional[dict] = Depends(get_optional_user)):
            if user:
                # Authenticated user logic
                ...
            else:
                # Unauthenticated user logic
                ...
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, request)
    except HTTPException:
        return None


def require_permission(permission: str):
    """
    Dependency factory for role-based access control.

    Usage:
        @router.delete("/admin/users")
        async def delete_user(
            user: dict = Depends(require_permission("admin:delete"))
        ):
            ...
    """

    async def permission_checker(
        current_user: Annotated[dict, Depends(get_current_user)],
    ) -> dict:
        user_permissions = current_user.get("permissions", [])
        user_roles = current_user.get("roles", [])

        # Check if user has specific permission
        if permission in user_permissions:
            return current_user

        # Check if user has role that grants permission
        # Admin role grants all permissions
        if "admin" in user_roles:
            return current_user

        # Check role-based permissions (simplified)
        role_permissions = {
            "admin": ["admin:*"],
            "trader": ["trade:*", "bot:*"],
            "viewer": ["read:*"],
        }

        for role in user_roles:
            role_perms = role_permissions.get(role, [])
            if any(
                perm == permission
                or perm.endswith(":*")
                and permission.startswith(perm[:-1])
                for perm in role_perms
            ):
                return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions: {permission} required",
        )

    return permission_checker
