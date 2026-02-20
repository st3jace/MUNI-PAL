"""
SEC-007 integration tests for JWT auth + role + ownership behavior.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from jose import jwt

from munipal.config import get_settings
from munipal.core.models.artifact import Artifact
from munipal.core.models.extraction import ExtractionJob
from munipal.core.models.fact import ExtractedFact


def _make_token(user_id: str, role: str = "analyst") -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(UTC) + timedelta(minutes=10),
    }
    return jwt.encode(payload, "test-secret", algorithm="HS256")


@pytest.fixture(autouse=True)
def enable_security_enforcement(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AUTH_ENFORCEMENT_V2", "true")
    monkeypatch.setenv("ROLE_ENFORCEMENT_V2", "true")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_missing_bearer_token_returns_401(test_client):
    response = await test_client.get("/api/v1/projects/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing bearer token"


@pytest.mark.asyncio
async def test_invalid_bearer_token_returns_401(test_client):
    response = await test_client.get(
        "/api/v1/projects/",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


@pytest.mark.asyncio
async def test_role_policy_enforced_with_jwt(test_client, factory):
    playbook = await factory.create_playbook()
    owner_id = str(uuid4())
    project = await factory.create_project(playbook_id=playbook["id"], owner_id=owner_id)

    viewer_token = _make_token(owner_id, role="viewer")
    response = await test_client.delete(
        f"/api/v1/projects/{project['id']}",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden: insufficient role privileges"


@pytest.mark.asyncio
async def test_project_ownership_enforced_with_jwt(test_client, factory):
    playbook = await factory.create_playbook()
    owner_id = str(uuid4())
    other_id = str(uuid4())
    project = await factory.create_project(playbook_id=playbook["id"], owner_id=owner_id)

    owner_token = _make_token(owner_id, role="analyst")
    other_token = _make_token(other_id, role="analyst")

    owner_resp = await test_client.get(
        f"/api/v1/projects/{project['id']}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert owner_resp.status_code == 200

    other_resp = await test_client.get(
        f"/api/v1/projects/{project['id']}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert other_resp.status_code == 403
    assert other_resp.json()["detail"] == "Forbidden: insufficient access to project"


@pytest.mark.asyncio
async def test_owner_can_read_project_scoped_objects_with_jwt(test_client, factory, db_session):
    playbook = await factory.create_playbook()
    owner_id = str(uuid4())
    project = await factory.create_project(playbook_id=playbook["id"], owner_id=owner_id)
    token = _make_token(owner_id, role="viewer")

    artifact_id = str(uuid4())
    db_session.add(
        Artifact(
            id=artifact_id,
            project_id=project["id"],
            filename="owner-doc.pdf",
            display_name="owner-doc.pdf",
            artifact_type="pdf",
            mime_type="application/pdf",
            file_size_bytes=1234,
            storage_path=f"{project['id']}/{artifact_id}.pdf",
            is_processed=True,
            is_extracted=True,
        )
    )

    job_id = str(uuid4())
    db_session.add(
        ExtractionJob(
            id=job_id,
            project_id=project["id"],
            job_type="api_extraction",
            target_schema_paths=["project.canonicaldescription"],
            artifact_ids=[artifact_id],
            status="completed",
        )
    )

    fact_id = str(uuid4())
    db_session.add(
        ExtractedFact(
            id=fact_id,
            schema_path="project.canonicaldescription",
            criticality="material",
            source_type="extracted",
            value={"text": "Owner project fact"},
            value_type="string",
            confidence_score=0.95,
            review_status="approved",
            project_id=project["id"],
            extraction_job_id=job_id,
        )
    )
    await db_session.flush()

    authz_headers = {"Authorization": f"Bearer {token}"}
    artifact_resp = await test_client.get(f"/api/v1/artifacts/{artifact_id}", headers=authz_headers)
    job_resp = await test_client.get(f"/api/v1/extraction/{job_id}", headers=authz_headers)
    fact_resp = await test_client.get(f"/api/v1/facts/{fact_id}", headers=authz_headers)

    assert artifact_resp.status_code == 200
    assert job_resp.status_code == 200
    assert fact_resp.status_code == 200


@pytest.mark.asyncio
async def test_non_owner_cannot_read_project_scoped_objects_with_jwt(test_client, factory, db_session):
    playbook = await factory.create_playbook()
    owner_id = str(uuid4())
    other_id = str(uuid4())
    project = await factory.create_project(playbook_id=playbook["id"], owner_id=owner_id)

    artifact_id = str(uuid4())
    db_session.add(
        Artifact(
            id=artifact_id,
            project_id=project["id"],
            filename="owner-doc.pdf",
            display_name="owner-doc.pdf",
            artifact_type="pdf",
            mime_type="application/pdf",
            file_size_bytes=1234,
            storage_path=f"{project['id']}/{artifact_id}.pdf",
            is_processed=True,
            is_extracted=True,
        )
    )

    job_id = str(uuid4())
    db_session.add(
        ExtractionJob(
            id=job_id,
            project_id=project["id"],
            job_type="api_extraction",
            target_schema_paths=["project.canonicaldescription"],
            artifact_ids=[artifact_id],
            status="completed",
        )
    )

    fact_id = str(uuid4())
    db_session.add(
        ExtractedFact(
            id=fact_id,
            schema_path="project.canonicaldescription",
            criticality="material",
            source_type="extracted",
            value={"text": "Owner project fact"},
            value_type="string",
            confidence_score=0.95,
            review_status="approved",
            project_id=project["id"],
            extraction_job_id=job_id,
        )
    )
    await db_session.flush()

    token = _make_token(other_id, role="viewer")
    authz_headers = {"Authorization": f"Bearer {token}"}
    artifact_resp = await test_client.get(f"/api/v1/artifacts/{artifact_id}", headers=authz_headers)
    job_resp = await test_client.get(f"/api/v1/extraction/{job_id}", headers=authz_headers)
    fact_resp = await test_client.get(f"/api/v1/facts/{fact_id}", headers=authz_headers)

    assert artifact_resp.status_code == 403
    assert job_resp.status_code == 403
    assert fact_resp.status_code == 403
