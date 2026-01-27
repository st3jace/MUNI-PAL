"""
ExtractionJob schemas.

Per spec: ExtractionJob is the async wrapper for AI and parsing work.
Jobs are processed by Celery workers and track extraction progress.
"""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from munipal.core.schemas.base import BaseSchema, JobStatus, TimestampSchema, UUIDSchema


class ExtractionJobBase(BaseSchema):
    """Base extraction job fields."""

    job_type: str = Field(
        ...,
        description="Type of extraction (e.g., 'project_description', 'cab_terms', 'slb_metrics')",
    )
    target_schema_paths: list[str] = Field(
        default_factory=list,
        description="Schema paths this job targets for extraction",
    )


class ExtractionJobCreate(ExtractionJobBase):
    """Schema for creating an extraction job."""

    project_id: UUID
    artifact_ids: list[UUID] = Field(
        ...,
        min_length=1,
        description="Artifacts to extract from",
    )
    chunk_ids: list[UUID] | None = Field(
        None,
        description="Specific chunks to process (if None, process all chunks in artifacts)",
    )


class ExtractionJobRead(ExtractionJobBase, UUIDSchema, TimestampSchema):
    """Schema for reading an extraction job."""

    project_id: UUID
    artifact_ids: list[UUID]
    chunk_ids: list[UUID] | None

    # Status tracking
    status: JobStatus = JobStatus.QUEUED
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Progress
    total_chunks: int = 0
    processed_chunks: int = 0
    facts_extracted: int = 0

    # Error handling
    error_message: str | None = None
    retry_count: int = 0


class ExtractionJobSummary(UUIDSchema):
    """Minimal job summary for listings."""

    job_type: str
    status: JobStatus
    facts_extracted: int
    created_at: datetime
    completed_at: datetime | None


class ExtractionProgress(BaseSchema):
    """Real-time progress update for an extraction job."""

    job_id: UUID
    status: JobStatus
    total_chunks: int
    processed_chunks: int
    facts_extracted: int
    current_chunk_id: UUID | None = None
    estimated_remaining_seconds: int | None = None
