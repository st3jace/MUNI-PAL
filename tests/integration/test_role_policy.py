"""
SEC-005 integration tests for role-based route policy.
"""

from uuid import uuid4

import pytest

from munipal.config import get_settings


@pytest.fixture(autouse=True)
def enable_role_enforcement(monkeypatch: pytest.MonkeyPatch):
    """Enable role enforcement while keeping compat auth mode."""
    monkeypatch.setenv("AUTH_ENFORCEMENT_V2", "false")
    monkeypatch.setenv("ROLE_ENFORCEMENT_V2", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_viewer_cannot_create_project(test_client):
    viewer_id = str(uuid4())
    response = await test_client.post(
        "/api/v1/projects/",
        headers={"X-User-Id": viewer_id, "X-User-Role": "viewer"},
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
async def test_analyst_cannot_delete_project(test_client, factory):
    playbook = await factory.create_playbook()
    analyst_id = str(uuid4())
    project = await factory.create_project(playbook_id=playbook["id"], owner_id=analyst_id)

    response = await test_client.delete(
        f"/api/v1/projects/{project['id']}",
        headers={"X-User-Id": analyst_id, "X-User-Role": "analyst"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden: insufficient role privileges"


@pytest.mark.asyncio
async def test_admin_can_delete_project(test_client, factory):
    playbook = await factory.create_playbook()
    admin_id = str(uuid4())
    project = await factory.create_project(playbook_id=playbook["id"], owner_id=admin_id)

    response = await test_client.delete(
        f"/api/v1/projects/{project['id']}",
        headers={"X-User-Id": admin_id, "X-User-Role": "admin"},
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_viewer_can_read_project(test_client, factory):
    playbook = await factory.create_playbook()
    viewer_id = str(uuid4())
    project = await factory.create_project(playbook_id=playbook["id"], owner_id=viewer_id)

    response = await test_client.get(
        f"/api/v1/projects/{project['id']}",
        headers={"X-User-Id": viewer_id, "X-User-Role": "viewer"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_viewer_cannot_create_extraction_job(test_client, factory):
    playbook = await factory.create_playbook()
    viewer_id = str(uuid4())
    project = await factory.create_project(playbook_id=playbook["id"], owner_id=viewer_id)

    response = await test_client.post(
        "/api/v1/extraction/",
        headers={"X-User-Id": viewer_id, "X-User-Role": "viewer"},
        json={
            "project_id": project["id"],
            "artifact_ids": [str(uuid4())],
            "target_schema_paths": [],
        },
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden: insufficient role privileges"
