"""Authentication routes — register, login, token refresh, and profile."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.api.dependencies import CurrentUserId, DbSession
from munipal.config import get_settings
from munipal.core.models import User

router = APIRouter()
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
#  Schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    organization: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str | None
    organization: str | None
    subscription_tier: str | None
    is_active: bool


# ---------------------------------------------------------------------------
#  Token helpers
# ---------------------------------------------------------------------------

def _create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def _create_tokens(user_id: str) -> TokenResponse:
    settings = get_settings()
    access_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    refresh_delta = timedelta(days=settings.jwt_refresh_token_expire_days)
    return TokenResponse(
        access_token=_create_token(user_id, "access", access_delta),
        refresh_token=_create_token(user_id, "refresh", refresh_delta),
        expires_in=int(access_delta.total_seconds()),
    )


# ---------------------------------------------------------------------------
#  Routes
# ---------------------------------------------------------------------------

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: DbSession):
    """Create a new user account and return tokens."""
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email=payload.email,
        hashed_password=_pwd_context.hash(payload.password),
        full_name=payload.full_name,
        organization=payload.organization,
        subscription_tier="free",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return _create_tokens(user.id)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: DbSession):
    """Authenticate with email and password."""
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not _pwd_context.verify(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated.",
        )

    return _create_tokens(user.id)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshRequest, db: DbSession):
    """Exchange a refresh token for new access + refresh tokens."""
    settings = get_settings()
    try:
        claims = jwt.decode(
            payload.refresh_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    if claims.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is not a refresh token.",
        )

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject.",
        )

    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated.",
        )

    return _create_tokens(user.id)


@router.get("/me", response_model=UserProfile)
async def get_profile(user_id: CurrentUserId, db: DbSession):
    """Get the current user's profile."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return UserProfile(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        organization=user.organization,
        subscription_tier=user.subscription_tier or "free",
        is_active=user.is_active,
    )
