"""
Artifact service - handles file uploads, storage, and management.

Per spec (WP2): Artifact Vault & Ingestion
- Accept messy inputs
- Normalize into immutable chunks
- Preserve provenance
"""

import hashlib
import os
import shutil
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.config import get_settings
from munipal.core.models import Artifact, Chunk, Project
from munipal.core.schemas.artifact import ArtifactRead, ArtifactSummary, ChunkRead
from munipal.core.schemas.base import ArtifactType

settings = get_settings()

# MIME type to artifact type mapping
MIME_TYPE_MAP = {
    "application/pdf": ArtifactType.PDF,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ArtifactType.DOCX,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ArtifactType.XLSX,
    "application/vnd.ms-excel": ArtifactType.XLS,
    "text/plain": ArtifactType.TXT,
    "text/csv": ArtifactType.CSV,
    "image/png": ArtifactType.PNG,
    "image/jpeg": ArtifactType.JPEG,
}


class ArtifactService:
    """Service for artifact management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage_path = Path(settings.artifact_storage_path)
        self._ensure_storage_exists()

    def _ensure_storage_exists(self):
        """Create storage directory if it doesn't exist."""
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def upload(
        self,
        project_id: UUID,
        file: UploadFile,
        display_name: str | None = None,
    ) -> ArtifactRead:
        """
        Upload and store an artifact.

        Returns the artifact record. Chunking happens async via Celery.
        """
        # Validate project exists
        project = await self.db.get(Project, str(project_id))
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Validate and map MIME type
        content_type = file.content_type or "application/octet-stream"
        if content_type not in MIME_TYPE_MAP:
            raise ValueError(f"Unsupported file type: {content_type}")

        artifact_type = MIME_TYPE_MAP[content_type]

        # Generate storage path
        artifact_id = str(uuid4())
        file_ext = Path(file.filename or "file").suffix
        storage_filename = f"{artifact_id}{file_ext}"
        project_storage_dir = self.storage_path / str(project_id)
        project_storage_dir.mkdir(parents=True, exist_ok=True)
        storage_file_path = project_storage_dir / storage_filename

        # Save file to storage
        file_size = 0
        try:
            with open(storage_file_path, "wb") as buffer:
                while chunk := await file.read(8192):
                    buffer.write(chunk)
                    file_size += len(chunk)
        except Exception as e:
            # Clean up on failure
            if storage_file_path.exists():
                storage_file_path.unlink()
            raise ValueError(f"Failed to save file: {e}")

        # Create artifact record
        artifact = Artifact(
            id=artifact_id,
            project_id=str(project_id),
            filename=file.filename or "unknown",
            display_name=display_name or file.filename,
            artifact_type=artifact_type.value,
            mime_type=content_type,
            file_size_bytes=file_size,
            storage_path=str(storage_file_path.relative_to(self.storage_path)),
            is_processed=False,
        )

        self.db.add(artifact)
        await self.db.flush()
        await self.db.refresh(artifact)

        # TODO: Dispatch Celery task for chunking
        # from munipal.workers.tasks.artifact_tasks import process_artifact
        # process_artifact.delay(artifact_id)

        return self._to_read_schema(artifact)

    async def get(self, artifact_id: UUID) -> ArtifactRead | None:
        """Get an artifact by ID."""
        artifact = await self.db.get(Artifact, str(artifact_id))
        if not artifact:
            return None
        return self._to_read_schema(artifact)

    async def list_for_project(
        self,
        project_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ArtifactSummary], int]:
        """List artifacts for a project with pagination."""
        # Count total
        count_result = await self.db.execute(
            select(func.count(Artifact.id)).where(Artifact.project_id == str(project_id))
        )
        total = count_result.scalar() or 0

        # Get paginated results
        result = await self.db.execute(
            select(Artifact)
            .where(Artifact.project_id == str(project_id))
            .order_by(Artifact.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        artifacts = result.scalars().all()

        summaries = []
        for artifact in artifacts:
            chunk_count = await self._count_chunks(artifact.id)
            summaries.append(
                ArtifactSummary(
                    id=UUID(artifact.id),
                    filename=artifact.filename,
                    artifact_type=ArtifactType(artifact.artifact_type),
                    is_processed=artifact.is_processed,
                    chunk_count=chunk_count,
                    created_at=artifact.created_at,
                )
            )

        return summaries, total

    async def get_chunks(
        self,
        artifact_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[ChunkRead], int]:
        """Get chunks for an artifact."""
        # Verify artifact exists
        artifact = await self.db.get(Artifact, str(artifact_id))
        if not artifact:
            raise ValueError(f"Artifact {artifact_id} not found")

        # Count total
        count_result = await self.db.execute(
            select(func.count(Chunk.id)).where(Chunk.artifact_id == str(artifact_id))
        )
        total = count_result.scalar() or 0

        # Get chunks
        result = await self.db.execute(
            select(Chunk)
            .where(Chunk.artifact_id == str(artifact_id))
            .order_by(Chunk.sequence_number)
            .offset(skip)
            .limit(limit)
        )
        chunks = result.scalars().all()

        return [self._chunk_to_read_schema(c) for c in chunks], total

    async def delete(self, artifact_id: UUID) -> bool:
        """
        Delete an artifact and its file.

        Per spec: Deleting an artifact orphans any ExtractedFacts that cite it,
        but does not delete those facts (they become unverifiable).
        """
        artifact = await self.db.get(Artifact, str(artifact_id))
        if not artifact:
            return False

        # Delete file from storage
        full_path = self.storage_path / artifact.storage_path
        if full_path.exists():
            full_path.unlink()

        # Delete database record (cascade deletes chunks)
        await self.db.delete(artifact)
        return True

    async def mark_processed(
        self,
        artifact_id: str,
        success: bool = True,
        error_message: str | None = None,
    ):
        """Mark an artifact as processed (called by Celery worker)."""
        artifact = await self.db.get(Artifact, artifact_id)
        if artifact:
            artifact.is_processed = success
            artifact.processing_error = error_message if not success else None
            await self.db.flush()

    async def _count_chunks(self, artifact_id: str) -> int:
        """Count chunks for an artifact."""
        result = await self.db.execute(
            select(func.count(Chunk.id)).where(Chunk.artifact_id == artifact_id)
        )
        return result.scalar() or 0

    def _to_read_schema(self, artifact: Artifact) -> ArtifactRead:
        """Convert artifact model to read schema."""
        return ArtifactRead(
            id=UUID(artifact.id),
            project_id=UUID(artifact.project_id),
            filename=artifact.filename,
            display_name=artifact.display_name,
            artifact_type=ArtifactType(artifact.artifact_type),
            mime_type=artifact.mime_type,
            file_size_bytes=artifact.file_size_bytes,
            storage_path=artifact.storage_path,
            is_processed=artifact.is_processed,
            chunk_count=0,  # Will be computed if needed
            processing_error=artifact.processing_error,
            created_at=artifact.created_at,
            updated_at=artifact.updated_at,
        )

    def _chunk_to_read_schema(self, chunk: Chunk) -> ChunkRead:
        """Convert chunk model to read schema."""
        from munipal.core.schemas.base import ChunkType

        return ChunkRead(
            id=UUID(chunk.id),
            artifact_id=UUID(chunk.artifact_id),
            chunk_type=ChunkType(chunk.chunk_type),
            sequence_number=chunk.sequence_number,
            page_number=chunk.page_number,
            sheet_name=chunk.sheet_name,
            section_title=chunk.section_title,
            text_content=chunk.text_content,
            content_hash=chunk.content_hash,
            has_image=chunk.has_image,
            facts_extracted=0,  # Will be computed if needed
            created_at=chunk.created_at,
            updated_at=chunk.updated_at,
        )
