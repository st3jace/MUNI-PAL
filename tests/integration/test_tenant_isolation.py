"""Phase 8 tenant isolation integration tests."""

from uuid import uuid4

import pytest

from munipal.config import get_settings
from munipal.core.models.user import User


@pytest.fixture(autouse=True)
def enable_tenant_isolation(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TENANT_ISOLATION_V2", "true")
    monkeypatch.setenv("AUTH_ENFORCEMENT_V2", "true")
    monkeypatch.setenv("ROLE_ENFORCEMENT_V2", "true")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _auth_headers(jwt_token_factory, user_id: str, tenant_id: str, role: str = "admin") -> dict[str, str]:
    token = jwt_token_factory(user_id=user_id, role=role, tenant_id=tenant_id)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_superuser_list_projects_is_filtered_by_tenant_header(
    test_client,
    factory,
    db_session,
    jwt_token_factory,
):
    superuser_id = str(uuid4())
    db_session.add(
        User(
            id=superuser_id,
            email=f"{superuser_id}@example.com",
            hashed_password="test",
            is_superuser=True,
            organization="tenant-alpha",
        )
    )
    playbook = await factory.create_playbook(is_default=True)
    await db_session.commit()

    alpha_create = await test_client.post(
        "/api/v1/projects/",
        headers=_auth_headers(jwt_token_factory, superuser_id, tenant_id="tenant-alpha"),
        json={
            "name": "Tenant Alpha Project",
            "issuer_name": "Issuer Alpha",
            "playbook_id": playbook["id"],
        },
    )
    assert alpha_create.status_code == 201

    beta_create = await test_client.post(
        "/api/v1/projects/",
        headers=_auth_headers(jwt_token_factory, superuser_id, tenant_id="tenant-beta"),
        json={
            "name": "Tenant Beta Project",
            "issuer_name": "Issuer Beta",
            "playbook_id": playbook["id"],
        },
    )
    assert beta_create.status_code == 201

    response = await test_client.get(
        "/api/v1/projects/",
        headers=_auth_headers(jwt_token_factory, superuser_id, tenant_id="tenant-alpha"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert len(payload["projects"]) == 1
    assert payload["projects"][0]["tenant_id"] == "tenant-alpha"


@pytest.mark.asyncio
async def test_superuser_cross_tenant_project_access_returns_403(
    test_client,
    factory,
    db_session,
    jwt_token_factory,
):
    superuser_id = str(uuid4())
    db_session.add(
        User(
            id=superuser_id,
            email=f"{superuser_id}@example.com",
            hashed_password="test",
            is_superuser=True,
            organization="tenant-alpha",
        )
    )
    playbook = await factory.create_playbook(is_default=True)
    await db_session.commit()

    beta_create = await test_client.post(
        "/api/v1/projects/",
        headers=_auth_headers(jwt_token_factory, superuser_id, tenant_id="tenant-beta"),
        json={
            "name": "Tenant Beta Project",
            "issuer_name": "Issuer Beta",
            "playbook_id": playbook["id"],
        },
    )
    assert beta_create.status_code == 201
    beta_project_id = beta_create.json()["id"]

    response = await test_client.get(
        f"/api/v1/projects/{beta_project_id}",
        headers=_auth_headers(jwt_token_factory, superuser_id, tenant_id="tenant-alpha"),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden: cross-tenant access denied"
