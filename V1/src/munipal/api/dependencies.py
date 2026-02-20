"""
API dependencies for FastAPI dependency injection.

Per spec: JWT-based authentication with role-based access control.
For initial development, we use a simplified auth approach.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.db.session import get_async_session

# Type alias for database session dependency
DbSession = Annotated[AsyncSession, Depends(get_async_session)]


# -----------------------------------------------------------------------------
# Simplified Auth (Development)
# TODO: Replace with full JWT auth implementation
# -----------------------------------------------------------------------------

async def get_current_user_id(
    x_user_id: str | None = Header(None, description="User ID for development auth"),
) -> str:
    """
    Get current user ID from request.

    Development mode: Uses X-User-Id header.
    Production mode: Will use JWT token validation.

    For now, if no user ID is provided, we use a default development user.
    """
    if x_user_id:
        return x_user_id

    # Default development user ID
    # In production, this would raise HTTPException if no valid auth
    return "00000000-0000-0000-0000-000000000001"


CurrentUserId = Annotated[str, Depends(get_current_user_id)]


async def require_auth(
    user_id: CurrentUserId,
) -> str:
    """
    Require authentication.

    In development, always passes with dev user.
    In production, will validate JWT and require valid user.
    """
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user_id


AuthenticatedUserId = Annotated[str, Depends(require_auth)]
