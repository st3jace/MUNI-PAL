"""
Artifact and Chunk schemas.

Per spec:
- Artifact: Any user-supplied input (docs, spreadsheets, images)
- Chunk: Immutable evidence units (page-based for PDFs, sheet-based for Excel)
"""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from munipal.core.schemas.base import (
    ArtifactType,
    BaseSchema,
    ChunkType,
    TimestampSchema,
    UUIDSchema,
)


# -----------------------------------------------------------------------------
# Artifact Schemas
# -----------------------------------------------------------------------------


class ArtifactBase(BaseSchema):
    """Base artifact fields."""

    filename: str = Field(..., min_length=1, max_length=255)
    display_name: str | None = Field(None, max_length=255)
    artifact_type: ArtifactType
    mime_type: str = Field(..., max_length=100)
    file_size_bytes: int = Field(..., ge=0)


class ArtifactCreate(BaseSchema):
    """Schema for artifact creation (internal use after upload)."""

    project_id: UUID
    filename: str
    display_name: str | None = None
    artifact_type: ArtifactType
    mime_type: str
    file_size_bytes: int
    storage_path: str  # Path in local storage or S3 key


class ArtifactRead(ArtifactBase, UUIDSchema, TimestampSchema):
    """Schema for reading an artifact."""

    project_id: UUID
    storage_path: str

    # Processing status (chunking)
    is_processed: bool = False
    chunk_count: int = 0
    processing_error: str | None = None

    # Extraction status (fact extraction)
    is_extracted: bool = False
    last_extraction_job_id: UUID | None = None


class ArtifactSummary(UUIDSchema):
    """Minimal artifact summary for listings."""

    filename: str
    display_name: str | None = None
    artifact_type: ArtifactType
    is_processed: bool
    is_extracted: bool = False
    chunk_count: int
    created_at: datetime


# -----------------------------------------------------------------------------
# Chunk Schemas
# -----------------------------------------------------------------------------


class ChunkBase(BaseSchema):
    """
    Base chunk fields.

    Per spec: Chunks are IMMUTABLE after creation.
    """

    chunk_type: ChunkType
    sequence_number: int = Field(..., ge=0, description="Order within artifact")

    # Location metadata
    page_number: int | None = Field(None, ge=1)
    sheet_name: str | None = None
    section_title: str | None = None

    # Content
    text_content: str | None = Field(None, description="Extracted text content")
    has_image: bool = False


class ChunkCreate(ChunkBase):
    """Schema for chunk creation (internal use during processing)."""

    artifact_id: UUID
    content_hash: str = Field(..., description="SHA-256 hash of content for deduplication")


class ChunkRead(ChunkBase, UUIDSchema, TimestampSchema):
    """Schema for reading a chunk."""

    artifact_id: UUID
    content_hash: str

    # Extraction status
    facts_extracted: int = 0


class ChunkSummary(UUIDSchema):
    """Minimal chunk summary."""

    chunk_type: ChunkType
    sequence_number: int
    page_number: int | None
    sheet_name: str | None
    facts_extracted: int
