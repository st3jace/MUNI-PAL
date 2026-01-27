"""
Artifact management endpoints.

Per spec: Artifact is any user-supplied input (documents, spreadsheets, images).
Artifacts are normalized into immutable Chunks with preserved provenance.
"""

from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status

from munipal.api.dependencies import AuthenticatedUserId, DbSession
from munipal.core.schemas.artifact import ArtifactRead, ArtifactSummary, ChunkRead
from munipal.services.artifact_service import ArtifactService

router = APIRouter()

# Supported file types for artifact upload
SUPPORTED_MIME_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/vnd.ms-excel": "xls",
    "text/plain": "txt",
    "text/csv": "csv",
    "image/png": "png",
    "image/jpeg": "jpeg",
}


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED, response_model=ArtifactRead)
async def upload_artifact(
    db: DbSession,
    user_id: AuthenticatedUserId,
    project_id: UUID = Form(...),
    display_name: str | None = Form(None),
    file: UploadFile = File(...),
) -> ArtifactRead:
    """
    Upload an artifact to a project.

    Accepts PDFs, Word docs, Excel files, CSVs, and images.
    Returns immediately with artifact ID; chunking happens async via Celery.

    Per spec: "Artifacts land in the vault; chunks are created async."

    Supported file types:
    - PDF (.pdf)
    - Word documents (.docx)
    - Excel files (.xlsx, .xls)
    - CSV (.csv)
    - Plain text (.txt)
    - Images (.png, .jpeg)
    """
    # Validate file type
    content_type = file.content_type or ""
    if content_type not in SUPPORTED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {content_type}. Supported types: {list(SUPPORTED_MIME_TYPES.keys())}",
        )

    service = ArtifactService(db)

    try:
        artifact = await service.upload(
            project_id=project_id,
            file=file,
            display_name=display_name,
        )
        return artifact
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/", response_model=dict)
async def list_artifacts(
    db: DbSession,
    user_id: AuthenticatedUserId,
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> dict:
    """List all artifacts for a project."""
    service = ArtifactService(db)
    artifacts, total = await service.list_for_project(
        project_id=project_id,
        skip=skip,
        limit=limit,
    )

    return {
        "artifacts": [a.model_dump() for a in artifacts],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{artifact_id}", response_model=ArtifactRead)
async def get_artifact(
    artifact_id: UUID,
    db: DbSession,
    user_id: AuthenticatedUserId,
) -> ArtifactRead:
    """Get artifact metadata and processing status."""
    service = ArtifactService(db)
    artifact = await service.get(artifact_id)

    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact {artifact_id} not found",
        )

    return artifact


@router.get("/{artifact_id}/chunks", response_model=dict)
async def list_artifact_chunks(
    artifact_id: UUID,
    db: DbSession,
    user_id: AuthenticatedUserId,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> dict:
    """
    List all chunks for an artifact.

    Per spec: Chunks are immutable evidence units (page-based for PDFs,
    sheet-based for Excel).
    """
    service = ArtifactService(db)

    try:
        chunks, total = await service.get_chunks(
            artifact_id=artifact_id,
            skip=skip,
            limit=limit,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return {
        "chunks": [c.model_dump() for c in chunks],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.delete("/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artifact(
    artifact_id: UUID,
    db: DbSession,
    user_id: AuthenticatedUserId,
) -> None:
    """
    Delete an artifact.

    Per spec: Deleting an artifact orphans any ExtractedFacts that cite it,
    but does not delete those facts (they become unverifiable).
    """
    service = ArtifactService(db)
    deleted = await service.delete(artifact_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact {artifact_id} not found",
        )


@router.post("/{artifact_id}/process", status_code=status.HTTP_202_ACCEPTED)
async def trigger_processing(
    artifact_id: UUID,
    db: DbSession,
    user_id: AuthenticatedUserId,
) -> dict:
    """
    Manually trigger processing/chunking for an artifact.

    Useful for retrying failed processing or processing artifacts
    that were uploaded before the chunking pipeline was ready.
    """
    service = ArtifactService(db)
    artifact = await service.get(artifact_id)

    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact {artifact_id} not found",
        )

    # TODO: Dispatch Celery task for chunking
    # from munipal.workers.tasks.artifact_tasks import process_artifact
    # task = process_artifact.delay(str(artifact_id))

    return {
        "artifact_id": str(artifact_id),
        "status": "processing_queued",
        "message": "Artifact processing has been queued. Check artifact status for progress.",
        # "task_id": task.id,  # When Celery is connected
    }
