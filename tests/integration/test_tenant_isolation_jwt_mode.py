"""Phase 9 tenant isolation integration tests for enforced JWT mode."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from jose import jwt

from munipal.config import get_settings
from munipal.core.models.user import User


def _make_token(
    *,
    user_id: str,
    role: str = "admin",
    tenant_claim_key: str = "tenant_id",
    tenant_id: str | None = None,
) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(UTC) + timedelta(minutes=10),
    }
    if tenant_claim_key and tenant_id:
        payload[tenant_claim_key] = tenant_id
    return jwt.encode(payload, "test-secret", algorithm="HS256")


@pytest.fixture(autouse=True)
def enable_enforced_jwt_tenant_mode(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AUTH_ENFORCEMENT_V2", "true")
    monkeypatch.setenv("ROLE_ENFORCEMENT_V2", "true")
    monkeypatch.setenv("TENANT_ISOLATION_V2", "true")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_jwt_subject_is_auto_provisioned_for_project_create(
    test_client,
    factory,
    db_session,
):
    user_id = str(uuid4())
    playbook = await factory.create_playbook(is_default=True)
    await db_session.commit()

    token = _make_token(
        user_id=user_id,
        tenant_claim_key="tenant_id",
        tenant_id="tenant-auto",
    )

    response = await test_client.post(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Auto-Provisioned User Project",
            "issuer_name": "Issuer Auto",
            "playbook_id": playbook["id"],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["owner_id"] == user_id
    assert payload["tenant_id"] == "tenant-auto"

    persisted_user = await db_session.get(User, user_id)
    assert persisted_user is not None
    assert persisted_user.email == f"{user_id}@jwt.local"
    assert persisted_user.organization == "tenant-auto"


@pytest.mark.asyncio
async def test_superuser_list_projects_is_filtered_by_jwt_tenant_claim(
    test_client,
    factory,
    db_session,
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

    alpha_token = _make_token(
        user_id=superuser_id,
        tenant_claim_key="tenant_id",
        tenant_id="tenant-alpha",
    )
    beta_token = _make_token(
        user_id=superuser_id,
        tenant_claim_key="tenant_id",
        tenant_id="tenant-beta",
    )

    alpha_create = await test_client.post(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {alpha_token}"},
        json={
            "name": "Tenant Alpha JWT Project",
            "issuer_name": "Issuer Alpha",
            "playbook_id": playbook["id"],
        },
    )
    assert alpha_create.status_code == 201

    beta_create = await test_client.post(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {beta_token}"},
        json={
            "name": "Tenant Beta JWT Project",
            "issuer_name": "Issuer Beta",
            "playbook_id": playbook["id"],
        },
    )
    assert beta_create.status_code == 201

    list_response = await test_client.get(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {alpha_token}"},
    )

    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["total"] == 1
    assert len(payload["projects"]) == 1
    assert payload["projects"][0]["tenant_id"] == "tenant-alpha"


@pytest.mark.asyncio
async def test_superuser_cross_tenant_project_access_returns_403_in_jwt_mode(
    test_client,
    factory,
    db_session,
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

    alpha_token = _make_token(
        user_id=superuser_id,
        tenant_claim_key="tenant_id",
        tenant_id="tenant-alpha",
    )
    beta_token = _make_token(
        user_id=superuser_id,
        tenant_claim_key="tenant_id",
        tenant_id="tenant-beta",
    )

    beta_create = await test_client.post(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {beta_token}"},
        json={
            "name": "Tenant Beta JWT Project",
            "issuer_name": "Issuer Beta",
            "playbook_id": playbook["id"],
        },
    )
    assert beta_create.status_code == 201
    beta_project_id = beta_create.json()["id"]

    read_response = await test_client.get(
        f"/api/v1/projects/{beta_project_id}",
        headers={"Authorization": f"Bearer {alpha_token}"},
    )

    assert read_response.status_code == 403
    assert read_response.json()["detail"] == "Forbidden: cross-tenant access denied"


@pytest.mark.asyncio
async def test_jwt_org_claim_drives_tenant_and_ignores_x_tenant_header(
    test_client,
    factory,
    db_session,
):
    superuser_id = str(uuid4())
    db_session.add(
        User(
            id=superuser_id,
            email=f"{superuser_id}@example.com",
            hashed_password="test",
            is_superuser=True,
            organization="legacy-org",
        )
    )
    playbook = await factory.create_playbook(is_default=True)
    await db_session.commit()

    org_claim_token = _make_token(
        user_id=superuser_id,
        tenant_claim_key="org",
        tenant_id="tenant-from-org-claim",
    )

    create_response = await test_client.post(
        "/api/v1/projects/",
        headers={
            "Authorization": f"Bearer {org_claim_token}",
            "X-Tenant-Id": "header-tenant-should-be-ignored",
        },
        json={
            "name": "Org Claim Tenant Project",
            "issuer_name": "Issuer Org",
            "playbook_id": playbook["id"],
        },
    )

    assert create_response.status_code == 201
    created_project = create_response.json()
    assert created_project["tenant_id"] == "tenant-from-org-claim"
