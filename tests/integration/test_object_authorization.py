"""
SEC-004 integration tests for object-level authorization.
"""

from uuid import uuid4

import pytest

from munipal.config import get_settings
from munipal.core.models.artifact import Artifact
from munipal.core.models.extraction import ExtractionJob
from munipal.core.models.fact import ExtractedFact


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
async def test_non_owner_cannot_access_artifact_extraction_and_fact_objects(
    test_client,
    factory,
    db_session,
    jwt_token_factory,
):
    playbook = await factory.create_playbook()
    owner_id = str(uuid4())
    other_user_id = str(uuid4())
    project = await factory.create_project(playbook_id=playbook["id"], owner_id=owner_id)

    artifact_id = str(uuid4())
    artifact = Artifact(
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
    db_session.add(artifact)

    job_id = str(uuid4())
    job = ExtractionJob(
        id=job_id,
        project_id=project["id"],
        job_type="api_extraction",
        target_schema_paths=["project.canonicaldescription"],
        artifact_ids=[artifact_id],
        status="completed",
    )
    db_session.add(job)

    fact_id = str(uuid4())
    fact = ExtractedFact(
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
    db_session.add(fact)
    await db_session.flush()

    artifact_resp = await test_client.get(
        f"/api/v1/artifacts/{artifact_id}",
        headers=_auth_headers(jwt_token_factory, other_user_id),
    )
    assert artifact_resp.status_code == 403

    job_resp = await test_client.get(
        f"/api/v1/extraction/{job_id}",
        headers=_auth_headers(jwt_token_factory, other_user_id),
    )
    assert job_resp.status_code == 403

    fact_resp = await test_client.get(
        f"/api/v1/facts/{fact_id}",
        headers=_auth_headers(jwt_token_factory, other_user_id),
    )
    assert fact_resp.status_code == 403


@pytest.mark.asyncio
async def test_non_owner_cannot_query_project_scoped_object_endpoints(
    test_client,
    factory,
    db_session,
    jwt_token_factory,
):
    playbook = await factory.create_playbook()
    owner_id = str(uuid4())
    other_user_id = str(uuid4())
    project = await factory.create_project(playbook_id=playbook["id"], owner_id=owner_id)

    artifact_id = str(uuid4())
    artifact = Artifact(
        id=artifact_id,
        project_id=project["id"],
        filename="owner-doc.pdf",
        display_name="owner-doc.pdf",
        artifact_type="pdf",
        mime_type="application/pdf",
        file_size_bytes=1234,
        storage_path=f"{project['id']}/{artifact_id}.pdf",
        is_processed=True,
        is_extracted=False,
    )
    db_session.add(artifact)
    await db_session.flush()

    artifacts_list_resp = await test_client.get(
        "/api/v1/artifacts/",
        params={"project_id": project["id"]},
        headers=_auth_headers(jwt_token_factory, other_user_id),
    )
    assert artifacts_list_resp.status_code == 403

    extraction_list_resp = await test_client.get(
        "/api/v1/extraction/",
        params={"project_id": project["id"]},
        headers=_auth_headers(jwt_token_factory, other_user_id),
    )
    assert extraction_list_resp.status_code == 403

    facts_list_resp = await test_client.get(
        "/api/v1/facts/",
        params={"project_id": project["id"]},
        headers=_auth_headers(jwt_token_factory, other_user_id),
    )
    assert facts_list_resp.status_code == 403


@pytest.mark.asyncio
async def test_owner_can_access_object_endpoints(test_client, factory, db_session, jwt_token_factory):
    playbook = await factory.create_playbook()
    owner_id = str(uuid4())
    project = await factory.create_project(playbook_id=playbook["id"], owner_id=owner_id)

    artifact_id = str(uuid4())
    artifact = Artifact(
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
    db_session.add(artifact)

    job_id = str(uuid4())
    job = ExtractionJob(
        id=job_id,
        project_id=project["id"],
        job_type="api_extraction",
        target_schema_paths=["project.canonicaldescription"],
        artifact_ids=[artifact_id],
        status="completed",
    )
    db_session.add(job)

    fact_id = str(uuid4())
    fact = ExtractedFact(
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
    db_session.add(fact)
    await db_session.flush()

    artifact_resp = await test_client.get(
        f"/api/v1/artifacts/{artifact_id}",
        headers=_auth_headers(jwt_token_factory, owner_id),
    )
    assert artifact_resp.status_code == 200

    job_resp = await test_client.get(
        f"/api/v1/extraction/{job_id}",
        headers=_auth_headers(jwt_token_factory, owner_id),
    )
    assert job_resp.status_code == 200

    fact_resp = await test_client.get(
        f"/api/v1/facts/{fact_id}",
        headers=_auth_headers(jwt_token_factory, owner_id),
    )
    assert fact_resp.status_code == 200
