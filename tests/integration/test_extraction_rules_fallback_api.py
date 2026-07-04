import pytest

from munipal.core.models import Artifact
from munipal.core.models.extraction import ExtractionJob


@pytest.mark.asyncio
async def test_run_extraction_job_uses_rules_fallback_when_anthropic_key_missing(
    test_client,
    factory,
    db_session,
    auth_headers,
    monkeypatch,
):
    playbook = await factory.create_playbook()
    project = await factory.create_project(playbook["id"], name="Oakport Demo")
    artifact = await factory.create_artifact(project["id"], filename="oakport_sources.pdf")
    artifact_model = await db_session.get(Artifact, artifact["id"])
    artifact_model.is_processed = True
    chunk = await factory.create_chunk(
        artifact["id"],
        content=(
            "Borrower: Oakport Health System\n"
            "Project location: Alameda County, California\n"
            "Total Project Cost: $42.5 million\n"
        ),
    )
    job = ExtractionJob(
        project_id=project["id"],
        job_type="api_extraction",
        artifact_ids=[artifact["id"]],
        chunk_ids=None,
        target_schema_paths=[
            "parties.borrower.name",
            "project.location.jurisdiction",
            "capital.project-cost",
        ],
        status="queued",
    )
    db_session.add(job)
    await db_session.commit()

    class MissingAnthropicClient:
        def __init__(self):
            raise ValueError("ANTHROPIC_API_KEY not configured")

    monkeypatch.setattr(
        "munipal.api.routes.extraction.AnthropicClient",
        MissingAnthropicClient,
    )

    response = await test_client.post(f"/api/v1/extraction/{job.id}/run", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["extraction_mode"] == "rules_based_fallback"
    assert payload["facts_extracted"] == 3

    facts_response = await test_client.get(
        "/api/v1/facts/?project_id=" + project["id"],
        headers=auth_headers,
    )
    assert facts_response.status_code == 200
    facts = facts_response.json()["facts"]
    by_path = {fact["schema_path"]: fact for fact in facts}
    assert by_path["parties.borrower.name"]["value"] == "Oakport Health System"
    assert by_path["capital.project-cost"]["value"] == 42500000

    refreshed_job = await db_session.get(ExtractionJob, job.id)
    assert refreshed_job.status == "completed"
    assert refreshed_job.error_message is None
    assert refreshed_job.processed_chunks == 1
    assert chunk["id"]
