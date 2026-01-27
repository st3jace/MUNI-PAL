"""
Extraction job management endpoints.

Per spec (WP3): AI Pipelines & Review
- Trigger extraction jobs
- Monitor extraction progress
- View extraction results
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from munipal.api.dependencies import AuthenticatedUserId, DbSession
from munipal.core.models import Artifact, ExtractionJob, Project
from munipal.core.schemas.extraction import ExtractionJobRead, ExtractionJobSummary

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
) -> ExtractionResponse:
    """
    Create and queue an extraction job.

    The job will process the specified artifacts and extract facts
    using the project's playbook extractors.

    Returns immediately - use GET /extraction/{job_id} to check status.
    """
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


@router.get("/{job_id}")
async def get_extraction_job(
    job_id: UUID,
    db: DbSession,
    user_id: AuthenticatedUserId,
) -> dict:
    """
    Get the status and details of an extraction job.
    """
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
) -> dict:
    """
    List extraction jobs for a project.
    """
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
) -> ExtractionResponse:
    """
    Retry a failed extraction job.
    """
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
