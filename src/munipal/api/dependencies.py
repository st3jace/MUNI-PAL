"""
API dependencies for FastAPI dependency injection.

Per spec: JWT-based authentication with role-based access control.
Auth enforcement is feature-flagged for safe rollout.
"""

from collections.abc import Mapping
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.config import get_settings
from munipal.db.session import get_async_session

# Type alias for database session dependency
DbSession = Annotated[AsyncSession, Depends(get_async_session)]


DEV_FALLBACK_USER_ID = "00000000-0000-0000-0000-000000000001"
DEFAULT_COMPAT_ROLE = "admin"
ALLOWED_ROLES = {"admin", "analyst", "viewer"}


def _unauthorized(detail: str = "Authentication required") -> HTTPException:
    """Build consistent 401 response for auth failures."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _extract_bearer_token(authorization: str | None) -> str:
    """Extract bearer token from Authorization header."""
    if not authorization:
        raise _unauthorized("Missing bearer token")

    parts = authorization.strip().split(" ", maxsplit=1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise _unauthorized("Invalid authorization scheme")

    return parts[1].strip()


def _decode_access_token(token: str) -> Mapping[str, object]:
    """Decode and validate JWT access token."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise _unauthorized("Invalid or expired token") from exc

    return payload

async def get_current_user_id(
    authorization: str | None = Header(None, description="Authorization: Bearer <token>"),
    x_user_id: str | None = Header(None, description="User ID for development auth"),
) -> str:
    """
    Get current user ID from request.

    With AUTH_ENFORCEMENT_V2=true:
    - Requires valid JWT bearer token in Authorization header
    - Returns token subject claim as user ID

    With AUTH_ENFORCEMENT_V2=false (compat mode):
    - Uses X-User-Id header when provided
    - Falls back to fixed development user ID
    """
    settings = get_settings()
    if settings.auth_enforcement_v2:
        token = _extract_bearer_token(authorization)
        payload = _decode_access_token(token)

        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject.strip():
            raise _unauthorized("Token subject is missing")

        return subject.strip()

    if x_user_id:
        return x_user_id

    return DEV_FALLBACK_USER_ID


CurrentUserId = Annotated[str, Depends(get_current_user_id)]


async def get_current_user_role(
    authorization: str | None = Header(None, description="Authorization: Bearer <token>"),
    x_user_role: str | None = Header(None, description="User role for development auth"),
) -> str:
    """
    Resolve current user role.

    With AUTH_ENFORCEMENT_V2=true:
    - Reads role from JWT `role` claim (defaults to `analyst` if absent)

    With AUTH_ENFORCEMENT_V2=false (compat mode):
    - Uses X-User-Role when provided
    - Falls back to DEFAULT_COMPAT_ROLE
    """
    settings = get_settings()

    if settings.auth_enforcement_v2:
        token = _extract_bearer_token(authorization)
        payload = _decode_access_token(token)
        role = payload.get("role", "analyst")
        if not isinstance(role, str):
            raise _unauthorized("Token role claim is invalid")
        role = role.strip().lower()
    else:
        role = (x_user_role or DEFAULT_COMPAT_ROLE).strip().lower()

    if role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: invalid role '{role}'",
        )

    return role


CurrentUserRole = Annotated[str, Depends(get_current_user_role)]


async def require_auth(
    user_id: CurrentUserId,
) -> str:
    """
    Require authentication.
    """
    if not user_id:
        raise _unauthorized()
    return user_id


AuthenticatedUserId = Annotated[str, Depends(require_auth)]


def require_roles(*allowed_roles: str):
    """
    Dependency factory for role-based access checks.

    Enforcement is gated by ROLE_ENFORCEMENT_V2.
    """
    normalized_allowed = {role.strip().lower() for role in allowed_roles}

    async def _check_role(role: CurrentUserRole) -> str:
        settings = get_settings()
        if not settings.role_enforcement_v2:
            return role

        if role not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: insufficient role privileges",
            )
        return role

    return _check_role
