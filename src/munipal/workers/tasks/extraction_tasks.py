"""
AI extraction tasks.

Per spec (WP3): AI Pipelines & Review
- Propose facts via schema-driven extraction
- Enable human review & approval
- Maintain confidence scores and provenance
"""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from munipal.core.models import (
    Artifact,
    Chunk,
    ExtractionJob,
    ExtractedFact,
    FactChunkAssociation,
    Playbook,
    Project,
)
from munipal.db.session import get_sync_session
from munipal.services.extraction.extractor import BatchExtractor, FactExtractor
from munipal.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


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
    logger.info(f"Running extraction job: {job_id}")

    session = get_sync_session()
    try:
        # Get the extraction job
        job = session.get(ExtractionJob, job_id)
        if not job:
            logger.error(f"Extraction job not found: {job_id}")
            return {
                "job_id": job_id,
                "status": "error",
                "error": "Job not found",
                "facts_extracted": 0,
            }

        # Update job status
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        session.commit()

        # Get project and playbook
        project = session.get(Project, job.project_id)
        if not project:
            job.status = "failed"
            job.error_message = "Project not found"
            session.commit()
            return {"job_id": job_id, "status": "error", "error": "Project not found"}

        playbook = session.get(Playbook, project.playbook_id)
        if not playbook:
            job.status = "failed"
            job.error_message = "Playbook not found"
            session.commit()
            return {"job_id": job_id, "status": "error", "error": "Playbook not found"}

        # Get chunks to process
        artifact_ids = job.artifact_ids or []
        chunk_ids = job.chunk_ids

        if chunk_ids:
            # Process specific chunks
            chunks = session.query(Chunk).filter(Chunk.id.in_(chunk_ids)).all()
        else:
            # Process all chunks from specified artifacts
            chunks = (
                session.query(Chunk)
                .filter(Chunk.artifact_id.in_(artifact_ids))
                .order_by(Chunk.sequence_number)
                .all()
            )

        job.total_chunks = len(chunks)
        session.commit()

        if not chunks:
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            job.error_message = "No chunks to process"
            session.commit()
            return {
                "job_id": job_id,
                "status": "completed",
                "facts_extracted": 0,
                "message": "No chunks found",
            }

        # Prepare chunk data for extraction
        chunk_data = [
            {
                "id": chunk.id,
                "text_content": chunk.text_content,
                "page_number": chunk.page_number,
                "sheet_name": chunk.sheet_name,
            }
            for chunk in chunks
        ]

        # Get extractors to run
        extractors = playbook.extractors or []
        target_paths = job.target_schema_paths

        # Filter extractors if specific paths are requested
        if target_paths:
            extractors = [
                e for e in extractors
                if any(p in e.get("target_schema_paths", []) for p in target_paths)
            ]

        if not extractors:
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            session.commit()
            return {
                "job_id": job_id,
                "status": "completed",
                "facts_extracted": 0,
                "message": "No applicable extractors",
            }

        # Run extraction
        try:
            batch_extractor = BatchExtractor()
            results = batch_extractor.extract_from_artifact(
                artifact_chunks=chunk_data,
                playbook_config={
                    "extractors": extractors,
                    "schema_paths": playbook.schema_paths or [],
                },
            )
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            session.commit()
            return {
                "job_id": job_id,
                "status": "error",
                "error": str(e),
                "facts_extracted": 0,
            }

        # Save extracted facts
        facts_created = 0
        for fact_data in results.get("facts", []):
            fact = create_fact_from_extraction(
                session=session,
                project_id=job.project_id,
                job_id=job_id,
                fact_data=fact_data,
                chunk_data=chunk_data,
            )
            if fact:
                session.add(fact)
                facts_created += 1

        # Update job status
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.facts_extracted = facts_created
        job.processed_chunks = len(chunks)
        session.commit()

        logger.info(f"Extraction job {job_id} completed: {facts_created} facts")

        return {
            "job_id": job_id,
            "status": "completed",
            "facts_extracted": facts_created,
            "summary": results.get("summary", {}),
        }

    except Exception as e:
        logger.error(f"Unexpected error in extraction job {job_id}: {e}")
        session.rollback()

        # Try to update job status
        try:
            job = session.get(ExtractionJob, job_id)
            if job:
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.now(timezone.utc)
                session.commit()
        except Exception:
            pass

        return {
            "job_id": job_id,
            "status": "error",
            "error": str(e),
            "facts_extracted": 0,
        }
    finally:
        session.close()


