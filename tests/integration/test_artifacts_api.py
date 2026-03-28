from pathlib import Path

import pytest

from munipal.services import artifact_service as artifact_service_module


@pytest.mark.asyncio
async def test_upload_artifact_enqueues_async_chunking(
    monkeypatch: pytest.MonkeyPatch,
    test_client,
    factory,
    db_session,
    tmp_path: Path,
    auth_headers,
):
    queued: dict[str, str] = {}

    def fake_enqueue(artifact_id: str) -> None:
        queued["artifact_id"] = artifact_id

    monkeypatch.setattr(
        artifact_service_module,
        "enqueue_artifact_processing_task",
        fake_enqueue,
    )
    monkeypatch.setattr(
        artifact_service_module.settings,
        "artifact_storage_path",
        str(tmp_path),
        raising=False,
    )

    playbook = await factory.create_playbook()
    project = await factory.create_project(playbook["id"])
    await db_session.commit()

    response = await test_client.post(
        "/api/v1/artifacts/upload",
        data={"project_id": project["id"], "display_name": "Input TXT"},
        files={"file": ("input.txt", b"hello world", "text/plain")},
        headers=auth_headers,
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["id"] == queued["artifact_id"]
    assert payload["processing_error"] is None


@pytest.mark.asyncio
async def test_upload_artifact_persists_dispatch_failure_message(
    monkeypatch: pytest.MonkeyPatch,
    test_client,
    factory,
    db_session,
    tmp_path: Path,
    auth_headers,
):
    def fake_enqueue(_artifact_id: str) -> None:
        raise RuntimeError("broker unavailable")

    monkeypatch.setattr(
        artifact_service_module,
        "enqueue_artifact_processing_task",
        fake_enqueue,
    )
    monkeypatch.setattr(
        artifact_service_module.settings,
        "artifact_storage_path",
        str(tmp_path),
        raising=False,
    )

    playbook = await factory.create_playbook()
    project = await factory.create_project(playbook["id"])
    await db_session.commit()

    response = await test_client.post(
        "/api/v1/artifacts/upload",
        data={"project_id": project["id"], "display_name": "Input TXT"},
        files={"file": ("input.txt", b"hello world", "text/plain")},
        headers=auth_headers,
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["processing_error"] is not None
    assert "chunk_dispatch_failed" in payload["processing_error"]
    assert "RuntimeError: broker unavailable" in payload["processing_error"]
