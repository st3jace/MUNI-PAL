"""
Extraction job management endpoints.

Per spec (WP3): AI Pipelines & Review
- Trigger extraction jobs
- Monitor extraction progress
- View extraction results
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from munipal.api.dependencies import AuthenticatedUserId, DbSession, require_roles
from munipal.core.models import Artifact, ExtractionJob, Project
from munipal.services.authorization_service import AuthorizationService

router = APIRouter()


class ExtractionRequest(BaseModel):
    """Request to create an extraction job."""

    project_id: UUID
    artifact_ids: list[UUID] = Field(..., min_length=1)
    target_schema_paths: list[str] | None = Field(
        None,
        description="Optional: specific schema paths to extract. If None, extracts all.",
    )


class ExtractionResponse(BaseModel):
    """Response from extraction job creation."""

    job_id: str
    status: str
    message: str


@router.post("/", response_model=ExtractionResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_extraction_job(
    request: ExtractionRequest,
    db: DbSession,
    user_id: AuthenticatedUserId,
    _: str = Depends(require_roles("admin", "analyst")),
) -> ExtractionResponse:
    """
    Create and queue an extraction job.

    The job will process the specified artifacts and extract facts
    using the project's playbook extractors.

    Returns immediately - use GET /extraction/{job_id} to check status.
    """
    authz = AuthorizationService(db)
    await authz.require_project_write(user_id, request.project_id)

    from uuid import uuid4

    # Verify project exists
    project = await db.get(Project, str(request.project_id))
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {request.project_id} not found",
        )

    # Verify all artifacts exist and belong to project
    artifact_ids_str = [str(aid) for aid in request.artifact_ids]
    for artifact_id in artifact_ids_str:
        await authz.require_artifact_read(user_id, UUID(artifact_id))
        artifact = await db.get(Artifact, artifact_id)
        if not artifact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact {artifact_id} not found",
            )
        if artifact.project_id != str(request.project_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Artifact {artifact_id} does not belong to project {request.project_id}",
            )
        if not artifact.is_processed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Artifact {artifact_id} has not been processed into chunks yet",
            )

    # Create extraction job
    job = ExtractionJob(
        id=str(uuid4()),
        project_id=str(request.project_id),
        job_type="api_extraction",
        artifact_ids=artifact_ids_str,
        target_schema_paths=request.target_schema_paths or [],
        status="queued",
    )
    db.add(job)
    await db.flush()

    # Queue Celery task
    # Note: In production, this would dispatch to Celery
    # from munipal.workers.tasks.extraction_tasks import run_extraction_job
    # run_extraction_job.delay(job.id)

    return ExtractionResponse(
        job_id=job.id,
        status="queued",
        message=f"Extraction job created for {len(request.artifact_ids)} artifact(s). Processing will begin shortly.",
    )


@router.post("/{job_id}/run", response_model=dict, status_code=status.HTTP_200_OK)
async def run_extraction_job(
    job_id: UUID,
    db: DbSession,
    user_id: AuthenticatedUserId,
    _: str = Depends(require_roles("admin", "analyst")),
) -> dict:
    """
    Run an extraction job synchronously.

    This endpoint is for development mode - in production, extraction
    runs asynchronously via Celery workers.

    Processes all artifacts in the job, extracts facts using Claude,
    and saves them to the database.
    """
    authz = AuthorizationService(db)
    await authz.require_extraction_job_write(user_id, job_id)

    import logging
    from datetime import datetime, timezone
    from uuid import uuid4 as gen_uuid4

    from sqlalchemy import select

    from munipal.core.models import Chunk
    from munipal.core.models.fact import ExtractedFact, FactChunkAssociation
    from munipal.services.extraction.anthropic_client import AnthropicClient
    from munipal.services.fact_service import FactService
    from munipal.services.playbook_data import EXTRACTORS, SCHEMA_PATHS

    logger = logging.getLogger(__name__)

    job = await db.get(ExtractionJob, str(job_id))
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extraction job {job_id} not found",
        )

    if job.status == "completed":
        return {
            "job_id": job.id,
            "status": "completed",
            "message": "Job already completed",
            "facts_extracted": job.facts_extracted,
        }

    # Update job status
    job.status = "running"
    job.started_at = datetime.now(timezone.utc)
    await db.flush()

    try:
        # Initialize Anthropic client
        client = AnthropicClient()

        total_facts = 0
        total_chunks = 0
        touched_schema_paths: set[str] = set()

        # Process each artifact
        for artifact_id in job.artifact_ids:
            artifact = await db.get(Artifact, artifact_id)
            if not artifact:
                continue

            # Get chunks for this artifact
            result = await db.execute(
                select(Chunk)
                .where(Chunk.artifact_id == artifact_id)
                .order_by(Chunk.sequence_number)
            )
            chunks = result.scalars().all()
            total_chunks += len(chunks)

            # Skip if no chunks
            if not chunks:
                continue

            # Combine chunk content for extraction
            combined_content = "\n\n---PAGE BREAK---\n\n".join(
                f"[Page {c.page_number or c.sequence_number + 1}]\n{c.text_content}"
                for c in chunks if c.text_content
            )

            if not combined_content.strip():
                continue

            # Run each extractor
            for extractor in EXTRACTORS:
                extractor_id = extractor.get("extractor_id", "unknown")
                target_paths = extractor.get("target_schema_paths", [])
                system_prompt = extractor.get("system_prompt", "Extract facts from the document.")
                prompt_template = extractor.get(
                    "extraction_prompt_template",
                    "Extract facts from:\n\n{content}"
                )

                try:
                    user_prompt = prompt_template.format(content=combined_content[:50000])  # Limit content size

                    # Call Claude API
                    response = client.extract_with_schema(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        schema_paths=target_paths,
                    )

                    # Process extracted facts
                    facts_data = response.get("facts", [])
                    for fact_data in facts_data:
                        schema_path = fact_data.get("schema_path")
                        if not schema_path:
                            continue

                        # Find criticality from schema paths
                        criticality = "secondary"
                        for sp in SCHEMA_PATHS:
                            if sp["path"] == schema_path:
                                criticality = sp.get("criticality", "secondary")
                                break

                        # Create fact record
                        fact = ExtractedFact(
                            id=str(gen_uuid4()),
                            schema_path=schema_path,
                            criticality=criticality,
                            value=fact_data.get("value"),
                            value_type=fact_data.get("value_type", "string"),
                            unit=fact_data.get("unit"),
                            confidence_score=fact_data.get("confidence", 0.7),
                            confidence_rationale=fact_data.get("confidence_rationale"),
                            project_id=job.project_id,
                            extraction_job_id=job.id,
                            review_status="pending",
                            lifecycle_state="pending_review",
                        )
                        db.add(fact)
                        await db.flush()
                        touched_schema_paths.add(schema_path)

                        # Link fact to source chunk (use first chunk as primary source)
                        source_quote = fact_data.get("source_quote", "")
                        assoc = FactChunkAssociation(
                            fact_id=fact.id,
                            chunk_id=chunks[0].id,
                            excerpt=source_quote[:500] if source_quote else None,
                        )
                        db.add(assoc)

                        total_facts += 1

                    logger.info(f"Extractor {extractor_id} extracted {len(facts_data)} facts")

                except Exception as e:
                    logger.error(f"Extractor {extractor_id} failed: {e}")
                    continue

        fact_service = FactService(db)
        for schema_path in touched_schema_paths:
            await fact_service.refresh_canonicalization_for_path(
                job.project_id,
                schema_path,
                actor_id=user_id,
                reason="extraction_ingest",
                source_action="run_extraction_job",
            )

        # Update job completion
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.facts_extracted = total_facts
        job.total_chunks = total_chunks
        job.processed_chunks = total_chunks

        # Mark artifacts as extracted
        for artifact_id in job.artifact_ids:
            artifact = await db.get(Artifact, artifact_id)
            if artifact:
                artifact.is_extracted = True
                artifact.last_extraction_job_id = job.id

        await db.flush()

        return {
            "job_id": job.id,
            "status": "completed",
            "message": f"Extracted {total_facts} facts from {total_chunks} chunks",
            "facts_extracted": total_facts,
            "total_chunks": total_chunks,
        }

    except Exception as e:
        logger.error(f"Extraction job {job_id} failed: {e}")
        job.status = "failed"
        job.error_message = str(e)
        await db.flush()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failed: {e}",
        )


@router.get("/{job_id}")
async def get_extraction_job(
    job_id: UUID,
    db: DbSession,
    user_id: AuthenticatedUserId,
    _: str = Depends(require_roles("admin", "analyst", "viewer")),
) -> dict:
    """
    Get the status and details of an extraction job.
    """
    authz = AuthorizationService(db)
    await authz.require_extraction_job_read(user_id, job_id)

    job = await db.get(ExtractionJob, str(job_id))
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extraction job {job_id} not found",
        )

    return {
        "id": job.id,
        "project_id": job.project_id,
        "job_type": job.job_type,
        "status": job.status,
        "artifact_ids": job.artifact_ids,
        "target_schema_paths": job.target_schema_paths,
        "total_chunks": job.total_chunks,
        "processed_chunks": job.processed_chunks,
        "facts_extracted": job.facts_extracted,
        "error_message": job.error_message,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "created_at": job.created_at.isoformat(),
    }


@router.get("/")
async def list_extraction_jobs(
    db: DbSession,
    user_id: AuthenticatedUserId,
    project_id: UUID,
    status_filter: str | None = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _: str = Depends(require_roles("admin", "analyst", "viewer")),
) -> dict:
    """
    List extraction jobs for a project.
    """
    authz = AuthorizationService(db)
    await authz.require_project_read(user_id, project_id)

    from sqlalchemy import func, select

    # Base query
    query = select(ExtractionJob).where(ExtractionJob.project_id == str(project_id))
    count_query = select(func.count(ExtractionJob.id)).where(
        ExtractionJob.project_id == str(project_id)
    )

    if status_filter:
        query = query.where(ExtractionJob.status == status_filter)
        count_query = count_query.where(ExtractionJob.status == status_filter)

    # Get total count
    total = (await db.execute(count_query)).scalar() or 0

    # Get paginated results
    query = query.order_by(ExtractionJob.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    jobs = result.scalars().all()

    return {
        "jobs": [
            {
                "id": job.id,
                "job_type": job.job_type,
                "status": job.status,
                "facts_extracted": job.facts_extracted,
                "created_at": job.created_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            }
            for job in jobs
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/{job_id}/retry", response_model=ExtractionResponse)
async def retry_extraction_job(
    job_id: UUID,
    db: DbSession,
    user_id: AuthenticatedUserId,
    _: str = Depends(require_roles("admin", "analyst")),
) -> ExtractionResponse:
    """
    Retry a failed extraction job.
    """
    authz = AuthorizationService(db)
    await authz.require_extraction_job_write(user_id, job_id)

    job = await db.get(ExtractionJob, str(job_id))
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extraction job {job_id} not found",
        )

    if job.status not in ("failed", "error"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is in status '{job.status}', can only retry failed jobs",
        )

    # Reset job status
    job.status = "queued"
    job.error_message = None
    job.retry_count = (job.retry_count or 0) + 1
    await db.flush()

    # Queue Celery task
    # from munipal.workers.tasks.extraction_tasks import run_extraction_job
    # run_extraction_job.delay(job.id)

    return ExtractionResponse(
        job_id=job.id,
        status="queued",
        message=f"Extraction job queued for retry (attempt {job.retry_count + 1})",
    )
