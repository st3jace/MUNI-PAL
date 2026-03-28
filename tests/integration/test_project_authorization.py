"""
SEC-003 integration tests for project ownership authorization.
"""

from uuid import uuid4

import pytest

from munipal.config import get_settings


@pytest.fixture(autouse=True)
def enable_jwt_auth(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AUTH_ENFORCEMENT_V2", "true")
    monkeypatch.setenv("ROLE_ENFORCEMENT_V2", "false")
    monkeypatch.setenv("TENANT_ISOLATION_V2", "false")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _auth_headers(jwt_token_factory, user_id: str, role: str = "admin", tenant_id: str = "default") -> dict[str, str]:
    token = jwt_token_factory(user_id=user_id, role=role, tenant_id=tenant_id)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_project_owner_can_read_project(test_client, factory, jwt_token_factory):
    playbook = await factory.create_playbook()
    owner_id = str(uuid4())
    project = await factory.create_project(playbook_id=playbook["id"], owner_id=owner_id)

    response = await test_client.get(
        f"/api/v1/projects/{project['id']}",
        headers=_auth_headers(jwt_token_factory, owner_id),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == project["id"]
    assert payload["owner_id"] == owner_id


@pytest.mark.asyncio
async def test_non_owner_get_project_returns_403(test_client, factory, jwt_token_factory):
    playbook = await factory.create_playbook()
    owner_id = str(uuid4())
    other_user_id = str(uuid4())
    project = await factory.create_project(playbook_id=playbook["id"], owner_id=owner_id)

    response = await test_client.get(
        f"/api/v1/projects/{project['id']}",
        headers=_auth_headers(jwt_token_factory, other_user_id),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden: insufficient access to project"


@pytest.mark.asyncio
async def test_non_owner_update_project_returns_403(test_client, factory, jwt_token_factory):
    playbook = await factory.create_playbook()
    owner_id = str(uuid4())
    other_user_id = str(uuid4())
    project = await factory.create_project(playbook_id=playbook["id"], owner_id=owner_id)

    response = await test_client.patch(
        f"/api/v1/projects/{project['id']}",
        headers=_auth_headers(jwt_token_factory, other_user_id),
        json={"name": "Unauthorized Update"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden: insufficient access to project"


@pytest.mark.asyncio
async def test_non_owner_delete_project_returns_403(test_client, factory, jwt_token_factory):
    playbook = await factory.create_playbook()
    owner_id = str(uuid4())
    other_user_id = str(uuid4())
    project = await factory.create_project(playbook_id=playbook["id"], owner_id=owner_id)

    response = await test_client.delete(
        f"/api/v1/projects/{project['id']}",
        headers=_auth_headers(jwt_token_factory, other_user_id),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden: insufficient access to project"


@pytest.mark.asyncio
async def test_list_projects_returns_only_owner_projects_for_non_superuser(test_client, factory, jwt_token_factory):
    playbook = await factory.create_playbook()
    owner_a = str(uuid4())
    owner_b = str(uuid4())

    project_a = await factory.create_project(playbook_id=playbook["id"], owner_id=owner_a, name="A")
    await factory.create_project(playbook_id=playbook["id"], owner_id=owner_b, name="B")

    response = await test_client.get(
        "/api/v1/projects/",
        headers=_auth_headers(jwt_token_factory, owner_a),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert len(payload["projects"]) == 1
    assert payload["projects"][0]["id"] == project_a["id"]
