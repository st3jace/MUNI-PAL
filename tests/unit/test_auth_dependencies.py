"""
Tests for auth dependency behavior.

SEC-001 scope:
- Keep compatibility behavior while AUTH_ENFORCEMENT_V2 is disabled
- Enforce JWT bearer validation when AUTH_ENFORCEMENT_V2 is enabled
"""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from jose import jwt

from munipal.api.dependencies import (
    DEFAULT_TENANT_ID,
    DEV_FALLBACK_USER_ID,
    get_current_tenant_id,
    get_current_user_id,
)
from munipal.config import get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Ensure env var changes are reflected per test."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_auth_compat_mode_uses_header_user_id(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AUTH_ENFORCEMENT_V2", "false")

    user_id = await get_current_user_id(
        authorization=None,
        x_user_id="test-user-id",
    )

    assert user_id == "test-user-id"


@pytest.mark.asyncio
async def test_auth_compat_mode_uses_dev_fallback_when_header_missing(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("AUTH_ENFORCEMENT_V2", "false")

    user_id = await get_current_user_id(
        authorization=None,
        x_user_id=None,
    )

    assert user_id == DEV_FALLBACK_USER_ID


@pytest.mark.asyncio
async def test_auth_enforced_mode_rejects_missing_authorization_header(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("AUTH_ENFORCEMENT_V2", "true")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id(
            authorization=None,
            x_user_id=DEV_FALLBACK_USER_ID,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing bearer token"


@pytest.mark.asyncio
async def test_auth_enforced_mode_rejects_non_bearer_scheme(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("AUTH_ENFORCEMENT_V2", "true")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id(
            authorization="Basic abc123",
            x_user_id=DEV_FALLBACK_USER_ID,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid authorization scheme"


@pytest.mark.asyncio
async def test_auth_enforced_mode_accepts_valid_jwt(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AUTH_ENFORCEMENT_V2", "true")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")

    token = jwt.encode(
        {
            "sub": "user-123",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        "test-secret",
        algorithm="HS256",
    )

    user_id = await get_current_user_id(
        authorization=f"Bearer {token}",
        x_user_id=DEV_FALLBACK_USER_ID,
    )

    assert user_id == "user-123"


@pytest.mark.asyncio
async def test_auth_enforced_mode_rejects_token_without_subject(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("AUTH_ENFORCEMENT_V2", "true")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")

    token = jwt.encode(
        {"exp": datetime.now(UTC) + timedelta(minutes=5)},
        "test-secret",
        algorithm="HS256",
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id(
            authorization=f"Bearer {token}",
            x_user_id=DEV_FALLBACK_USER_ID,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token subject is missing"


@pytest.mark.asyncio
async def test_tenant_compat_mode_uses_header_tenant_id(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AUTH_ENFORCEMENT_V2", "false")

    tenant_id = await get_current_tenant_id(
        authorization=None,
        x_tenant_id="tenant-alpha",
    )

    assert tenant_id == "tenant-alpha"


@pytest.mark.asyncio
async def test_tenant_compat_mode_falls_back_to_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AUTH_ENFORCEMENT_V2", "false")

    tenant_id = await get_current_tenant_id(
        authorization=None,
        x_tenant_id=None,
    )

    assert tenant_id == DEFAULT_TENANT_ID


@pytest.mark.asyncio
async def test_tenant_enforced_mode_reads_tenant_claim(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AUTH_ENFORCEMENT_V2", "true")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")

    token = jwt.encode(
        {
            "sub": "user-123",
            "tenant_id": "tenant-jwt",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        "test-secret",
        algorithm="HS256",
    )

    tenant_id = await get_current_tenant_id(
        authorization=f"Bearer {token}",
        x_tenant_id=None,
    )

    assert tenant_id == "tenant-jwt"


@pytest.mark.asyncio
async def test_tenant_enforced_mode_defaults_when_claim_missing(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("AUTH_ENFORCEMENT_V2", "true")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")

    token = jwt.encode(
        {
            "sub": "user-123",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        "test-secret",
        algorithm="HS256",
    )

    tenant_id = await get_current_tenant_id(
        authorization=f"Bearer {token}",
        x_tenant_id=None,
    )

    assert tenant_id == DEFAULT_TENANT_ID
