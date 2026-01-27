"""
Artifact management endpoints.

Per spec: Artifact is any user-supplied input (documents, spreadsheets, images).
Artifacts are normalized into immutable Chunks with preserved provenance.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.db.session import get_async_session

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


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_artifact(
    project_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Upload an artifact to a project.

    Accepts PDFs, Word docs, Excel files, CSVs, and images.
    Returns immediately with artifact ID; chunking happens async via Celery.

    Per spec: "Artifacts land in the vault; chunks are created async."
    """
    # Validate file type
    content_type = file.content_type or ""
    if content_type not in SUPPORTED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {content_type}. Supported types: {list(SUPPORTED_MIME_TYPES.keys())}",
        )

    # TODO: Implement artifact upload
    # 1. Save file to storage (local or S3)
    # 2. Create artifact record in database
    # 3. Dispatch Celery task for chunking
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Artifact upload not yet implemented",
    )


@router.get("/")
async def list_artifacts(
    project_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """List all artifacts for a project."""
    # TODO: Implement artifact listing
    return {"artifacts": [], "total": 0}


@router.get("/{artifact_id}")
async def get_artifact(
    artifact_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Get artifact metadata and chunk information."""
    # TODO: Implement artifact retrieval
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Artifact {artifact_id} not found",
    )


@router.get("/{artifact_id}/chunks")
async def list_artifact_chunks(
    artifact_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    List all chunks for an artifact.

    Per spec: Chunks are immutable evidence units (page-based for PDFs,
    sheet-based for Excel).
    """
    # TODO: Implement chunk listing
    return {"chunks": [], "total": 0}


@router.delete("/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artifact(
    artifact_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> None:
    """
    Delete an artifact.

    Per spec: Deleting an artifact orphans any ExtractedFacts that cite it,
    but does not delete those facts (they become unverifiable).
    """
    # TODO: Implement artifact deletion
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Artifact deletion not yet implemented",
    )