def create_fact_from_extraction(
    session,
    project_id: str,
    job_id: str,
    fact_data: dict,
    chunk_data: list[dict],
) -> ExtractedFact | None:
    """Create an ExtractedFact from extraction results."""
    schema_path = fact_data.get("schema_path")
    if not schema_path:
        return None

    # Determine criticality from schema path
    # (In a full implementation, this would look up from playbook)
    criticality = "secondary"
    if "cab." in schema_path or "slb." in schema_path or "finmodel." in schema_path:
        criticality = "critical"
    elif "revenue." in schema_path or "feedstock." in schema_path:
        criticality = "material"

    fact = ExtractedFact(
        id=str(uuid4()),
        project_id=project_id,
        extraction_job_id=job_id,
        schema_path=schema_path,
        criticality=criticality,
        value={"extracted": fact_data.get("value")},
        value_type=fact_data.get("value_type", "string"),
        unit=fact_data.get("unit"),
        confidence_score=fact_data.get("confidence_score", 0.5),
        confidence_rationale=fact_data.get("confidence_rationale"),
        review_status="pending",
    )

    # Link to source chunk if we have a source quote
    source_quote = fact_data.get("source_quote")
    if source_quote and chunk_data:
        # Find the chunk containing this quote (simplified: use first chunk)
        # In production, would search for the chunk containing the quote
        chunk_id = chunk_data[0].get("id")
        if chunk_id:
            association = FactChunkAssociation(
                fact_id=fact.id,
                chunk_id=str(chunk_id),
                excerpt=source_quote[:500] if source_quote else None,
            )
            session.add(association)

    return fact


@celery_app.task(bind=True, name="munipal.workers.tasks.extraction_tasks.extract_from_artifact")
def extract_from_artifact(
    self,
    project_id: str,
    artifact_id: str,
    extractor_ids: list[str] | None = None,
) -> dict:
    """
    Create and run an extraction job for an artifact.

    Convenience task that creates an ExtractionJob and processes it.
    """
    logger.info(f"Creating extraction job for artifact {artifact_id}")

    session = get_sync_session()
    try:
        # Verify artifact exists and is processed
        artifact = session.get(Artifact, artifact_id)
        if not artifact:
            return {
                "artifact_id": artifact_id,
                "status": "error",
                "error": "Artifact not found",
            }

        if not artifact.is_processed:
            return {
                "artifact_id": artifact_id,
                "status": "error",
                "error": "Artifact not yet processed into chunks",
            }

        # Create extraction job
        job = ExtractionJob(
            id=str(uuid4()),
            project_id=project_id,
            job_type="artifact_extraction",
            artifact_ids=[artifact_id],
            status="queued",
        )
        session.add(job)
        session.commit()

        job_id = job.id
        session.close()

        # Run the job
        return run_extraction_job(job_id)

    except Exception as e:
        logger.error(f"Error creating extraction job: {e}")
        session.rollback()
        session.close()
        return {
            "artifact_id": artifact_id,
            "status": "error",
            "error": str(e),
        }


@celery_app.task(bind=True, name="munipal.workers.tasks.extraction_tasks.batch_extract")
def batch_extract(
    self,
    project_id: str,
    artifact_ids: list[str],
    extractor_ids: list[str] | None = None,
) -> dict:
    """
    Run extraction on multiple artifacts.

    Creates a single extraction job covering all artifacts.
    """
    logger.info(f"Batch extraction for {len(artifact_ids)} artifacts in project {project_id}")

    session = get_sync_session()
    try:
        # Create extraction job
        job = ExtractionJob(
            id=str(uuid4()),
            project_id=project_id,
            job_type="batch_extraction",
            artifact_ids=artifact_ids,
            status="queued",
        )
        session.add(job)
        session.commit()

        job_id = job.id
        session.close()

        # Run the job
        return run_extraction_job(job_id)

    except Exception as e:
        logger.error(f"Error in batch extraction: {e}")
        session.rollback()
        session.close()
        return {
            "project_id": project_id,
            "artifact_count": len(artifact_ids),
            "status": "error",
            "error": str(e),
        }
