"""
AI extraction tasks.

Per spec (WP3): AI Pipelines & Review
- Propose facts via schema-driven extraction
- Enable human review & approval
- Maintain confidence scores and provenance
"""

from uuid import UUID

from munipal.workers.celery_app import celery_app


@celery_app.task(bind=True, name="munipal.workers.tasks.extraction_tasks.run_extraction_job")
def run_extraction_job(self, job_id: str) -> dict:
    """
    Run an extraction job using the configured extractor.

    This task:
    1. Loads the extraction job configuration
    2. Retrieves relevant chunks from artifacts
    3. Calls the Anthropic API with the extractor's prompt
    4. Parses the response into ExtractedFacts
    5. Saves facts with confidence scores and provenance

    Per spec: AI proposes; humans approve.
    """
    # TODO: Implement extraction job execution
    return {
        "job_id": job_id,
        "status": "not_implemented",
        "facts_extracted": 0,
    }


@celery_app.task(bind=True, name="munipal.workers.tasks.extraction_tasks.extract_from_chunk")
def extract_from_chunk(
    self,
    project_id: str,
    chunk_id: str,
    extractor_id: str,
    target_paths: list[str],
) -> dict:
    """
    Extract facts from a single chunk using a specific extractor.

    Per spec: Extractors are idempotent - re-running produces identical results.
    """
    # TODO: Implement single-chunk extraction
    return {
        "chunk_id": chunk_id,
        "extractor_id": extractor_id,
        "status": "not_implemented",
        "facts_extracted": 0,
    }


@celery_app.task(bind=True, name="munipal.workers.tasks.extraction_tasks.batch_extract")
def batch_extract(
    self,
    project_id: str,
    artifact_ids: list[str],
    extractor_ids: list[str] | None = None,
) -> dict:
    """
    Run all relevant extractors on a batch of artifacts.

    If extractor_ids is None, runs all extractors defined in the project's playbook.
    """
    # TODO: Implement batch extraction
    return {
        "project_id": project_id,
        "artifact_count": len(artifact_ids),
        "status": "not_implemented",
        "jobs_created": 0,
    }
