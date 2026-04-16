"""Integration tests for auth routes — register, login, refresh, and profile."""

import pytest
from jose import jwt

from munipal.config import get_settings
from munipal.core.models import User


@pytest.fixture
async def registered_user(db_session):
    """Create a user directly in the DB for login/refresh/profile tests."""
    from munipal.api.routes.auth import _hash_password

    user = User(
        email="alice@example.com",
        hashed_password=_hash_password("Str0ng!Pass"),
        full_name="Alice Test",
        organization="Test Org",
        subscription_tier="free",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestRegister:
    """POST /api/v1/auth/register"""

    async def test_register_success(self, test_client):
        resp = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "password": "S3cure!pw",
                "full_name": "New User",
                "organization": "Acme Corp",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    async def test_register_duplicate_email(self, test_client, registered_user):
        resp = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": registered_user.email,
                "password": "AnyPass1!",
            },
        )
        assert resp.status_code == 409

    async def test_register_invalid_email(self, test_client):
        resp = await test_client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "x"},
        )
        assert resp.status_code == 422


class TestLogin:
    """POST /api/v1/auth/login"""

    async def test_login_success(self, test_client, registered_user):
        resp = await test_client.post(
            "/api/v1/auth/login",
            json={"email": "alice@example.com", "password": "Str0ng!Pass"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_wrong_password(self, test_client, registered_user):
        resp = await test_client.post(
            "/api/v1/auth/login",
            json={"email": "alice@example.com", "password": "wrong"},
        )
        assert resp.status_code == 401

    async def test_login_unknown_email(self, test_client):
        resp = await test_client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "x"},
        )
        assert resp.status_code == 401

    async def test_login_deactivated_user(self, test_client, db_session, registered_user):
        registered_user.is_active = False
        await db_session.commit()

        resp = await test_client.post(
            "/api/v1/auth/login",
            json={"email": "alice@example.com", "password": "Str0ng!Pass"},
        )
        assert resp.status_code == 403


class TestRefresh:
    """POST /api/v1/auth/refresh"""

    async def test_refresh_success(self, test_client, registered_user):
        # Login first to get tokens
        login_resp = await test_client.post(
            "/api/v1/auth/login",
            json={"email": "alice@example.com", "password": "Str0ng!Pass"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        resp = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_with_access_token_rejected(self, test_client, registered_user):
        login_resp = await test_client.post(
            "/api/v1/auth/login",
            json={"email": "alice@example.com", "password": "Str0ng!Pass"},
        )
        access_token = login_resp.json()["access_token"]

        resp = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        assert resp.status_code == 401

    async def test_refresh_with_garbage_token(self, test_client):
        resp = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "not.a.token"},
        )
        assert resp.status_code == 401

    async def test_refresh_deactivated_user(self, test_client, db_session, registered_user):
        login_resp = await test_client.post(
            "/api/v1/auth/login",
            json={"email": "alice@example.com", "password": "Str0ng!Pass"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        registered_user.is_active = False
        await db_session.commit()

        resp = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 401


class TestProfile:
    """GET /api/v1/auth/me — uses dev fallback auth (AUTH_ENFORCEMENT_V2=false)."""

    async def test_get_profile(self, test_client, db_session):
        """With auth enforcement off, the dev fallback user ID is used."""
        from munipal.api.dependencies import DEV_FALLBACK_USER_ID

        user = User(
            id=DEV_FALLBACK_USER_ID,
            email="dev@example.com",
            hashed_password="unused",
            full_name="Dev User",
            subscription_tier="free",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        resp = await test_client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "dev@example.com"
        assert data["is_active"] is True
