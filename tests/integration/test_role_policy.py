"""
SEC-005 integration tests for role-based route policy.
"""

from uuid import uuid4

import pytest

from munipal.config import get_settings


@pytest.fixture(autouse=True)
def enable_role_enforcement(monkeypatch: pytest.MonkeyPatch):
    """Enable role enforcement in JWT-auth mode."""
    monkeypatch.setenv("AUTH_ENFORCEMENT_V2", "true")
    monkeypatch.setenv("ROLE_ENFORCEMENT_V2", "true")
    monkeypatch.setenv("TENANT_ISOLATION_V2", "false")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _auth_headers(jwt_token_factory, user_id: str, role: str, tenant_id: str = "default") -> dict[str, str]:
    token = jwt_token_factory(user_id=user_id, role=role, tenant_id=tenant_id)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_viewer_cannot_create_project(test_client, jwt_token_factory):
    viewer_id = str(uuid4())
    response = await test_client.post(
        "/api/v1/projects/",
        headers=_auth_headers(jwt_token_factory, viewer_id, role="viewer"),
        json={
            "name": "Viewer Project",
            "description": "Should be blocked",
            "issuer_name": "Issuer",
            "project_location": "Test City, ST",
            "target_bond_amount": 1000000.0,
        },
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden: insufficient role privileges"


@pytest.mark.asyncio
async def test_analyst_cannot_delete_project(test_client, factory, jwt_token_factory):
    playbook = await factory.create_playbook()
    analyst_id = str(uuid4())
    project = await factory.create_project(playbook_id=playbook["id"], owner_id=analyst_id)

    response = await test_client.delete(
        f"/api/v1/projects/{project['id']}",
        headers=_auth_headers(jwt_token_factory, analyst_id, role="analyst"),
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden: insufficient role privileges"


@pytest.mark.asyncio
async def test_admin_can_delete_project(test_client, factory, jwt_token_factory):
    playbook = await factory.create_playbook()
    admin_id = str(uuid4())
    project = await factory.create_project(playbook_id=playbook["id"], owner_id=admin_id)

    response = await test_client.delete(
        f"/api/v1/projects/{project['id']}",
        headers=_auth_headers(jwt_token_factory, admin_id, role="admin"),
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_viewer_can_read_project(test_client, factory, jwt_token_factory):
    playbook = await factory.create_playbook()
    viewer_id = str(uuid4())
    project = await factory.create_project(playbook_id=playbook["id"], owner_id=viewer_id)

    response = await test_client.get(
        f"/api/v1/projects/{project['id']}",
        headers=_auth_headers(jwt_token_factory, viewer_id, role="viewer"),
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_viewer_cannot_create_extraction_job(test_client, factory, jwt_token_factory):
    playbook = await factory.create_playbook()
    viewer_id = str(uuid4())
    project = await factory.create_project(playbook_id=playbook["id"], owner_id=viewer_id)

    response = await test_client.post(
        "/api/v1/extraction/",
        headers=_auth_headers(jwt_token_factory, viewer_id, role="viewer"),
        json={
            "project_id": project["id"],
            "artifact_ids": [str(uuid4())],
            "target_schema_paths": [],
        },
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden: insufficient role privileges"
