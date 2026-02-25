from munipal.services import artifact_service as artifact_service_module


def test_enqueue_artifact_processing_task_calls_worker_delay(monkeypatch):
    calls: dict[str, str] = {}

    class FakeTask:
        @staticmethod
        def delay(artifact_id: str) -> None:
            calls["artifact_id"] = artifact_id

    monkeypatch.setattr(
        "munipal.workers.tasks.artifact_tasks.process_artifact",
        FakeTask,
    )

    artifact_service_module.enqueue_artifact_processing_task("artifact-123")

    assert calls["artifact_id"] == "artifact-123"
